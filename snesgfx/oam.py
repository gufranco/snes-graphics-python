"""The sprite table, which is one table with a second one bolted onto the end.

A sprite needs nine bits of horizontal position and a size flag, and the four
byte entry it gets has room for neither. So thirty two bytes are added after the
five hundred and twelve, holding two bits for each of the hundred and twenty
eight sprites, four sprites to a byte, in the order they appear in the first
table.

That arrangement is the whole difficulty. A sprite's data is in two places, the
second place is shared with three of its neighbours, and reading a sprite means
finding its byte and then its two bit slot inside it. Writing one back means
touching those bits without disturbing the neighbours.

The ninth bit of the position is not the top of a wider number. It makes the
position negative: a sprite at nine bits of one and a low byte of two hundred and
forty is sixteen pixels off the left of the screen, not two hundred and seventy
two pixels along it. That is how a sprite scrolls in from the left, and reading
the bit as a magnitude puts it on the wrong side.

The size flag chooses between two sizes rather than naming one. Which two comes
from a register that applies to every sprite at once, so a sprite is never simply
large: it is the larger of whichever pair is in force.
"""

from collections.abc import Sequence
from typing import override

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
    ((32, 32), (64, 64)),
)


class Truncated(Exception):
    pass


class OutOfRange(Exception):
    pass


class Sprite:
    """One sprite, with the two halves of its data brought together."""

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
        """Where the sprite actually sits, with the ninth bit read as a sign."""
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
    """Every sprite in a table, with its two bits from the second table folded in."""
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
    """The bytes a full table of sprites occupies."""
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
    """The two sizes a setting chooses between, small first."""
    if not 0 <= setting < len(SIZES):
        raise OutOfRange(f"{setting} is not a size setting; there are {len(SIZES)}")
    return SIZES[setting]


def size_of(sprite: "Sprite", setting: int) -> tuple[int, int]:
    """How large a sprite actually is, which needs the setting as well as the flag."""
    small, large = sizes(setting)
    return large if sprite.large else small
