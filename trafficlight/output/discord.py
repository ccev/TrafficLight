from __future__ import annotations

from typing import TYPE_CHECKING, Sequence, Iterable, TypeVar

import aiohttp
import discord

from trafficlight.config import config
from .base import BaseOutput

if TYPE_CHECKING:
    from trafficlight.proto_utils.proto import Proto, Message

T = TypeVar("T")


def chunks(iter_: Sequence[T], size: int) -> Iterable[Sequence[T]]:
    """Yield equally sized chunks from an iterable"""
    for i in range(0, len(iter_), size):
        yield iter_[i : i + size]


class DiscordOutput(BaseOutput):
    async def start(self) -> None:
        pass

    async def add_record(self, rpc_id: int, rpc_status: int, protos: list[Proto], rpc_handle: int | None = None) -> None:
        now = discord.utils.utcnow()
        embeds = []

        footer_text = f"RPC ID {rpc_id} | RPC STATUS {rpc_status}"
        if rpc_handle is not None:
            footer_text = f"{footer_text} | RPC HANDLE {rpc_handle}"

        for proto in protos:
            embed = discord.Embed(title=f"{proto.method_value} | {proto.method_name}")
            embed.set_footer(text=footer_text)
            embed.timestamp = now
            self._add_discord_field(proto, embed)
            embeds.append(embed)

        async with aiohttp.ClientSession() as session:
            webhook: discord.Webhook = discord.Webhook.from_url(config.webhook, session=session)

            for part_embeds in chunks(embeds, 10):
                await webhook.send(
                    embeds=part_embeds,
                    avatar_url="https://www.br.de/kinder/gruen-ddr-dpa-100~_v-img__16__9__l_-"
                    "1dc0e8f74459dd04c91a0d45af4972b9069f1135.jpg?version=f989e",
                    username="Traffic Light 🚦",
                )

    @staticmethod
    def _add_discord_field(proto: Proto, embed: discord.Embed) -> None:
        def make_message_text(message: Message, prefix: str = "") -> None:
            def get_payload() -> str:
                data = message.to_string(False)
                if message.payload is None:
                    data = "[Blackbox]\n" + data
                value = f"```\n{data}\n```"
                if len(value) > 1024:
                    print(f"{message.type} {message.name}: {message.to_string()}")
                    return "`[Payload too long for Discord. Check logs]`"
                return value

            if message.name is None:
                formatted_payload = get_payload()
                name = f"{prefix}[Unknown {message.type} Message]"
            else:
                name = f"{prefix}{message.type}: {message.name}"
                if message.payload is not None and len(message.payload.ListFields()) == 0:
                    formatted_payload = "`{}`"
                else:
                    formatted_payload = get_payload()
            embed.add_field(name=name, value=formatted_payload, inline=False)

        for proto_message in proto.messages:
            make_message_text(proto_message)

        if proto.proxy:
            proxy_preifx = f"Proxy: {proto.proxy.method_value} | {proto.proxy.method_name}\n"
            for proto_message in proto.messages:
                make_message_text(proto_message, prefix=proxy_preifx)
