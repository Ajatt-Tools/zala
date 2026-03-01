"""
Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""

from PyQt6.QtCore import QSize, Qt, QRectF, QPointF, QMargins, pyqtSignal, QRect
from PyQt6.QtGui import QColor, QBrush, QPen, QPixmap, QPainter, QKeyEvent, QMouseEvent
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsRectItem, QGraphicsView, QWidget

from zala.rubber_band import UserSelectionRubberBand
from zala.config import ScreenshotPreviewOpts
from zala.utils import q_emit


def add_border(
    scene: QGraphicsScene,
    box_size: QSize,
    opts: ScreenshotPreviewOpts | None = None,
) -> QGraphicsRectItem:
    """Add a semi-transparent overlay with a colored border to the graphics scene."""
    opts = opts or ScreenshotPreviewOpts()

    # Reference: https://doc.qt.io/qt-6/qbrush.html#details
    fill_brush = QBrush()
    fill_brush.setStyle(Qt.BrushStyle.Dense7Pattern)
    fill_brush.setColor(opts.fill_brush_color)

    outline_pen = QPen()
    # Reference: https://doc.qt.io/qt-6/qt.html#PenStyle-enum
    outline_pen.setStyle(Qt.PenStyle.SolidLine)
    # Reference: https://doc.qt.io/qt-6/qt.html#PenJoinStyle-enum
    outline_pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
    outline_pen.setColor(opts.outline_color)
    outline_pen.setWidth(opts.border_thickness)

    return scene.addRect(
        QRectF(
            QPointF(opts.border_thickness / 2, opts.border_thickness / 2),
            box_size.shrunkBy(QMargins(0, 0, opts.border_thickness, opts.border_thickness)).toSizeF(),
        ),
        outline_pen,
        fill_brush,
    )


class ScreenshotPreview(QGraphicsView):
    """Fullscreen graphics view that displays a screenshot and handles region selection via rubber band."""

    _scene: QGraphicsScene
    _screen_pixmap: QPixmap
    _rubber_band: UserSelectionRubberBand

    selection_finished = pyqtSignal(QRect)
    selection_aborted = pyqtSignal()

    def __init__(
        self, screen_pixmap: QPixmap, parent: QWidget | None = None, opts: ScreenshotPreviewOpts | None = None
    ):
        """Initialize the preview with the captured screen pixmap and set up the rubber band selection."""
        super().__init__(parent)
        # Assign member variables
        self._screen_pixmap = screen_pixmap
        self._scene = QGraphicsScene(self)
        self._rubber_band = UserSelectionRubberBand(self, opts=opts)
        # Set properties
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setObjectName("main_window_contents")
        self.setScene(self._scene)
        # Draw scene
        self._scene.addPixmap(self._screen_pixmap)
        self.setSceneRect(self._screen_pixmap.rect().toRectF())
        add_border(self._scene, box_size=self._screen_pixmap.size(), opts=opts)

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
        """Begin rubber band selection on left mouse button press."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._rubber_band.set_selection_start(event.pos())
            self._rubber_band.show()
        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Update rubber band selection as the mouse moves while the left button is held."""
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._rubber_band.set_selection_end(event.pos())
            self._rubber_band.show()
        return super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Finalize the rubber band selection on left mouse button release and emit the selected region."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._rubber_band.set_selection_end(event.pos())
            self._rubber_band.hide()
            q_emit(self.selection_finished, self._rubber_band.geometry())
        return super().mouseReleaseEvent(event)
