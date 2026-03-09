"""
Reverse translation input bar.
User types in Spanish → Enter → translates to English → auto-copies to clipboard.
"""
import logging
import pyperclip
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout,
                              QLineEdit, QPushButton, QLabel)
from PyQt6.QtCore import QTimer
from modules.parser.message_parser import ChatMessage
from modules.history.context_memory import ContextMemory

logger = logging.getLogger(__name__)


class ReverseInputBar(QWidget):
    """Bottom bar for reverse translation (target→source direction)."""

    def __init__(self, llm_engine, settings, parent=None):
        super().__init__(parent)
        self._llm = llm_engine
        self._settings = settings
        self._last_result = ""
        self._empty_memory = ContextMemory(max_size=0)
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 4, 8, 8)
        outer.setSpacing(4)

        row = QHBoxLayout()
        self._input = QLineEdit()
        self._input.setPlaceholderText(
            "Escribe en español... (Enter para traducir y copiar)"
        )
        self._input.setObjectName("reverseInput")
        self._input.returnPressed.connect(self._on_enter)

        self._copy_btn = QPushButton("📋")
        self._copy_btn.setFixedWidth(36)
        self._copy_btn.setToolTip("Copiar última traducción")
        self._copy_btn.setObjectName("copyButton")
        self._copy_btn.clicked.connect(self._copy_last)

        row.addWidget(self._input)
        row.addWidget(self._copy_btn)

        self._feedback = QLabel("")
        self._feedback.setObjectName("feedbackLabel")
        self._feedback.setStyleSheet("color:#00BFFF; font-size:10pt;")
        self._feedback.setVisible(False)

        outer.addLayout(row)
        outer.addWidget(self._feedback)

    def _on_enter(self):
        text = self._input.text().strip()
        if not text:
            return
        self._input.setEnabled(False)
        dummy = ChatMessage(user="me", message=text, raw=text)
        # Reverse direction: target→source
        self._llm.translate_async(
            msg=dummy,
            history=self._empty_memory,
            source_lang=self._settings.target_language,
            target_lang=self._settings.source_language,
            on_ready=self._on_ready,
            on_error=self._on_error,
        )

    def _on_ready(self, _original: ChatMessage, translated: str):
        self._last_result = translated
        pyperclip.copy(translated)
        self._input.clear()
        self._input.setEnabled(True)
        self._show_feedback(f"✅ Copiado: {translated}")

    def _on_error(self, _original: ChatMessage, error: str):
        self._input.setEnabled(True)
        self._show_feedback(f"❌ Error: {error[:60]}")

    def _show_feedback(self, text: str):
        self._feedback.setText(text)
        self._feedback.setVisible(True)
        QTimer.singleShot(3000, lambda: self._feedback.setVisible(False))

    def _copy_last(self):
        if self._last_result:
            pyperclip.copy(self._last_result)
            self._show_feedback(f"✅ Copiado: {self._last_result[:60]}")