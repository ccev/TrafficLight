from __future__ import annotations

from typing import TYPE_CHECKING

from rich.box import SQUARE
from rich.style import Style
from rich.table import Table
from rich.text import Text
from textual import events
from textual.reactive import Reactive
from textual.widget import Widget
from textual.widgets import Footer

from .models import Mode

if TYPE_CHECKING:
    from .app import TrafficLightGui

#  A lot of the text input code was taken from https://github.com/sirfuzzalot/textual-inputs


class InputWidget(Widget):
    app: TrafficLightGui

    input_text: str = Reactive("")
    command_mode: bool = Reactive(False)
    cursor = Text("|", style=Style(color="grey50"))
    _cursor_position: int = Reactive(0)
    _text_offset = 0

    DEFAULT_CSS = """
    InputWidget {
        height: 3;
        dock: bottom;
    }
    """

    def render(self):
        table = Table(box=SQUARE, header_style=None, show_header=False, expand=True)

        if self.command_mode:
            command_text = ">"
            column_kwargs = {"style": Style(color="cyan")}
        else:
            command_text = f"> {self.app.current_mode.value}"
            column_kwargs = {}
        table.add_column(min_width=len(command_text), **column_kwargs)

        table.add_column(ratio=1)
        table.add_row(command_text, self._render_text_with_cursor())
        return table

    # async def watch_input_text(self, new_value: str):
    #     await self.app.scroll.update_requests()

    def _render_text_with_cursor(self) -> Text:
        text = self.input_text
        left, right = self._text_offset_window()
        text = text[left:right]

        # convert the cursor to be relative to this view
        cursor_relative_position = self._cursor_position - self._text_offset
        return Text.assemble(
            text[:cursor_relative_position],
            self.cursor,
            text[cursor_relative_position:],
        )

    @property
    def _visible_width(self):
        width, _ = self.size
        width -= 2
        return width

    def _text_offset_window(self):
        return self._text_offset, self._text_offset + self._visible_width

    def _update_offset_left(self):
        visibility_left = 3
        if self._cursor_position < self._text_offset + visibility_left:
            self._text_offset = max(0, self._cursor_position - visibility_left)

    def _update_offset_right(self):
        _, right = self._text_offset_window()
        if self._cursor_position > right:
            self._text_offset = self._cursor_position - self._visible_width

    def cursor_left(self):
        if self.command_mode:
            return
        if self._cursor_position > 0:
            self._cursor_position -= 1
            self._update_offset_left()

    def cursor_right(self):
        if self.command_mode:
            return
        if self._cursor_position < len(self.input_text):
            self._cursor_position = self._cursor_position + 1
            self._update_offset_right()

    def cursor_home(self):
        if self.command_mode:
            return
        self._cursor_position = 0
        self._update_offset_left()

    def cursor_end(self):
        if self.command_mode:
            return
        self._cursor_position = len(self.input_text)
        self._update_offset_right()

    def key_backspace(self):
        if self.command_mode:
            return
        if self._cursor_position > 0:
            self.input_text = self.input_text[: self._cursor_position - 1] + self.input_text[self._cursor_position :]
            self._cursor_position -= 1
            self._update_offset_left()

    def key_delete(self):
        if self.command_mode:
            return
        if self._cursor_position < len(self.input_text):
            self.input_text = self.input_text[: self._cursor_position] + self.input_text[self._cursor_position + 1 :]

    def end_command_mode(self):
        self.command_mode = False

    def key_printable(self, event: events.Key):
        if self.command_mode:
            self.end_command_mode()

            try:
                self.app.current_mode = Mode[event.key.upper()]
            except KeyError:
                pass
        else:
            self.input_text = (
                self.input_text[: self._cursor_position] + event.key + self.input_text[self._cursor_position :]
            )

            if not self._cursor_position > len(self.input_text):
                self._cursor_position += 1
                self._update_offset_right()
