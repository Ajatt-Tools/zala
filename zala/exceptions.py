"""
Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""


class ZalaException(Exception):
    """Base exception for all Zala-specific errors."""

    pass

class CaptureScreenError(ZalaException):
    pass
