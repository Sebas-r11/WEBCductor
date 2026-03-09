"""
Screen capture engine module.
Periodically captures a defined screen zone and emits frames via Qt signal.
"""
import logging
import time
import numpy as np
import mss
import cv2
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


class CaptureEngine(QThread):
    """
    QThread that continuously captures a screen zone at a given interval.
    Emits frame_ready(np.ndarray) with each new BGR frame.
    """
    frame_ready = pyqtSignal(object)  # np.ndarray

    def __init__(self, zone: dict, interval_ms: int = 1000, parent=None):
        super().__init__(parent)
        self._zone = zone
        self._interval = interval_ms / 1000.0
        self._running = False
        self._paused = False

    def run(self):
        self._running = True
        logger.info("CaptureEngine started. Zone: %s", self._zone)
        with mss.mss() as sct:
            while self._running:
                if not self._paused:
                    try:
                        monitor = {
                            "top": self._zone["y"],
                            "left": self._zone["x"],
                            "width": self._zone["w"],
                            "height": self._zone["h"],
                        }
                        screenshot = sct.grab(monitor)
                        frame = np.array(screenshot)
                        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                        self.frame_ready.emit(frame_bgr)
                    except Exception as e:
                        logger.error("Capture error: %s", e)
                time.sleep(self._interval)
        logger.info("CaptureEngine stopped.")

    def set_zone(self, zone: dict):
        self._zone = zone

    def set_interval(self, interval_ms: int):
        self._interval = interval_ms / 1000.0

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def stop(self):
        self._running = False
        self.wait()