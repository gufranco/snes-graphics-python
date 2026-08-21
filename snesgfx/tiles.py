"""Tiles, which the hardware stores as bit planes rather than as pixels.

A pixel's colour number is not held in one place. Each bit of it lives in a
separate plane, and a plane holds that one bit for all sixty four pixels of the
tile. Reading a pixel means gathering one bit from each plane and stacking them.

The planes are not laid out the way that description suggests either. The first
two are interleaved by row: two bytes for row zero, two for row one, and so on to
the end of the tile. Only then does the third plane begin, again interleaved with
the fourth. So a four bit tile is two of those interleaved pairs, one after the
other, and an eight bit tile is four.

Every consequence people find surprising follows from that layout. Changing a
tile from four bits to eight is not a conversion of each pixel; it is appending
two more plane pairs. Reading the first sixteen bytes of a four bit tile gives a
complete two bit tile, so the smaller depths are not a different format so much
as a prefix of the larger ones.

Within a row the leftmost pixel comes from the highest bit, which is the opposite
of the order the bytes are numbered in and the source of most mirroring bugs.

There is nothing to measure here. The format is exact, so the checks are exact
too: every two bit tile that can exist is round tripped, and every plane of every
depth is shown to reach its own bit and no other.

Three depths exist and no others. Six bits per pixel appears in some tools and in
no Super Nintendo background mode, and Mode 7 does not store its tiles this way
at all, so neither is here. Mode 7 is in its own module.
"""

from collections.abc import Sequence

TILE_PIXELS = 64

TILE_WIDTH = 8

DEPTHS = (2, 4, 8)

PLANE_PAIR_BYTES = 16

NAMES = {
    "2bpp": 2,
    "4bpp": 4,
    "8bpp": 8,
    "4-colour": 2,
    "16-colour": 4,
    "256-colour": 8,
}


class UnknownDepth(Exception):
    pass


class Truncated(Exception):
    pass


class OutOfRange(Exception):
    pass


def _listed() -> str:
    return ", ".join(str(depth) for depth in DEPTHS)


def depth_of(name: str | int) -> int:
    """The bit depth something is called, however it happens to be written."""
    if isinstance(name, int):
        if name in DEPTHS:
            return name
        raise UnknownDepth(f"{name} is not a depth the hardware has; it has {_listed()}")
    found = NAMES.get(str(name).strip().lower())
    if found is None:
        raise UnknownDepth(f"{name} is not a depth the hardware has; it has {_listed()}")
    return found


def _checked(depth: int) -> int:
    if depth not in DEPTHS:
        raise UnknownDepth(f"{depth} is not a depth the hardware has; it has {_listed()}")
    return depth


def tile_bytes(depth: int) -> int:
    """How many bytes one tile of that depth occupies."""
    return _checked(depth) * TILE_WIDTH


def _plane_offset(plane: int) -> int:
    """Where a plane's first byte sits, which is the whole of the layout.

    Planes are paired and each pair is interleaved by row, so the pair a plane
    belongs to decides which sixteen byte block it is in and its parity within
    the pair decides which byte of each row it takes.
    """
    return (plane // 2) * PLANE_PAIR_BYTES + (plane % 2)


def decode(data: bytes | bytearray, depth: int) -> list[int]:
    """One tile, as sixty four colour numbers read left to right, top to bottom."""
    depth = _checked(depth)
    size = tile_bytes(depth)
    if len(data) != size:
        raise Truncated(f"a {depth} bit tile is {size} bytes, not {len(data)}")

    pixels = [0] * TILE_PIXELS
    for plane in range(depth):
        offset = _plane_offset(plane)
        weight = 1 << plane
        for row in range(TILE_WIDTH):
            byte = data[offset + row * 2]
            if not byte:
                continue
            base = row * TILE_WIDTH
            for column in range(TILE_WIDTH):
                if byte & (0x80 >> column):
                    pixels[base + column] |= weight
    return pixels


def encode(pixels: Sequence[int], depth: int) -> bytes:
    """The bytes a tile of those colour numbers occupies."""
    depth = _checked(depth)
    if len(pixels) != TILE_PIXELS:
        raise Truncated(f"a tile is {TILE_PIXELS} pixels, not {len(pixels)}")
    limit = 1 << depth
    data = bytearray(tile_bytes(depth))

    for index, value in enumerate(pixels):
        if not 0 <= value < limit:
            raise OutOfRange(f"{value} does not fit in {depth} bits")
        if not value:
            continue
        row, column = divmod(index, TILE_WIDTH)
        bit = 0x80 >> column
        for plane in range(depth):
            if value & (1 << plane):
                data[_plane_offset(plane) + row * 2] |= bit
    return bytes(data)


def decode_sheet(data: bytes | bytearray, depth: int) -> list[list[int]]:
    """Every tile in a run of bytes, refusing a run that stops mid tile."""
    size = tile_bytes(depth)
    if len(data) % size:
        raise Truncated(f"{len(data)} bytes is not a whole number of {depth} bit tiles")
    return [decode(data[at : at + size], depth) for at in range(0, len(data), size)]


def encode_sheet(sheet: Sequence[Sequence[int]], depth: int) -> bytes:
    """The bytes a run of tiles occupies."""
    return b"".join(encode(pixels, depth) for pixels in sheet)


def flip(pixels: Sequence[int], horizontal: bool = False, vertical: bool = False) -> list[int]:
    """A tile mirrored the way a background or sprite entry can ask for."""
    out = list(pixels)
    if horizontal:
        out = [
            out[row * TILE_WIDTH + (TILE_WIDTH - 1 - column)]
            for row in range(TILE_WIDTH)
            for column in range(TILE_WIDTH)
        ]
    if vertical:
        out = [
            out[(TILE_WIDTH - 1 - row) * TILE_WIDTH + column]
            for row in range(TILE_WIDTH)
            for column in range(TILE_WIDTH)
        ]
    return out
