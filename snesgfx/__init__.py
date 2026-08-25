"""The Super Nintendo graphics formats, encoded and decoded exactly.

    from snesgfx import describe

    sheet = describe("4bpp").decode(data)

These are layouts rather than parts, so there is no silicon to be faithful to and
nothing to measure. A layout is right or wrong, so the checks are exhaustive
where the input space allows it: every two bit tile that can exist is round
tripped, every one of the thirty two thousand seven hundred and sixty eight
colours the hardware can name is shown to survive the conversion to bytes and
back, and every sixteen bit map entry is shown to survive its own.
"""

from . import errors as errors
from . import mode7 as mode7
from . import models as models
from . import oam as oam
from . import palette as palette
from . import tilemap as tilemap
from . import tiles as tiles
from .errors import OutOfRange, Truncated, UnknownDepth, UnknownFormat
from .models import FORMATS, Format, describe
from .version import VERSION

__version__ = VERSION

__all__ = [
    "FORMATS",
    "Format",
    "OutOfRange",
    "Truncated",
    "UnknownDepth",
    "UnknownFormat",
    "__version__",
    "describe",
]
