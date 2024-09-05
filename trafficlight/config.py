from __future__ import annotations

import sys
from enum import Enum

import tomllib
from pydantic import BaseModel, ValidationError


class Output(Enum):
    UI = "ui"
    PRINT = "print"
    DISCORD = "discord"


class Config(BaseModel):
    host: str = "0.0.0.0"
    port: int = 3335
    output: Output = Output.UI
    webhook: str = ""
    use_golbat_raws: bool = False


try:
    with open("config.toml", mode="rb") as _config_file:
        _raw_config = tomllib.load(_config_file)

    try:
        _config = Config(**_raw_config)
    except ValidationError as e:
        print(f"Config validation error!\n{e}")
        sys.exit(1)
except FileNotFoundError:
    _config = Config()

config = _config
