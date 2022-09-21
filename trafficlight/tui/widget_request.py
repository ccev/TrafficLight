from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Iterable

from rich.console import Group
from rich.padding import Padding
from rich.rule import Rule
from rich.style import Style
from rich.table import Table, Column
from rich.text import Text
from textual.app import ComposeResult
from textual.layout import Container
from textual.message import Message, MessageTarget
from textual.reactive import reactive, Reactive
from textual.widget import Widget
from textual.widgets import Static

from trafficlight.proto_utils import get_method_text, REQUEST_HEADER
from .models import NoPostStatic, Mode, HOVER_CLASS

if TYPE_CHECKING:
    from trafficlight.proto_utils import Proto, Message as ProtoMessage


class ProtoContainer(Container):
    pass


class ProtoWidget(NoPostStatic):
    mouse_over: Reactive[bool] = reactive(False)

    class Clicked(Message):
        """Inspect this proto"""

        def __init__(self, sender: MessageTarget, proto: Proto):
            self.proto: Proto = proto
            super().__init__(sender)

    def __init__(self, proto: Proto):
        super().__init__()
        self._proto: Proto = proto

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

    def _make_message_text(self, message: ProtoMessage, table: Table) -> None:
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

    def render(self) -> Group:
        self.set_class(self.mouse_over, HOVER_CLASS)
        return self._content

    async def on_enter(self) -> None:
        self.mouse_over = True

    async def on_leave(self) -> None:
        self.mouse_over = False

    async def on_click(self) -> None:
        await self.emit(self.Clicked(self, self._proto))


class RequestWidget(Widget):
    text: Text

    def __init__(self, time: datetime, rpc_id: int, rpc_status: int, protos: list[Proto]):
        super().__init__()

        self.protos: list[ProtoWidget] = []
        self._composed: bool = False

        self._rpc_id: int = rpc_id
        self._rpc_status: int = rpc_status
        self._time: datetime = time

        self.make_text()

        for proto in protos:
            self.protos.append(ProtoWidget(proto))

    def make_text(self) -> None:
        self.text = Text("\n", no_wrap=True)
        self.text.append(self._time.strftime("%H:%M:%S"), style=REQUEST_HEADER)
        self.text.append(" | ")
        self.text.append(f"RPC ID {self._rpc_id}", style=REQUEST_HEADER)
        self.text.append(" | ")
        self.text.append(f"RPC Status {self._rpc_status}\n", style=REQUEST_HEADER)

    def compose(self) -> ComposeResult:
        yield NoPostStatic(self.text, id="request-head")
        for proto in self.protos:
            yield proto
        yield Static(Rule(style=Style(color="grey15")))
        self._composed = True

    def update_head(self) -> None:
        if self._composed:
            self.query_one("#request-head", NoPostStatic).update(self.text)

    def filter(self, mode: Mode, first_only: bool, text: str) -> None:
        self.display = False

        if first_only:
            self.text = Text()
            self.update_head()

            for proto in self.protos[1:]:
                proto.display = False
        elif not self.text:
            self.make_text()
            self.update_head()

        for proto in self.protos[: 1 if first_only else None]:
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
