from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Iterable

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

from .models import NoPostStatic, Mode
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

        self.plain_text: str = ""
        self._content: Group = self._get_content(proto)

    @property
    def method_name(self) -> str:
        return self._proto.method_name

    @property
    def proxy_method_name(self) -> str:
        return self._proto.proxy.method_name if self._proto.proxy else ""

    @property
    def message_names(self) -> Iterable[str]:
        for message in self._proto.messages:
            if message.name:
                yield message.name.casefold()

        if self._proto.proxy:
            for message in self._proto.proxy.messages:
                if message.name:
                    yield message.name.casefold()

    def _get_content(self, this_proto: Proto) -> Group:
        text = get_method_text(this_proto)
        text.append("\n")
        self.plain_text += text.plain

        table = Table.grid(Column(), Column(), Column())
        self._make_message_text(this_proto.request, table)
        self._make_message_text(this_proto.response, table)

        if this_proto.proxy:
            proxy_group = self._get_content(this_proto.proxy)
            table.add_row()
            table.add_row("Proxy", self._middle_column_text, proxy_group)

        return Group(text, table)

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
        self.plain_text += text.plain
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

        self.rpc_id = rpc_id

        self.text = Text("\n", no_wrap=True)
        self.text.append(time.strftime("%H:%M:%S"), style=REQUEST_HEADER)
        self.text.append(" | ")
        self.text.append(f"RPC ID {rpc_id}", style=REQUEST_HEADER)
        self.text.append(" | ")
        self.text.append(f"RPC Status {rpc_status}\n", style=REQUEST_HEADER)

        for proto in protos:
            self.protos.append(ProtoWidget(proto))

    def compose(self):
        yield NoPostStatic(self.text)
        for proto in self.protos:
            yield proto
        yield Static(Rule(style=Style(color="grey15")))

    def filter(self, mode: Mode, first_only: bool, text: str):
        self.display = False

        if first_only:
            for proto in self.protos[1:]:
                proto.display = False

        for proto in self.protos[:1 if first_only else None]:
            if mode == Mode.FILTER_METHODS:
                proto.display = text in proto.method_name.casefold() or text in proto.proxy_method_name.casefold()
            elif mode == Mode.FILTER_MESSAGES:
                proto.display = text in "".join(proto.message_names)
            elif mode == Mode.FILTER_TEXT:
                proto.display = text in self.text.plain.casefold() or text in proto.plain_text.casefold()
            else:
                proto.display = True

            if proto.display:
                self.display = True
