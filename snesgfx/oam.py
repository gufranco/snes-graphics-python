from collections.abc import Sequence
from typing import override

from .errors import OutOfRange, Truncated

SPRITES = 128

LOW_ENTRY_BYTES = 4

LOW_TABLE_BYTES = SPRITES * LOW_ENTRY_BYTES

HIGH_TABLE_BYTES = SPRITES // 4

TABLE_BYTES = LOW_TABLE_BYTES + HIGH_TABLE_BYTES

SCREEN_WIDTH = 256

SIZES = (
    ((8, 8), (16, 16)),
    ((8, 8), (32, 32)),
    ((8, 8), (64, 64)),
    ((16, 16), (32, 32)),
    ((16, 16), (64, 64)),
    ((32, 32), (64, 64)),
    ((16, 32), (32, 64)),
    ((16, 32), (32, 32)),
)


class Sprite:
    __slots__ = (
        "block",
        "horizontal_flip",
        "large",
        "priority",
        "table",
        "tile",
        "vertical_flip",
        "x",
        "y",
    )

    def __init__(
        self,
        x: int = 0,
        y: int = 0,
        tile: int = 0,
        block: int = 0,
        priority: int = 0,
        table: int = 0,
        horizontal_flip: bool = False,
        vertical_flip: bool = False,
        large: bool = False,
    ) -> None:
        self.x = x
        self.y = y
        self.tile = tile
        self.block = block
        self.priority = priority
        self.table = table
        self.horizontal_flip = horizontal_flip
        self.vertical_flip = vertical_flip
        self.large = large

    @property
    def screen_x(self) -> int:
        return int(self.x) - 0x200 if self.x >= SCREEN_WIDTH else int(self.x)

    @override
    def __eq__(self, other: object) -> bool:
        return all(getattr(self, name) == getattr(other, name) for name in self.__slots__)

    @override
    def __hash__(self) -> int:
        return hash(tuple(getattr(self, name) for name in self.__slots__))

    @override
    def __repr__(self) -> str:
        return f"<Sprite at {self.x},{self.y} tile {self.tile} block {self.block}>"


def _high_bits(data: bytes | bytearray, index: int) -> int:
    byte = data[LOW_TABLE_BYTES + index // 4]
    return (byte >> ((index % 4) * 2)) & 0x03


def decode(data: bytes | bytearray) -> list["Sprite"]:
    if len(data) != TABLE_BYTES:
        raise Truncated(f"a sprite table is {TABLE_BYTES} bytes, not {len(data)}")

    found = []
    for index in range(SPRITES):
        at = index * LOW_ENTRY_BYTES
        attributes = data[at + 3]
        high = _high_bits(data, index)
        found.append(
            Sprite(
                x=data[at] | ((high & 0x01) << 8),
                y=data[at + 1],
                tile=data[at + 2] | ((attributes & 0x01) << 8),
                block=(attributes >> 1) & 0x07,
                priority=(attributes >> 4) & 0x03,
                table=attributes & 0x01,
                horizontal_flip=bool(attributes & 0x40),
                vertical_flip=bool(attributes & 0x80),
                large=bool(high & 0x02),
            )
        )
    return found


def _checked(value: int, limit: int, what: str) -> int:
    if not 0 <= value < limit:
        raise OutOfRange(f"{value} does not fit in a sprite's {what}")
    return value


def encode(sprites: Sequence["Sprite"]) -> bytes:
    if len(sprites) != SPRITES:
        raise Truncated(f"a sprite table holds {SPRITES} sprites, not {len(sprites)}")

    data = bytearray(TABLE_BYTES)
    for index, sprite in enumerate(sprites):
        at = index * LOW_ENTRY_BYTES
        data[at] = _checked(sprite.x, 0x200, "horizontal position") & 0xFF
        data[at + 1] = _checked(sprite.y, 0x100, "vertical position")
        data[at + 2] = _checked(sprite.tile, 0x200, "tile number") & 0xFF
        data[at + 3] = (
            (sprite.tile >> 8)
            | (_checked(sprite.block, 0x08, "palette block") << 1)
            | (_checked(sprite.priority, 0x04, "priority") << 4)
            | (0x40 if sprite.horizontal_flip else 0)
            | (0x80 if sprite.vertical_flip else 0)
        )
        high = ((sprite.x >> 8) & 0x01) | (0x02 if sprite.large else 0)
        data[LOW_TABLE_BYTES + index // 4] |= high << ((index % 4) * 2)
    return bytes(data)


def sizes(setting: int) -> tuple[tuple[int, int], tuple[int, int]]:
    if not 0 <= setting < len(SIZES):
        raise OutOfRange(f"{setting} is not a size setting; there are {len(SIZES)}")
    return SIZES[setting]


def size_of(sprite: "Sprite", setting: int) -> tuple[int, int]:
    small, large = sizes(setting)
    return large if sprite.large else small
