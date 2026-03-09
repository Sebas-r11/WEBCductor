"""
Username detection patterns for different chat platforms.
"""
import re
import logging

logger = logging.getLogger(__name__)

PATTERNS: dict[str, str] = {
    "twitch":  r"^(?P<user>[a-zA-Z0-9_]{1,25}):\s*(?P<message>.+)$",
    "discord": r"^(?P<user>[a-zA-Z0-9_.\-]{1,32})\s{2,}(?P<message>.+)$",
    "kick":    r"^\[(?P<user>[^\]]+)\]:\s*(?P<message>.+)$",
    "generic": r"^(?P<user>\S+)\s[-:]\s(?P<message>.+)$",
}

PLATFORM_LABELS = {
    "twitch":  "Twitch / StreamElements",
    "discord": "Discord",
    "kick":    "Kick",
    "generic": "Generic (user: msg)",
    "manual":  "Manual (Custom Regex)",
}


def get_pattern(name: str, custom: str = "") -> re.Pattern | None:
    """Returns compiled regex for the given platform name."""
    if name == "manual":
        if not custom:
            logger.warning("Manual pattern selected but no custom regex provided.")
            return None
        try:
            compiled = re.compile(custom)
            if "user" not in compiled.groupindex or "message" not in compiled.groupindex:
                logger.error("Custom pattern must have (?P<user>) and (?P<message>) groups.")
                return None
            return compiled
        except re.error as e:
            logger.error("Invalid custom regex: %s", e)
            return None
    raw = PATTERNS.get(name, PATTERNS["generic"])
    try:
        return re.compile(raw)
    except re.error as e:
        logger.error("Failed to compile pattern '%s': %s", name, e)
        return None