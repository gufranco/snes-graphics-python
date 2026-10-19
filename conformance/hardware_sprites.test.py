import json
import sys
import unittest
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from snesgfx import oam

HERE = Path(__file__).resolve().parent

FIGURES: dict[str, Any] = json.loads((HERE / "hardware.json").read_text())

OBJECTS: dict[str, Any] = FIGURES["objectData"]

WORD_BYTES = 2

ATTRIBUTES = {
    "OBJ H-POSITION": "x",
    "OBJ V-POSITION": "y",
    "NAME": "tile",
    "COLOR": "block",
    "OBJ PRIORITY": "priority",
    "H": "horizontal_flip",
    "V": "vertical_flip",
}

FLAGS = {"H", "V"}

SPRITE = 77


def mask(field: dict[str, Any]) -> int:
    return int(field["mask"], 16)


def shift(field: dict[str, Any]) -> int:
    held = mask(field)
    return (held & -held).bit_length() - 1


def full(field: dict[str, Any]) -> int | bool:
    return True if field["name"] in FLAGS else mask(field) >> shift(field)


def blank(field: dict[str, Any]) -> int | bool:
    return False if field["name"] in FLAGS else 0


def a_table_with(sprite: oam.Sprite, index: int = SPRITE) -> list[oam.Sprite]:
    return [sprite if at == index else oam.Sprite() for at in range(oam.SPRITES)]


def sprite_with(field: dict[str, Any]) -> oam.Sprite:
    options: dict[str, Any] = {ATTRIBUTES[field["name"]]: full(field)}
    return oam.Sprite(**options)


def object_words(table: bytes, index: int = SPRITE) -> list[int]:
    start = index * OBJECTS["wordsPerObject"] * WORD_BYTES
    return [
        int.from_bytes(table[at : at + WORD_BYTES], "little")
        for at in range(start, start + OBJECTS["wordsPerObject"] * WORD_BYTES, WORD_BYTES)
    ]


def raw_table(field: dict[str, Any], index: int = SPRITE) -> bytes:
    table = bytearray(oam.TABLE_BYTES)
    at = (index * OBJECTS["wordsPerObject"] + field["word"]) * WORD_BYTES
    table[at : at + WORD_BYTES] = mask(field).to_bytes(WORD_BYTES, "little")
    return bytes(table)


def read_fields(sprite: oam.Sprite) -> dict[str, Any]:
    return {name: getattr(sprite, attribute) for name, attribute in ATTRIBUTES.items()}


def high_word(table: bytes, index: int) -> int:
    word = OBJECTS["highTable"]["firstWord"] + index // OBJECTS["highTable"]["objectsPerWord"]
    return int.from_bytes(table[word * WORD_BYTES : (word + 1) * WORD_BYTES], "little")


def high_bit(index: int, bit: int) -> int:
    high = OBJECTS["highTable"]
    place: int = (index % high["objectsPerWord"]) * high["bitsPerObject"] + bit
    return 1 << place


class ObjectDataTest(unittest.TestCase):
    def test_the_table_holds_the_printed_number_of_objects(self) -> None:
        # Arrange
        printed = OBJECTS["objects"]

        # Act
        held = oam.SPRITES

        # Assert
        self.assertEqual(held, printed)

    def test_and_ends_on_the_last_word_the_figure_numbers(self) -> None:
        # Arrange
        printed = OBJECTS["highTable"]["lastWord"] + 1

        # Act
        held = oam.TABLE_BYTES // WORD_BYTES

        # Assert
        self.assertEqual(held, printed)

    def test_a_sprite_writes_each_printed_field_into_its_own_bits(self) -> None:
        # Arrange
        fields = OBJECTS["fields"]

        # Act
        words = [object_words(oam.encode(a_table_with(sprite_with(field)))) for field in fields]

        # Assert
        self.assertEqual(
            words,
            [[mask(field) if at == field["word"] else 0 for at in range(2)] for field in fields],
        )

    def test_a_sprite_reads_each_printed_field_from_its_own_bits(self) -> None:
        # Arrange
        fields = OBJECTS["fields"]

        # Act
        read = [read_fields(oam.decode(raw_table(field))[SPRITE]) for field in fields]

        # Assert
        self.assertEqual(
            read,
            [
                {other["name"]: full(other) if other is field else blank(other) for other in fields}
                for field in fields
            ],
        )

    def test_each_sprite_keeps_its_two_high_bits_where_the_figure_puts_them(self) -> None:
        # Arrange
        high = OBJECTS["highTable"]
        sprites = range(oam.SPRITES)

        # Act
        found = [
            high_word(oam.encode(a_table_with(oam.Sprite(x=0x100, large=True), one)), one)
            for one in sprites
        ]

        # Assert
        self.assertEqual(
            found,
            [
                high_bit(one, high["positionMsbBit"]) | high_bit(one, high["sizeBit"])
                for one in sprites
            ],
        )

    def test_the_ninth_position_bit_gives_the_printed_range(self) -> None:
        # Arrange
        position = OBJECTS["position"]
        ends = (1 << (position["bits"] - 1), (1 << (position["bits"] - 1)) - 1)

        # Act
        found = tuple(oam.Sprite(x=end).screen_x for end in ends)

        # Assert
        self.assertEqual(found, (position["lowest"], position["highest"]))


class ObjectSizeTest(unittest.TestCase):
    def test_each_printed_setting_gives_the_printed_square_sizes(self) -> None:
        # Arrange
        printed = FIGURES["objectSizes"]["settings"]

        # Act
        held = [oam.sizes(setting) for setting, _, _ in printed]

        # Assert
        self.assertEqual(held, [((small, small), (large, large)) for _, small, large in printed])


if __name__ == "__main__":
    unittest.main(verbosity=1)
