from __future__ import annotations

import random
from typing import TYPE_CHECKING, Type

import pyperclip
from rich.style import Style
from rich.text import Text
from textual import events
from textual.color import Color
from textual.reactive import Reactive
from textual.widget import Widget
from textual.widgets import Static, TextInput

from trafficlight.proto_utils import ALL_ACTION_NAMES, ACTION_PREFIXES, MESSAGE_NAMES
from .models import Mode, Toggle, CommandEnum, Action
from .models import NoPostStatic

if TYPE_CHECKING:
    from .app import TrafficLightGui


class CustomTextInput(TextInput, can_focus=False):
    app: TrafficLightGui

    def __init__(self):
        command_key = random.choices(("↲", ">"), weights=(0.2, 0.8), k=1)[0]
        super().__init__(
            placeholder=f"Press {command_key} to open the command input or start typing",
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


class CommandHelpEntry(NoPostStatic):
    app: TrafficLightGui

    def __init__(self, command: CommandEnum):
        self._command = command
        text = self.get_text()

        super().__init__(text, id=str(command.id))

        self.styles.padding = (0, 0, 1, 0)

    def get_text(self, toggle_value: bool = False) -> Text:
        text = Text()
        text.append(str(self._command.value), style=Style(color="rgb(127, 240, 212)"))
        text.append(" - ", style=Style(color="grey50"))

        if isinstance(self._command, Toggle):
            if toggle_value:
                text.append("▣ ", style=Style(color="rgb(86, 209, 108)"))
            else:
                text.append("□ ", style=Style(color="rgb(145, 145, 145)"))
        text.append(self._command.title)
        return text

    def update_text(self, toggle_value: bool = False):
        text = self.get_text(toggle_value)
        super().update(text)

    async def on_click(self, event: events.Click) -> None:
        self.app.input.set_command_mode(False)
        if isinstance(self._command, Mode):
            self.app.current_mode = self._command
        elif isinstance(self._command, Toggle):
            self.app.toggle_toggle(self._command)
        elif isinstance(self._command, Action):
            self.app.input.trigger_action(self._command)


class HelpEntryContainer(Widget):
    DEFAULT_CSS = """
    HelpEntryContainer {
        height: auto;
        width: 1fr;
        max-width: 45;
        padding-left: 1;
        overflow: hidden;
    }
    """

    def __init__(self, command: Type[CommandEnum]):
        super().__init__(id=command.__name__)
        self._command: Type[CommandEnum] = command

    def compose(self):
        yield Static(self._command.__name__.upper() + "S", id="command-title")
        for cmd in self._command:
            yield CommandHelpEntry(cmd)


class CommandHelp(Widget):
    def __init__(self):
        super().__init__(id="command-help")
        self.display = False

    def compose(self):
        yield HelpEntryContainer(Mode)
        yield HelpEntryContainer(Toggle)
        yield HelpEntryContainer(Action)

    def update_toggle(self, toggle: Toggle, value: bool) -> None:
        entry: CommandHelpEntry = self.query_one(f"#{toggle.id}")
        entry.update_text(value)


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

    def trigger_action(self, action: Action):
        if action == Action.COPY_INSPECTED:
            text = self.app.inspect_widget.get_copyable_text()
            if text:
                pyperclip.copy(text)
                pyperclip.paste()
        elif action == Action.EMPTY_LOG:
            self.app.screen_widget.clear()
            self.app.inspect_widget.clear()

    def input_key(self, event: events.Key):
        if self.command_mode:
            self.set_command_mode(False)
            if event.key.isprintable():

                try:
                    self.app.current_mode = Mode(event.key.lower())
                except ValueError:
                    pass

                try:
                    toggle = Toggle(event.key.lower())
                    self.app.toggle_toggle(toggle)
                except ValueError:
                    pass

                try:
                    action = Action(event.key.lower())
                    self.trigger_action(action)
                except ValueError:
                    pass
        else:
            self.text_input.input_key(event)
