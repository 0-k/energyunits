"""Internal helper to emit warnings that point at the caller's code."""

import os
import sys
import warnings

from .exceptions import EnergyUnitsWarning

_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))


def warn(message: str, category: type = EnergyUnitsWarning) -> None:
    """Emit ``message`` with a stack level pointing outside of this package."""
    # stacklevel=2 is the direct caller of this function; walk outwards from there.
    level = 2
    frame = sys._getframe(1)
    while frame is not None:
        filename = os.path.abspath(frame.f_code.co_filename)
        if not filename.startswith(_PACKAGE_DIR + os.sep):
            break
        frame = frame.f_back
        level += 1
    warnings.warn(message, category, stacklevel=level)
