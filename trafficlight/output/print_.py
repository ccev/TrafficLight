from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from rich.console import Console
from rich.rule import Rule
from rich.text import Text

from trafficlight.proto_format import MessageFormatter, get_method_text
from .base import BaseOutput

if TYPE_CHECKING:
    from trafficlight.proto import Proto, Message


class PrintOutput(BaseOutput):
    console: Console

    async def start(self) -> None:
        self.console = Console(width=None)

    async def add_record(self, rpc_id: int, rpc_status: int, protos: list[Proto]):
        time = datetime.now()
        text = Text(f"{time} | RPC ID {rpc_id} | RPC STATUS {rpc_status}\n\n", no_wrap=True, overflow="ellipsis")

        formatter = MessageFormatter(text=text, one_line=True)
        for proto in protos:
            # text += self._get_text(proto) + "\n"

            text = formatter.format_proto(proto)

        self.console.print(text + "-" * 100 + "\n", overflow="ignore", crop=False, soft_wrap=False)
        self.console.print(Rule(style=""))

    def _get_text(self, proto: Proto, indent: int = 1):
        def get_message_text(message: Message) -> str:
            if message.name is None:
                name = f"[Unknown {message.type} Message]"
                data = f"Blackbox: {message.blackbox}"
            else:
                name = f"{message.type} | {message.name}"
                if message.payload is None:
                    data = f"Error decoding message. Blackbox: {message.blackbox}"
                elif len(message.payload.ListFields()) == 0:
                    data = "{}"
                else:
                    data = message.to_string()

            return name.ljust(50) + data

        text = f"{proto.method_value} | {proto.method_name}\n"

        for proto_message in (proto.request, proto.response):
            text += "\t" * indent + get_message_text(proto_message) + "\n"

        if proto.proxy:
            text += "\n" + "\t" * indent + "Proxy: " + self._get_text(proto.proxy, indent=indent + 1)

        return text
