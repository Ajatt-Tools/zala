"""
Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""

import dataclasses
import enum
import typing
from typing import Self

from PyQt6.QtCore import QPoint, QRect, Qt, pyqtSignal
from PyQt6.QtGui import (
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPen,
    QPixmap,
    QResizeEvent,
    QTransform,
    QWheelEvent,
)
from PyQt6.QtWidgets import (
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
    QWidget,
)

from zala.config import ScreenshotPreviewOpts, ZoomOpts
from zala.help_label import ZalaHelpLabel
from zala.rubber_band import UserSelectionRubberBand
from zala.screenshot import TakenScreenshot, add_padding
from zala.utils import clamp, make_brush, make_solid_pen, q_emit


@dataclasses.dataclass
class PreviewState:
    """Holds the current zoom and rotation state for the screenshot preview view."""

    zoom: float = 1.0
    rotation: float = 0.0

    def apply(self, view: QGraphicsView) -> QGraphicsView:
        """
        Apply the current zoom and rotation as a single combined transform.
        Rotation is applied first, then scale.
        """
        view.setTransform(QTransform().rotate(self.rotation).scale(self.zoom, self.zoom))
        return view

    def set_zoom(self, new_scale: float) -> Self:
        """Set the zoom level to the given scale value."""
        self.zoom = new_scale
        return self

    def set_rotation(self, rotation: float) -> Self:
        """Set the rotation angle in degrees."""
        self.rotation = rotation
        return self


class UserSelectionResult(typing.NamedTuple):
    """Result of a user's region selection, containing a pixmap on success or an error message on failure."""

    pixmap: QPixmap | None = None
    rect: QRect | None = None
    error: str = ""

    def is_empty(self) -> bool:
        """Return True if neither a pixmap nor an error has been set."""
        return not (self.pixmap or self.error)


class ZalaAction(enum.Enum):
    """Enumeration of possible user actions during preview interaction."""

    pan = enum.auto()
    selection = enum.auto()
    none = enum.auto()


class ZalaMouseButton(enum.Enum):
    """Enumeration of mouse buttons used for preview interaction."""

    left = enum.auto()
    right = enum.auto()
    none = enum.auto()


def get_pressed_button(event: QMouseEvent) -> ZalaMouseButton:
    """Return which mouse button is currently pressed in the event."""
    if event.buttons() & Qt.MouseButton.LeftButton:
        return ZalaMouseButton.left
    if event.buttons() & Qt.MouseButton.RightButton:
        return ZalaMouseButton.right
    return ZalaMouseButton.none


