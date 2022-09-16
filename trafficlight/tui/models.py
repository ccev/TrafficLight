from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from textual.widgets import Static

if TYPE_CHECKING:
    pass


class Mode(Enum):
    W = "Watch"
    T = "Filter Text"
    M = "Filter Methods"
    S = "Filter Messages"
    P = "Pause"


class NoPostStatic(Static):
    def post_render(self, renderable):
        return renderable
