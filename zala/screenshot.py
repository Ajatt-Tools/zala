"""
Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""

import pathlib
import typing
from collections.abc import Sequence

from PyQt6.QtGui import QColor, QCursor, QPainter, QPixmap, QScreen
from PyQt6.QtWidgets import QApplication
from loguru import logger

from zala.exceptions import CaptureScreenError
from zala.utils import generate_output_file_path
from zala.wayland_hacks import (
    find_focused_screen_wayland,
    grab_window_wayland,
    is_wayland,
)


class PaddedPixmap(typing.NamedTuple):
    pixmap: QPixmap
    padding_size: int


def add_padding(pixmap: QPixmap, padding_size: int, padding_color: QColor = QColor(128, 128, 128)) -> PaddedPixmap:
    """
    Add gray padding bars on all sides of the image.
    This prevents incorrect/glitchy rotation.

    Args:
        pixmap: The original pixmap to pad.
        padding_size: How many pixels to pad on each side.
        padding_color: The color for padding bars (default: gray #808080).

    Returns:
        A new pixmap with padding added on all sides.
    """
    new_width = pixmap.width() + 2 * padding_size
    new_height = pixmap.height() + 2 * padding_size

    padded = QPixmap(new_width, new_height)
    padded.fill(padding_color)

    painter = QPainter(padded)
    painter.drawPixmap(padding_size, padding_size, pixmap)
    painter.end()

    logger.debug(f"Added padding of {padding_size} pixels on all sides.")
    return PaddedPixmap(pixmap=padded, padding_size=padding_size)


def repr_screen(screen: QScreen) -> str:
    """Return a human-readable string describing the screen's name, position, and size."""
    geometry = screen.geometry()
    top_left = geometry.topLeft()
    size = geometry.size()
    return f"Name {screen.name()}. Position {top_left.x(), top_left.y()}. Size {size.width()}x{size.height()}."


def debug_screens(screens: Sequence[QScreen]) -> None:
    """Log debug information about each available screen."""
    logger.debug(f"Found {len(screens)} screens.")
    for idx, screen in enumerate(screens):
        logger.debug(f"Screen #{idx}. {repr_screen(screen)}")


def grab_window(screen: QScreen) -> QPixmap:
    """
    Capture the entire screen contents and return as a pixmap scaled to the screen geometry.

    On Wayland, QScreen.grabWindow() always returns a null pixmap.
    In that case, try other screenshot programs found in the system.

    https://doc.qt.io/qt-6/qscreen.html#grabWindow
    """
    pixmap = screen.grabWindow(x=0, y=0).scaled(screen.geometry().size())
    if pixmap.isNull():
        if is_wayland():
            logger.debug("Wayland detected, using external screenshot tool.")
            return grab_window_wayland(screen)
        else:
            logger.warning("Screen grab returned a null pixmap on non-Wayland session.")
    return pixmap


def find_screen_with_cursor(screens: Sequence[QScreen]) -> QScreen:
    """
    Find and return the screen that currently contains the mouse cursor.

    On Wayland, QCursor.pos() always reports (0, 0) because the
    protocol does not expose the global pointer position to clients.  In that
    case we query compositor-specific tools (Hyprland, Sway) to determine the
    active output, and fall back to the primary screen only when no tool is
    available.
    """

    if not screens:
        raise CaptureScreenError("no screens available.")

    if is_wayland():
        logger.debug(
            "Wayland detected: global cursor position is unavailable via Qt. Querying compositor-specific tools."
        )
        screen = find_focused_screen_wayland(screens)
        if screen is not None:
            return screen
        logger.debug("Could not determine cursor screen on Wayland. Falling back to the primary screen.")
        return screens[0]

    cursor = QCursor.pos()  # Get the current position of the cursor
    # Iterate through the screens to find which one contains the cursor position
    logger.debug(f"QCursor is at {cursor.x(), cursor.y()}.")
    for screen in screens:
        if screen.geometry().contains(cursor):
            return screen
    raise CaptureScreenError("couldn't find active screen.")


class TakenScreenshot(typing.NamedTuple):
    """Result of capturing a screen, holding the pixmap and the source screen."""

    pixmap: QPixmap
    screen: QScreen


class ScreenshotSaveResult(typing.NamedTuple):
    """Result of saving a screenshot, indicating success and the file path used."""

    success: bool
    file_path: pathlib.Path


def save_screenshot(pixmap: QPixmap, output_file_path: str | None) -> ScreenshotSaveResult:
    """Save a pixmap to disk at the given path, or generate a default path if none is provided."""
    output_file_path = pathlib.Path(output_file_path) if output_file_path else generate_output_file_path()
    return ScreenshotSaveResult(pixmap.save(str(output_file_path)), output_file_path)


class ZalaScreenshot:
    """
    Take screenshots.
    """

    _app: QApplication

    def __init__(self, app: QApplication) -> None:
        """Initialize the screenshot helper with the running QApplication instance."""
        self._app = app

    def find_available_screens(self) -> list[QScreen]:
        """Return a list of all screens currently available to the application."""
        return self._app.screens()

    def capture_screen(self, index: int | None = None) -> TakenScreenshot:
        """
        Capture a screenshot from the screen at the given index, or the screen under the cursor if None.

        Args:
            index: Screen index to capture, or None to capture the screen under the cursor.
        """
        screens = self.find_available_screens()
        debug_screens(screens)
        try:
            target_screen = screens[index]
        except TypeError:
            target_screen = find_screen_with_cursor(screens)
        except IndexError as e:
            raise CaptureScreenError(f"screen #{index} does not exist") from e
        pixmap = grab_window(target_screen)
        if pixmap.isNull():
            raise CaptureScreenError("failed to take screenshot. pixmap is null")
        logger.debug(f"Screen {target_screen.name()} taken.")

        return TakenScreenshot(pixmap, target_screen)
