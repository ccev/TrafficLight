from __future__ import annotations

from typing import TYPE_CHECKING

from textual.layout import Vertical

if TYPE_CHECKING:
    from .app import TrafficLightGui
    from .widget_request import RequestWidget


class ScreenWidget(Vertical):
    app: TrafficLightGui

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.styles.padding = (0, 0, 0, 1)
        self.styles.width = 65
        self.styles.dock = "left"

    def add_requests(self, requests: list[RequestWidget]):
        self.mount(*requests)
