"""
3-step setup wizard shown at application startup.
"""
import logging
from PyQt6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QWidget, QRubberBand, QApplication, QSizePolicy,
)
from PyQt6.QtCore import Qt, QRect, QPoint, QSize, pyqtSignal
from PyQt6.QtGui import QPainter, QColor
from modules.screen_capture.window_selector import list_windows, get_window_rect
from modules.translation.ollama_checker import check_ollama, get_install_instructions

logger = logging.getLogger(__name__)

PAGE_WINDOW = 0
PAGE_OLLAMA = 1
PAGE_READY  = 2


class ZoneSelector(QWidget):
    """Full-screen rubber-band zone selector."""
    zone_selected = pyqtSignal(dict)

    def __init__(self, screen_pixmap, parent=None):
        super().__init__(parent)
        self._pixmap = screen_pixmap
        self._origin = QPoint()
        self._rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setWindowOpacity(0.75)

    def paintEvent(self, _):
        p = QPainter(self)
        p.drawPixmap(0, 0, self._pixmap)
        p.fillRect(self.rect(), QColor(0, 0, 0, 90))

    def mousePressEvent(self, e):
        self._origin = e.pos()
        self._rubber_band.setGeometry(QRect(self._origin, QSize()))
        self._rubber_band.show()

    def mouseMoveEvent(self, e):
        self._rubber_band.setGeometry(QRect(self._origin, e.pos()).normalized())

    def mouseReleaseEvent(self, e):
        rect = QRect(self._origin, e.pos()).normalized()
        self._rubber_band.hide()
        self.hide()
        if rect.width() > 10 and rect.height() > 10:
            self.zone_selected.emit(
                {"x": rect.x(), "y": rect.y(), "w": rect.width(), "h": rect.height()}
            )
        self.close()


class WindowZonePage(QWizardPage):
    """Page 1 — Select window and capture zone."""

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._zone = settings.capture_zone.copy()
        self._hwnd = settings.selected_hwnd
        self._windows: list[dict] = []
        self.setTitle("Step 1 — Select Window & Zone")
        self.setSubTitle(
            "Choose the chat window, then click 'Select Zone' to draw the capture area."
        )
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        row = QHBoxLayout()
        self._combo = QComboBox()
        self._combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._combo.currentIndexChanged.connect(self._on_win_change)
        ref = QPushButton("↻ Refresh")
        ref.clicked.connect(self._populate)
        row.addWidget(QLabel("Window:"))
        row.addWidget(self._combo, 1)
        row.addWidget(ref)
        layout.addLayout(row)

        zone_btn = QPushButton("🔲 Select Zone (drag on screen)")
        zone_btn.clicked.connect(self._start_zone)
        layout.addWidget(zone_btn)

        self._zone_lbl = QLabel("No zone selected yet.")
        self._zone_lbl.setStyleSheet("color:#AAAAAA;")
        layout.addWidget(self._zone_lbl)

        self._populate()
        self._update_lbl()

    def _populate(self):
        self._windows = list_windows()
        self._combo.clear()
        for w in self._windows:
            self._combo.addItem(w["title"], w["hwnd"])
        for i, w in enumerate(self._windows):
            if w["hwnd"] == self._settings.selected_hwnd:
                self._combo.setCurrentIndex(i)
                break

    def _on_win_change(self, idx: int):
        if 0 <= idx < len(self._windows):
            self._hwnd = self._windows[idx]["hwnd"]

    def _start_zone(self):
        screen = QApplication.primaryScreen()
        pixmap = screen.grabWindow(0)
        self._sel = ZoneSelector(pixmap)
        self._sel.zone_selected.connect(self._on_zone)
        self._sel.show()

    def _on_zone(self, zone: dict):
        self._zone = zone
        self._update_lbl()

    def _update_lbl(self):
        z = self._zone
        if z.get("w", 0) > 0:
            self._zone_lbl.setText(
                f"✅ Zone: x={z['x']}, y={z['y']}, w={z['w']}, h={z['h']}"
            )
        else:
            self._zone_lbl.setText("No zone selected yet.")
        self.completeChanged.emit()

    def isComplete(self) -> bool:
        return self._zone.get("w", 0) > 0

    def get_result(self) -> dict:
        return {
            "hwnd": self._hwnd,
            "title": self._combo.currentText(),
            "zone": self._zone,
        }


