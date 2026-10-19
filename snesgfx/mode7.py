from typing import override

from .errors import Truncated

FIELD_TILES = 128

TILE_WIDTH = 8

FIELD_PIXELS = FIELD_TILES * TILE_WIDTH

FRACTION_BITS = 8

TRUNCATE = ~0x3F

SIGN13 = 0x1000

RANGE13 = 0x2000

SIGN16 = 0x8000

RANGE16 = 0x10000

OFFSET_SIGN = 0x2000

OFFSET_MASK = 0x3FF


def signed13(value: int) -> int:
    value &= RANGE13 - 1
    return value - RANGE13 if value & SIGN13 else value


def signed16(value: int) -> int:
    value &= RANGE16 - 1
    return value - RANGE16 if value & SIGN16 else value


def clipped(offset: int) -> int:
    return offset | ~OFFSET_MASK if offset & OFFSET_SIGN else offset & OFFSET_MASK


class Matrix:
    __slots__ = ("_a", "_b", "_c", "_d")

    def __init__(self, a: int, b: int, c: int, d: int) -> None:
        self._a, self._b, self._c, self._d = a, b, c, d

    @property
    def a(self) -> int:
        return signed16(self._a)

    @property
    def b(self) -> int:
        return signed16(self._b)

    @property
    def c(self) -> int:
        return signed16(self._c)

    @property
    def d(self) -> int:
        return signed16(self._d)

    @override
    def __repr__(self) -> str:
        return f"<Matrix a={self.a} b={self.b} c={self.c} d={self.d}>"


class Field:
    __slots__ = ("centre", "matrix", "scroll")

    def __init__(
        self,
        matrix: "Matrix",
        centre: tuple[int, int] = (0, 0),
        scroll: tuple[int, int] = (0, 0),
    ) -> None:
        self.matrix = matrix
        self.centre = centre
        self.scroll = scroll

    def at(self, x: int, y: int) -> tuple[int, int]:
        centre_x, centre_y = (signed13(value) for value in self.centre)
        scroll_x, scroll_y = (signed13(value) for value in self.scroll)
        origin_x = clipped(scroll_x - centre_x)
        origin_y = clipped(scroll_y - centre_y)

        field_x = (
            (self.matrix.a * origin_x & TRUNCATE)
            + (self.matrix.b * origin_y & TRUNCATE)
            + (self.matrix.b * y & TRUNCATE)
            + (self.matrix.a * x)
            + (centre_x << FRACTION_BITS)
        )
        field_y = (
            (self.matrix.c * origin_x & TRUNCATE)
            + (self.matrix.d * origin_y & TRUNCATE)
            + (self.matrix.d * y & TRUNCATE)
            + (self.matrix.c * x)
            + (centre_y << FRACTION_BITS)
        )
        return field_x >> FRACTION_BITS, field_y >> FRACTION_BITS

    @override
    def __repr__(self) -> str:
        return f"<Field centre={self.centre} scroll={self.scroll}>"


def wrap(x: int, y: int) -> tuple[int, int]:
    return x % FIELD_PIXELS, y % FIELD_PIXELS


def outside(x: int, y: int) -> bool:
    return not (0 <= x < FIELD_PIXELS and 0 <= y < FIELD_PIXELS)


def deinterleave(vram: bytes | bytearray) -> tuple[bytes, bytes]:
    if len(vram) % 2:
        raise Truncated(f"{len(vram)} bytes is not a whole number of words")
    return bytes(vram[0::2]), bytes(vram[1::2])


def interleave(names: bytes | bytearray, pixels: bytes | bytearray) -> bytes:
    if len(names) != len(pixels):
        raise Truncated(f"{len(names)} names and {len(pixels)} pixels are not the same length")
    out = bytearray(len(names) * 2)
    out[0::2] = names
    out[1::2] = pixels
    return bytes(out)


def tile(pixels: bytes | bytearray, index: int) -> list[int]:
    at = index * TILE_WIDTH * TILE_WIDTH
    end = at + TILE_WIDTH * TILE_WIDTH
    if end > len(pixels):
        raise Truncated(f"tile {index} is past the end of {len(pixels)} bytes")
    return list(pixels[at:end])


def name_at(names: bytes | bytearray, x: int, y: int) -> int:
    column = (x // TILE_WIDTH) % FIELD_TILES
    row = (y // TILE_WIDTH) % FIELD_TILES
    return names[row * FIELD_TILES + column]
