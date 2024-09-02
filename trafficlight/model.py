from pydantic import BaseModel, Field
from .config import config


class ProtoModel(BaseModel):
    if config.use_golbat_raws:
        method: int = Field(alias="type")
        request: str | None
        response: str | None = Field(alias="payload")
    else:
        method: int
        request: str | None
        response: str | None


class RequestModel(BaseModel):
    if config.use_golbat_raws:
        rpcid: int = 0
        rpchandle: int | None
        rpcstatus: int = 0
        protos: list[ProtoModel] = Field(alias="contents")
    else:
        rpcid: int
        rpchandle: int | None
        rpcstatus: int
        protos: list[ProtoModel]