class OllamaCheckPage(QWizardPage):
    """Page 2 — Verify Ollama."""

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._selected_model = settings.ollama_model
        self._ok = False
        self.setTitle("Step 2 — Verify Ollama")
        self.setSubTitle("WEBCductor needs a local Ollama LLM for contextual translation.")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        check_btn = QPushButton("🔍 Check Ollama Status")
        check_btn.clicked.connect(self._check)
        layout.addWidget(check_btn)

        self._status = QLabel("Press 'Check' to verify Ollama.")
        self._status.setWordWrap(True)
        layout.addWidget(self._status)

        layout.addWidget(QLabel("Available models:"))
        self._model_combo = QComboBox()
        self._model_combo.setVisible(False)
        self._model_combo.currentTextChanged.connect(
            lambda t: setattr(self, "_selected_model", t)
        )
        layout.addWidget(self._model_combo)

        self._instructions = QLabel("")
        self._instructions.setWordWrap(True)
        self._instructions.setStyleSheet("color:#FFAA00; font-size:9pt;")
        self._instructions.setVisible(False)
        layout.addWidget(self._instructions)

    def _check(self):
        result = check_ollama()
        if result["running"]:
            self._ok = True
            self._status.setText("✅ Ollama is running!")
            self._status.setStyleSheet("color:#00FF88;")
            self._model_combo.clear()
            for m in result["models"]:
                self._model_combo.addItem(m)
            self._model_combo.setVisible(True)
            self._instructions.setVisible(False)
            idx = self._model_combo.findText(self._settings.ollama_model)
            if idx >= 0:
                self._model_combo.setCurrentIndex(idx)
        else:
            self._ok = False
            self._status.setText("❌ Ollama not found.")
            self._status.setStyleSheet("color:#FF4444;")
            self._model_combo.setVisible(False)
            self._instructions.setText(get_install_instructions())
            self._instructions.setVisible(True)
        self.completeChanged.emit()

    def isComplete(self) -> bool:
        return self._ok

    def get_result(self) -> dict:
        return {"model": self._selected_model or self._settings.ollama_model}


class ReadyPage(QWizardPage):
    """Page 3 — Summary and start."""

    def __init__(self, wizard_ref, parent=None):
        super().__init__(parent)
        self._wizard = wizard_ref
        self.setTitle("Step 3 — Ready to Start")
        self.setSubTitle("Everything is set. Click Finish to start translating.")
        layout = QVBoxLayout(self)
        self._summary = QLabel("Configuration summary will appear here.")
        self._summary.setWordWrap(True)
        self._summary.setStyleSheet("color:#FFFFFF; font-size:10pt; padding:8px;")
        layout.addWidget(self._summary)

    def initializePage(self):
        try:
            p1 = self._wizard.page(PAGE_WINDOW).get_result()
            p2 = self._wizard.page(PAGE_OLLAMA).get_result()
            s = self._wizard._settings
            self._summary.setText(
                f"📸 Window:  {p1.get('title','N/A')}\n"
                f"🔲 Zone:    x={p1['zone']['x']}, y={p1['zone']['y']}, "
                f"w={p1['zone']['w']}, h={p1['zone']['h']}\n"
                f"🤖 Model:   {p2.get('model','N/A')}\n"
                f"🌐 Direction: {s.source_language} → {s.target_language}"
            )
        except Exception as e:
            logger.warning("Summary error: %s", e)


class SetupWizard(QWizard):
    """3-step startup wizard."""

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self.setWindowTitle("WEBCductor — Setup")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setMinimumSize(540, 440)

        self._p_window = WindowZonePage(settings)
        self._p_ollama = OllamaCheckPage(settings)
        self._p_ready  = ReadyPage(self)

        self.addPage(self._p_window)
        self.addPage(self._p_ollama)
        self.addPage(self._p_ready)

    def get_final_settings(self):
        """Merge wizard results into settings and save."""
        p1 = self._p_window.get_result()
        p2 = self._p_ollama.get_result()
        self._settings.selected_hwnd = p1["hwnd"]
        self._settings.selected_window_title = p1["title"]
        self._settings.capture_zone = p1["zone"]
        self._settings.ollama_model = p2["model"]
        self._settings.save()
        return self._settings