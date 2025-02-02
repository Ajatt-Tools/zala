"""
Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""

from collections.abc import Callable

from PyQt6.QtCore import pyqtSignal, pyqtBoundSignal

MISSING = object()


def qconnect(signal: Callable | pyqtSignal | pyqtBoundSignal, func: Callable) -> None:
    """Helper to work around type checking not working with signal.connect(func)."""
    signal.connect(func)  # type: ignore


def q_emit(signal: Callable | pyqtSignal | pyqtBoundSignal, value=MISSING) -> None:
    """Helper to work around type checking not working with signal.emit(func)."""
    if value is not MISSING:
        signal.emit(value)  # type: ignore
    else:
        signal.emit()  # type: ignore
