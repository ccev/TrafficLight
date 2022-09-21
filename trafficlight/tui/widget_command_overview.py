from __future__ import annotations
from typing import Type, TYPE_CHECKING

from rich.style import Style
from rich.text import Text
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static
from textual.message import Message, MessageTarget

from .models import CommandEnum, Mode, Toggle, Action, ALL_COMMANDS, NoPostStatic

if TYPE_CHECKING:
    from .app import TrafficLightGui


class SetCommandMode(Message):
    def __init__(self, sender: MessageTarget, value: bool):
        super().__init__(sender)
        self.value = value


class CommandReceived(Message):
    def __init__(self, sender: MessageTarget, command: CommandEnum):
        super().__init__(sender)
        self.command: CommandEnum = command


class CommandOverview(Widget):
    def __init__(self):
        super().__init__()
        self.display = False

    def compose(self) -> ComposeResult:
        for command in ALL_COMMANDS:
            yield CommandEntryContainer(command)

    def update_toggle(self, toggle: Toggle, value: bool) -> None:
        entry: CommandEntry = self.query_one(f"#{toggle.id}")
        entry.update_text(value)


class CommandEntryContainer(Widget):
    def __init__(self, command: Type[CommandEnum]):
        super().__init__(id=command.__name__)
        self._command: Type[CommandEnum] = command

    def compose(self) -> ComposeResult:
        yield Static(self._command.plural().upper(), id="command-title")
        for cmd in self._command:
            yield CommandEntry(cmd)


class CommandEntry(NoPostStatic):
    app: TrafficLightGui

    def __init__(self, command: CommandEnum):
        self._command = command
        text = self.get_text()
        super().__init__(text, id=str(command.id))

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

    def update_text(self, toggle_value: bool = False) -> None:
        text = self.get_text(toggle_value)
        super().update(text)

    async def on_click(self) -> None:
        await self.emit(SetCommandMode(self, False))
        await self.emit(CommandReceived(self, self._command))
