from pydantic import BaseModel


class ProtoModel(BaseModel):
    method: int
    request: str
    response: str


class RequestModel(BaseModel):
    rpcid: int
    rpcstatus: int
    protos: list[ProtoModel]
