import os
import random
import sys
import unittest
from collections.abc import Sequence
from pathlib import Path
from typing import override

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from snesgfx import tiles
from snesgfx.errors import OutOfRange, Truncated, UnknownDepth


def rows(pixels: Sequence[int]) -> list[Sequence[int]]:
    return [pixels[at : at + 8] for at in range(0, 64, 8)]


class ShapeTest(unittest.TestCase):
    def test_a_tile_is_eight_by_eight_whatever_its_depth(self) -> None:
        for depth in tiles.DEPTHS:
            self.assertEqual(len(tiles.decode(bytes(tiles.tile_bytes(depth)), depth)), 64)

    def test_each_depth_takes_the_bytes_the_format_says(self) -> None:
        self.assertEqual([tiles.tile_bytes(depth) for depth in tiles.DEPTHS], [16, 32, 64])

    def test_a_depth_the_hardware_does_not_have_is_refused(self) -> None:
        with self.assertRaises(UnknownDepth):
            tiles.tile_bytes(3)

    def test_six_bits_a_pixel_is_not_a_depth_this_hardware_has(self) -> None:
        with self.assertRaises(UnknownDepth):
            tiles.depth_of("6bpp")

    def test_and_the_refusal_lists_the_ones_it_does(self) -> None:
        with self.assertRaises(UnknownDepth) as caught:
            tiles.decode(b"", 5)

        self.assertIn("2", str(caught.exception))

    def test_data_of_the_wrong_length_is_refused_rather_than_padded(self) -> None:
        with self.assertRaises(Truncated):
            tiles.decode(bytes(15), 2)


