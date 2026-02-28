"""
Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""

import typing

from PyQt6.QtCore import QRect, QSize, Qt, pyqtSignal
from PyQt6.QtGui import (
    QCloseEvent,
    QPixmap,
)
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
)
from loguru import logger

from zala.consts import APP_NAME
from zala.screenshot import TakenScreenshot
from zala.screenshot_preview import ScreenshotPreview
from zala.utils import qconnect, q_emit


class UserSelectionResult(typing.NamedTuple):
    pixmap: QPixmap | None = None
    error: str = ""

    def is_empty(self) -> bool:
        return not (self.pixmap or self.error)


class ZalaSelect(QMainWindow):
    """
    The main window that is being shown when the app is called.
    """

    _taken: TakenScreenshot
    _user_selected: UserSelectionResult
    _min_selection_size: QSize = QSize(10, 10)

    selection_finished = pyqtSignal(UserSelectionResult)

    def __init__(self, screen: TakenScreenshot, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(APP_NAME)
        self._user_selected = UserSelectionResult()
        self._taken = screen
        self._set_fullscreen_settings()
        self._init_ui()
        self._preview = ScreenshotPreview(screen_pixmap=self._taken.pixmap, parent=self)
        self.setCentralWidget(self._preview)
        qconnect(self._preview.selection_finished, self._handle_selection_finished)
        qconnect(self._preview.selection_aborted, self._handle_selection_aborted)

    @property
    def user_selection(self) -> QPixmap | None:
        return self._user_selected.pixmap

    def _set_fullscreen_settings(self):
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

    def _init_ui(self):
        self.setMinimumSize(320, 240)

    def showFullScreen(self) -> None:
        logger.debug("Zala window is opening.")
        QApplication.setOverrideCursor(Qt.CursorShape.CrossCursor)
        geometry = self._taken.screen.geometry()
        self.move(geometry.topLeft())
        self.resize(geometry.size())
        return super().showFullScreen()

    def closeEvent(self, event: QCloseEvent) -> None:
        logger.debug("Zala window is closing.")
        # Restore cursor
        QApplication.restoreOverrideCursor()
        if self._user_selected.is_empty():
            q_emit(self.selection_finished, UserSelectionResult(error="selection aborted"))
        else:
            q_emit(self.selection_finished, self._user_selected)
        return super().closeEvent(event)

    def _handle_selection_finished(self, selection: QRect) -> bool:
        logger.debug("Region selection finished.")
        if (
            selection.width() >= self._min_selection_size.width()
            and selection.height() >= self._min_selection_size.height()
        ):
            self._user_selected = UserSelectionResult(pixmap=self._taken.pixmap.copy(selection))
        else:
            self._user_selected = UserSelectionResult(error="region is too small")
            logger.debug(f"Region is too small.")
        return self.close()  # self.closeEvent() will fire.

    def _handle_selection_aborted(self) -> bool:
        logger.debug("Region selection aborted.")
        self._user_selected = UserSelectionResult(error="selection aborted")
        return self.close()  # self.closeEvent() will fire.