class ScreenshotPreview(QGraphicsView):
    """Fullscreen graphics view that displays a screenshot and handles region selection via rubber band."""

    _scene: QGraphicsScene
    _taken: TakenScreenshot
    _rubber_band: UserSelectionRubberBand
    _pan_start: QPoint | None
    _help_label: ZalaHelpLabel

    selection_finished = pyqtSignal(UserSelectionResult)
    selection_aborted = pyqtSignal()

    def __init__(
        self,
        taken: TakenScreenshot,
        parent: QWidget | None = None,
        opts: ScreenshotPreviewOpts | None = None,
        zoomopts: ZoomOpts | None = None,
    ):
        """Initialize the preview with the captured screen pixmap and set up the rubber band selection."""
        super().__init__(parent)

        # Assign member variables
        self._opts = opts or ScreenshotPreviewOpts()
        self._zoomopts = zoomopts or ZoomOpts()
        self._state = PreviewState()
        self._taken = taken
        self._padded = add_padding(
            self._taken.pixmap,
            padding_size=max(taken.pixmap.width(), taken.pixmap.height()),
        )
        self._scene = QGraphicsScene(self)
        self._rubber_band = UserSelectionRubberBand(self, opts=opts)
        self._pan_start = None
        self._help_label = ZalaHelpLabel(self).setup_help_label(self.viewport(), is_visible=opts.show_help)

        # Set properties
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setObjectName("main_window_contents")
        self.setScene(self._scene)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        # Draw scene
        self._scene.addPixmap(self._padded.pixmap)
        self._fill_viewport_with_pattern()
        self.setSceneRect(self._padded.pixmap.rect().toRectF())
        self._center_on_content()

    def _fill_viewport_with_pattern(self) -> QGraphicsRectItem:
        """
        Add fill overlay to the scene.

        Note: The border is drawn separately as a fixed viewport-level overlay in paintEvent so it stays visible at any zoom level.
        Unset pen to avoid drawing the border here.
        """
        return self._scene.addRect(
            self._taken.pixmap.rect().toRectF(),
            QPen(Qt.PenStyle.NoPen),
            make_brush(self._opts.fill_brush_pattern, self._opts.fill_brush_color),
        )

    def _center_on_content(self) -> None:
        """Center the view on the actual screenshot content, skipping the padding bars."""

        center_x = self._padded.padding_size + self._taken.pixmap.width() / 2
        center_y = self._padded.padding_size + self._taken.pixmap.height() / 2
        self.centerOn(center_x, center_y)

    def _ongoing_action(self) -> ZalaAction:
        """Return the current user action based on rubber band and pan state."""
        if self._rubber_band.has_selection_start():
            return ZalaAction.selection
        if self._pan_start is not None:
            return ZalaAction.pan
        return ZalaAction.none

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """
        Key is pressed, but not released.
        Doesn't work when app is in background.

        Reference: https://doc.qt.io/qt-6/qwidget.html#keyPressEvent
        """
        match event.key():
            case Qt.Key.Key_Escape | Qt.Key.Key_Q:
                # 'q' for quit
                q_emit(self.selection_aborted)
            case Qt.Key.Key_I:
                # 'i' for info
                self._help_label.toggle_visibility()
        return super().keyPressEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        Begin rubber band selection on left mouse button press.
        Begin panning on right mouse button press.

        Reference: https://doc.qt.io/qt-6/qrubberband.html#details
        """
        match event.button():
            case Qt.MouseButton.LeftButton:
                self._rubber_band.set_selection_start(event.pos())
                self._rubber_band.show()
            case Qt.MouseButton.RightButton:
                self._pan_start = event.pos()
        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """
        Update rubber band selection as the mouse moves while the left button is held.
        Pan the view while the right button is held.
        """
        match get_pressed_button(event), self._ongoing_action():
            case ZalaMouseButton.left, ZalaAction.selection:
                self._rubber_band.set_selection_end(event.pos())
                self._rubber_band.show()
            case ZalaMouseButton.right, ZalaAction.pan:
                delta = event.pos() - self._pan_start
                self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
                self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
                self._pan_start = event.pos()
        return super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """
        Finalize the rubber band selection on left mouse button release and emit the selected region.
        End panning on right mouse button release.
        """
        match event.button(), self._ongoing_action():
            case Qt.MouseButton.LeftButton, ZalaAction.selection:
                self._rubber_band.set_selection_end(event.pos())
                self._rubber_band.hide()
                self._emit_selection_result()
                self._rubber_band.reset_start_point()
            case Qt.MouseButton.RightButton, ZalaAction.pan:
                self._pan_start = None

        return super().mouseReleaseEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        """
        Reference: https://doc.qt.io/qt-6/qgraphicsview.html#wheelEvent
        Note that calling super().wheelEvent(event) here will result in extra scrolling up or down.
        """
        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self._rotate_screenshot_preview(event)
        else:
            self._zoom_screenshot_preview(event)

    def paintEvent(self, event: QPaintEvent) -> None:
        """
        Draw the scene.
        """
        super().paintEvent(event)
        self._draw_viewport_border()

    def _emit_selection_result(self) -> None:
        """Emit the selection result with the captured pixmap if the region is large enough."""
        rect = self._rubber_band.geometry()
        if self._opts.rect_has_sufficient_size(rect):
            q_emit(self.selection_finished, UserSelectionResult(pixmap=self.grab(rect), rect=rect))
        else:
            q_emit(self.selection_finished, UserSelectionResult(error="Region is too small."))

    def _zoom_screenshot_preview(self, event: QWheelEvent) -> None:
        """
        Zoom in or out on the screenshot when the scroll wheel is used.
        https://doc.qt.io/qt-6/qwheelevent.html
        """
        zo = self._zoomopts

        # angleDelta().y() provides the angle through which the common vertical mouse wheel was rotated since the previous event.
        zoom_factor = zo.zoom_in_factor if event.angleDelta().y() > 0 else zo.zoom_out_factor

        # Compute the new cumulative scale to enforce min/max limits.
        # This implementation uses the same factor for both width and height.
        # Clamp to min/max limits and skip if the scale would not change.
        new_scale = clamp(zo.min_zoom, self._state.zoom * zoom_factor, zo.max_zoom)

        # Skip if already at the zoom limit.
        if new_scale == self._state.zoom:
            return

        # Apply centered on the position under the cursor (AnchorUnderMouse is set in __init__).
        self._state.set_zoom(new_scale).apply(self)

    def _rotate_screenshot_preview(self, event: QWheelEvent) -> None:
        """
        Rotate the screenshot preview when Shift+scroll is used.
        Scroll up rotates clockwise; scroll down rotates counterclockwise.
        Rotation is always centered on the cursor position.
        """
        step = self._zoomopts.rotation_step
        delta = step if event.angleDelta().y() > 0 else -step

        # Apply the new transform without any built-in anchor adjustment.
        # AnchorUnderMouse / AnchorViewCenter rely on scroll bar range, which may be
        # zero when the scene doesn't fill the viewport, causing inconsistent behavior.
        self._state.set_rotation((self._state.rotation + delta) % 360).apply(self)

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

    def resizeEvent(self, event: QResizeEvent | None) -> None:
        """Reposition the help label when the viewport is resized."""
        super().resizeEvent(event)
        self._help_label.position_help_label(self.viewport())
