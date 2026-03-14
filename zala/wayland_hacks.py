"""
Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""

import json
import os
import pathlib
import shutil
import subprocess
from collections.abc import Sequence
import typing

from loguru import logger
from PyQt6.QtCore import QPoint, QRect
from PyQt6.QtGui import QPixmap, QScreen

from zala.exceptions import CaptureScreenError
from zala.utils import zala_temp_file

# Wayland is SHIT. But this program has to support it because some people still use Wayland.
# To be able to take screenshots on Wayland, some ugly hacks can be used.


def is_wayland() -> bool:
    """Return True if the current session is running under the Wayland display protocol."""
    return bool(os.environ.get("WAYLAND_DISPLAY"))


def screen_physical_rect(screen: QScreen) -> QRect:
    """
    Return the screen's geometry expressed in physical (device) pixels.

    Qt's QScreen.geometry() is in device-independent (logical) pixels.
    Multiplying by the device pixel ratio gives the corresponding rectangle
    in the coordinate space of a full-desktop screenshot PNG.
    """
    dpr = screen.devicePixelRatio()
    geo = screen.geometry()
    return QRect(
        round(geo.x() * dpr),
        round(geo.y() * dpr),
        round(geo.width() * dpr),
        round(geo.height() * dpr),
    )


def load_screenshot_pixmap(tmp_path: pathlib.Path, screen: QScreen, full_desktop: bool) -> QPixmap:
    """
    Load a screenshot PNG from tmp_path and return a QPixmap sized to
    screen's logical (device-independent) pixel dimensions.

    When *full_desktop* is True the PNG contains the entire virtual
    desktop (all monitors combined) and must be cropped to the target screen
    before being returned.  When it is False (e.g. grim -o) the PNG
    already contains exactly the target screen.
    """
    pixmap = QPixmap(str(tmp_path))
    if pixmap.isNull():
        return pixmap
    if full_desktop:
        # Tools such as gnome-screenshot and spectacle capture the entire
        # virtual desktop. Crop to the target screen's physical geometry so
        # that only its pixels remain.
        pixmap = pixmap.copy(screen_physical_rect(screen))
    # Scale from physical pixels to logical pixels, mirroring the original X11/XCB path:
    return pixmap.scaled(screen.geometry().size())


def find_wayland_screenshot_program() -> str:
    """
    Return the name of the screenshot tool to use on Wayland.

    Tools are tried in the following order of preference:

    1. grim – wlroots-native; captures a specific output with `-o`.
    2. gnome-screenshot – GNOME Wayland; captures the full desktop.
    3. spectacle – KDE Plasma; captures the full desktop.
    """
    for tool in ("grim", "gnome-screenshot", "spectacle"):
        if shutil.which(tool):
            return tool
    raise CaptureScreenError(
        "No Wayland screenshot tool was found. Please install one of: grim, gnome-screenshot, spectacle."
    )


def grab_window_wayland(screen: QScreen) -> QPixmap:
    """
    Capture the entire screen on Wayland by delegating to an external screenshot tool,
    since QScreen.grabWindow() always returns a null pixmap on Wayland.

    For tools that capture the full virtual desktop
    the result is cropped to the target screen's geometry before being returned.
    A CaptureScreenError is raised if none of the tools are available.
    """
    with zala_temp_file(suffix=".png") as tmp_path:
        match find_wayland_screenshot_program():
            case "grim":
                # 'grim -o' captures exactly the named output at native resolution.
                cmd = ["grim", "-o", screen.name(), tmp_path]
                full_desktop = False
            case "gnome-screenshot":
                cmd = ["gnome-screenshot", "-f", tmp_path]
                full_desktop = True
            case "spectacle":
                cmd = ["spectacle", "-n", "-b", "-f", "-o", tmp_path]
                full_desktop = True
            case _:
                raise CaptureScreenError(
                    "No Wayland screenshot tool was found. Please install one of: grim, gnome-screenshot, spectacle."
                )

        tool = cmd[0]
        logger.debug(f"Running {tool!r} to capture Wayland output '{screen.name()}'.")
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            stderr = result.stderr.decode(errors="replace").strip()
            raise CaptureScreenError(f"{tool} exited with code {result.returncode}: {stderr}")

        pixmap = load_screenshot_pixmap(tmp_path, screen, full_desktop)
        if pixmap.isNull():
            raise CaptureScreenError(f"{tool} produced an unreadable image.")
        return pixmap


class SwayOutput(typing.TypedDict):
    focused: bool
    name: str


def find_cursor_position_hyprland() -> QPoint | None:
    """
    Attempt to determine the cursor position on Hyprland.
    """
    try:
        result = subprocess.run(
            ["hyprctl", "cursorpos"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            # Output format: "1234, 567"
            x_str, y_str = result.stdout.strip().split(",")
            cursor = QPoint(int(x_str.strip()), int(y_str.strip()))
            logger.debug(f"Hyprland reports cursor at {cursor.x(), cursor.y()}.")
            return cursor
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
        logger.debug(f"Hyprland failed to determine cursor position.")
    return None


def find_focused_screen_sway() -> str | None:
    """
    Attempt to determine which screen the cursor is on.
    """
    try:
        result = subprocess.run(
            ["swaymsg", "-r", "-t", "get_outputs"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            outputs = typing.cast(list[SwayOutput], json.loads(result.stdout))
            focused_name = next(
                # Sometimes the dict has no 'focused' key.
                (output["name"] for output in outputs if output.get("focused")),
                None,
            )
            if focused_name:
                logger.debug(f"Sway reports focused output: {focused_name!r}.")
                return focused_name
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError, KeyError, TypeError, AttributeError):
        logger.debug(f"sway failed to determine focused screen.")
    return None


def find_focused_screen_wayland(screens: Sequence[QScreen]) -> QScreen | None:
    """
    Attempt to determine which screen the cursor is on by querying
    compositor-specific command-line tools.

    Wayland does not expose the global pointer position to clients, so Qt always reports QCursor.pos() as (0, 0).
    As a workaround try the following tools in order:

    * Hyprland: `hyprctl cursorpos` returns "x, y" coordinates.
    * Sway: `swaymsg -r -t get_outputs` returns a JSON list of outputs.
      The entry with "focused": true is the active monitor.

    Returns None if neither tool is available or succeeds, so the caller can decide on a suitable fallback.
    """
    # Hyprland
    cursor = find_cursor_position_hyprland()
    if cursor is not None:
        for screen in screens:
            if screen.geometry().contains(cursor):
                return screen

    # Sway
    focused_name = find_focused_screen_sway()
    if focused_name:
        for screen in screens:
            if screen.name() == focused_name:
                return screen

    return None
