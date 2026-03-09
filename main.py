"""
WEBCductor — Desktop AI Chat Translator
Entry point. Boots all modules, runs the setup wizard, and starts the pipeline.
"""
import sys
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("webcductor.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("main")

from PyQt6.QtWidgets import QApplication
from config.settings import AppSettings
from modules.screen_capture.capture_engine import CaptureEngine
from modules.ocr.ocr_engine import OCREngine
from modules.ocr.error_corrector import correct
from modules.parser.message_parser import MessageParser
from modules.history.context_memory import ContextMemory
from modules.translation.llm_engine import LLMEngine
from modules.overlay.overlay_window import OverlayWindow
from modules.overlay.wizard import SetupWizard


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("WEBCductor")

    # Load QSS stylesheet
    qss_path = os.path.join("assets", "styles", "overlay.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())

    # Load settings
    settings = AppSettings.load()
    logger.info("Settings loaded. Model=%s", settings.ollama_model)

    # Run setup wizard
    wizard = SetupWizard(settings)
    if wizard.exec() != QWizard.DialogCode.Accepted:
        logger.info("Wizard cancelled — exiting.")
        sys.exit(0)
    settings = wizard.get_final_settings()
    logger.info("Wizard done. Zone=%s Model=%s", settings.capture_zone, settings.ollama_model)

    # Initialize core modules (OCR is slow — init once here)
    logger.info("Initializing OCR engine...")
    ocr_engine   = OCREngine()
    context_mem  = ContextMemory(max_size=settings.history_size)
    msg_parser   = MessageParser(settings.username_pattern, settings.custom_pattern)
    llm_engine   = LLMEngine(model=settings.ollama_model)

    # Build UI
    overlay = OverlayWindow(settings, llm_engine)
    overlay.show()

    # Capture engine
    capture = CaptureEngine(
        zone=settings.capture_zone,
        interval_ms=settings.capture_interval_ms,
    )

    # Pipeline slot
    def on_frame(frame):
        ocr_lines = ocr_engine.extract(frame)
        for line in ocr_lines:
            line.text = correct(line.text)
        ocr_lines = [l for l in ocr_lines if l.text]
        new_msgs = msg_parser.parse(ocr_lines)
        for msg in new_msgs:
            if not context_mem.is_duplicate(msg):
                context_mem.add(msg)
                llm_engine.translate_async(
                    msg=msg,
                    history=context_mem,
                    source_lang=settings.source_language,
                    target_lang=settings.target_language,
                    on_ready=overlay.add_message,
                    on_error=lambda m, e: logger.error(
                        "Translation failed [%s]: %s", m.user, e
                    ),
                )

    capture.frame_ready.connect(on_frame)
    capture.start()

    # Global hotkey
    try:
        import keyboard
        keyboard.add_hotkey(settings.hotkey_toggle, overlay.toggle_visibility)
        logger.info("Hotkey registered: %s", settings.hotkey_toggle)
    except Exception as e:
        logger.warning("Could not register hotkey: %s", e)

    logger.info("WEBCductor running. Capturing: %s", settings.capture_zone)
    code = app.exec()

    # Cleanup
    capture.stop()
    context_mem.clear()
    settings.save()
    sys.exit(code)


if __name__ == "__main__":
    main()