import json
import sys
import unittest
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from snesgfx import mode7

HERE = Path(__file__).resolve().parent

FIGURES: dict[str, Any] = json.loads((HERE / "hardware.json").read_text())["mode7"]

CENTRE = 100


def one_at_the_point() -> int:
    point: int = FIGURES["matrix"]["fractionBits"]
    return 1 << point


def low_bit(span: str) -> int:
    return int(span.rsplit(maxsplit=1)[-1][1:])


class MatrixTest(unittest.TestCase):
    def test_a_parameter_of_one_at_the_printed_point_leaves_a_pixel_where_it_was(self) -> None:
        # Arrange
        one = 1 << FIGURES["matrix"]["fractionBits"]
        field = mode7.Field(mode7.Matrix(a=one, b=0, c=0, d=one))

        # Act
        shown = field.at(10, 20)

        # Assert
        self.assertEqual(shown, (10, 20))

    def test_the_top_bit_of_a_parameter_is_its_sign(self) -> None:
        # Arrange
        top = 1 << (FIGURES["matrix"]["bits"] - 1)

        # Act
        read = mode7.Matrix(a=top, b=0, c=0, d=0).a

        # Assert
        self.assertEqual(read, -top)

    def test_the_centre_is_taken_off_before_the_matrix_and_put_back_after(self) -> None:
        # Arrange
        double = 2 * one_at_the_point()
        printed = FIGURES["formula"]["quote"]
        field = mode7.Field(mode7.Matrix(a=double, b=0, c=0, d=double), centre=(CENTRE, CENTRE))

        # Act
        shown = field.at(CENTRE, CENTRE)

        # Assert
        self.assertEqual(
            (shown, "X1 - X0" in printed, printed.endswith("+ [X0, Y0]")),
            ((CENTRE, CENTRE), True, True),
        )


class FieldTest(unittest.TestCase):
    def test_the_field_is_the_printed_number_of_dots_across(self) -> None:
        # Arrange
        printed = FIGURES["screen"]["fieldDots"]

        # Act
        held = (mode7.FIELD_PIXELS, mode7.FIELD_TILES * mode7.TILE_WIDTH)

        # Assert
        self.assertEqual(held, (printed, printed))

    def test_a_name_is_the_low_byte_of_the_word_and_a_dot_the_high_byte(self) -> None:
        # Arrange
        screen = FIGURES["screen"]
        word = (0xA5 << low_bit(screen["characterDataBits"])) | (
            0x3C << low_bit(screen["nameBits"])
        )

        # Act
        names, dots = mode7.deinterleave(word.to_bytes(2, "little"))

        # Assert
        self.assertEqual((list(names), list(dots)), ([0x3C], [0xA5]))

    def test_a_character_is_the_printed_number_of_bytes(self) -> None:
        # Arrange
        printed = FIGURES["screen"]["characterBytes"]

        # Act
        held = len(mode7.tile(bytes(printed), 0))

        # Assert
        self.assertEqual(held, printed)

    def test_a_centre_and_a_scroll_take_the_printed_range(self) -> None:
        # Arrange
        bits = FIGURES["centre"]["bits"]
        ends = (1 << (bits - 1), (1 << (bits - 1)) - 1)

        # Act
        read = tuple(mode7.signed13(end) for end in ends)

        # Assert
        self.assertEqual(
            read, (FIGURES["screen"]["scrollLowest"], FIGURES["screen"]["scrollHighest"])
        )


if __name__ == "__main__":
    unittest.main(verbosity=1)
