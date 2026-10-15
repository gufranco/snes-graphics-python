from collections.abc import Sequence
from typing import override

from .errors import OutOfRange, Truncated

QUADRANT_TILES = 32

QUADRANT_ENTRIES = QUADRANT_TILES * QUADRANT_TILES

BYTES_PER_ENTRY = 2

SCREEN_SIZES = ((32, 32), (64, 32), (32, 64), (64, 64))

TILE_MASK = 0x03FF

BLOCK_SHIFT = 10

BLOCK_MASK = 0x07

PRIORITY_BIT = 0x2000

HORIZONTAL_BIT = 0x4000

VERTICAL_BIT = 0x8000


class Entry:
    __slots__ = ("block", "horizontal_flip", "priority", "tile", "vertical_flip")

    def __init__(
        self,
        tile: int = 0,
        block: int = 0,
        priority: bool = False,
        horizontal_flip: bool = False,
        vertical_flip: bool = False,
    ) -> None:
        self.tile = tile
        self.block = block
        self.priority = priority
        self.horizontal_flip = horizontal_flip
        self.vertical_flip = vertical_flip

    @classmethod
    def from_word(cls, word: int) -> "Entry":
        return cls(
            tile=word & TILE_MASK,
            block=(word >> BLOCK_SHIFT) & BLOCK_MASK,
            priority=bool(word & PRIORITY_BIT),
            horizontal_flip=bool(word & HORIZONTAL_BIT),
            vertical_flip=bool(word & VERTICAL_BIT),
        )

    @property
    def word(self) -> int:
        if not 0 <= self.tile <= TILE_MASK:
            raise OutOfRange(f"{self.tile} does not fit in a map entry's ten bit tile number")
        if not 0 <= self.block <= BLOCK_MASK:
            raise OutOfRange(f"{self.block} does not fit in a map entry's three bit palette block")
        return (
            self.tile
            | (self.block << BLOCK_SHIFT)
            | (PRIORITY_BIT if self.priority else 0)
            | (HORIZONTAL_BIT if self.horizontal_flip else 0)
            | (VERTICAL_BIT if self.vertical_flip else 0)
        )

    @override
    def __eq__(self, other: object) -> bool:
        return all(getattr(self, name) == getattr(other, name) for name in self.__slots__)

    @override
    def __hash__(self) -> int:
        return hash(tuple(getattr(self, name) for name in self.__slots__))

    @override
    def __repr__(self) -> str:
        return f"<Entry tile {self.tile} block {self.block}>"


def screen_size(size: int) -> tuple[int, int]:
    if not 0 <= size < len(SCREEN_SIZES):
        raise OutOfRange(f"{size} is not a screen size; there are {len(SCREEN_SIZES)}")
    return SCREEN_SIZES[size]


def offset_of(x: int, y: int, size: int) -> int:
    width, height = screen_size(size)
    x %= width
    y %= height

    quadrant = 0
    if x >= QUADRANT_TILES:
        quadrant += 1
        x -= QUADRANT_TILES
    if y >= QUADRANT_TILES:
        quadrant += 2 if width > QUADRANT_TILES else 1
        y -= QUADRANT_TILES
    return quadrant * QUADRANT_ENTRIES + y * QUADRANT_TILES + x


def decode(data: bytes | bytearray) -> list["Entry"]:
    if len(data) % BYTES_PER_ENTRY:
        raise Truncated(f"{len(data)} bytes is not a whole number of entries")
    return [
        Entry.from_word(data[at] | (data[at + 1] << 8))
        for at in range(0, len(data), BYTES_PER_ENTRY)
    ]


def encode(entries: Sequence["Entry"]) -> bytes:
    data = bytearray()
    for found in entries:
        word = found.word
        data.append(word & 0xFF)
        data.append(word >> 8)
    return bytes(data)


def entry_at(entries: Sequence["Entry"], x: int, y: int, size: int) -> "Entry":
    return entries[offset_of(x, y, size)]
