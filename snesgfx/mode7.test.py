import sys
import unittest
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from snesgfx import mode7

IDENTITY = mode7.Matrix(a=0x0100, b=0x0000, c=0x0000, d=0x0100)


def placed(**overrides: Any) -> Any:
    settings: dict[str, Any] = {
        "matrix": IDENTITY,
        "centre": (0, 0),
        "scroll": (0, 0),
    }
    settings.update(overrides)
    return mode7.Field(**settings)


class SignTest(unittest.TestCase):
    def test_a_thirteen_bit_value_below_the_halfway_point_is_itself(self) -> None:
        self.assertEqual(mode7.signed13(0x0FFF), 0x0FFF)

    def test_and_above_it_is_negative(self) -> None:
        self.assertEqual(mode7.signed13(0x1FFF), -1)

    def test_a_sixteen_bit_value_signs_at_its_own_halfway_point(self) -> None:
        self.assertEqual(mode7.signed16(0xFFFF), -1)
        self.assertEqual(mode7.signed16(0x7FFF), 0x7FFF)

    def test_the_matrix_reads_its_entries_as_signed(self) -> None:
        matrix = mode7.Matrix(a=0xFF00, b=0, c=0, d=0)

        self.assertEqual(matrix.a, -256)


class TransformTest(unittest.TestCase):
    def test_the_identity_matrix_leaves_a_pixel_where_it_was(self) -> None:
        field = placed()

        self.assertEqual(field.at(10, 20), (10, 20))

    def test_the_origin_maps_to_the_origin(self) -> None:
        self.assertEqual(placed().at(0, 0), (0, 0))

    def test_scrolling_moves_the_field_under_the_screen(self) -> None:
        field = placed(scroll=(5, 7))

        self.assertEqual(field.at(0, 0), (5, 7))

    def test_the_centre_is_subtracted_before_the_matrix_and_added_after(self) -> None:
        field = placed(centre=(100, 100))

        self.assertEqual(field.at(0, 0), (0, 0))

    def test_doubling_the_matrix_doubles_the_distance_from_the_centre(self) -> None:
        field = placed(matrix=mode7.Matrix(a=0x0200, b=0, c=0, d=0x0200))

        self.assertEqual(field.at(10, 20), (20, 40))

    def test_a_half_scale_matrix_halves_it(self) -> None:
        field = placed(matrix=mode7.Matrix(a=0x0080, b=0, c=0, d=0x0080))

        self.assertEqual(field.at(10, 20), (5, 10))

    def test_the_off_diagonal_entries_shear_the_field(self) -> None:
        field = placed(matrix=mode7.Matrix(a=0x0100, b=0x0100, c=0, d=0x0100))

        self.assertEqual(field.at(0, 4), (4, 4))

    def test_a_negative_matrix_entry_mirrors_the_field(self) -> None:
        field = placed(matrix=mode7.Matrix(a=0xFF00, b=0, c=0, d=0x0100))

        self.assertEqual(field.at(10, 0), (-10, 0))


class TruncationTest(unittest.TestCase):
    def test_the_hardware_throws_away_the_low_six_bits_of_each_product(self) -> None:
        field = placed(matrix=mode7.Matrix(a=0x0001, b=0, c=0, d=0x0100), scroll=(0, 0))

        self.assertEqual(field.at(1, 0), (0, 0))

    def test_a_product_large_enough_to_survive_truncation_does(self) -> None:
        field = placed(matrix=mode7.Matrix(a=0x0001, b=0, c=0, d=0x0100))

        self.assertEqual(field.at(0x4000, 0)[0], 0x40)

    def test_truncation_applies_to_the_row_terms_too(self) -> None:
        field = placed(matrix=mode7.Matrix(a=0x0100, b=0x0001, c=0, d=0x0100))

        self.assertEqual(field.at(0, 1), (0, 1))


class WrapTest(unittest.TestCase):
    def test_a_coordinate_inside_the_field_is_left_alone(self) -> None:
        self.assertEqual(mode7.wrap(100, 200), (100, 200))

    def test_a_coordinate_past_the_edge_comes_back_round(self) -> None:
        self.assertEqual(mode7.wrap(1024, 0), (0, 0))

    def test_a_negative_coordinate_comes_back_from_the_other_side(self) -> None:
        self.assertEqual(mode7.wrap(-1, 0), (1023, 0))

    def test_a_coordinate_outside_the_field_can_be_asked_about_instead(self) -> None:
        self.assertTrue(mode7.outside(1024, 0))
        self.assertFalse(mode7.outside(1023, 1023))


class LayoutTest(unittest.TestCase):
    def test_the_two_halves_of_the_word_hold_different_things(self) -> None:
        vram = bytes([0x11, 0x22, 0x33, 0x44])

        names, pixels = mode7.deinterleave(vram)

        self.assertEqual(list(names), [0x11, 0x33])
        self.assertEqual(list(pixels), [0x22, 0x44])

    def test_the_two_halves_go_back_together(self) -> None:
        vram = bytes([0x11, 0x22, 0x33, 0x44])

        names, pixels = mode7.deinterleave(vram)

        self.assertEqual(mode7.interleave(names, pixels), vram)

    def test_data_of_odd_length_is_refused(self) -> None:
        with self.assertRaises(mode7.Truncated):
            mode7.deinterleave(bytes(3))

    def test_halves_of_different_lengths_are_refused(self) -> None:
        with self.assertRaises(mode7.Truncated):
            mode7.interleave(bytes(2), bytes(3))

    def test_a_mode_seven_tile_is_stored_pixel_by_pixel(self) -> None:
        pixels = bytes(range(64))

        self.assertEqual(mode7.tile(pixels, 0), list(range(64)))

    def test_a_tile_past_the_end_of_the_data_is_refused(self) -> None:
        with self.assertRaises(mode7.Truncated):
            mode7.tile(bytes(64), 1)

    def test_the_tile_a_field_position_lands_in_is_the_one_the_map_names(self) -> None:
        names = bytes([7]) + bytes(0x3FFF)

        self.assertEqual(mode7.name_at(names, 3, 4), 7)

    def test_a_position_in_the_second_tile_reads_the_second_entry(self) -> None:
        names = bytes([0, 9]) + bytes(0x3FFE)

        self.assertEqual(mode7.name_at(names, 8, 0), 9)

    def test_a_position_on_the_second_row_of_tiles_skips_a_whole_row(self) -> None:
        names = bytearray(0x4000)
        names[128] = 5

        self.assertEqual(mode7.name_at(bytes(names), 0, 8), 5)


class ReadingTest(unittest.TestCase):
    def test_a_matrix_prints_as_its_four_entries(self) -> None:
        self.assertIn("256", repr(IDENTITY))

    def test_a_field_prints_as_where_it_is_centred(self) -> None:
        self.assertIn("centre", repr(placed()))


if __name__ == "__main__":
    unittest.main()
