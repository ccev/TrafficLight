from __future__ import annotations

import base64
import json
import sys
from typing import Type, Iterable, TYPE_CHECKING

from blackboxprotobuf.lib.api import decode_message, _json_safe_transform
from google.protobuf import text_format, descriptor
from google.protobuf.internal.enum_type_wrapper import EnumTypeWrapper
from google.protobuf.message import Message as ProtobufMessage

from trafficlight import protos

if TYPE_CHECKING:
    from trafficlight.model import ProtoModel


all_types = protos.AllTypesAndMessagesResponsesProto
MESSAGES: dict[int, descriptor.FieldDescriptor] = all_types.AllMessagesProto.DESCRIPTOR.fields_by_number
RESPONSES: dict[int, descriptor.FieldDescriptor] = all_types.AllResponsesProto.DESCRIPTOR.fields_by_number
METHODS: dict[int, descriptor.EnumValueDescriptor] = all_types.AllResquestTypesProto.DESCRIPTOR.values_by_number
MESSAGE_TYPE_TO_ID: dict[str, int] = {m.message_type.name: n for n, m in MESSAGES.items()}


def _get_method_names(method_enum: EnumTypeWrapper) -> list[str]:
    return [d.name for d in method_enum.DESCRIPTOR.values]


def _get_message_names(all_messages: Type[ProtobufMessage]) -> list[str]:
    return [f.message_type.name for f in all_messages.DESCRIPTOR.fields]


MESSAGE_NAMES: list[str] = _get_message_names(all_types.AllMessagesProto) + _get_message_names(
    all_types.AllResponsesProto
)

# NOTE not all game* still in all_types.AllResquestTypesProto but.
# Maybe uses all in one, ex:
# ALL_ACTION_NAMES: list[str] = _get_method_names(all_types.AllResquestTypesProto)  # type: ignore
# ACTION_PREFIXES: list[str] = ["REQUEST_TYPE_"] # type: ignore

METHOD_NAMES: list[str] = _get_method_names(protos.Method)  # type: ignore
SOCIAL_ACTION_NAMES: list[str] = _get_method_names(protos.InternalSocialAction)  # type: ignore
CLIENT_ACTION_NAMES: list[str] = _get_method_names(protos.PlatformClientAction)  # type: ignore
ADVENTURE_SYNC_ACTION_NAMES: list[str] = _get_method_names(protos.GameAdventureSyncAction)  # type: ignore
PLAYER_SUBMISSION_ACTION_NAMES: list[str] = _get_method_names(protos.TitanPlayerSubmissionAction)  # type: ignore
FITNESS_ACTION_NAMES: list[str] = _get_method_names(protos.GameFitnessAction)  # type: ignore
GAME_REGISTRY_ACTIONS: list[str] = _get_method_names(protos.GameAccountRegistryActions)  # type: ignore
GAME_ANTI_CHEAT_ACTIONS: list[str] = _get_method_names(protos.GameAnticheatAction)  # type: ignore
GAME_AUTH_ACTIONS: list[str] = _get_method_names(protos.GameAuthenticationActionMethod)  # type: ignore
GAME_BACKGROUND_ACTIONS: list[str] = _get_method_names(protos.GameBackgroundModeAction)  # type: ignore
GAME_CHAT_ACTIONS: list[str] = _get_method_names(protos.GameChatActions)  # type: ignore
GAME_CRM_ACTIONS: list[str] = _get_method_names(protos.GameCrmActions)  # type: ignore
GAME_GM_TEMPLATE_ACTIONS: list[str] = _get_method_names(protos.GameGmTemplatesAction)  # type: ignore
GAME_IAP_ACTIONS: list[str] = _get_method_names(protos.GameIapAction)  # type: ignore
GAME_NOTIFICATION_ACTIONS: list[str] = _get_method_names(protos.GameNotificationAction)  # type: ignore
GAME_PASSCODE_ACTIONS: list[str] = _get_method_names(protos.GamePasscodeAction)  # type: ignore
GAME_PING_ACTIONS: list[str] = _get_method_names(protos.GamePingAction)  # type: ignore
GAME_PLAYER_ACTIONS: list[str] = _get_method_names(protos.GamePlayerAction)  # type: ignore
GAME_POI_ACTIONS: list[str] = _get_method_names(protos.GamePoiAction)  # type: ignore
GAME_PUSH_NOTIFICATION_ACTIONS: list[str] = _get_method_names(protos.GamePushNotificationAction)  # type: ignore
GAME_SOCIAL_ACTIONS: list[str] = _get_method_names(protos.GameSocialAction)  # type: ignore
GAME_TELEMETRY_ACTIONS: list[str] = _get_method_names(protos.GameTelemetryAction)  # type: ignore
GAME_WEB_TOKEN_ACTIONS: list[str] = _get_method_names(protos.GameWebTokenAction)  # type: ignore

