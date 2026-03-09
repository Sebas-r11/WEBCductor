"""
OCR post-processing and error correction module.
Cleans common OCR artifacts from extracted text.
"""
import re
import logging

logger = logging.getLogger(__name__)

_SUBSTITUTIONS = [
    (r"\|", "I"),
    (r"\bl\b", "1"),
]

_NOISE_PATTERN = re.compile(r"^[^a-zA-Z0-9]+$")


def correct(text: str) -> str:
    """
    Clean a single OCR text line.
    Returns empty string if the line is pure noise.
    """
    if not text:
        return ""
    text = text.strip()
    if _NOISE_PATTERN.match(text):
        return ""
    for pattern, replacement in _SUBSTITUTIONS:
        text = re.sub(pattern, replacement, text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()