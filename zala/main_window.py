"""
Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""

from loguru import logger
from PyQt6.QtCore import QMargins, QPointF, QRect, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import (
    QBrush,
    QCloseEvent,
    QColor,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPen,
    QPixmap,
)
from PyQt6.QtWidgets import (
    QApplication,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
    QMainWindow,
    QWidget,
)

from zala.consts import APP_NAME
from zala.rubber_band import UserSelectionRubberBand
from zala.screenshot import TakenScreenshot, ZalaException, ZalaScreenshot
from zala.utils import q_emit, qconnect


def add_border(
    scene: QGraphicsScene,
    box_size: QSize,
    border_thickness: int = 2,
    outline_color: QColor = QColor(255, 0, 0),
) -> QGraphicsRectItem:
    # Reference: https://doc.qt.io/qt-6/qbrush.html#details
    fill_brush = QBrush()
    fill_brush.setStyle(Qt.BrushStyle.Dense7Pattern)
    fill_brush.setColor(QColor(127, 127, 127, 85))

    outline_pen = QPen()
    # Reference: https://doc.qt.io/qt-6/qt.html#PenStyle-enum
    outline_pen.setStyle(Qt.PenStyle.SolidLine)
    # Reference: https://doc.qt.io/qt-6/qt.html#PenJoinStyle-enum
    outline_pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
    outline_pen.setColor(outline_color)
    outline_pen.setWidth(border_thickness)

    return scene.addRect(
        QRectF(
            QPointF(border_thickness / 2, border_thickness / 2),
            box_size.shrunkBy(QMargins(0, 0, border_thickness, border_thickness)).toSizeF(),
        ),
        outline_pen,
        fill_brush,
    )


class ScreenshotPreview(QGraphicsView):
    """
    Fullscreen view
    """

    _scene: QGraphicsScene
    _screen_pixmap: QPixmap
    _rubber_band: UserSelectionRubberBand

    selection_finished = pyqtSignal(QRect)
    selection_aborted = pyqtSignal()

    def __init__(self, screen_pixmap: QPixmap, parent: QWidget | None = None):
        super().__init__(parent)
        # Assign member variables
        self._screen_pixmap = screen_pixmap
        self._scene = QGraphicsScene(self)
        self._rubber_band = UserSelectionRubberBand(self)
        # Set properties
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setObjectName("main_window_contents")
        self.setScene(self._scene)
        # Draw scene
        self._scene.addPixmap(self._screen_pixmap)
        self.setSceneRect(self._screen_pixmap.rect().toRectF())
        add_border(self._scene, box_size=self._screen_pixmap.size(), border_thickness=2)

    # Reference: https://doc.qt.io/qt-6/qwidget.html#keyPressEvent

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """
        Key is pressed, but not released.
        Doesn't work when app is in background.
        """
        if event.key() == Qt.Key.Key_Escape:
            q_emit(self.selection_aborted)
        return super().keyPressEvent(event)

    # Reference: https://doc.qt.io/qt-6/qrubberband.html#details

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._rubber_band.set_selection_start(event.pos())
            self._rubber_band.show()
        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._rubber_band.set_selection_end(event.pos())
            self._rubber_band.show()
        return super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._rubber_band.set_selection_end(event.pos())
            self._rubber_band.hide()
            q_emit(self.selection_finished, self._rubber_band.geometry())
        return super().mouseReleaseEvent(event)


class ZalaSelect(QMainWindow):
    """
    The main window that is being shown when the app is called.
    """

    _taken: TakenScreenshot
    _user_selected: QPixmap | None = None

    def __init__(self, scr: ZalaScreenshot, parent=None):
        super().__init__(parent)
        self.setWindowTitle(APP_NAME)
        self._scr = scr
        self._taken = self._scr.capture_screen()
        self._set_fullscreen_settings()
        self._init_ui()
        self._preview = ScreenshotPreview(screen_pixmap=self._taken.pixmap, parent=self)
        self.setCentralWidget(self._preview)
        qconnect(self._preview.selection_finished, self._handle_selection_finished)
        qconnect(self._preview.selection_aborted, self._handle_selection_aborted)

    @property
    def user_selection(self) -> QPixmap:
        if self._user_selected is None:
            raise ZalaException("user selection is empty")
        return self._user_selected

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

    def showFullScreen(self):
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
        return super().closeEvent(event)

    def _handle_selection_finished(self, selection: QRect) -> bool:
        logger.debug("Region selection finished.")
        self._user_selected = self._taken.pixmap.copy(selection)
        return self.close()  # self.closeEvent() will fire.

    def _handle_selection_aborted(self) -> bool:
        logger.debug("Region selection aborted.")
        return self.close()  # self.closeEvent() will fire.