ALL_ACTION_NAMES: list[str] = (
    METHOD_NAMES
    + SOCIAL_ACTION_NAMES
    + CLIENT_ACTION_NAMES
    + ADVENTURE_SYNC_ACTION_NAMES
    + PLAYER_SUBMISSION_ACTION_NAMES
    + FITNESS_ACTION_NAMES
    + GAME_REGISTRY_ACTIONS
    + GAME_ANTI_CHEAT_ACTIONS
    + GAME_AUTH_ACTIONS
    + GAME_BACKGROUND_ACTIONS
    + GAME_CHAT_ACTIONS
    + GAME_CRM_ACTIONS
    + GAME_GM_TEMPLATE_ACTIONS
    + GAME_IAP_ACTIONS
    + GAME_NOTIFICATION_ACTIONS
    + GAME_PASSCODE_ACTIONS
    + GAME_PING_ACTIONS
    + GAME_PLAYER_ACTIONS
    + GAME_POI_ACTIONS
    + GAME_PUSH_NOTIFICATION_ACTIONS
    + GAME_SOCIAL_ACTIONS
    + GAME_TELEMETRY_ACTIONS
    + GAME_WEB_TOKEN_ACTIONS
)

ACTION_PREFIXES: list[str] = [
    "METHOD_",
    "SOCIAL_ACTION_",
    "PLATFORM_",
    "GAME_LOCATION_AWARENESS_ACTION_",
    "TITAN_PLAYER_SUBMISSION_ACTION_",
    "GAME_FITNESS_ACTION_",
    "GAME_ACCOUNT_REGISTRY_ACTION_",
    "GAME_ANTICHEAT_ACTION_",
    "GAME_AUTHENTICATION_ACTION_",
    "GAME_BACKGROUND_MODE_ACTION_",
    "GAME_CHAT_ACTION_",
    "CRM_ACTION_",
    "GAME_GM_TEMPLATES_ACTION_",
    "GAME_IAP_ACTION_",
    "GAME_NOTIFICATION_ACTION_",
    "GAME_PASSCODE_ACTION_",
    "GAME_PING_ACTION_",
    "GAME_PLAYER_ACTION_",
    "GAME_POI_ACTION_",
    "GAME_PUSH_NOTIFICATION_ACTION_",
    "GAME_SOCIAL_ACTION_",
    "GAME_TELEMETRY_ACTION_",
    "GAME_WEB_TOKEN_ACTION_"
]


class Message:
    messages: dict[int, descriptor.FieldDescriptor]

    def __init__(self, method_id: int, raw: str | bytes):
        self._raw: str | bytes = raw

        self.name: str | None = None
        _message = self.messages.get(method_id)
        if _message is not None:
            self.name = _message.message_type.name

        self.payload: ProtobufMessage | None = None
        if self.name is not None:
            self.payload = self.decode_proto()

        self.blackbox: dict | None = None
        if self.name is None or self.payload is None:
            self.blackbox = self.decode_blackbox()

    @property
    def type(self) -> str:
        return self.__class__.__name__

    def decode_b64(self) -> bytes:
        if isinstance(self._raw, bytes):
            return self._raw

        return base64.b64decode(self._raw.rstrip("\0"))

    def decode_proto(self) -> ProtobufMessage | None:
        if self.name is None:
            return None

        message = getattr(sys.modules["trafficlight.protos"], self.name)

        if message is None:
            return None

        try:
            decoded = self.decode_b64()
            return message.FromString(decoded)
        except Exception as e:
            print(f"error decoding {message} with {self._raw}: {e}")
            return None

    def decode_blackbox(self) -> dict:
        decoded = self.decode_b64()

        value, typedef = decode_message(decoded)
        return _json_safe_transform(values=value, typedef=typedef, toBytes=False)

    def to_string(self, one_line: bool = True) -> str:
        if self.payload is None:
            indent = None if one_line else 2
            return json.dumps(self.blackbox, ensure_ascii=False, indent=indent)
        else:
            return text_format.MessageToString(self.payload, as_one_line=one_line)


class Request(Message):
    messages = MESSAGES


class Respone(Message):
    messages = RESPONSES


class Proto:
    def __init__(self, rpc_id: int, method_value: int, raw_request: str | bytes, raw_response: str | bytes):
        self.rpc_id: int = rpc_id
        self.method_value: int = method_value
        self.method_name: str | None = self.get_method_name()
        self.request: Request = Request(self.method_value, raw_request)
        self.response: Respone = Respone(self.method_value, raw_response)

        self.proxy: Proto | None = None
        if isinstance(self.request.payload, protos.ProxyRequestProto) and isinstance(
            self.response.payload, protos.ProxyResponseProto
        ):
            self.proxy = Proto(
                rpc_id=rpc_id,
                method_value=self.request.payload.action,
                raw_request=self.request.payload.payload,
                raw_response=self.response.payload.payload,
            )

    @property
    def messages(self) -> Iterable[Message]:
        yield self.request
        yield self.response

    @staticmethod
    def get_message_name(messages: dict, value: int) -> str | None:
        try:
            return messages[value].message_type.name

        except KeyError:
            return None

    @staticmethod
    def _get_method_name_basic(value: int) -> str | None:
        name: descriptor.EnumValueDescriptor | None = METHODS.get(value)

        if name is None:
            return None

        return name.name[13:]

    def get_method_name(self) -> str | None:
        name = self._get_method_name_basic(self.method_value)

        if (
            self.method_value not in MESSAGES.keys()
            and self.method_value not in RESPONSES.keys()
            and name is not None
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
    def from_raw(cls, rpc_id: int, data: ProtoModel) -> Proto:
        return cls(
            rpc_id=rpc_id,
            method_value=data.method,
            raw_request=data.request if data.request else "",
            raw_response=data.response if data.response else "",
        )
