from __future__ import annotations

from typing import TYPE_CHECKING

from textual.layout import Vertical
from .models import Mode

if TYPE_CHECKING:
    from .app import TrafficLightGui
    from .widget_request import RequestWidget


class ScreenWidget(Vertical):
    app: TrafficLightGui
    children: list[RequestWidget]

    def _filter_requests(self, requests: list[RequestWidget]) -> None:
        text = self.app.filter_text.casefold()

        for request in requests:
            request.filter(mode=self.app.current_mode, text=text)

    def filter(self):
        self._filter_requests(self.children)

    def add_requests(self, requests: list[RequestWidget]):
        self._filter_requests(requests)
        self.mount(*requests)
