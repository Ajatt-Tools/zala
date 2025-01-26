"""
Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""

from PyQt6.QtCore import QPoint, QRect, QSize
from PyQt6.QtGui import QColor, QPainter, QPaintEvent, QPen
from PyQt6.QtWidgets import QRubberBand, QWidget


class UserSelectionRubberBand(QRubberBand):
    """
    Rubber band that is shown when the user selects an area of the pixmap.
    """

    _border_color: QColor = QColor(0, 0, 255)
    _border_thickness: int = 2
    _fill_color: QColor = QColor(0, 128, 255, 60)
    _selection_start: QPoint = QPoint()

    def __init__(
        self,
        parent: QWidget,
        shape: QRubberBand.Shape = QRubberBand.Shape.Rectangle,
        thickness=2,
        border_color: QColor = QColor(0, 0, 255),
        fill_color=QColor(0, 128, 255, 60),
    ) -> None:
        super().__init__(shape, parent)
        self.set_border(border_color, thickness)
        self.set_fill(fill_color)
        self.hide()

    def set_border(self, color: QColor, thickness: int) -> None:
        self._border_color = color
        self._border_thickness = thickness

    def set_fill(self, color: QColor) -> None:
        self._fill_color = color

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter()
        painter.begin(self)
        # Mask
        painter.fillRect(event.rect(), self._fill_color)
        # Border
        painter.setPen(QPen(self._border_color, self._border_thickness))
        painter.drawRect(event.rect())
        painter.end()
        # return super().paintEvent(event)

    def set_selection_start(self, point: QPoint) -> None:
        self._selection_start = point
        self.setGeometry(QRect(self._selection_start, QSize()))

    def set_selection_end(self, point: QPoint) -> None:
        self.setGeometry(QRect(self._selection_start, point).normalized())
