from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from trafficlight.tui import TrafficLightGui
from .base import BaseOutput

if TYPE_CHECKING:
    from trafficlight.proto_utils.proto import Proto


class UiOutput(BaseOutput):
    app: TrafficLightGui

    async def start(self) -> None:
        self.app = TrafficLightGui()
        asyncio.create_task(self.app.run_app())

    async def add_record(self, rpc_id: int, rpc_status: int, protos: list[Proto], rpc_handle: int | None = None) -> None:
        self.app.add_record(rpc_id=rpc_id, rpc_status=rpc_status, protos=protos, rpc_handle=rpc_handle)
