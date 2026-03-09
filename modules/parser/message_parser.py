"""
Message parser module.
Converts OCR lines into structured ChatMessage objects.
"""
import logging
import time
from dataclasses import dataclass, field
from modules.ocr.ocr_engine import OCRLine
from modules.parser.username_patterns import get_pattern

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """A single parsed chat message."""
    user: str
    message: str
    raw: str
    timestamp: float = field(default_factory=time.time)


class MessageParser:
    """Parses OCR lines into ChatMessage objects."""

    def __init__(self, pattern_name: str = "twitch", custom_pattern: str = ""):
        self._pattern = get_pattern(pattern_name, custom_pattern)
        self._pattern_name = pattern_name

    def update_pattern(self, pattern_name: str, custom_pattern: str = "") -> None:
        self._pattern = get_pattern(pattern_name, custom_pattern)
        self._pattern_name = pattern_name

    def parse(self, ocr_lines: list[OCRLine]) -> list[ChatMessage]:
        """
        Parse OCR lines into ChatMessages.
        Unmatched lines are appended to the previous message (multi-line support).
        """
        if self._pattern is None:
            return []

        messages: list[ChatMessage] = []
        current: ChatMessage | None = None

        for line in ocr_lines:
            text = line.text.strip()
            if not text:
                continue
            match = self._pattern.match(text)
            if match:
                if current is not None:
                    messages.append(current)
                current = ChatMessage(
                    user=match.group("user").strip(),
                    message=match.group("message").strip(),
                    raw=text,
                )
            else:
                if current is not None:
                    current.message += " " + text
                    current.raw += " " + text

        if current is not None:
            messages.append(current)

        return messages