from pydantic import BaseModel, Field


class ProtoModel(BaseModel):
    method: int = Field(alias="type")
    request: str | None
    response: str | None = Field(alias="payload")

    class Config:
        allow_population_by_field_name = True

class RequestModel(BaseModel):
    rpcid: int = 0
    rpchandle: int | None
    rpcstatus: int = 0
    protos: list[ProtoModel] = Field(alias="contents")

    class Config:
        allow_population_by_field_name = True
