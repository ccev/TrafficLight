from pydantic import BaseModel


class ProtoModel(BaseModel):
    method: int
    request: str | None
    response: str | None


class RequestModel(BaseModel):
    rpcid: int
    rpcstatus: int
    protos: list[ProtoModel]
