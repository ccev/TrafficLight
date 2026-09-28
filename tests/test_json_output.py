from __future__ import annotations

import asyncio
import base64
import io
import json
import unittest
from contextlib import redirect_stdout

from trafficlight import protos
from trafficlight.output.json_ import JsonOutput
from trafficlight.proto_utils.proto import Proto, Request


class MessageToJsonTests(unittest.TestCase):
    def test_decoded_request_reports_type_and_dict_data(self) -> None:
        # method 106 = GET_MAP_OBJECTS; empty bytes decode to an all-defaults GetMapObjectsProto.
        obj = Request(106, "").to_json_obj()
        self.assertEqual(obj["type"], "GetMapObjectsProto")
        self.assertTrue(obj["decoded"])
        self.assertIsInstance(obj["data"], dict)
        # No base64 blob — the raw bytes never appear in the JSON object.
        self.assertNotIn("payload", obj)

    def test_unknown_method_falls_back_to_blackbox(self) -> None:
        # Unknown method id => no proto name; still decode the wire bytes generically.
        # field 1 (varint) = 5  ->  b"\x08\x05"
        obj = Request(9_999_999, "CAU=").to_json_obj()
        self.assertIsNone(obj["type"])
        self.assertFalse(obj["decoded"])
        self.assertIsInstance(obj["data"], dict)
        self.assertEqual(obj["data"].get("1"), 5)


class ProtoToJsonTests(unittest.TestCase):
    def test_proxy_rpc_nests_the_inner_decoded_method(self) -> None:
        # method 5012 wraps a real method inside ProxyRequestProto.action + .payload.
        inner_req = protos.GetMapObjectsProto(cell_id=[7]).SerializeToString()
        inner_resp = protos.GetMapObjectsOutProto().SerializeToString()
        outer_req = protos.ProxyRequestProto(action=106, payload=inner_req).SerializeToString()
        outer_resp = protos.ProxyResponseProto(payload=inner_resp).SerializeToString()

        proto = Proto(
            rpc_id=1,
            method_value=5012,
            raw_request=base64.b64encode(outer_req).decode(),
            raw_response=base64.b64encode(outer_resp).decode(),
        )
        obj = proto.to_json_obj()

        self.assertEqual(obj["method"], 5012)
        self.assertEqual(obj["request"]["type"], "ProxyRequestProto")
        self.assertIn("proxy", obj)
        proxy = obj["proxy"]
        self.assertEqual(proxy["method"], 106)
        self.assertEqual(proxy["request"]["type"], "GetMapObjectsProto")
        self.assertEqual(proxy["request"]["data"], {"cell_id": ["7"]})

    def test_non_proxy_rpc_has_no_proxy_key(self) -> None:
        obj = Proto(rpc_id=1, method_value=106, raw_request="", raw_response="").to_json_obj()
        self.assertNotIn("proxy", obj)


class JsonOutputEnvelopeTests(unittest.TestCase):
    def test_add_record_emits_one_jsonl_object_with_rotom_fields(self) -> None:
        proto = Proto(rpc_id=42, method_value=106, raw_request="", raw_response="")
        out = JsonOutput()

        buf = io.StringIO()
        with redirect_stdout(buf):
            asyncio.run(out.add_record(rpc_id=42, rpc_status=1, protos=[proto], rpc_handle=7))

        lines = [ln for ln in buf.getvalue().splitlines() if ln.strip()]
        self.assertEqual(len(lines), 1, "exactly one JSONL record per rpc envelope")
        rec = json.loads(lines[0])

        self.assertEqual(rec["rpc_id"], 42)
        self.assertEqual(rec["rpc_status"], 1)
        self.assertEqual(rec["rpc_handle"], 7)
        self.assertIn("timestamp", rec)

        self.assertEqual(len(rec["protos"]), 1)
        p = rec["protos"][0]
        self.assertEqual(p["method"], 106)
        self.assertEqual(p["method_name"], "METHOD_GET_MAP_OBJECTS")
        self.assertEqual(p["request"]["type"], "GetMapObjectsProto")
        self.assertIn("response", p)


if __name__ == "__main__":
    unittest.main()
