#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pydantic import BaseModel


class ProtoModel(BaseModel):
    method: int
    request: str
    response: str


class RequestModel(BaseModel):
    rpcid: int
    rpcstatus: int
    protos: list[ProtoModel]
