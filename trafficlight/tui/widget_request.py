from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from rich.console import Group
from rich.padding import Padding
from rich.rule import Rule
from rich.style import Style
from rich.table import Table, Column
from rich.text import Text
from textual import events
from textual.color import Color
from textual.layout import Container
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

from .models import NoPostStatic
from .proto_format import get_method_text, REQUEST_HEADER

if TYPE_CHECKING:
    from .app import TrafficLightGui
    from trafficlight.proto import Proto, Message


class ProtoContainer(Container):
    pass


class ProtoWidget(NoPostStatic):
    app: TrafficLightGui
    mouse_over = reactive(False)

    def __init__(self, proto: Proto):
        super().__init__()
        self.styles.margin = (0, 0, 1, 0)
        self._proto = proto

        self._middle_column_text = Padding("|", (0, 1))
        self._content = self._get_content(proto)

    def _get_content(self, this_proto: Proto) -> Group:
        text = get_method_text(this_proto)

        table = Table.grid(Column(), Column(), Column())
        self._make_message_text(this_proto.request, table)
        text.append("\n")
        self._make_message_text(this_proto.response, table)

        elements = [text, table]

        if this_proto.proxy:
            proxy_group = self._get_content(this_proto.proxy)
            table.add_row()
            table.add_row("Proxy", self._middle_column_text, proxy_group)

        return Group(*elements)

    def _make_message_text(self, message: Message, table: Table):
        if message.name is None:
            name = f"[Unknown Message]"
            data = f"Blackbox: {message.blackbox}"
        else:
            name = message.name
            if message.payload is None:
                data = f"Error decoding message. Blackbox: {message.blackbox}"
            elif len(message.payload.ListFields()) == 0:
                data = "{}"
            else:
                data = message.to_string()

        text = Text(no_wrap=True)
        text.append(name + "\n")
        text.append(data, style=Style(color="grey50"))
        table.add_row(message.type, self._middle_column_text, text)

    def render(self):
        if self.mouse_over:
            self.styles.background = Color(25, 25, 25)
        else:
            self.styles.background = None
        return self._content

    async def on_enter(self, event: events.Enter) -> None:
        self.mouse_over = True

    async def on_leave(self, event: events.Leave) -> None:
        self.mouse_over = False

    async def _on_click(self, event: events.Click) -> None:
        self.app.inspect_proto(self._proto)


class RequestWidget(Widget):
    def __init__(self, time: datetime, rpc_id: int, rpc_status: int, protos: list[Proto]):
        super().__init__()

        self.styles.height = "auto"
        self.protos: list[ProtoWidget] = []

        self.text = Text("\n", no_wrap=True)
        self.text.append(time.strftime("%H:%M:%S"), style=REQUEST_HEADER)
        self.text.append(" | ")
        self.text.append(f"RPC ID {rpc_id}", style=REQUEST_HEADER)
        self.text.append(" | ")
        self.text.append(f"RPC Status {rpc_status}\n\n", style=REQUEST_HEADER)

        for proto in protos:
            self.protos.append(ProtoWidget(proto))

    def compose(self):
        yield NoPostStatic(self.text)
        for proto in self.protos:
            yield proto
        yield Static(Rule(style=Style(color="grey15")))
