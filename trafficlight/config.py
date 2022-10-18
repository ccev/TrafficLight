#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from enum import Enum

import rtoml
from pydantic import BaseModel, ValidationError


class Output(Enum):
    UI = "ui"
    PRINT = "print"
    DISCORD = "discord"


class Config(BaseModel):
    host: str
    port: int
    output: Output
    webhook: str


with open("config.toml", mode="r") as _config_file:
    _raw_config = rtoml.load(_config_file)

try:
    _config = Config(**_raw_config)
except ValidationError as e:
    print(f"Config validation error!\n{e}")
    sys.exit(1)

config = _config
