from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from textual import events
from textual.app import App
from textual.layout import Horizontal, Container
from textual.widgets import Static
from textual.reactive import reactive, Reactive, var

from .models import Mode
from .widget_input import InputWidget, CommandHelp
from .widget_inspect import InspectWidget
from .widget_request import RequestWidget
from .widget_screen import ScreenWidget

if TYPE_CHECKING:
    from trafficlight.proto import Proto


class TrafficLightGui(App):
    input: InputWidget = InputWidget()
    scroll: ScreenWidget = ScreenWidget()
    current_mode: Reactive[Mode] = var(Mode.WATCH)
    filter_text: Reactive[str] = reactive("")

    def __init__(self):
        super().__init__(css_path="_style.css")

        self.incoming_requests: list[RequestWidget] = []

    def compose(self):
        yield Horizontal(self.scroll, InspectWidget())
        yield CommandHelp()
        yield self.input

    def toggle_command_help(self, show: bool):
        cmd_help = self.query_one("#command-help")
        cmd_help.display = show

    def watch_filter_text(self, _):
        self.scroll.filter()

    def watch_current_mode(self, _):
        self.scroll.filter()

    def on_mount(self):
        self.set_interval(1, self.process_queue)

    async def process_queue(self):
        if self.incoming_requests:
            self.scroll.add_requests(self.incoming_requests)
            self.incoming_requests.clear()

    def inspect_proto(self, proto: Proto):
        self.query_one("#inspect").set_proto(proto)

    def add_record(self, rpc_id: int, rpc_status: int, protos: list[Proto]):
        if self.current_mode == Mode.PAUSE:
            return

        request = RequestWidget(time=datetime.now(), rpc_id=rpc_id, rpc_status=rpc_status, protos=protos)

        self.incoming_requests.append(request)

    async def on_key(self, event: events.Key) -> None:
        if event.key == ">":
            self.input.set_command_mode(not self.input.command_mode)
        else:
            self.input.input_key(event)

    async def run_app(self):
        await self._process_messages()
