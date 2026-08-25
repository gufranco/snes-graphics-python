"""Which formats this package covers, named the way people name them.

These are not models of a part, so there is no silicon to be faithful to. They
are layouts, and a layout is either right or wrong with nothing in between. What
the catalogue buys is one way in: a tool that reads a cartridge does not want to
know that four bit tiles and the sprite table need different call shapes, only
that it has bytes and a name for what they are.

Every entry decodes and encodes, and the pair is a round trip on every input the
format accepts. That is the whole contract.
"""

from collections.abc import Callable, Sequence
from typing import Any, override

from . import mode7, oam, palette, tilemap, tiles
from .errors import UnknownFormat


class Format:
    """One layout: what it is, and how to read and write it."""

    __slots__ = ("aliases", "decode", "encode", "name", "summary")

    def __init__(
        self,
        name: str,
        summary: str,
        decode: Callable[..., Any],
        encode: Callable[..., bytes],
        aliases: Sequence[str] = (),
    ) -> None:
        self.name = name
        self.summary = summary
        self.decode = decode
        self.encode = encode
        self.aliases = tuple(aliases)

    @override
    def __repr__(self) -> str:
        return f"<Format {self.name}>"


def _tile_format(depth: int, summary: str, aliases: Sequence[str]) -> "Format":
    return Format(
        name=f"{depth}bpp",
        summary=summary,
        decode=lambda data: tiles.decode_sheet(data, depth),
        encode=lambda sheet: tiles.encode_sheet(sheet, depth),
        aliases=aliases,
    )


_CATALOGUE = (
    _tile_format(
        2,
        "Two bit planes, four colours, sixteen bytes a tile. The depth the "
        "hardware reaches furthest with and the one text is usually drawn in.",
        ("4-colour", "2bit"),
    ),
    _tile_format(
        4,
        "Four bit planes, sixteen colours, thirty two bytes a tile. What most "
        "backgrounds and every sprite use.",
        ("16-colour", "4bit"),
    ),
    _tile_format(
        8,
        "Eight bit planes, two hundred and fifty six colours, sixty four bytes a "
        "tile. Available to one background at a time and rarely worth it.",
        ("256-colour", "8bit"),
    ),
    Format(
        name="mode7",
        summary=(
            "The rotating background, whose tiles are stored a pixel to a byte "
            "and whose map shares the same words as its pixels."
        ),
        decode=mode7.deinterleave,
        encode=lambda halves: mode7.interleave(*halves),
        aliases=("mode-7", "m7"),
    ),
    Format(
        name="palette",
        summary=(
            "Fifteen bit colour, five bits a channel with blue highest, two "
            "bytes a colour and the top bit of each word unused."
        ),
        decode=palette.decode,
        encode=palette.encode,
        aliases=("cgram", "colours", "colors"),
    ),
    Format(
        name="tilemap",
        summary=(
            "The background map, sixteen bits an entry, stored as up to four "
            "blocks of thirty two by thirty two rather than as a rectangle."
        ),
        decode=tilemap.decode,
        encode=tilemap.encode,
        aliases=("map", "screen", "bg"),
    ),
    Format(
        name="oam",
        summary=(
            "The sprite table, four bytes a sprite plus two more bits each in a "
            "second table shared four sprites to a byte."
        ),
        decode=oam.decode,
        encode=oam.encode,
        aliases=("sprites", "objects", "obj"),
    ),
)

FORMATS = {found.name: found for found in _CATALOGUE}

_BY_ALIAS = {}
for _found in _CATALOGUE:
    _BY_ALIAS[_found.name] = _found
    for _alias in _found.aliases:
        _BY_ALIAS[_alias.replace("-", "")] = _found


def _normalise(name: str) -> str:
    return str(name).strip().lower().replace("-", "").replace("_", "").replace(" ", "")


def describe(name: str) -> "Format":
    """The format of that name, however it happens to be written."""
    found = _BY_ALIAS.get(_normalise(name))
    if found is None:
        raise UnknownFormat(
            f"{name} is not a format this package covers; it has {', '.join(sorted(FORMATS))}"
        )
    return found
