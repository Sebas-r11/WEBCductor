"""
Application settings module.
Defines AppSettings dataclass and provides load/save functionality via JSON.
"""
from dataclasses import dataclass, field, asdict
import json
import os
import logging

logger = logging.getLogger(__name__)

SETTINGS_PATH = "settings.json"


@dataclass
class AppSettings:
    ollama_model: str = "llama3.2"
    source_language: str = "English"
    target_language: str = "Spanish"
    history_size: int = 35
    overlay_opacity: float = 0.85
    capture_interval_ms: int = 1000
    username_pattern: str = "twitch"
    custom_pattern: str = ""
    hotkey_toggle: str = "ctrl+shift+t"
    font_size: int = 12
    selected_window_title: str = ""
    selected_hwnd: int = 0
    capture_zone: dict = field(default_factory=lambda: {"x": 0, "y": 0, "w": 400, "h": 300})

    def save(self, path: str = SETTINGS_PATH) -> None:
        """Serialize settings to JSON file."""
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=2)
            logger.info("Settings saved to %s", path)
        except Exception as e:
            logger.error("Failed to save settings: %s", e)

    @classmethod
    def load(cls, path: str = SETTINGS_PATH) -> "AppSettings":
        """Load settings from JSON file. Returns defaults if file not found."""
        if not os.path.exists(path):
            logger.info("No settings file found, using defaults.")
            return cls()
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            defaults = asdict(cls())
            defaults.update(data)
            return cls(**{k: defaults[k] for k in cls.__dataclass_fields__})
        except Exception as e:
            logger.error("Failed to load settings: %s. Using defaults.", e)
            return cls()