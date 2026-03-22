"""
Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""

import dataclasses

from PyQt6.QtCore import QRect, QSize, Qt
from PyQt6.QtGui import QColor


@dataclasses.dataclass
class ScreenshotPreviewOpts:
    """Configuration options for the rubber band's border and fill colors."""

    border_thickness: int = 2
    # for rubber band
    border_color: QColor = dataclasses.field(default_factory=lambda: QColor(0, 0, 255))
    fill_color: QColor = dataclasses.field(default_factory=lambda: QColor(0, 128, 255, 60))
    # for whole screen
    outline_color: QColor = dataclasses.field(default_factory=lambda: QColor(255, 0, 0))
    fill_brush_color: QColor = dataclasses.field(default_factory=lambda: QColor(127, 127, 127, 85))
    fill_brush_pattern: Qt.BrushStyle = dataclasses.field(default_factory=lambda: Qt.BrushStyle.Dense7Pattern)
    min_selection_size: QSize = dataclasses.field(default_factory=lambda: QSize(10, 10))
    show_help: bool = True
    draw_overlay_mesh: bool = True

    def rect_has_sufficient_size(self, rect: QRect) -> bool:
        """
        Return True if the given rectangle meets the minimum size requirement.

        The rectangle is considered sufficiently large when both its width and
        height are at least the configured min_selection_size.
        """
        return rect.width() >= self.min_selection_size.width() and rect.height() >= self.min_selection_size.height()


@dataclasses.dataclass
class ZoomOpts:
    """Configuration options for zoom and rotation behavior in the preview."""

    zoom_in_factor: float = 1.25
    zoom_out_factor: float = 1.0 / 1.25  # zoom out by 0.8
    min_zoom: float = 1.0
    max_zoom: float = 10.0
    rotation_step: float = 5.0  # degrees per scroll notch when Shift is held
