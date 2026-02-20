"""Message tool for CLI interaction."""

from typing import Any

from nanobot.agent.tools.base import Tool


class MessageTool(Tool):
    """Tool for CLI - no-op since output is shown directly."""

    @property
    def name(self) -> str:
        return "message"

    @property
    def description(self) -> str:
        return "Send a message to the user. Use this when you want to communicate something."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The message content to send"
                }
            },
            "required": ["content"]
        }

    async def execute(self, content: str, **kwargs: Any) -> str:
        # In CLI mode, messages are shown directly in the response
        return "Message displayed"
