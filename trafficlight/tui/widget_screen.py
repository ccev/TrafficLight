from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

from textual.containers import Vertical
from textual.dom import NodeList

from .models import Toggle

if TYPE_CHECKING:
    from .app import TrafficLightGui
    from .widget_request import RequestWidget


class ScreenWidget(Vertical):
    app: TrafficLightGui

    def _filter_requests(self, requests: Iterable[RequestWidget]) -> None:
        text = self.app.filter_text.casefold().strip()
        first_only = self.app.toggles[Toggle.FIRST_PROTO_ONLY]

        for request in requests:
            request.filter(mode=self.app.current_mode, first_only=first_only, text=text)

    def filter(self) -> None:
        self._filter_requests((c for c in self.children if isinstance(c, RequestWidget)))

    async def add_requests(self, requests: list[RequestWidget]) -> None:
        self._filter_requests(requests)
        await self.mount(*requests)

        if self.app.toggles[Toggle.FOLLOW]:
            requests[-1].scroll_visible()

    def clear(self) -> None:
        for child in self.children:
            if isinstance(child, RequestWidget):
                child.remove()
