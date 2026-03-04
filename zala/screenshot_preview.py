"""
Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""

from PyQt6.QtCore import Qt, pyqtSignal, QRect
from PyQt6.QtGui import QPen, QPixmap, QPainter, QKeyEvent, QMouseEvent, QWheelEvent, QPaintEvent, QTransform
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsRectItem, QGraphicsView, QWidget

from zala.config import ScreenshotPreviewOpts, ZoomOpts
from zala.rubber_band import UserSelectionRubberBand
from zala.utils import q_emit, make_solid_pen, make_brush, clamp


class ScreenshotPreview(QGraphicsView):
    """Fullscreen graphics view that displays a screenshot and handles region selection via rubber band."""

    _scene: QGraphicsScene
    _screen_pixmap: QPixmap
    _rubber_band: UserSelectionRubberBand

    selection_finished = pyqtSignal(QRect)
    selection_aborted = pyqtSignal()

    def __init__(
        self,
        screen_pixmap: QPixmap,
        parent: QWidget | None = None,
        opts: ScreenshotPreviewOpts | None = None,
        zoomopts: ZoomOpts | None = None,
    ):
        """Initialize the preview with the captured screen pixmap and set up the rubber band selection."""
        super().__init__(parent)

        # Assign member variables
        self._opts = opts or ScreenshotPreviewOpts()
        self._zoomopts = zoomopts or ZoomOpts()
        self._screen_pixmap = screen_pixmap
        self._scene = QGraphicsScene(self)
        self._rubber_band = UserSelectionRubberBand(self, opts=opts)

        # Set properties
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setObjectName("main_window_contents")
        self.setScene(self._scene)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        # Draw scene
        self._scene.addPixmap(self._screen_pixmap)
        self._fill_viewport_with_pattern()
        self.setSceneRect(self._screen_pixmap.rect().toRectF())

    def _fill_viewport_with_pattern(self) -> QGraphicsRectItem:
        """
        Add fill overlay to the scene.

        Note: The border is drawn separately as a fixed viewport-level overlay in paintEvent so it stays visible at any zoom level.
        Unset pen to avoid drawing the border here.
        """

        return self._scene.addRect(
            self._screen_pixmap.rect().toRectF(),
            QPen(Qt.PenStyle.NoPen),
            make_brush(self._opts.fill_brush_pattern, self._opts.fill_brush_color),
        )

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """
        Key is pressed, but not released.
        Doesn't work when app is in background.

        Reference: https://doc.qt.io/qt-6/qwidget.html#keyPressEvent
        """
        if event.key() == Qt.Key.Key_Escape:
            q_emit(self.selection_aborted)
        return super().keyPressEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        Begin rubber band selection on left mouse button press.

        Reference: https://doc.qt.io/qt-6/qrubberband.html#details
        """
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
            q_emit(self.selection_finished, self._current_scene_rectangle())
        return super().mouseReleaseEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        """
        Reference: https://doc.qt.io/qt-6/qgraphicsview.html#wheelEvent
        Note that calling super().wheelEvent(event) here will result in extra scrolling up or down.
        """
        self._zoom_screenshot_preview(event)

    def paintEvent(self, event: QPaintEvent) -> None:
        """
        Draw the scene.
        """
        super().paintEvent(event)
        self._draw_viewport_border()

    def _current_scene_rectangle(self) -> QRect:
        """
        Map rubber band rect from view (widget) coordinates to scene coordinates.
        This ensures the correct image region is selected when the view is zoomed.

        https://doc.qt.io/qt-6/qgraphicsview.html#mapToScene-3
        https://doc.qt.io/qt-6/qpolygonf.html#boundingRect
        """
        return self.mapToScene(self._rubber_band.geometry()).boundingRect().toRect()

    def _zoom_screenshot_preview(self, event: QWheelEvent) -> QWheelEvent:
        """
        Zoom in or out on the screenshot when the scroll wheel is used.
        https://doc.qt.io/qt-6/qwheelevent.html
        """
        zo = self._zoomopts

        # angleDelta().y() provides the angle through which the common vertical mouse wheel was rotated since the previous event.
        zoom_factor = zo.zoom_in_factor if event.angleDelta().y() > 0 else zo.zoom_out_factor

        # Compute the new cumulative scale to enforce min/max limits.
        # Returns the **horizontal** scaling factor: https://doc.qt.io/qt-6/qtransform.html#m11
        # This implementation uses the same factor for both width and height.
        current_scale = self.transform().m11()
        new_scale = clamp(zo.min_zoom, current_scale * zoom_factor, zo.max_zoom)

        # Skip if already at the zoom limit.
        if new_scale == current_scale:
            return event

        # Apply the new absolute scale centered on the position under the cursor.
        self.setTransform(QTransform.fromScale(new_scale, new_scale))

        return event

    def _draw_viewport_border(self) -> None:
        """
        Paint a fixed-position border on the viewport.

        The border is drawn at widget (viewport) level rather than in the scene so
        that it stays at a constant pixel size and is always fully visible,
        regardless of the current zoom level.
        """
        viewport = self.viewport()
        if viewport is None:
            return
        thickness = self._opts.border_thickness
        half_thickness = thickness // 2

        painter = QPainter(viewport)
        painter.setPen(make_solid_pen(self._opts.outline_color, thickness))
        painter.drawRect(viewport.rect().adjusted(half_thickness, half_thickness, -half_thickness, -half_thickness))
        painter.end()