class PlaneTest(unittest.TestCase):
    def test_the_first_plane_is_the_low_bit_of_every_pixel(self) -> None:
        data = bytearray(16)
        data[0] = 0b1010_0000

        pixels = tiles.decode(bytes(data), 2)

        self.assertEqual(rows(pixels)[0], [1, 0, 1, 0, 0, 0, 0, 0])

    def test_the_second_plane_is_the_next_bit_up(self) -> None:
        data = bytearray(16)
        data[1] = 0b1010_0000

        pixels = tiles.decode(bytes(data), 2)

        self.assertEqual(rows(pixels)[0], [2, 0, 2, 0, 0, 0, 0, 0])

    def test_the_two_planes_of_a_row_sit_next_to_each_other(self) -> None:
        data = bytearray(16)
        data[2] = 0xFF

        pixels = tiles.decode(bytes(data), 2)

        self.assertEqual(rows(pixels)[1], [1] * 8)

    def test_the_third_plane_of_a_four_bit_tile_starts_after_the_first_two(self) -> None:
        data = bytearray(32)
        data[16] = 0xFF

        pixels = tiles.decode(bytes(data), 4)

        self.assertEqual(rows(pixels)[0], [4] * 8)

    def test_the_leftmost_pixel_comes_from_the_highest_bit(self) -> None:
        data = bytearray(16)
        data[0] = 0x80

        pixels = tiles.decode(bytes(data), 2)

        self.assertEqual(pixels[0], 1)
        self.assertEqual(pixels[7], 0)

    def test_every_plane_of_an_eight_bit_tile_reaches_its_own_bit(self) -> None:
        for plane in range(8):
            data = bytearray(64)
            data[(plane // 2) * 16 + (plane % 2)] = 0xFF

            pixels = tiles.decode(bytes(data), 8)

            self.assertEqual(rows(pixels)[0], [1 << plane] * 8, f"plane {plane}")


class RoundTripTest(unittest.TestCase):
    def test_two_bit_tiles_survive_a_round_trip_for_every_possible_tile(self) -> None:
        for low in range(256):
            for high in range(256):
                data = bytes([low, high] + [0] * 14)

                self.assertEqual(tiles.encode(tiles.decode(data, 2), 2), data)

    def test_the_other_depths_survive_it_over_a_large_sample(self) -> None:
        source = random.Random(1)
        for depth in (4, 8):
            for _ in range(2000):
                data = bytes(source.randrange(256) for _ in range(tiles.tile_bytes(depth)))

                self.assertEqual(tiles.encode(tiles.decode(data, depth), depth), data)

    def test_pixels_survive_a_round_trip_the_other_way_round(self) -> None:
        source = random.Random(2)
        for depth in tiles.DEPTHS:
            limit = 1 << depth
            for _ in range(500):
                pixels = [source.randrange(limit) for _ in range(64)]

                self.assertEqual(tiles.decode(tiles.encode(pixels, depth), depth), pixels)

    def test_a_pixel_too_large_for_the_depth_is_refused(self) -> None:
        with self.assertRaises(OutOfRange):
            tiles.encode([4] + [0] * 63, 2)

    def test_a_run_of_pixels_that_is_not_a_tile_is_refused(self) -> None:
        with self.assertRaises(Truncated):
            tiles.encode([0] * 63, 2)


class SheetTest(unittest.TestCase):
    def test_a_sheet_holds_as_many_tiles_as_the_bytes_allow(self) -> None:
        sheet = tiles.decode_sheet(bytes(16 * 4), 2)

        self.assertEqual(len(sheet), 4)

    def test_a_sheet_that_stops_mid_tile_is_refused(self) -> None:
        with self.assertRaises(Truncated):
            tiles.decode_sheet(bytes(24), 2)

    def test_a_sheet_survives_a_round_trip(self) -> None:
        source = random.Random(3)
        data = bytes(source.randrange(256) for _ in range(32 * 5))

        self.assertEqual(tiles.encode_sheet(tiles.decode_sheet(data, 4), 4), data)

    def test_an_empty_sheet_is_a_sheet(self) -> None:
        self.assertEqual(tiles.decode_sheet(b"", 4), [])


class FlipTest(unittest.TestCase):
    def test_flipping_across_reverses_every_row(self) -> None:
        pixels = list(range(64))

        flipped = tiles.flip(pixels, horizontal=True)

        self.assertEqual(rows(flipped)[0], list(reversed(range(8))))

    def test_flipping_down_reverses_the_order_of_the_rows(self) -> None:
        pixels = list(range(64))

        flipped = tiles.flip(pixels, vertical=True)

        self.assertEqual(rows(flipped)[0], list(range(56, 64)))

    def test_flipping_both_ways_is_a_half_turn(self) -> None:
        pixels = list(range(64))

        flipped = tiles.flip(pixels, horizontal=True, vertical=True)

        self.assertEqual(flipped, list(reversed(range(64))))

    def test_flipping_twice_the_same_way_changes_nothing(self) -> None:
        pixels = list(range(64))

        self.assertEqual(tiles.flip(tiles.flip(pixels, horizontal=True), horizontal=True), pixels)

    def test_flipping_no_way_at_all_changes_nothing(self) -> None:
        pixels = list(range(64))

        self.assertEqual(tiles.flip(pixels), pixels)


class NameTest(unittest.TestCase):
    def test_each_depth_is_known_by_the_name_people_use_for_it(self) -> None:
        self.assertEqual(tiles.depth_of("4bpp"), 4)

    def test_the_bit_count_alone_names_it_too(self) -> None:
        self.assertEqual(tiles.depth_of(4), 4)

    def test_the_colour_count_names_it_as_well(self) -> None:
        self.assertEqual(tiles.depth_of("16-colour"), 4)

    def test_a_name_no_depth_answers_to_is_refused(self) -> None:
        with self.assertRaises(UnknownDepth):
            tiles.depth_of("3bpp")

    def test_a_depth_given_as_a_number_outside_the_set_is_refused(self) -> None:
        with self.assertRaises(UnknownDepth):
            tiles.depth_of(6)


class HandedInTest(unittest.TestCase):
    """That a caller with bytes needs no file, no directory and no variable.

    Every layout here is reached by handing the bytes over. `SNES_CARTRIDGE_DIR`
    exists for the corpus runner under `conformance/` and never reaches this
    package, so it is set to a directory that does not exist for the whole of
    this class: if any of these calls had grown a file read, it would fail here
    rather than quietly reading whatever that machine happened to have.
    """

    @override
    def setUp(self) -> None:
        held = os.environ.get("SNES_CARTRIDGE_DIR")
        self.addCleanup(os.environ.__setitem__, "SNES_CARTRIDGE_DIR", held or "")
        os.environ["SNES_CARTRIDGE_DIR"] = "/nowhere-at-all"

    def test_a_tile_is_decoded_from_bytes_alone(self) -> None:
        data = bytes.fromhex("3c00423cbd7ea566a566bd7e423c3c00")

        found = tiles.decode(data, 2)

        self.assertEqual(len(found), 64)

    def test_and_encoded_back_to_the_same_bytes(self) -> None:
        data = bytes.fromhex("3c00423cbd7ea566a566bd7e423c3c00")

        found = tiles.encode(tiles.decode(data, 2), 2)

        self.assertEqual(found, data)

    def test_no_file_under_the_package_names_that_variable(self) -> None:
        package = Path(__file__).resolve().parent
        naming = [
            one.name
            for one in sorted(package.glob("*.py"))
            if "SNES_CARTRIDGE_DIR" in one.read_text()
        ]

        self.assertEqual(naming, [Path(__file__).name])


if __name__ == "__main__":
    unittest.main()
