from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import pyperclip
from textual import events
from textual.app import App, ComposeResult
from textual.keys import Keys
from textual.layout import Horizontal
from textual.reactive import reactive, Reactive, var

from .models import Mode, Toggle, Action
from .widget_command_overview import CommandOverview, CommandEntry, CommandReceived
from .widget_input import InputWidget
from .widget_inspect import InspectWidget
from .widget_request import RequestWidget, ProtoWidget
from .widget_screen import ScreenWidget

if TYPE_CHECKING:
    from trafficlight.proto_utils import Proto


class TrafficLightGui(App):
    current_mode: Reactive[Mode] = var(Mode.WATCH)
    filter_text: Reactive[str] = reactive("")

    def __init__(self):
        super().__init__(css_path="_style.css", title="Traffic Light")

        self.incoming_requests: list[RequestWidget] = []
        self.toggles: dict[Toggle, bool] = {t: False for t in Toggle}

    def compose(self) -> ComposeResult:
        yield Horizontal(ScreenWidget(), InspectWidget())
        yield InputWidget()

    @property
    def inspect_widget(self) -> InspectWidget:
        return self.query_one(InspectWidget)

    @property
    def screen_widget(self) -> ScreenWidget:
        return self.query_one(ScreenWidget)

    @property
    def command_overview(self) -> CommandOverview:
        return self.query_one(CommandOverview)

    @property
    def input_widget(self) -> InputWidget:
        return self.query_one(InputWidget)

    def on_mount(self) -> None:
        self.set_interval(0.2, self.process_queue)

    async def on_key(self, event: events.Key) -> None:
        await self.input_widget.input_key(event)

    async def on_proto_widget_clicked(self, event: ProtoWidget.Clicked) -> None:
        await self.inspect_widget.set_proto(event.proto)

    def on_command_received(self, event: CommandReceived) -> None:
        if isinstance(event.command, Mode):
            self.current_mode = event.command
        elif isinstance(event.command, Toggle):
            self.toggle_toggle(event.command)
        elif isinstance(event.command, Action):
            self.trigger_action(event.command)

    def watch_filter_text(self, _) -> None:
        self.screen_widget.filter()
        if self.current_mode == Mode.FILTER_TEXT:
            self.inspect_widget.search_text(self.filter_text)

    def watch_current_mode(self, _) -> None:
        self.screen_widget.filter()
        self.inspect_widget.search_text(self.filter_text if self.current_mode == Mode.FILTER_TEXT else "")

    def toggle_toggle(self, toggle: Toggle) -> None:
        self.toggles[toggle] = result = not self.toggles.get(toggle, False)

        if toggle == Toggle.FIRST_PROTO_ONLY:
            self.screen_widget.filter()

        self.command_overview.update_toggle(toggle, result)

    def trigger_action(self, action: Action) -> None:
        if action == Action.COPY_INSPECTED:
            text = self.inspect_widget.get_copyable_text()
            if text:
                pyperclip.copy(text)
                pyperclip.paste()
        elif action == Action.EMPTY_LOG:
            self.screen_widget.clear()
            self.inspect_widget.clear()

    async def process_queue(self) -> None:
        if self.incoming_requests:
            await self.screen_widget.add_requests(self.incoming_requests)
            self.incoming_requests.clear()

    def add_record(self, rpc_id: int, rpc_status: int, protos: list[Proto]) -> None:
        if self.toggles[Toggle.PAUSE]:
            return

        request = RequestWidget(time=datetime.now(), rpc_id=rpc_id, rpc_status=rpc_status, protos=protos)
        self.incoming_requests.append(request)

    async def run_app(self) -> None:
        await self._process_messages()
