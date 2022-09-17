from __future__ import annotations

from enum import Enum
from types import DynamicClassAttribute
from typing import TYPE_CHECKING

from textual.widgets import Static

if TYPE_CHECKING:
    pass


class Mode(Enum):
    WATCH = "w"
    PAUSE = "p"
    FILTER_TEXT = "t"
    FILTER_METHODS = "m"
    FILTER_MESSAGES = "s"

    @DynamicClassAttribute
    def title(self) -> str:
        return self.name.title().replace("_", " ")


class NoPostStatic(Static):
    def post_render(self, renderable):
        return renderable
