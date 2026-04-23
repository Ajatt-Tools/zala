"""
Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""

from collections.abc import Callable

from loguru import logger

from zala.config import ScreenshotPreviewOpts
from zala.main_window import ZalaSelect
from zala.screenshot import ZalaScreenshot
from zala.screenshot_preview import UserSelectionResult
from zala.utils import qconnect


class ZalaTakeScreenRegion:
    """
    Handles screen region selection for screenshot capture.

    This class manages the lifecycle of a selection window (ZalaSelect)
    that allows the user to select a region of the screen.
    """

    _sel: None | ZalaSelect = None
    _scr: ZalaScreenshot

    def __init__(self, scr: ZalaScreenshot) -> None:
        """
        Initialize the region selector with a screenshot utility.
        """
        self._scr = scr
        self._sel = None

    def _cleanup_selection_window(self) -> None:
        """Properly clean up the previous ZalaSelect window."""
        if self._sel is not None:
            logger.debug(f"deleting {self._sel.__class__.__name__} window")
            # https://doc.qt.io/qt-6/qwidget.html#close
            self._sel.close()
            self._sel.deleteLater()
            self._sel = None

    def select_area(self, on_finish: Callable[[UserSelectionResult], None], opts: ScreenshotPreviewOpts) -> None:
        """
        Launch a full‑screen selection window for the user to choose a region.

        Captures the current screen, creates a ZalaSelect window with the captured
        image, and connects the provided callback to the selection‑finished signal.
        The window is shown full‑screen.

        Args:
            on_finish: Callback called when selection is complete.
            opts: Configuration options for the preview widget.
        """
        self._sel = ZalaSelect(self._scr.capture_screen(), opts=opts)
        qconnect(self._sel.selection_finished, on_finish)
        qconnect(self._sel.selection_finished, lambda selection: self._cleanup_selection_window())
        self._sel.showFullScreen()
