"""
Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""

import pathlib
import typing
from collections.abc import Sequence

from loguru import logger
from PyQt6.QtGui import QCursor, QPixmap, QScreen
from PyQt6.QtWidgets import QApplication

from zala.exceptions import ZalaException
from zala.utils import generate_output_file_path


def repr_screen(screen: QScreen) -> str:
    geometry = screen.geometry()
    top_left = geometry.topLeft()
    size = geometry.size()
    return f"Name {screen.name()}. Position {top_left.x(), top_left.y()}. Size {size.width()}x{size.height()}."


def debug_screens(screens: Sequence[QScreen]) -> None:
    logger.debug(f"Found {len(screens)} screens.")
    for idx, screen in enumerate(screens):
        logger.debug(f"Screen #{idx}. {repr_screen(screen)}")


def grab_window(screen: QScreen) -> QPixmap:
    return screen.grabWindow(x=0, y=0).scaled(screen.geometry().size())


def find_screen_with_cursor(screens: Sequence[QScreen]) -> QScreen:
    cursor = QCursor.pos()  # Get the current position of the cursor
    # Iterate through the screens to find which one contains the cursor position
    logger.debug(f"Cursor is at {cursor.x(), cursor.y()}.")
    for screen in screens:
        if screen.geometry().contains(cursor):
            return screen
    raise RuntimeError("couldn't find active screen.")


class TakenScreenshot(typing.NamedTuple):
    pixmap: QPixmap
    screen: QScreen


class ScreenshotSaveResult(typing.NamedTuple):
    success: bool
    file_path: pathlib.Path


def save_screenshot(pixmap: QPixmap, output_file_path: str | None) -> ScreenshotSaveResult:
    output_file_path = pathlib.Path(output_file_path) if output_file_path else generate_output_file_path()
    return ScreenshotSaveResult(pixmap.save(str(output_file_path)), output_file_path)


class ZalaScreenshot:
    """
    Take screenshots.
    """

    _app: QApplication

    def __init__(self, app: QApplication) -> None:
        self._app = app

    def find_available_screens(self) -> list[QScreen]:
        return self._app.screens()

    def capture_screen(self, index: int | None = None) -> TakenScreenshot:
        screens = self.find_available_screens()
        debug_screens(screens)
        try:
            target_screen = screens[index]
        except TypeError:
            target_screen = find_screen_with_cursor(screens)
        except IndexError as e:
            raise ZalaException(f"screen #{index} does not exist") from e
        pixmap = grab_window(target_screen)
        logger.debug(f"Screen {target_screen.name()} taken.")
        return TakenScreenshot(pixmap, target_screen)
