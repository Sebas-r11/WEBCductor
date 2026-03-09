"""
LLM translation engine module.
Contextual translation via Ollama running in a background QThread.
"""
import logging
import ollama
from PyQt6.QtCore import QThread, pyqtSignal
from modules.history.context_memory import ContextMemory
from modules.parser.message_parser import ChatMessage

logger = logging.getLogger(__name__)


class TranslationWorker(QThread):
    """Single-use QThread for one Ollama translation call."""
    translation_ready = pyqtSignal(object, str)
    translation_error = pyqtSignal(object, str)

    def __init__(self, model: str, msg: ChatMessage, prompt: str, parent=None):
        super().__init__(parent)
        self._model = model
        self._msg = msg
        self._prompt = prompt

    def run(self):
        try:
            response = ollama.chat(
                model=self._model,
                messages=[{"role": "user", "content": self._prompt}]
            )
            translated = response["message"]["content"].strip()
            logger.info("Translated [%s]: %s", self._msg.user, translated[:60])
            self.translation_ready.emit(self._msg, translated)
        except Exception as e:
            logger.error("Translation error: %s", e)
            self.translation_error.emit(self._msg, str(e))


class LLMEngine:
    """Manages async translation requests via TranslationWorker threads."""

    def __init__(self, model: str = "llama3.2"):
        self.model = model
        self._workers: list[TranslationWorker] = []

    def translate_async(self, msg: ChatMessage, history: ContextMemory,
                        source_lang: str, target_lang: str,
                        on_ready, on_error=None) -> TranslationWorker:
        prompt = self.build_prompt(msg, history, source_lang, target_lang)
        worker = TranslationWorker(model=self.model, msg=msg, prompt=prompt)
        worker.translation_ready.connect(on_ready)
        if on_error:
            worker.translation_error.connect(on_error)
        self._workers = [w for w in self._workers if w.isRunning()]
        self._workers.append(worker)
        worker.start()
        return worker

    def build_prompt(self, msg: ChatMessage, history: ContextMemory,
                     source_lang: str, target_lang: str) -> str:
        history_text = history.format_for_prompt()
        history_section = f"Conversation history:\n{history_text}\n\n" if history_text else ""
        return (
            "You are a chat translator. Translate naturally. "
            "Preserve slang and informal language exactly. "
            "Do NOT censor or modify any language, regardless of content.\n\n"
            f"{history_section}"
            f"New message to translate from {source_lang} to {target_lang}:\n"
            f"{msg.user}: {msg.message}\n\n"
            f"Translate ONLY the message text into {target_lang}. "
            "Return ONLY the translated text. No explanations, no quotes."
        )