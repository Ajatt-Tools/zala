"""
Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""

from loguru import logger
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
)

from zala.config import ScreenshotPreviewOpts
from zala.consts import APP_NAME
from zala.screenshot import TakenScreenshot, repr_pixmap
from zala.screenshot_preview import ScreenshotPreview, UserSelectionResult
from zala.utils import ensure_cursor_restored, q_emit, qconnect


class ZalaSelect(QMainWindow):
    """
    The main window that is being shown when the app is called.
    """

    _taken: TakenScreenshot
    _selection_result_emitted: bool

    selection_finished = pyqtSignal(UserSelectionResult)

    def __init__(
        self,
        screen: TakenScreenshot,
        parent: QWidget | None = None,
        opts: ScreenshotPreviewOpts | None = None,
    ) -> None:
        """Initialize the selection window with the captured screen and set up the preview widget."""
        super().__init__(parent)
        self.setWindowTitle(APP_NAME)
        self._selection_result_emitted = False
        self._taken = screen
        self._set_fullscreen_settings()
        self._init_ui()
        self._preview = ScreenshotPreview(taken=self._taken, parent=self, opts=opts)
        self.setCentralWidget(self._preview)
        qconnect(self._preview.selection_finished, self._handle_selection_finished)
        qconnect(self._preview.selection_aborted, self._handle_selection_aborted)

    def _set_fullscreen_settings(self) -> None:
        """Configure the window for frameless, transparent fullscreen display."""
        # By setting the border thickness and margin to zero,
        # we ensure that the whole screen is captured.
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("QGraphicsView, QMainWindow {border:0px; margin:0px;} ")

        # Enables the widget to have a transparent background.
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # FramelessWindowHint flag also enables transparent background.
        # WindowStaysOnTopHint & Popup flags ensures that the widget is the top window.
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)

    def _init_ui(self) -> None:
        """Set the minimum window size."""
        self.setMinimumSize(320, 240)

    def showFullScreen(self) -> None:
        """
        Show the window in fullscreen mode, positioned on the captured screen with a cross cursor.
        https://doc.qt.io/qt-6/qwidget.html#showFullScreen
        """
        logger.debug("Zala window is opening.")
        geometry = self._taken.screen.geometry()
        self.move(geometry.topLeft())
        self.resize(geometry.size())
        QApplication.setOverrideCursor(Qt.CursorShape.CrossCursor)
        return super().showFullScreen()

    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Restore the cursor and emit an abort if no selection result was emitted yet.

        This is a safety net for unexpected closes (e.g. window manager).
        Normal closes go through _handle_selection_finished or _handle_selection_aborted,
        which emit the result before calling close().
        """
        logger.debug("Zala window is closing.")
        # Restore cursor
        ensure_cursor_restored()
        if not self._selection_result_emitted:
            self._selection_result_emitted = True
            q_emit(self.selection_finished, UserSelectionResult(error="closed without selection"))
        return super().closeEvent(event)

    def _handle_selection_finished(self, selection: UserSelectionResult) -> bool:
        """Emit the selection result and close the window."""
        if selection.pixmap:
            logger.debug(f"Selection finished: {repr_pixmap(selection.pixmap)}")
        else:
            logger.debug(selection.error.capitalize())
        self._selection_result_emitted = True
        q_emit(self.selection_finished, selection)
        return self.close()  # self.closeEvent() will fire.

    def _handle_selection_aborted(self) -> bool:
        """Emit an abort error and close the window."""
        logger.debug("Region selection aborted.")
        self._selection_result_emitted = True
        q_emit(self.selection_finished, UserSelectionResult(error="selection aborted"))
        return self.close()  # self.closeEvent() will fire.
