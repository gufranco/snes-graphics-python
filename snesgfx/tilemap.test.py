import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from snesgfx import tilemap


def word_of(entry):
    return entry.word


class EntryTest(unittest.TestCase):
    def test_the_low_ten_bits_are_the_tile_number(self):
        self.assertEqual(tilemap.Entry.from_word(0x03FF).tile, 0x3FF)

    def test_the_next_three_are_the_palette_block(self):
        self.assertEqual(tilemap.Entry.from_word(0x1C00).block, 7)

    def test_the_bit_above_those_is_the_priority(self):
        self.assertTrue(tilemap.Entry.from_word(0x2000).priority)

    def test_the_top_two_are_the_mirroring(self):
        found = tilemap.Entry.from_word(0xC000)

        self.assertTrue(found.horizontal_flip)
        self.assertTrue(found.vertical_flip)

    def test_a_cleared_word_is_a_plain_entry(self):
        found = tilemap.Entry.from_word(0x0000)

        self.assertEqual((found.tile, found.block), (0, 0))
        self.assertFalse(found.priority)

    def test_every_word_survives_a_round_trip(self):
        for word in range(0x10000):
            self.assertEqual(tilemap.Entry.from_word(word).word, word)

    def test_a_tile_number_too_large_for_ten_bits_is_refused(self):
        entry = tilemap.Entry(tile=0x400)

        with self.assertRaises(tilemap.OutOfRange):
            word_of(entry)

    def test_a_palette_block_too_large_for_three_bits_is_refused(self):
        entry = tilemap.Entry(block=8)

        with self.assertRaises(tilemap.OutOfRange):
            word_of(entry)


class ScreenTest(unittest.TestCase):
    def test_the_smallest_screen_is_one_quadrant(self):
        self.assertEqual(tilemap.screen_size(0), (32, 32))

    def test_a_wide_screen_is_two_side_by_side(self):
        self.assertEqual(tilemap.screen_size(1), (64, 32))

    def test_a_tall_screen_is_two_stacked(self):
        self.assertEqual(tilemap.screen_size(2), (32, 64))

    def test_the_largest_is_four(self):
        self.assertEqual(tilemap.screen_size(3), (64, 64))

    def test_a_size_the_hardware_does_not_have_is_refused(self):
        with self.assertRaises(tilemap.OutOfRange):
            tilemap.screen_size(4)


class QuadrantTest(unittest.TestCase):
    def test_a_position_in_the_first_quadrant_is_where_it_says(self):
        self.assertEqual(tilemap.offset_of(3, 4, size=3), 4 * 32 + 3)

    def test_the_second_quadrant_starts_a_whole_quadrant_along(self):
        self.assertEqual(tilemap.offset_of(32, 0, size=3), tilemap.QUADRANT_ENTRIES)

    def test_the_third_quadrant_of_a_tall_screen_follows_the_first(self):
        self.assertEqual(tilemap.offset_of(0, 32, size=2), tilemap.QUADRANT_ENTRIES)

    def test_the_third_quadrant_of_a_full_screen_follows_two(self):
        self.assertEqual(tilemap.offset_of(0, 32, size=3), 2 * tilemap.QUADRANT_ENTRIES)

    def test_the_fourth_quadrant_follows_three(self):
        self.assertEqual(tilemap.offset_of(32, 32, size=3), 3 * tilemap.QUADRANT_ENTRIES)

    def test_a_position_past_the_screen_wraps_back_into_it(self):
        self.assertEqual(tilemap.offset_of(64, 0, size=3), tilemap.offset_of(0, 0, size=3))

    def test_a_narrow_screen_wraps_at_its_own_width(self):
        self.assertEqual(tilemap.offset_of(32, 0, size=0), tilemap.offset_of(0, 0, size=0))


class MapTest(unittest.TestCase):
    def test_a_map_holds_one_entry_for_every_two_bytes(self):
        self.assertEqual(len(tilemap.decode(bytes(8))), 4)

    def test_an_entry_is_two_bytes_low_first(self):
        self.assertEqual(tilemap.decode(bytes([0x34, 0x12]))[0].word, 0x1234)

    def test_a_map_of_odd_length_is_refused(self):
        with self.assertRaises(tilemap.Truncated):
            tilemap.decode(bytes(3))

    def test_a_map_survives_a_round_trip(self):
        source = random.Random(1)
        data = bytes(source.randrange(256) for _ in range(tilemap.QUADRANT_ENTRIES * 2))

        self.assertEqual(tilemap.encode(tilemap.decode(data)), data)

    def test_an_empty_map_is_a_map(self):
        self.assertEqual(tilemap.decode(b""), [])

    def test_reading_a_position_reaches_the_entry_the_hardware_would(self):
        data = bytearray(tilemap.QUADRANT_ENTRIES * 2 * 4)
        at = tilemap.offset_of(32, 32, size=3) * 2
        data[at] = 0x07

        found = tilemap.entry_at(tilemap.decode(bytes(data)), 32, 32, size=3)

        self.assertEqual(found.tile, 7)


class ReadingTest(unittest.TestCase):
    def test_an_entry_prints_as_the_tile_and_the_block(self):
        found = repr(tilemap.Entry(tile=9, block=2))

        self.assertIn("9", found)
        self.assertIn("2", found)

    def test_two_entries_holding_the_same_thing_are_the_same_entry(self):
        self.assertEqual(tilemap.Entry(tile=1), tilemap.Entry(tile=1))

    def test_and_two_holding_different_things_are_not(self):
        self.assertNotEqual(tilemap.Entry(tile=1), tilemap.Entry(tile=2))

    def test_entries_holding_the_same_thing_collapse_in_a_set(self):
        self.assertEqual({tilemap.Entry(tile=1), tilemap.Entry(tile=1)}, {tilemap.Entry(tile=1)})


if __name__ == "__main__":
    unittest.main()
