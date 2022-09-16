from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from textual import events
from textual.app import App
from textual.layout import Horizontal

from .models import Mode
from .widget_input import InputWidget
from .widget_inspect import InspectWidget
from .widget_request import RequestWidget
from .widget_screen import ScreenWidget

if TYPE_CHECKING:
    from trafficlight.proto import Proto


class TrafficLightGui(App):
    input: InputWidget = InputWidget()
    scroll: ScreenWidget = ScreenWidget()
    current_mode: Mode = Mode.W

    def __init__(self):
        super().__init__(css_path="_style.css")

        self.incoming_requests: list[RequestWidget] = []

    def compose(self):
        yield Horizontal(self.scroll, InspectWidget())
        yield self.input

    def on_mount(self):
        self.set_interval(1, self.process_queue)

    async def process_queue(self):
        if self.incoming_requests:
            self.scroll.add_requests(self.incoming_requests)
            self.incoming_requests.clear()

    def inspect_proto(self, proto: Proto):
        self.query_one("#inspect").set_proto(proto)

    def add_record(self, rpc_id: int, rpc_status: int, protos: list[Proto]):
        if self.current_mode == Mode.P:
            return

        request = RequestWidget(time=datetime.now(), rpc_id=rpc_id, rpc_status=rpc_status, protos=protos)

        self.incoming_requests.append(request)

    async def on_key(self, event: events.Key) -> None:
        if event.key == "left":
            self.input.cursor_left()
        elif event.key == "right":
            self.input.cursor_right()
        elif event.key == "home":
            self.input.cursor_home()
        elif event.key == "end":
            self.input.cursor_end()
        elif event.key == "ctrl+h":
            self.input.key_backspace()
        elif event.key == "delete":
            self.input.key_delete()
        elif event.key == "escape":
            self.input.end_command_mode()
        elif len(event.key) == 1 and event.key.isprintable():
            if event.key == ">":
                self.input.command_mode = not self.input.command_mode
            else:
                self.input.key_printable(event)

        await self.scroll.dispatch_key(event)

    async def run_app(self):
        await self._process_messages()
