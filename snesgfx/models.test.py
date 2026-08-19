import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from snesgfx import models


class CatalogueTest(unittest.TestCase):
    def test_the_catalogue_covers_every_tile_depth(self):
        for name in ("2bpp", "4bpp", "8bpp"):
            self.assertIn(name, models.FORMATS)

    def test_and_the_formats_that_are_not_tiles(self):
        for name in ("mode7", "palette", "tilemap", "oam"):
            self.assertIn(name, models.FORMATS)

    def test_every_format_says_what_it_is(self):
        for found in models.FORMATS.values():
            self.assertTrue(found.summary.strip())

    def test_a_format_prints_as_something_a_person_can_read(self):
        self.assertIn("4bpp", repr(models.describe("4bpp")))


class NameTest(unittest.TestCase):
    def test_a_format_is_found_by_its_own_name(self):
        self.assertEqual(models.describe("4bpp").name, "4bpp")

    def test_case_does_not_matter(self):
        self.assertEqual(models.describe("4BPP").name, "4bpp")

    def test_neither_do_the_separators_people_write(self):
        self.assertEqual(models.describe("Mode-7").name, "mode7")

    def test_an_alias_reaches_the_format_it_names(self):
        self.assertEqual(models.describe("16-colour").name, "4bpp")
        self.assertEqual(models.describe("sprites").name, "oam")

    def test_a_name_no_format_answers_to_is_refused(self):
        with self.assertRaises(models.UnknownFormat):
            models.describe("6bpp")

    def test_and_the_refusal_lists_what_there_is(self):
        with self.assertRaises(models.UnknownFormat) as caught:
            models.describe("nothing")

        self.assertIn("4bpp", str(caught.exception))


class RoundTripTest(unittest.TestCase):
    def test_a_tile_format_decodes_and_encodes_through_the_catalogue(self):
        found = models.describe("4bpp")
        data = bytes(range(32))

        self.assertEqual(found.encode(found.decode(data)), data)

    def test_the_palette_does_too(self):
        found = models.describe("palette")
        data = bytes([0x34, 0x12, 0x00, 0x7F])

        self.assertEqual(found.encode(found.decode(data)), data)

    def test_so_does_the_map(self):
        found = models.describe("tilemap")
        data = bytes([0x34, 0x12])

        self.assertEqual(found.encode(found.decode(data)), data)

    def test_and_the_sprite_table(self):
        found = models.describe("oam")
        data = bytes(544)

        self.assertEqual(found.encode(found.decode(data)), data)

    def test_mode_seven_data_round_trips_as_the_two_halves_it_is(self):
        found = models.describe("mode7")
        data = bytes([0x11, 0x22, 0x33, 0x44])

        self.assertEqual(found.encode(found.decode(data)), data)


if __name__ == "__main__":
    unittest.main()
