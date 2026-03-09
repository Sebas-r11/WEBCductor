"""
Message widget module.
Displays one translated chat message with a highlight animation on arrival.
"""
import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import QTimer
from modules.parser.message_parser import ChatMessage

logger = logging.getLogger(__name__)

ACCENT = "#00BFFF"
DIM    = "#AAAAAA"
WHITE  = "#FFFFFF"
HIGHLIGHT = "background-color: rgba(0,191,255,0.18); border-radius:6px; padding:4px;"
NORMAL    = "background-color: transparent; border-radius:6px; padding:4px;"


class MessageWidget(QWidget):
    """
    Displays: username (cyan) / original (dim) / → translation (white).
    Plays a highlight flash on creation.
    """

    def __init__(self, original: ChatMessage, translation: str,
                 font_size: int = 12, parent=None):
        super().__init__(parent)
        self._build_ui(original, translation, font_size)
        self._play_highlight()

    def _build_ui(self, original: ChatMessage, translation: str, font_size: int):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(2)

        user_lbl = QLabel(original.user)
        user_lbl.setStyleSheet(
            f"color:{ACCENT}; font-weight:bold; font-size:{font_size-1}pt;"
        )
        orig_lbl = QLabel(original.message)
        orig_lbl.setStyleSheet(f"color:{DIM}; font-size:{font_size-2}pt;")
        orig_lbl.setWordWrap(True)

        trans_lbl = QLabel(f"→ {translation}")
        trans_lbl.setStyleSheet(
            f"color:{WHITE}; font-size:{font_size}pt; font-weight:500;"
        )
        trans_lbl.setWordWrap(True)

        layout.addWidget(user_lbl)
        layout.addWidget(orig_lbl)
        layout.addWidget(trans_lbl)
        self.setStyleSheet(NORMAL)

    def _play_highlight(self):
        self.setStyleSheet(HIGHLIGHT)
        QTimer.singleShot(1500, lambda: self.setStyleSheet(NORMAL))