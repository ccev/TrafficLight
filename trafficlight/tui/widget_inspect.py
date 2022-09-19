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
    def update_proto(self, proto: Proto):
        if proto.proxy:
            text = Text("Proxy: ")
            get_method_text(proto.proxy, text)
        else:
            text = get_method_text(proto)

        self.update(text)

    def clear(self):
        self.update("")


class InspectBody(NoPostStatic):
    def update_proto(self, proto: Proto):
        formatter = MessageFormatter()
        text = formatter.format_proto(proto)
        self.update(Padding(text, (1, 0, 0, 1)))

    def clear(self):
        self.update("")


class InspectWidget(Vertical):
    proto: Proto | None = None

    def __init__(self):
        super().__init__(id="inspect")

    def compose(self):
        yield InspectHeader("")
        yield Vertical(InspectBody())

    def get_copyable_text(self) -> str:
        if self.proto is None:
            return ""

        text = Text()
        get_method_text(self.proto, text)
        text.append("\n\n")

        formatter = MessageFormatter(text=text, indent_guides=False, types=False)
        text = formatter.format_proto(self.proto)
        return text.plain

    def set_proto(self, proto: Proto) -> None:
        self.proto = proto
        for element in (InspectHeader, InspectBody):
            self.query_one(element).update_proto(proto)
        # self.refresh(layout=True)

    def clear(self) -> None:
        if self.proto is None:
            return

        for element in (InspectHeader, InspectBody):
            self.query_one(element).clear()
