"""
Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""

from PyQt6.QtCore import QPoint, QRect, QSize
from PyQt6.QtGui import QColor, QPainter, QPaintEvent, QPen
from PyQt6.QtWidgets import QRubberBand, QWidget

from zala.config import ScreenshotPreviewOpts


class UserSelectionRubberBand(QRubberBand):
    """
    Rubber band that is shown when the user selects an area of the pixmap.
    """

    _selection_start: QPoint = QPoint()
    _opts: ScreenshotPreviewOpts

    def __init__(
        self,
        parent: QWidget,
        shape: QRubberBand.Shape = QRubberBand.Shape.Rectangle,
        opts: ScreenshotPreviewOpts | None = None,
    ) -> None:
        """Initialize the rubber band with optional shape and styling options."""
        super().__init__(shape, parent)
        self._opts = opts or ScreenshotPreviewOpts()
        self.hide()

    def set_border(self, color: QColor, thickness: int) -> None:
        """Set the border color and thickness for the rubber band."""
        self._opts.border_color = color
        self._opts.border_thickness = thickness

    def set_fill(self, color: QColor) -> None:
        """Set the fill color for the rubber band interior."""
        self._opts.fill_color = color

    def paintEvent(self, event: QPaintEvent) -> None:
        """Paint the rubber band with the configured fill color and border."""
        painter = QPainter()
        painter.begin(self)
        # Mask
        painter.fillRect(event.rect(), self._opts.fill_color)
        # Border
        painter.setPen(QPen(self._opts.border_color, self._opts.border_thickness))
        painter.drawRect(event.rect())
        painter.end()
        # return super().paintEvent(event)

    def set_selection_start(self, point: QPoint) -> None:
        """Set the starting point of the selection and reset the geometry."""
        self._selection_start = point
        self.setGeometry(QRect(self._selection_start, QSize()))

    def set_selection_end(self, point: QPoint) -> None:
        """Set the ending point of the selection and update the geometry to the normalized rectangle."""
        self.setGeometry(QRect(self._selection_start, point).normalized())
