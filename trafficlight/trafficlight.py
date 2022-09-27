import asyncio
import json

from aiohttp import web
from pydantic import ValidationError

from .config import config
from .model import RequestModel
from .output import get_output
from .proto_utils import Proto

output = get_output(config.output)


class TrafficReceiver:
    @staticmethod
    async def process_data(data: RequestModel):
        processed_protos = [Proto.from_raw(data.rpcid, p) for p in data.protos]
        await output.add_record(rpc_id=data.rpcid, rpc_status=data.rpcstatus, protos=processed_protos)

    @staticmethod
    async def __traffic_post(request: web.Request):
        try:
            data = await request.json()
        except json.JSONDecodeError:
            return web.Response(status=400, text="bad json")

        try:
            model = RequestModel(**data)
        except ValidationError as e:
            return web.Response(status=400, text=f"malformed data: {e}")

        await TrafficReceiver.process_data(model)

        return web.Response(text="OK")

    def get_app(self):
        app = web.Application()
        app.add_routes([web.post("/", self.__traffic_post)])

        return app


t = TrafficReceiver()
server = t.get_app()


async def main():
    await output.start()
    asyncio.create_task(web._run_app(server, host=config.host, port=config.port, print=lambda _: _))
    await asyncio.Event().wait()


def run():
    asyncio.run(main())
