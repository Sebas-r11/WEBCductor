"""
OCR engine module.
Wraps PaddleOCR for text extraction from captured frames.
Must be initialized once at startup.
"""
import logging
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class OCRLine:
    """Represents one line of text detected by OCR."""
    text: str
    bbox: list
    confidence: float


class OCREngine:
    """
    Wrapper around PaddleOCR.
    Initialize once at app startup — init takes 3-5 seconds.
    """
    MIN_CONFIDENCE = 0.6

    def __init__(self):
        logger.info("Initializing PaddleOCR engine...")
        try:
            from paddleocr import PaddleOCR
            self._ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
            logger.info("PaddleOCR initialized successfully.")
        except Exception as e:
            logger.error("Failed to initialize PaddleOCR: %s", e)
            self._ocr = None

    def extract(self, frame: np.ndarray) -> list[OCRLine]:
        """
        Run OCR on a BGR numpy frame.
        Returns list of OCRLine sorted top-to-bottom, filtered by confidence.
        """
        if self._ocr is None:
            return []
        try:
            result = self._ocr.ocr(frame, cls=True)
            lines = []
            if result and result[0]:
                for item in result[0]:
                    bbox, (text, confidence) = item
                    if confidence >= self.MIN_CONFIDENCE and text.strip():
                        lines.append(OCRLine(text=text.strip(), bbox=bbox, confidence=confidence))
            lines.sort(key=lambda l: l.bbox[0][1])
            return lines
        except Exception as e:
            logger.error("OCR extraction error: %s", e)
            return []