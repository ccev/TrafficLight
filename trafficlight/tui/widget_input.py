from __future__ import annotations

from typing import TYPE_CHECKING

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.color import Color
from textual.keys import Keys
from textual.reactive import Reactive
from textual.widget import Widget
from textual.widgets import Input
from textual.widgets import Static

from .models import ALL_COMMANDS
from .widget_command_overview import CommandOverview, SetCommandMode, CommandReceived

if TYPE_CHECKING:
    from .app import TrafficLightGui


# class CustomTextInput(Input, can_focus=False):
#     app: TrafficLightGui
#     _suggestion_suffix: str
#
#     DEFAULT_CSS = ""
#     BINDINGS = []
#
#     def __init__(self):
#         command_key = random.choices(("↲", ">"), weights=(0.2, 0.8), k=1)[0]
#         super().__init__(
#             placeholder=f"Press {command_key} to open the command input or start typing"
#         )
#         self.has_focus = True
#         # self._editor.insert = self.insert
#
#     def search_autocompleter(self, start: str) -> str | None:
#         def match(against: str) -> bool:
#             return against.casefold().startswith(start.casefold())
#
#         if self.current_mode == Mode.FILTER_METHODS:
#             for action_prefix in ACTION_PREFIXES:
#                 if start.casefold() != action_prefix.casefold() and match(action_prefix):
#                     return action_prefix
#             for action in ALL_ACTION_NAMES:
#                 if match(action):
#                     return action
#         elif self.current_mode == Mode.FILTER_MESSAGES:
#             for message in MESSAGE_NAMES:
#                 if match(message):
#                     return message
#         return None
#
#     def filter_text(self, text: str) -> str:
#         if self.current_mode == Mode.FILTER_METHODS:
#             if len(text.upper()) == len(text):
#                 text = text.upper()
#         return text
#
#     def insert(self, text: str) -> bool:
#         new_text = (
#             self._editor.content[: self._editor.cursor_index] + text + self._editor.content[self._editor.cursor_index :]
#         )
#         self._editor.content = self.filter_text(new_text)
#         self._editor.cursor_index = min(len(self._editor.content), self._editor.cursor_index + len(text))
#         return True
#
#     @property
#     def current_mode(self) -> Mode:
#         return self.app.current_mode
#
#     def input_key(self, event: events.Key) -> None:
#         if event.key == "tab":
#             if self._suggestion_suffix and self._editor.cursor_at_end:
#                 self._editor.insert(self._suggestion_suffix)
#                 self._suggestion_suffix = ""
#                 self._reset_visible_range()
#         else:
#             super()._on_key(event)
#
#         self.app.filter_text = self._editor.content


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


class InputContainer(Widget):
    pass


class CustomInput(Input):
    DEFAULT_CSS = ""
    can_focus = False
    has_focus = Reactive(False)

    BINDINGS = [
        Binding("left", "cursor_left", "cursor left", show=False),
        Binding("right", "cursor_right", "cursor right", show=False),
        Binding("backspace", "delete_left", "delete left", show=False),
        Binding("home", "home", "home", show=False),
        Binding("end", "end", "end", show=False),
        Binding("ctrl+d", "delete_right", "delete right", show=False),
        Binding("enter", "submit", "submit", show=False),
    ]

    async def input_key(self, event: events.Key) -> None:
        self._cursor_visible = True
        if self.cursor_blink:
            self.blink_timer.reset()

        if event.key == Keys.Left:
            self.action_cursor_left()
        elif event.key == Keys.Right:
            self.action_cursor_right()
        elif event.key == Keys.Backspace:
            self.action_delete_left()
        elif event.key == Keys.Home:
            self.action_home()
        elif event.key == Keys.End:
            self.action_end()
        elif event.key == "ctrl+d" or event.key == Keys.Delete:
            self.action_delete_right()
        elif event.is_printable:
            assert event.character is not None
            self.insert_text_at_cursor(event.character)
        else:
            return

        event.prevent_default()
        event.stop()


class InputWidget(Widget):
    command_mode: bool = False

    def compose(self) -> ComposeResult:
        yield CommandOverview()
        yield InputContainer(CommandInput(), CustomInput())

    @property
    def text_input(self) -> CustomInput:
        return self.query_one(CustomInput)

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
        print(event)
        if event.character == ">" or event.key == Keys.Enter or event.key == Keys.Return:
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
            await self.text_input.input_key(event)
