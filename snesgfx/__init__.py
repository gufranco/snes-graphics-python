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

from . import mode7, models, oam, palette, tilemap, tiles
from .models import FORMATS, Format, UnknownFormat, describe
from .version import VERSION

__version__ = VERSION

__all__ = [
    "FORMATS",
    "Format",
    "UnknownFormat",
    "__version__",
    "describe",
    "mode7",
    "models",
    "oam",
    "palette",
    "tilemap",
    "tiles",
]
