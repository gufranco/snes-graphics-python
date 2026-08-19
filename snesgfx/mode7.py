"""Mode 7, which is a matrix multiply the hardware performs slightly wrong.

The transform itself is ordinary. A screen position has the centre subtracted,
is multiplied by a two by two matrix of eight point eight fixed point numbers,
and has the centre added back. What makes it worth writing down is that the
multiplier does not keep the whole product: the low six bits of each term are
discarded before the terms are added.

That truncation is not a rounding mode anyone would choose. It means a matrix
entry small enough that its product falls under sixty four contributes nothing at
all, so a very slow rotation does not creep, it stays exactly still until the
product crosses the threshold and then jumps. Software that scales by fractions
this small looks broken on a model that keeps the full product and correct on
hardware.

The layout is the other half. Mode 7 does not store its tilemap and its pixels in
separate places: they share the same words, the map in the low byte and the
pixels in the high byte, so a dump of that memory is the two interleaved and
neither is readable until they are separated.

The field is a hundred and twenty eight tiles square and coordinates outside it
either wrap or fall off, depending on a register. Both are here; which one
applies is the caller's to decide, because it is a setting rather than a property
of the arithmetic.
"""

FIELD_TILES = 128

TILE_WIDTH = 8

FIELD_PIXELS = FIELD_TILES * TILE_WIDTH

FRACTION_BITS = 8

TRUNCATE = ~0x3F

SIGN13 = 0x1000

RANGE13 = 0x2000

SIGN16 = 0x8000

RANGE16 = 0x10000


class Truncated(Exception):
    pass


def signed13(value):
    """A thirteen bit register value read as signed, which is how the hardware reads it."""
    value &= RANGE13 - 1
    return value - RANGE13 if value & SIGN13 else value


def signed16(value):
    """A sixteen bit matrix entry read as signed."""
    value &= RANGE16 - 1
    return value - RANGE16 if value & SIGN16 else value


class Matrix:
    """The four eight point eight entries, held as the hardware holds them."""

    __slots__ = ("_a", "_b", "_c", "_d")

    def __init__(self, a, b, c, d):
        self._a, self._b, self._c, self._d = a, b, c, d

    @property
    def a(self):
        return signed16(self._a)

    @property
    def b(self):
        return signed16(self._b)

    @property
    def c(self):
        return signed16(self._c)

    @property
    def d(self):
        return signed16(self._d)

    def __repr__(self):
        return f"<Matrix a={self.a} b={self.b} c={self.c} d={self.d}>"


class Field:
    """One Mode 7 background, and where a screen position lands in it."""

    def __init__(self, matrix, centre=(0, 0), scroll=(0, 0)):
        self.matrix = matrix
        self.centre = centre
        self.scroll = scroll

    def at(self, x, y):
        """Where a screen position lands in the field, in whole pixels.

        Each term is truncated to a multiple of sixty four before being added,
        which is what the hardware's multiplier does and the reason a matrix entry
        below a certain size has no effect at all.
        """
        centre_x, centre_y = (signed13(value) for value in self.centre)
        scroll_x, scroll_y = (signed13(value) for value in self.scroll)
        origin_x = scroll_x - centre_x
        origin_y = scroll_y - centre_y

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

    def __repr__(self):
        return f"<Field centre={self.centre} scroll={self.scroll}>"


def wrap(x, y):
    """A field position brought back inside the field, which is one of two settings."""
    return x % FIELD_PIXELS, y % FIELD_PIXELS


def outside(x, y):
    """Whether a field position is off the field, which is the other setting."""
    return not (0 <= x < FIELD_PIXELS and 0 <= y < FIELD_PIXELS)


def deinterleave(vram):
    """The tilemap and the pixels, which share the same words in memory."""
    if len(vram) % 2:
        raise Truncated(f"{len(vram)} bytes is not a whole number of words")
    return bytes(vram[0::2]), bytes(vram[1::2])


def interleave(names, pixels):
    """The two halves put back into the words they share."""
    if len(names) != len(pixels):
        raise Truncated(f"{len(names)} names and {len(pixels)} pixels are not the same length")
    out = bytearray(len(names) * 2)
    out[0::2] = names
    out[1::2] = pixels
    return bytes(out)


def tile(pixels, index):
    """One Mode 7 tile, which is stored a pixel to a byte rather than in planes."""
    at = index * TILE_WIDTH * TILE_WIDTH
    end = at + TILE_WIDTH * TILE_WIDTH
    if end > len(pixels):
        raise Truncated(f"tile {index} is past the end of {len(pixels)} bytes")
    return list(pixels[at:end])


def name_at(names, x, y):
    """Which tile the map puts at a field position."""
    column = (x // TILE_WIDTH) % FIELD_TILES
    row = (y // TILE_WIDTH) % FIELD_TILES
    return names[row * FIELD_TILES + column]
