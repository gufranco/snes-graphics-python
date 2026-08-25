"""Colour, which the hardware keeps as fifteen bits in a sixteen bit word.

Five bits per channel, blue highest and red lowest, with the top bit of the word
unused. A conversion to eight bits per channel therefore throws information away
in one direction and has to invent it in the other, and the way it invents it is
what decides whether a round trip is lossless.

Shifting left by three and leaving zeroes is the obvious way and it is wrong at
the top end: the brightest red a cartridge can name becomes `F8`, not `FF`, so a
palette that should reach white does not. Repeating the value's own high bits
into the gap fixes that, maps the brightest five bit value onto the brightest
eight bit one, and leaves black at black. That is what the hardware's own output
does and what this module does, which is why every one of the thirty two thousand
seven hundred and sixty eight colours here survives a round trip exactly.

Which colours a tile can reach depends on its depth. Two bit tiles see four at a
time, four bit tiles sixteen, and eight bit tiles the whole table, so the palette
number in a tilemap or sprite entry means a different stride at each depth. The
first colour of whichever block is in use is not drawn at all; it is the one the
layer behind shows through.
"""

from collections.abc import Sequence

from .errors import OutOfRange, Truncated

COLOURS = 256

BYTES_PER_COLOUR = 2

WORD_MASK = 0x7FFF

CHANNEL_BITS = 5

CHANNEL_MASK = 0x1F

BLOCKS = {2: 4, 4: 16, 8: 256}

TRANSPARENT = 0


def _narrow(channel: int) -> int:
    if not 0 <= channel <= 0xFF:
        raise OutOfRange(f"{channel} is not a channel value; a channel is one byte")
    return channel >> 3


def _widen(value: int) -> int:
    """Five bits into eight, by repeating the value's own high bits into the gap.

    Shifting and padding with zeroes would leave the brightest colour the
    hardware can name three steps short of the brightest byte, so a palette that
    reaches white would not. Repeating maps the top of one range onto the top of
    the other and keeps the bottom at zero.
    """
    return (value << 3) | (value >> 2)


def to_word(red: int, green: int, blue: int) -> int:
    """The fifteen bit word for a colour, dropping what the hardware cannot hold."""
    return _narrow(red) | (_narrow(green) << CHANNEL_BITS) | (_narrow(blue) << (CHANNEL_BITS * 2))


def to_rgb(word: int) -> tuple[int, int, int]:
    """The three channels a word names, widened to a byte each."""
    if not 0 <= word <= 0xFFFF:
        raise OutOfRange(f"{word} is not a colour word; a word is sixteen bits")
    word &= WORD_MASK
    return (
        _widen(word & CHANNEL_MASK),
        _widen((word >> CHANNEL_BITS) & CHANNEL_MASK),
        _widen((word >> (CHANNEL_BITS * 2)) & CHANNEL_MASK),
    )


def decode(data: bytes | bytearray) -> list[tuple[int, int, int]]:
    """Every colour in a run of bytes, two bytes each, low byte first."""
    if len(data) % BYTES_PER_COLOUR:
        raise Truncated(f"{len(data)} bytes is not a whole number of colours")
    return [to_rgb(data[at] | (data[at + 1] << 8)) for at in range(0, len(data), BYTES_PER_COLOUR)]


def encode(colours: Sequence[tuple[int, int, int]]) -> bytes:
    """The bytes a run of colours occupies."""
    data = bytearray()
    for red, green, blue in colours:
        word = to_word(red, green, blue)
        data.append(word & 0xFF)
        data.append(word >> 8)
    return bytes(data)


def normalise(data: bytes | bytearray) -> bytes:
    """The same bytes with the unused top bit cleared, which is what a round trip keeps."""
    if len(data) % BYTES_PER_COLOUR:
        raise Truncated(f"{len(data)} bytes is not a whole number of colours")
    out = bytearray(data)
    for at in range(1, len(out), BYTES_PER_COLOUR):
        out[at] &= 0x7F
    return bytes(out)


def block_size(depth: int) -> int:
    """How many colours a tile of that depth reaches at once."""
    found = BLOCKS.get(depth)
    if found is None:
        raise OutOfRange(f"{depth} is not a depth with a palette block; it has {sorted(BLOCKS)}")
    return found


def block_start(depth: int, block: int) -> int:
    """Where a palette block begins in the table."""
    size = block_size(depth)
    if not 0 <= block < COLOURS // size:
        raise OutOfRange(f"block {block} is past the end of the table at {depth} bits")
    return block * size


def resolve(
    table: Sequence[tuple[int, int, int]], pixel: int, depth: int, block: int
) -> tuple[int, int, int] | None:
    """The colour the hardware would show for a pixel of that number."""
    size = block_size(depth)
    if not 0 <= pixel < size:
        raise OutOfRange(f"{pixel} is not a colour number a {depth} bit tile can hold")
    return table[block_start(depth, block) + pixel]


def is_transparent(pixel: int) -> bool:
    """Whether a colour number is the one the layer behind shows through."""
    return pixel == TRANSPARENT
