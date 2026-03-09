"""
Settings panel dialog — full configuration UI.
"""
import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QSlider, QSpinBox, QLineEdit, QRadioButton, QPushButton,
    QGroupBox, QButtonGroup, QFormLayout,
)
from PyQt6.QtCore import Qt
from modules.translation.ollama_checker import check_ollama
from modules.parser.username_patterns import PLATFORM_LABELS

logger = logging.getLogger(__name__)


class SettingsPanel(QDialog):
    """Settings dialog. Edits AppSettings in-place on Save."""

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self.setWindowTitle("WEBCductor — Settings")
        self.setMinimumWidth(440)
        self.setObjectName("settingsDialog")
        self._build_ui()
        self._load_values()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # LLM
        g = QGroupBox("🤖 LLM Model")
        fl = QFormLayout(g)
        self._model_combo = QComboBox()
        self._model_combo.setEditable(True)
        ref_btn = QPushButton("↻")
        ref_btn.setFixedWidth(30)
        ref_btn.clicked.connect(self._populate_models)
        row = QHBoxLayout()
        row.addWidget(self._model_combo)
        row.addWidget(ref_btn)
        fl.addRow("Model:", row)
        layout.addWidget(g)

        # Languages
        g2 = QGroupBox("🌐 Languages")
        fl2 = QFormLayout(g2)
        self._src = QComboBox()
        self._src.addItems(["English", "Spanish"])
        self._tgt = QComboBox()
        self._tgt.addItems(["Spanish", "English"])
        fl2.addRow("Source:", self._src)
        fl2.addRow("Target:", self._tgt)
        layout.addWidget(g2)

        # Capture
        g3 = QGroupBox("📸 Capture")
        vl = QVBoxLayout(g3)
        irow = QHBoxLayout()
        irow.addWidget(QLabel("Interval:"))
        self._int_btns: dict[int, QRadioButton] = {}
        self._int_grp = QButtonGroup(self)
        for ms, lbl in [(500, "0.5s"), (1000, "1s"), (2000, "2s")]:
            b = QRadioButton(lbl)
            self._int_btns[ms] = b
            self._int_grp.addButton(b)
            irow.addWidget(b)
        vl.addLayout(irow)
        fl3 = QFormLayout()
        self._pat_combo = QComboBox()
        for key, lbl in PLATFORM_LABELS.items():
            self._pat_combo.addItem(lbl, key)
        self._pat_combo.currentIndexChanged.connect(self._on_pat_change)
        self._custom_re = QLineEdit()
        self._custom_re.setPlaceholderText("^(?P<user>\\S+):\\s*(?P<message>.+)$")
        self._custom_lbl = QLabel("Custom Regex:")
        fl3.addRow("Pattern:", self._pat_combo)
        fl3.addRow(self._custom_lbl, self._custom_re)
        vl.addLayout(fl3)
        layout.addWidget(g3)

        # Overlay
        g4 = QGroupBox("🪟 Overlay")
        fl4 = QFormLayout(g4)
        self._op_slider = QSlider(Qt.Orientation.Horizontal)
        self._op_slider.setRange(40, 100)
        self._op_lbl = QLabel("85%")
        self._op_slider.valueChanged.connect(lambda v: self._op_lbl.setText(f"{v}%"))
        op_row = QHBoxLayout()
        op_row.addWidget(self._op_slider)
        op_row.addWidget(self._op_lbl)
        self._font_spin = QSpinBox()
        self._font_spin.setRange(8, 24)
        fl4.addRow("Opacity:", op_row)
        fl4.addRow("Font Size:", self._font_spin)
        layout.addWidget(g4)

        # History
        g5 = QGroupBox("📜 History")
        fl5 = QFormLayout(g5)
        self._hist_slider = QSlider(Qt.Orientation.Horizontal)
        self._hist_slider.setRange(10, 50)
        self._hist_lbl = QLabel("35")
        self._hist_slider.valueChanged.connect(lambda v: self._hist_lbl.setText(str(v)))
        h_row = QHBoxLayout()
        h_row.addWidget(self._hist_slider)
        h_row.addWidget(self._hist_lbl)
        fl5.addRow("Messages:", h_row)
        layout.addWidget(g5)

        # Hotkeys
        g6 = QGroupBox("⌨ Hotkeys")
        fl6 = QFormLayout(g6)
        self._hk_input = QLineEdit()
        self._hk_input.setPlaceholderText("ctrl+shift+t")
        fl6.addRow("Toggle Overlay:", self._hk_input)
        layout.addWidget(g6)

        # Buttons
        btn_row = QHBoxLayout()
        save_btn = QPushButton("💾 Save")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

        self._populate_models()
        self._on_pat_change()

    def _populate_models(self):
        self._model_combo.clear()
        result = check_ollama()
        if result["running"] and result["models"]:
            for m in result["models"]:
                self._model_combo.addItem(m)
        else:
            self._model_combo.addItem(self._settings.ollama_model)

    def _on_pat_change(self):
        is_manual = self._pat_combo.currentData() == "manual"
        self._custom_re.setVisible(is_manual)
        self._custom_lbl.setVisible(is_manual)

    def _load_values(self):
        s = self._settings
        idx = self._model_combo.findText(s.ollama_model)
        if idx >= 0:
            self._model_combo.setCurrentIndex(idx)
        else:
            self._model_combo.setEditText(s.ollama_model)
        self._src.setCurrentText(s.source_language)
        self._tgt.setCurrentText(s.target_language)
        if s.capture_interval_ms in self._int_btns:
            self._int_btns[s.capture_interval_ms].setChecked(True)
        for i in range(self._pat_combo.count()):
            if self._pat_combo.itemData(i) == s.username_pattern:
                self._pat_combo.setCurrentIndex(i)
                break
        self._custom_re.setText(s.custom_pattern)
        self._op_slider.setValue(int(s.overlay_opacity * 100))
        self._font_spin.setValue(s.font_size)
        self._hist_slider.setValue(s.history_size)
        self._hk_input.setText(s.hotkey_toggle)
        self._on_pat_change()

    def _save(self):
        s = self._settings
        s.ollama_model = self._model_combo.currentText().strip()
        s.source_language = self._src.currentText()
        s.target_language = self._tgt.currentText()
        for ms, btn in self._int_btns.items():
            if btn.isChecked():
                s.capture_interval_ms = ms
                break
        s.username_pattern = self._pat_combo.currentData()
        s.custom_pattern = self._custom_re.text().strip()
        s.overlay_opacity = self._op_slider.value() / 100.0
        s.font_size = self._font_spin.value()
        s.history_size = self._hist_slider.value()
        s.hotkey_toggle = self._hk_input.text().strip()
        s.save()
        self.accept()