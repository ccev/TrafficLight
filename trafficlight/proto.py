from __future__ import annotations

import base64
import json
import sys
from typing import TypeVar

from blackboxprotobuf.lib.interface import decode_message, _get_json_writeable_obj
from google.protobuf import text_format
from google.protobuf.message import Message as ProtobufMessage

import protos

MESSAGES = protos.AllTypesAndMessagesResponsesProto.AllMessagesProto.DESCRIPTOR.fields_by_number
RESPONSES = protos.AllTypesAndMessagesResponsesProto.AllResponsesProto.DESCRIPTOR.fields_by_number
METHODS = protos.AllTypesAndMessagesResponsesProto.AllResquestTypesProto.DESCRIPTOR.values_by_number
METHOD_NAMES = protos.AllTypesAndMessagesResponsesProto.AllResquestTypesProto.DESCRIPTOR.values_by_name
MESSAGE_TYPE_TO_ID: dict[str, int] = {m.message_type.name: n for n, m in MESSAGES.items()}

AnyMessage = TypeVar("AnyMessage", bound=ProtobufMessage)


class Message:
    type: str
    messages: RESPONSES | MESSAGES

    raw: str
    name: str | None
    payload: AnyMessage | None = None
    blackbox: dict | None = None

    def __init__(self, method_id: int, raw: str):
        self.raw = raw

        try:
            self.name = self.messages[method_id].message_type.name
        except KeyError:
            self.name = None

        if self.name is not None:
            self.payload = self.decode_proto()
        if self.name is None or self.payload is None:
            self.blackbox = self.decode_blackbox()

    def decode_b64(self):
        try:
            return base64.b64decode(self.raw.rstrip("\0"))
        except TypeError:
            return self.raw

    def decode_proto(self) -> ProtobufMessage | None:
        message = getattr(sys.modules["protos"], self.name)
        try:
            decoded = self.decode_b64()
            return message.FromString(decoded)
        except Exception as e:
            print(f"error decoding {message} with {self.raw}: {e}")
            return None

    def decode_blackbox(self) -> dict:
        decoded = self.decode_b64()

        value, message_type = decode_message(decoded)
        value_cleaned = {}
        _get_json_writeable_obj(value, value_cleaned, False)
        return value_cleaned

    def to_string(self, one_line: bool = True) -> str:
        if self.payload is None:
            indent = None if one_line else 2
            return json.dumps(self.blackbox, ensure_ascii=False, indent=indent)
        else:
            return text_format.MessageToString(self.payload, as_one_line=one_line)


class Request(Message):
    type = "Request"
    messages = MESSAGES


class Respone(Message):
    type = "Response"
    messages = RESPONSES


class Proto:
    rpc_id: int
    method_value: int
    method_name: str | None
    request: Request
    response: Respone
    proxy: Proto | None = None

    def __init__(self, rpc_id: int, method_value: int, raw_request: str, raw_response: str):
        self.rpc_id = rpc_id
        self.method_value = method_value
        self.method_name = self.get_method_name()
        self.request = Request(self.method_value, raw_request)
        self.response = Respone(self.method_value, raw_response)

        if (
            self.method_value == 5012 and self.request.payload is not None and self.response.payload is not None
        ):  # CLIENT_ACTION_PROXY_SOCIAL_ACTION
            self.proxy = Proto(
                rpc_id=rpc_id,
                method_value=self.request.payload.action,
                raw_request=self.request.payload.payload,
                raw_response=self.response.payload.payload,
            )

    @staticmethod
    def get_message_name(messages: dict, value: int) -> str | None:
        try:
            return messages[value].message_type.name

        except KeyError:
            return None

    @staticmethod
    def _get_method_name_basic(value: int) -> str | None:
        name: AnyMessage | None = METHODS.get(value)
        if name is None:
            return None
        return name.name[13:]

    def get_method_name(self):
        name = self._get_method_name_basic(self.method_value)

        if (
            self.method_value not in MESSAGES.keys()
            and self.method_value not in RESPONSES.keys()
            and name.startswith("SOCIAL_ACTION_")
        ):
            # mainly for proxy. trying to map the method name to a message name and get the method id this way

            possible_base_name = "".join(s.title() for s in name[14:].split("_"))
            # i.e. SOCIAL_ACTION_GET_INBOX to GetInbox

            for possible_name in (possible_base_name + "V2Proto", possible_base_name + "Proto"):
                method_value = MESSAGE_TYPE_TO_ID.get(possible_name)
                if method_value is None:
                    continue

                name = self._get_method_name_basic(method_value)
                if name is not None:
                    self.method_value = method_value
                    break

        return name

    @classmethod
    def from_vm(cls, rpc_id: int, data: dict):
        return cls(
            rpc_id=rpc_id, method_value=data["method"], raw_request=data["request"], raw_response=data["response"]
        )
