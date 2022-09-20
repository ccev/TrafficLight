from __future__ import annotations

from enum import Enum
from types import DynamicClassAttribute

from textual.widgets import Static


class CommandEnum(Enum):
    @DynamicClassAttribute
    def title(self) -> str:
        # THIS_NAME -> This Name
        return self.name.title().replace("_", " ")

    @DynamicClassAttribute
    def id(self) -> str:
        # THIS_NAME -> this-name
        return self.name.lower().replace("_", "-")


class Mode(CommandEnum):
    WATCH = "w"
    FILTER_TEXT = "t"
    FILTER_METHODS = "m"
    FILTER_MESSAGES = "s"


class Toggle(CommandEnum):
    PAUSE = "p"
    FIRST_PROTO_ONLY = "1"
    FOLLOW = "f"


class Action(CommandEnum):
    EMPTY_LOG = "e"
    COPY_INSPECTED = "c"


class NoPostStatic(Static):
    def post_render(self, renderable):
        return renderable
