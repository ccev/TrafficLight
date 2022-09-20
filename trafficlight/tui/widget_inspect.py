from __future__ import annotations

from typing import TYPE_CHECKING

from rich.padding import Padding
from rich.text import Text
from textual.layout import Vertical
from rich.style import Style

from .models import NoPostStatic, Mode
from .proto_format import MessageFormatter, get_method_text

if TYPE_CHECKING:
    from trafficlight.proto import Proto
    from .app import TrafficLightGui


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
    _text: Text = Text()
    app: TrafficLightGui

    def update_proto(self, proto: Proto):
        formatter = MessageFormatter()
        self._text = formatter.format_proto(proto)

        if self.app.current_mode == Mode.FILTER_TEXT:
            self.highlight_text(self.app.filter_text)
        else:
            self.update_text()

    def update_text(self, text: Text | None = None):
        self.update(Padding(self._text if text is None else text, (1, 0, 0, 1)))

    def highlight_text(self, text: str):
        copied_text = self._text.copy()
        copied_text.highlight_words(
            (text.strip(),), style=Style(bgcolor="rgb(250, 250, 135)", color="black"), case_sensitive=False
        )
        self.update_text(copied_text)

    def clear(self):
        self._text = Text()
        self.update_text()


class InspectWidget(Vertical):
    proto: Proto | None = None
    _composed: bool = False

    def __init__(self):
        super().__init__(id="inspect")

    def compose(self):
        yield InspectHeader("")
        yield Vertical(InspectBody())
        self._composed = True

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

    def search_text(self, text: str):
        if not self._composed:
            return
        self.query_one(InspectBody).highlight_text(text)
