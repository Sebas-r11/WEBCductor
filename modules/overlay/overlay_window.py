"""
Main overlay window module.
Transparent, always-on-top, movable panel for displaying translations.
"""
import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QScrollArea, QFrame)
from PyQt6.QtCore import Qt, QPoint, QTimer
from modules.parser.message_parser import ChatMessage
from modules.overlay.message_widget import MessageWidget
from modules.overlay.reverse_input import ReverseInputBar

logger = logging.getLogger(__name__)


class TitleBar(QWidget):
    """Custom draggable title bar."""

    def __init__(self, parent_window, on_close, on_settings):
        super().__init__(parent_window)
        self._parent_window = parent_window
        self._drag_pos = QPoint()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 4, 4)

        title = QLabel("🌐 WEBCductor")
        title.setStyleSheet("color:#00BFFF; font-weight:bold; font-size:11pt;")

        btn_cfg = QPushButton("⚙")
        btn_cfg.setFixedSize(24, 24)
        btn_cfg.setObjectName("titleButton")
        btn_cfg.setToolTip("Settings")
        btn_cfg.clicked.connect(on_settings)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(24, 24)
        btn_close.setObjectName("titleButtonClose")
        btn_close.setToolTip("Close")
        btn_close.clicked.connect(on_close)

        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(btn_cfg)
        layout.addWidget(btn_close)
        self.setFixedHeight(36)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = (
                event.globalPosition().toPoint()
                - self._parent_window.frameGeometry().topLeft()
            )

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self._parent_window.move(
                event.globalPosition().toPoint() - self._drag_pos
            )


class OverlayWindow(QWidget):
    """Transparent always-on-top overlay showing translated messages."""

    def __init__(self, settings, llm_engine, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._llm_engine = llm_engine
        self._setup_window()
        self._build_ui()
        self.update_opacity(settings.overlay_opacity)

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(350, 450)
        self.resize(420, 560)

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)

        self._container = QFrame(self)
        self._container.setObjectName("overlayContainer")
        c_layout = QVBoxLayout(self._container)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(0)

        c_layout.addWidget(
            TitleBar(self, on_close=self.close, on_settings=self._open_settings)
        )

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#333;")
        c_layout.addWidget(sep)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setObjectName("messageScroll")
        self._scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self._msg_container = QWidget()
        self._msg_container.setObjectName("messageContainer")
        self._msg_layout = QVBoxLayout(self._msg_container)
        self._msg_layout.setContentsMargins(4, 4, 4, 4)
        self._msg_layout.setSpacing(2)
        self._msg_layout.addStretch()

        self._scroll.setWidget(self._msg_container)
        c_layout.addWidget(self._scroll, stretch=1)

        self._reverse_bar = ReverseInputBar(self._llm_engine, self._settings)
        c_layout.addWidget(self._reverse_bar)

        main.addWidget(self._container)

    def add_message(self, original: ChatMessage, translation: str):
        """Add translated message and scroll to bottom."""
        widget = MessageWidget(original, translation, self._settings.font_size)
        self._msg_layout.insertWidget(self._msg_layout.count() - 1, widget)
        QTimer.singleShot(
            50,
            lambda: self._scroll.verticalScrollBar().setValue(
                self._scroll.verticalScrollBar().maximum()
            ),
        )

    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()

    def update_opacity(self, opacity: float):
        self.setWindowOpacity(max(0.1, min(1.0, opacity)))

    def _open_settings(self):
        from modules.overlay.settings_panel import SettingsPanel
        panel = SettingsPanel(self._settings, parent=self)
        panel.exec()
        self.update_opacity(self._settings.overlay_opacity)