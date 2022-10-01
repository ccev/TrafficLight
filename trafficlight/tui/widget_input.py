from __future__ import annotations

import random
from typing import TYPE_CHECKING, Type

import pyperclip
from rich.style import Style
from rich.text import Text
from textual import events
from textual.color import Color
from textual.reactive import Reactive, reactive
from textual.widget import Widget
from textual.widgets import Static, TextInput
from textual.layout import Horizontal, Vertical
from textual.app import ComposeResult
from textual.keys import Keys

from trafficlight.proto_utils import ALL_ACTION_NAMES, ACTION_PREFIXES, MESSAGE_NAMES
from .models import Mode, Toggle, CommandEnum, Action, ALL_COMMANDS
from .models import NoPostStatic
from .widget_command_overview import CommandOverview, SetCommandMode, CommandReceived

if TYPE_CHECKING:
    from .app import TrafficLightGui


class CustomTextInput(TextInput, can_focus=False):
    app: TrafficLightGui
    _suggestion_suffix: str

    def __init__(self):
        command_key = random.choices(("↲", ">"), weights=(0.2, 0.8), k=1)[0]
        super().__init__(
            placeholder=f"Press {command_key} to open the command input or start typing",
            autocompleter=self.search_autocompleter,
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

    def input_key(self, event: events.Key) -> None:
        if event.key == "tab":
            if self._suggestion_suffix and self._editor.cursor_at_end:
                self._editor.insert(self._suggestion_suffix)
                self._suggestion_suffix = ""
                self._reset_visible_range()
        else:
            super()._on_key(event)

        self.app.filter_text = self._editor.content


class CommandInput(Static):
    app: TrafficLightGui
    in_input: bool = False

    def render(self) -> str:
        if self.in_input:
            self.styles.color = Color(127, 240, 212)
            mode = ""
        else:
            self.styles.color = None
            mode = self.app.current_mode.title

        return f"> {mode}"

    def set_in_input(self, in_input: bool) -> None:
        self.in_input = in_input
        self.refresh(layout=True)

    async def on_click(self) -> None:
        await self.emit(SetCommandMode(self, not self.in_input))


class SearchInput(Widget):
    def compose(self) -> ComposeResult:
        yield CustomTextInput()


class InputContainer(Widget):
    pass


class InputWidget(Widget):
    command_mode: bool = False

    def compose(self) -> ComposeResult:
        yield CommandOverview()
        yield InputContainer(CommandInput(), SearchInput())

    @property
    def text_input(self) -> CustomTextInput:
        return self.query_one(CustomTextInput)

    @property
    def command_input(self) -> CommandInput:
        return self.query_one(CommandInput)

    @property
    def command_overview(self) -> CommandOverview:
        return self.query_one(CommandOverview)

    def on_set_command_mode(self, event: SetCommandMode) -> None:
        self.set_command_mode(event.value)

    def set_command_mode(self, enable: bool):
        self.command_mode = enable
        self.command_overview.display = enable
        self.command_input.set_in_input(enable)
        self.refresh()

    async def input_key(self, event: events.Key) -> None:
        if event.char == ">" or event.key == Keys.Enter or event.key == Keys.Return:
            self.set_command_mode(not self.command_mode)
            return

        if self.command_mode:
            self.set_command_mode(False)
            if event.key.isprintable():
                for command in ALL_COMMANDS:
                    try:
                        selected_command = command(event.key.lower())
                    except ValueError:
                        continue
                    else:
                        await self.emit(CommandReceived(self, selected_command))
        else:
            self.text_input.input_key(event)
