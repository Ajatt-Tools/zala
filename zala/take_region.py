"""
Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""

import threading
from collections.abc import Callable
from contextlib import ExitStack

from loguru import logger
from PyQt6.QtWidgets import QMainWindow

from zala.config import ScreenshotPreviewOpts
from zala.exceptions import SelectionInProgressError
from zala.main_window import ZalaSelect
from zala.screenshot import ZalaScreenshot
from zala.screenshot_preview import UserSelectionResult
from zala.utils import qconnect


def close_and_delete(window: QMainWindow) -> None:
    """Close a window and schedule it for deletion."""
    logger.debug(f"deleting {window.__class__.__name__} window")
    # https://doc.qt.io/qt-6/qwidget.html#close
    window.close()
    window.deleteLater()


class ZalaTakeScreenRegion:
    """
    Handles screen region selection for screenshot capture.

    This class manages the lifecycle of a selection window (ZalaSelect)
    that allows the user to select a region of the screen.
    If a selection is already in progress, an exception is raised.
    """

    _sel: None | ZalaSelect = None
    _scr: ZalaScreenshot
    _lock: threading.Lock

    def __init__(self, scr: ZalaScreenshot) -> None:
        """
        Initialize the region selector with a screenshot utility.
        """
        self._scr = scr
        self._sel = None
        self._lock = threading.Lock()

    def _cleanup_selection_window(self) -> None:
        """Properly clean up the previous ZalaSelect window."""
        if (sel := self._sel) is not None:
            self._sel = None
            close_and_delete(sel)

    def select_area(self, on_finish: Callable[[UserSelectionResult], None], opts: ScreenshotPreviewOpts) -> None:
        """
        Launch a fullscreen selection window for the user to choose a region.

        Captures the current screen, creates a ZalaSelect window with the captured
        image, and connects the provided callback to the selection_finished signal.
        The window is shown full-screen.

        Args:
            on_finish: Callback called when selection is complete.
            opts: Configuration options for the preview widget.

        Raises:
            SelectionInProgressError: If another region selection is already in progress.
        """
        if not self._lock.acquire(blocking=False):
            raise SelectionInProgressError("a region selection is already in progress")
        with ExitStack() as stack:
            # Auto-release the lock on any non-local exit from this block until
            # ownership is handed off to the signal handler below.
            stack.callback(self._lock.release)
            self._cleanup_selection_window()
            self._sel = window = ZalaSelect(self._scr.capture_screen(), opts=opts)

            def handle_finished(selection: UserSelectionResult) -> None:
                """Run the client callback, then always release the lock and clean up."""
                try:
                    on_finish(selection)
                finally:
                    self._lock.release()
                    self._cleanup_selection_window()

            qconnect(window.selection_finished, handle_finished)
            window.showFullScreen()
            # After the signal handler is connected, cancel the auto-release.
            # Ownership is now with the signal callback.
            stack.pop_all()
