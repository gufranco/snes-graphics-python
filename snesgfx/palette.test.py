import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from snesgfx import palette
from snesgfx.errors import OutOfRange, Truncated


class WordTest(unittest.TestCase):
    def test_black_is_zero(self) -> None:
        self.assertEqual(palette.to_word(0, 0, 0), 0x0000)

    def test_the_brightest_white_leaves_the_top_bit_clear(self) -> None:
        self.assertEqual(palette.to_word(0xF8, 0xF8, 0xF8), 0x7FFF)

    def test_red_sits_in_the_low_five_bits(self) -> None:
        self.assertEqual(palette.to_word(0xF8, 0, 0), 0x001F)

    def test_green_in_the_next_five(self) -> None:
        self.assertEqual(palette.to_word(0, 0xF8, 0), 0x03E0)

    def test_and_blue_in_the_five_above_those(self) -> None:
        self.assertEqual(palette.to_word(0, 0, 0xF8), 0x7C00)

    def test_the_low_three_bits_of_a_channel_are_thrown_away(self) -> None:
        self.assertEqual(palette.to_word(0xFF, 0, 0), palette.to_word(0xF8, 0, 0))

    def test_a_channel_outside_a_byte_is_refused(self) -> None:
        with self.assertRaises(OutOfRange):
            palette.to_word(0x100, 0, 0)

    def test_a_negative_channel_is_refused_too(self) -> None:
        with self.assertRaises(OutOfRange):
            palette.to_word(-1, 0, 0)


class ColourTest(unittest.TestCase):
    def test_a_word_reads_back_as_the_three_channels(self) -> None:
        self.assertEqual(palette.to_rgb(0x7FFF), (0xFF, 0xFF, 0xFF))

    def test_zero_reads_back_as_black(self) -> None:
        self.assertEqual(palette.to_rgb(0x0000), (0, 0, 0))

    def test_the_top_bit_of_the_word_is_ignored(self) -> None:
        self.assertEqual(palette.to_rgb(0xFFFF), palette.to_rgb(0x7FFF))

    def test_a_channel_is_widened_by_repeating_its_own_high_bits(self) -> None:
        self.assertEqual(palette.to_rgb(0x0001)[0], 0x08)

    def test_every_word_widens_to_channels_that_narrow_back_to_it(self) -> None:
        for word in range(0x8000):
            red, green, blue = palette.to_rgb(word)

            self.assertEqual(palette.to_word(red, green, blue), word)

    def test_a_word_wider_than_sixteen_bits_is_refused(self) -> None:
        with self.assertRaises(OutOfRange):
            palette.to_rgb(0x1_0000)


class TableTest(unittest.TestCase):
    def test_a_table_holds_two_hundred_and_fifty_six_colours(self) -> None:
        self.assertEqual(len(palette.decode(bytes(512))), 256)

    def test_a_colour_is_two_bytes_low_first(self) -> None:
        found = palette.decode(bytes([0xFF, 0x7F]))

        self.assertEqual(found[0], (0xFF, 0xFF, 0xFF))

    def test_a_table_of_odd_length_is_refused(self) -> None:
        with self.assertRaises(Truncated):
            palette.decode(bytes(3))

    def test_a_table_survives_a_round_trip(self) -> None:
        source = random.Random(1)
        data = bytes(source.randrange(256) for _ in range(512))

        self.assertEqual(palette.encode(palette.decode(data)), palette.normalise(data))

    def test_the_unused_top_bit_does_not_survive_the_round_trip(self) -> None:
        self.assertEqual(palette.encode(palette.decode(bytes([0x00, 0x80]))), bytes([0x00, 0x00]))

    def test_an_empty_table_is_a_table(self) -> None:
        self.assertEqual(palette.decode(b""), [])

    def test_clearing_the_unused_bit_refuses_a_table_of_odd_length(self) -> None:
        with self.assertRaises(Truncated):
            palette.normalise(bytes(3))


class BlockTest(unittest.TestCase):
    def test_a_four_bit_tile_reaches_sixteen_colours_at_a_time(self) -> None:
        self.assertEqual(palette.block_size(4), 16)

    def test_a_two_bit_tile_reaches_four(self) -> None:
        self.assertEqual(palette.block_size(2), 4)

    def test_an_eight_bit_tile_reaches_the_whole_table(self) -> None:
        self.assertEqual(palette.block_size(8), 256)

    def test_a_block_starts_where_its_number_puts_it(self) -> None:
        self.assertEqual(palette.block_start(4, 3), 48)

    def test_the_first_block_starts_at_the_beginning(self) -> None:
        self.assertEqual(palette.block_start(2, 0), 0)

    def test_a_depth_with_no_palette_block_is_refused(self) -> None:
        with self.assertRaises(OutOfRange):
            palette.block_size(3)

    def test_a_block_number_past_the_end_of_the_table_is_refused(self) -> None:
        with self.assertRaises(OutOfRange):
            palette.block_start(4, 16)

    def test_a_depth_with_only_one_block_refuses_a_second(self) -> None:
        with self.assertRaises(OutOfRange):
            palette.block_start(8, 1)

    def test_resolving_a_pixel_gives_the_colour_the_hardware_would_show(self) -> None:
        table = [(0, 0, 0)] * 256
        table[48 + 5] = (0x10, 0x20, 0x30)

        self.assertEqual(palette.resolve(table, 5, depth=4, block=3), (0x10, 0x20, 0x30))

    def test_a_pixel_too_large_for_its_depth_is_refused(self) -> None:
        with self.assertRaises(OutOfRange):
            palette.resolve([(0, 0, 0)] * 256, 16, depth=4, block=0)


class TransparencyTest(unittest.TestCase):
    def test_the_first_colour_of_a_block_is_the_one_that_shows_through(self) -> None:
        self.assertTrue(palette.is_transparent(0))

    def test_and_no_other_colour_is(self) -> None:
        self.assertFalse(palette.is_transparent(1))


if __name__ == "__main__":
    unittest.main()
