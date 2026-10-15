from collections.abc import Sequence

from .errors import OutOfRange, Truncated, UnknownDepth

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


def _listed() -> str:
    return ", ".join(str(depth) for depth in DEPTHS)


def depth_of(name: str | int) -> int:
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
    return _checked(depth) * TILE_WIDTH


def _plane_offset(plane: int) -> int:
    return (plane // 2) * PLANE_PAIR_BYTES + (plane % 2)


def decode(data: bytes | bytearray, depth: int) -> list[int]:
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
    size = tile_bytes(depth)
    if len(data) % size:
        raise Truncated(f"{len(data)} bytes is not a whole number of {depth} bit tiles")
    return [decode(data[at : at + size], depth) for at in range(0, len(data), size)]


def encode_sheet(sheet: Sequence[Sequence[int]], depth: int) -> bytes:
    return b"".join(encode(pixels, depth) for pixels in sheet)


def flip(pixels: Sequence[int], horizontal: bool = False, vertical: bool = False) -> list[int]:
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
