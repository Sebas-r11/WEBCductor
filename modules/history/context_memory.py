"""
Conversation context memory module.
Rolling buffer of recent messages for LLM context.
"""
import logging
from collections import deque
from modules.parser.message_parser import ChatMessage

logger = logging.getLogger(__name__)


class ContextMemory:
    """Rolling in-memory buffer of the last N chat messages."""

    def __init__(self, max_size: int = 35):
        self._memory: deque[ChatMessage] = deque(maxlen=max_size)

    def add(self, msg: ChatMessage) -> None:
        self._memory.append(msg)

    def get_all(self) -> list[ChatMessage]:
        return list(self._memory)

    def format_for_prompt(self) -> str:
        return "\n".join(f"{m.user}: {m.message}" for m in self._memory)

    def is_duplicate(self, msg: ChatMessage) -> bool:
        recent = list(self._memory)[-5:]
        return any(m.user == msg.user and m.message == msg.message for m in recent)

    def clear(self) -> None:
        self._memory.clear()

    def __len__(self) -> int:
        return len(self._memory)