"""
Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""

import sys
from typing import Sequence

import fire
from PyQt6.QtGui import QPixmap, QCursor, QScreen
from PyQt6.QtWidgets import QApplication
from loguru import logger



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
    for screen in screens:
        if screen.geometry().contains(cursor):
            return screen
    raise RuntimeError("couldn't find active screen.")


class ZalaScreenshot:
    """
    Take screenshots.
    """

    _app: QApplication

    def __init__(self, app: QApplication) -> None:
        self._app = app

    def find_available_screens(self) -> list[QScreen]:
        return self._app.screens()

    def capture_screen(self, index: int | None) -> QPixmap:
        screens = self.find_available_screens()
        debug_screens(screens)
        try:
            target_screen = screens[index]
        except IndexError as e:
            raise ZalaException(f"screen #{index} does not exist") from e
        except TypeError:
            target_screen = find_screen_with_cursor(screens)
        pixmap = grab_window(target_screen)
        logger.debug(f"Screenshot taken. {repr_screen(target_screen)}")
        return pixmap


class CLI:
    """
    Screenshot taking app in PyQt.
    """

    def screens(self) -> None:
        """
        List available screens.
        """
        app = QApplication(sys.argv)
        scr = ZalaScreenshot(app)
        for idx, screen in enumerate(scr.find_available_screens()):
            print(f"Screen {idx}. {repr_screen(screen)}")

    def take_screen(self, number: int | None = None):
        """
        Capture screen.
        Args:
            number: Screen number.
        """
        app = QApplication(sys.argv)
        scr = ZalaScreenshot(app)
        pixmap = scr.capture_screen(number)
        pixmap.save("/tmp/screen.png")

    def select(self):
        raise NotImplementedError
        # app = QApplication(sys.argv)
        # window = ZalaApp()
        # window.showFullScreen()
        # app.exit(app.exec())


class ZalaException(Exception):
    pass


def main():
    try:
        fire.Fire(CLI)
    except ZalaException as e:
        print(f"Error: {e}.")


if __name__ == "__main__":
    main()
