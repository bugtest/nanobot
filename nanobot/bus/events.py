"""Event types for CLI interaction."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class UserMessage:
    """User message from CLI."""

    content: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AssistantMessage:
    """Assistant response to CLI."""

    content: str
    timestamp: datetime = field(default_factory=datetime.now)
