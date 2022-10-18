#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from trafficlight.config import Output as _OutputType
from .base import BaseOutput
from .discord import DiscordOutput
from .print_ import PrintOutput
from .ui import UiOutput


def get_output(output_type: _OutputType) -> BaseOutput:
    if output_type == _OutputType.PRINT:
        return PrintOutput()
    elif output_type == _OutputType.DISCORD:
        return DiscordOutput()

    return UiOutput()
