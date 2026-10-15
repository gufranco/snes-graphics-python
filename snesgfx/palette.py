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
    return (value << 3) | (value >> 2)


def to_word(red: int, green: int, blue: int) -> int:
    return _narrow(red) | (_narrow(green) << CHANNEL_BITS) | (_narrow(blue) << (CHANNEL_BITS * 2))


def to_rgb(word: int) -> tuple[int, int, int]:
    if not 0 <= word <= 0xFFFF:
        raise OutOfRange(f"{word} is not a colour word; a word is sixteen bits")
    word &= WORD_MASK
    return (
        _widen(word & CHANNEL_MASK),
        _widen((word >> CHANNEL_BITS) & CHANNEL_MASK),
        _widen((word >> (CHANNEL_BITS * 2)) & CHANNEL_MASK),
    )


def decode(data: bytes | bytearray) -> list[tuple[int, int, int]]:
    if len(data) % BYTES_PER_COLOUR:
        raise Truncated(f"{len(data)} bytes is not a whole number of colours")
    return [to_rgb(data[at] | (data[at + 1] << 8)) for at in range(0, len(data), BYTES_PER_COLOUR)]


def encode(colours: Sequence[tuple[int, int, int]]) -> bytes:
    data = bytearray()
    for red, green, blue in colours:
        word = to_word(red, green, blue)
        data.append(word & 0xFF)
        data.append(word >> 8)
    return bytes(data)


def normalise(data: bytes | bytearray) -> bytes:
    if len(data) % BYTES_PER_COLOUR:
        raise Truncated(f"{len(data)} bytes is not a whole number of colours")
    out = bytearray(data)
    for at in range(1, len(out), BYTES_PER_COLOUR):
        out[at] &= 0x7F
    return bytes(out)


def block_size(depth: int) -> int:
    found = BLOCKS.get(depth)
    if found is None:
        raise OutOfRange(f"{depth} is not a depth with a palette block; it has {sorted(BLOCKS)}")
    return found


def block_start(depth: int, block: int) -> int:
    size = block_size(depth)
    if not 0 <= block < COLOURS // size:
        raise OutOfRange(f"block {block} is past the end of the table at {depth} bits")
    return block * size


def resolve(
    table: Sequence[tuple[int, int, int]], pixel: int, depth: int, block: int
) -> tuple[int, int, int] | None:
    size = block_size(depth)
    if not 0 <= pixel < size:
        raise OutOfRange(f"{pixel} is not a colour number a {depth} bit tile can hold")
    return table[block_start(depth, block) + pixel]


def is_transparent(pixel: int) -> bool:
    return pixel == TRANSPARENT
