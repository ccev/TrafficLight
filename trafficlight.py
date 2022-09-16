import asyncio

from aiohttp import web

from trafficlight import Proto
from trafficlight.config import config
from trafficlight.output import get_output

output = get_output(config.output)


class TrafficReceiver:
    @staticmethod
    async def __traffic_post(request: web.Request):
        data = await request.json()

        rpc_id: int = data["rpcid"]
        rpc_status: int = data["rpcstatus"]
        sent_protos = data["protos"]
        processed_protos = [Proto.from_vm(rpc_id, p) for p in sent_protos]

        await output.add_record(rpc_id=rpc_id, rpc_status=rpc_status, protos=processed_protos)

        return web.Response(text="OK")

    def get_app(self):
        app = web.Application()
        app.add_routes([web.post("/", self.__traffic_post)])

        return app


t = TrafficReceiver()
server = t.get_app()


async def main():
    await output.start()
    asyncio.create_task(web._run_app(server, host=config.host, port=config.port))
    await asyncio.Event().wait()

asyncio.run(main())
