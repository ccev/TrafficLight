from trafficlight.config import Output as _OutputType
from .base import AnyOutput
from .discord import DiscordOutput
from .print_ import PrintOutput
from .ui import UiOutput


def get_output(output_type: _OutputType) -> AnyOutput:
    if output_type == _OutputType.UI:
        return UiOutput()
    elif output_type == _OutputType.PRINT:
        return PrintOutput()
    elif output_type == _OutputType.DISCORD:
        return DiscordOutput()
