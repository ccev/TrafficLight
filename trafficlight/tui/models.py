from typing import Type
from enum import Enum
from types import DynamicClassAttribute

from textual.widgets import Static


HOVER_CLASS = "hover"


class CommandEnum(Enum):
    @classmethod
    def plural(cls) -> str:
        return cls.__name__ + "s"

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


ALL_COMMANDS: list[Type[CommandEnum]] = [Mode, Toggle, Action]


class NoPostStatic(Static):
    def post_render(self, renderable):
        return renderable
