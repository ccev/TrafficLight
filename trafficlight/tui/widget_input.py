from __future__ import annotations

from typing import TYPE_CHECKING

from textual import events
from textual.color import Color
from textual.css.query import NoMatchingNodesError
from textual.reactive import Reactive
from textual.widget import Widget
from textual.widgets import Static, TextInput
from textual.layout import Horizontal
from rich.text import Text
from rich.style import Style
from .models import NoPostStatic
from textual import events

from trafficlight.proto import ALL_ACTION_NAMES, ACTION_PREFIXES, MESSAGE_NAMES
from .models import Mode

if TYPE_CHECKING:
    from .app import TrafficLightGui


class CustomTextInput(TextInput, can_focus=False):
    app: TrafficLightGui

    def __init__(self):
        super().__init__(
            placeholder="Press > to open the command input or start typing",
            autocompleter=self.search_autocompleter,
            id="custom-text-input",
        )
        self.has_focus = True
        self._editor.insert = self.insert

    def search_autocompleter(self, start: str) -> str | None:
        def match(against: str) -> bool:
            return against.casefold().startswith(start.casefold())

        if self.current_mode == Mode.FILTER_METHODS:
            for action_prefix in ACTION_PREFIXES:
                if start.casefold() != action_prefix.casefold() and match(action_prefix):
                    return action_prefix
            for action in ALL_ACTION_NAMES:
                if match(action):
                    return action
        elif self.current_mode == Mode.FILTER_MESSAGES:
            for message in MESSAGE_NAMES:
                if match(message):
                    return message
        return None

    def filter_text(self, text: str) -> str:
        if self.current_mode == Mode.FILTER_METHODS:
            if len(text.upper()) == len(text):
                text = text.upper()
        return text

    def insert(self, text: str) -> bool:
        new_text = (
            self._editor.content[: self._editor.cursor_index] + text + self._editor.content[self._editor.cursor_index :]
        )
        self._editor.content = self.filter_text(new_text)
        self._editor.cursor_index = min(len(self._editor.content), self._editor.cursor_index + len(text))
        return True

    @property
    def current_mode(self) -> Mode:
        return self.app.current_mode

    def input_key(self, event: events.Key):
        if event.key in ("tab", "enter"):
            if self._suggestion_suffix and self._editor.cursor_at_end:
                self._editor.insert(self._suggestion_suffix)
                self._suggestion_suffix = ""
                self._reset_visible_range()
        else:
            super()._on_key(event)

        self.app.filter_text = self._editor.content


class CommandInput(Static):
    app: TrafficLightGui

    def __init__(self):
        super().__init__(id="command-input")
        self.in_input: bool = False

    @property
    def current_mode(self) -> Mode:
        return self.app.current_mode

    def render(self):
        if self.in_input:
            self.styles.color = Color(127, 240, 212)
            mode = ""
        else:
            self.styles.color = None
            mode = self.current_mode.title

        return f"> {mode}"

    def set_in_input(self, in_input: bool):
        self.in_input = in_input
        self.refresh(layout=True)

    async def on_click(self, event: events.Click):
        self.app.input.set_command_mode(not self.in_input)


class SearchInput(Widget):
    def compose(self):
        yield CustomTextInput()


class SelectModeWidget(NoPostStatic):
    app: TrafficLightGui

    def __init__(self, mode: Mode):
        self._mode = mode

        text = Text()
        text.append(str(mode.value), style=Style(color="rgb(127, 240, 212)"))
        text.append(" - ", style=Style(color="grey50"))
        text.append(mode.title)
        super().__init__(text)
        self.styles.padding = (0, 0, 1, 0)

    async def on_click(self, event: events.Click) -> None:
        self.app.current_mode = self._mode
        self.app.input.set_command_mode(False)


class CommandHelp(Widget):
    def __init__(self):
        super().__init__(*(SelectModeWidget(m) for m in Mode), id="command-help")
        self.display = False


class InputWidget(Widget):
    app: TrafficLightGui

    command_mode: bool = Reactive(False)

    DEFAULT_CSS = """
    InputWidget {
        height: auto;
        dock: bottom;
    }
    """

    @property
    def text_input(self) -> CustomTextInput:
        return self.query_one("#custom-text-input")

    @property
    def command_input(self) -> CommandInput:
        return self.query_one("#command-input")

    def compose(self):
        yield CommandInput()
        yield SearchInput()

    def set_command_mode(self, enable: bool):
        self.app.toggle_command_help(enable)
        self.command_mode = enable
        self.command_input.set_in_input(enable)

    def input_key(self, event: events.Key):
        if self.command_mode:
            self.set_command_mode(False)
            if event.key.isprintable():

                try:
                    self.app.current_mode = Mode(event.key.lower())
                except ValueError:
                    pass
        else:
            self.text_input.input_key(event)
