from __future__ import annotations

import json
from typing import TYPE_CHECKING

from rich.padding import Padding
from rich.text import Text
from textual.color import Color
from textual.layout import Vertical

from .proto_format import MessageFormatter, MESSAGE_NAME, BRACKETS, get_method_text
from .models import NoPostStatic

if TYPE_CHECKING:
    from trafficlight.proto import Proto, Message


class InspectHeader(NoPostStatic):
    def __init__(self, text: str):
        super().__init__(text, id="inspect-header")

    def update_proto(self, proto: Proto):
        if proto.proxy:
            text = Text("Proxy: ")
            get_method_text(proto.proxy, text)
        else:
            text = get_method_text(proto)

        self.update(text)


def build_message_text(message: Message, text: Text):
    if message.name is None:
        text.append("Unknown Message ")
        text.append(json.dumps(message.blackbox, indent=4) + "\n")
    else:
        text.append(message.name, style=MESSAGE_NAME)
        text.append(" {\n", style=BRACKETS)
        formatter = MessageFormatter(text)
        formatter.print_message(message.payload)
        text.append("}\n", style=BRACKETS)


class InspectBody(NoPostStatic):
    def __init__(self):
        super().__init__("", id="inspect-body")

    def update_proto(self, proto: Proto):
        text = Text()

        def build_text(this_proto: Proto):
            for message in (this_proto.request, this_proto.response):
                build_message_text(message, text)
                text.append("\n")

        build_text(proto)
        if proto.proxy:
            text.append("\n")
            build_text(proto.proxy)

        self.update(Padding(text, (1, 0, 0, 1)))


class InspectWidget(Vertical):
    proto: Proto

    def __init__(self):
        super().__init__(id="inspect")

    def compose(self):
        yield InspectHeader("")
        yield Vertical(InspectBody())

    def set_proto(self, proto: Proto):
        self.proto = proto
        self.query_one("#inspect-header").update_proto(proto)
        self.query_one("#inspect-body").update_proto(proto)
        self.refresh(layout=True)
