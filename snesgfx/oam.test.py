import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from snesgfx import oam
from snesgfx.errors import OutOfRange, Truncated


def blank() -> bytearray:
    return bytearray(oam.TABLE_BYTES)


class ShapeTest(unittest.TestCase):
    def test_the_table_holds_a_hundred_and_twenty_eight_sprites(self) -> None:
        self.assertEqual(len(oam.decode(bytes(oam.TABLE_BYTES))), oam.SPRITES)

    def test_the_table_is_the_size_the_hardware_gives_it(self) -> None:
        self.assertEqual(oam.TABLE_BYTES, 544)

    def test_a_table_of_the_wrong_size_is_refused(self) -> None:
        with self.assertRaises(Truncated):
            oam.decode(bytes(512))


class LowTableTest(unittest.TestCase):
    def test_the_first_byte_is_the_low_eight_bits_of_the_horizontal_position(self) -> None:
        data = blank()
        data[0] = 0x42

        self.assertEqual(oam.decode(bytes(data))[0].x, 0x42)

    def test_the_second_byte_is_the_vertical_position(self) -> None:
        data = blank()
        data[1] = 0x37

        self.assertEqual(oam.decode(bytes(data))[0].y, 0x37)

    def test_the_third_byte_is_the_tile_number(self) -> None:
        data = blank()
        data[2] = 0x5A

        self.assertEqual(oam.decode(bytes(data))[0].tile, 0x5A)

    def test_the_fourth_byte_carries_everything_else(self) -> None:
        data = blank()
        data[3] = 0b1110_1011

        found = oam.decode(bytes(data))[0]

        self.assertTrue(found.vertical_flip)
        self.assertTrue(found.horizontal_flip)
        self.assertEqual(found.priority, 2)
        self.assertEqual(found.block, 5)
        self.assertEqual(found.table, 1)

    def test_a_sprite_with_a_clear_fourth_byte_is_plain(self) -> None:
        found = oam.decode(bytes(oam.TABLE_BYTES))[0]

        self.assertFalse(found.horizontal_flip)
        self.assertEqual(found.priority, 0)

    def test_the_second_sprite_starts_four_bytes_along(self) -> None:
        data = blank()
        data[4] = 0x99

        self.assertEqual(oam.decode(bytes(data))[1].x, 0x99)


class HighTableTest(unittest.TestCase):
    def test_the_ninth_bit_of_the_position_lives_in_the_second_table(self) -> None:
        data = blank()
        data[512] = 0b0000_0001

        self.assertEqual(oam.decode(bytes(data))[0].x, 0x100)

    def test_and_the_size_bit_sits_beside_it(self) -> None:
        data = blank()
        data[512] = 0b0000_0010

        self.assertTrue(oam.decode(bytes(data))[0].large)

    def test_each_byte_of_the_second_table_carries_four_sprites(self) -> None:
        data = blank()
        data[512] = 0b1000_0000

        self.assertTrue(oam.decode(bytes(data))[3].large)

    def test_the_second_byte_carries_the_next_four(self) -> None:
        data = blank()
        data[513] = 0b0000_0010

        self.assertTrue(oam.decode(bytes(data))[4].large)

    def test_the_ninth_bit_makes_a_position_negative_rather_than_far_right(self) -> None:
        data = blank()
        data[0] = 0xF0
        data[512] = 0b0000_0001

        self.assertEqual(oam.decode(bytes(data))[0].screen_x, -16)

    def test_a_position_without_the_ninth_bit_is_where_it_says(self) -> None:
        data = blank()
        data[0] = 0x10

        self.assertEqual(oam.decode(bytes(data))[0].screen_x, 0x10)


class RoundTripTest(unittest.TestCase):
    def test_a_table_survives_a_round_trip(self) -> None:
        source = random.Random(1)
        data = bytes(source.randrange(256) for _ in range(oam.TABLE_BYTES))

        self.assertEqual(oam.encode(oam.decode(data)), data)

    def test_a_table_of_defaults_encodes_to_zeroes(self) -> None:
        self.assertEqual(oam.encode([oam.Sprite() for _ in range(oam.SPRITES)]), bytes(544))

    def test_a_run_that_is_not_a_full_table_is_refused(self) -> None:
        with self.assertRaises(Truncated):
            oam.encode([oam.Sprite()])

    def test_a_field_too_large_for_its_bits_is_refused(self) -> None:
        with self.assertRaises(OutOfRange):
            oam.encode([oam.Sprite(tile=0x200)] + [oam.Sprite()] * 127)

    def test_a_priority_outside_the_two_bits_it_has_is_refused(self) -> None:
        with self.assertRaises(OutOfRange):
            oam.encode([oam.Sprite(priority=4)] + [oam.Sprite()] * 127)


class SizeTest(unittest.TestCase):
    def test_a_size_setting_names_two_sizes(self) -> None:
        self.assertEqual(oam.sizes(0), ((8, 8), (16, 16)))

    def test_the_last_setting_is_the_largest_pair(self) -> None:
        self.assertEqual(oam.sizes(7), ((32, 32), (64, 64)))

    def test_a_setting_the_hardware_does_not_have_is_refused(self) -> None:
        with self.assertRaises(OutOfRange):
            oam.sizes(8)

    def test_a_small_sprite_takes_the_first_of_the_pair(self) -> None:
        self.assertEqual(oam.size_of(oam.Sprite(large=False), setting=0), (8, 8))

    def test_a_large_one_takes_the_second(self) -> None:
        self.assertEqual(oam.size_of(oam.Sprite(large=True), setting=0), (16, 16))


class ReadingTest(unittest.TestCase):
    def test_a_sprite_prints_as_where_it_is_and_what_it_shows(self) -> None:
        found = repr(oam.Sprite(x=10, y=20, tile=5))

        self.assertIn("10", found)
        self.assertIn("5", found)

    def test_two_sprites_holding_the_same_thing_are_the_same_sprite(self) -> None:
        self.assertEqual(oam.Sprite(x=1), oam.Sprite(x=1))

    def test_and_two_holding_different_things_are_not(self) -> None:
        self.assertNotEqual(oam.Sprite(x=1), oam.Sprite(x=2))

    def test_sprites_holding_the_same_thing_collapse_in_a_set(self) -> None:
        self.assertEqual({oam.Sprite(x=1), oam.Sprite(x=1)}, {oam.Sprite(x=1)})


if __name__ == "__main__":
    unittest.main()
