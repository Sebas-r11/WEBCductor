"""
Ollama availability checker module.
"""
import logging
import requests

logger = logging.getLogger(__name__)

TAGS_ENDPOINT = "http://localhost:11434/api/tags"


def check_ollama() -> dict:
    """Returns {"running": bool, "models": list[str], "error": str}."""
    try:
        response = requests.get(TAGS_ENDPOINT, timeout=3)
        response.raise_for_status()
        data = response.json()
        models = [m["name"] for m in data.get("models", [])]
        logger.info("Ollama running. Models: %s", models)
        return {"running": True, "models": models, "error": ""}
    except requests.exceptions.ConnectionError:
        return {"running": False, "models": [], "error": "Ollama is not running."}
    except Exception as e:
        return {"running": False, "models": [], "error": str(e)}


def get_install_instructions() -> str:
    return (
        "Ollama is not running or not installed.\n\n"
        "Follow these steps:\n\n"
        "  1. Download Ollama:  https://ollama.com/download\n"
        "  2. Install and launch Ollama.\n"
        "  3. Open PowerShell / CMD and run:\n\n"
        "         ollama pull llama3.2\n\n"
        "  4. Wait for the model to download (~2 GB).\n"
        "  5. Click 'Retry' once Ollama is running."
    )