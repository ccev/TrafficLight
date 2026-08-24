from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING

from .base import BaseOutput

if TYPE_CHECKING:
    from trafficlight.proto_utils.proto import Proto


class JsonOutput(BaseOutput):
    """Emit one JSON object per RPC envelope (JSONL) to stdout.

    Same information the `print` output shows, but as machine-readable JSON instead of a rendered
    table — pipe it to a file (`trafficlight run > traffic.jsonl`) and query it with jq/scripts.

    The record mirrors the Rotom-style envelope the receiver ingests (rpc id / status / handle +
    a `protos` list keyed by `method`), except the request/response are the DECODED protos as JSON
    objects — never the raw base64 payloads.
    """

    async def start(self) -> None:
        pass

    async def add_record(self, rpc_id: int, rpc_status: int, protos: list[Proto], rpc_handle: int | None = None) -> None:
        record = {
            "timestamp": datetime.now().isoformat(),
            "rpc_id": rpc_id,
            "rpc_status": rpc_status,
            "rpc_handle": rpc_handle,
            "protos": [proto.to_json_obj() for proto in protos],
        }
        print(json.dumps(record, ensure_ascii=False))
