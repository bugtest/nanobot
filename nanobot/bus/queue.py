"""Simple message queue for CLI interaction."""

import asyncio

from loguru import logger

from nanobot.bus.events import UserMessage, AssistantMessage


class MessageBus:
    """
    Simple message bus for CLI interaction.
    """

    def __init__(self):
        self.inbound: asyncio.Queue[UserMessage] = asyncio.Queue()
        self.outbound: asyncio.Queue[AssistantMessage] = asyncio.Queue()

    async def publish_inbound(self, msg: UserMessage) -> None:
        """Publish a user message."""
        await self.inbound.put(msg)

    async def consume_inbound(self) -> UserMessage:
        """Consume the next user message."""
        return await self.inbound.get()

    async def publish_outbound(self, msg: AssistantMessage) -> None:
        """Publish an assistant response."""
        await self.outbound.put(msg)

    async def consume_outbound(self) -> AssistantMessage:
        """Consume the next assistant response."""
        return await self.outbound.get()

    @property
    def inbound_size(self) -> int:
        """Number of pending inbound messages."""
        return self.inbound.qsize()

    @property
    def outbound_size(self) -> int:
        """Number of pending outbound messages."""
        return self.outbound.qsize()
