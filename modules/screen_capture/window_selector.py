"""
Window selector module.
Enumerates all visible, non-minimized desktop windows using pywin32.
"""
import logging
import win32gui

logger = logging.getLogger(__name__)


def list_windows() -> list[dict]:
    """
    Returns a list of dicts {"hwnd": int, "title": str}
    for all visible, non-minimized windows with non-empty titles.
    """
    windows = []

    def _enum_callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) and not win32gui.IsIconic(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title.strip():
                windows.append({"hwnd": hwnd, "title": title})

    try:
        win32gui.EnumWindows(_enum_callback, None)
    except Exception as e:
        logger.error("Error enumerating windows: %s", e)
    return windows


def get_window_rect(hwnd: int) -> dict:
    """
    Returns absolute screen coordinates of a window.
    Returns {"x": int, "y": int, "w": int, "h": int}.
    """
    try:
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        return {"x": left, "y": top, "w": right - left, "h": bottom - top}
    except Exception as e:
        logger.error("Error getting window rect for hwnd %s: %s", hwnd, e)
        return {"x": 0, "y": 0, "w": 800, "h": 600}