"""The cartridge check, held to inputs whose answer is known in advance.

Every decision it makes is taken as an argument, so a machine with a library of
cartridge images and a machine with none both exercise every path. The readings
themselves are checked against tiles built here, where what the right answer is
was decided before the code ran.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, override

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from conformance import against_cartridges as check
from snesgfx import tiles


def _stripes() -> bytes:
    return tiles.encode([at % 16 for at in range(tiles.TILE_PIXELS)], check.DEPTH)


PICTURE = bytes.fromhex("ff0f00ff00ffc3333ccc0f00000f3300f00fff0000ff0ff0c3f033cc3cc3f033")
"""A tile the published layout reads as more structured than the other two.

Searched for rather than reasoned out, because a tile that is perfectly flat
under the right layout can only be built from two byte values and a region of
those reads as padding. This one scores thirty against sixteen and thirteen, and
sixty four of it hold exactly the eight distinct bytes a region needs to be
judged at all.
"""


def _pictures() -> bytes:
    """A region of that tile."""
    return PICTURE * check.TILES_PER_REGION


class ReadingTest(unittest.TestCase):
    def test_the_documented_reading_is_the_package_itself(self) -> None:
        raw = _stripes()

        self.assertEqual(check.documented(raw), tiles.decode(raw, check.DEPTH))

    def test_every_reading_answers_a_whole_tile(self) -> None:
        raw = _stripes()

        held = [len(read(raw)) for _, read in check.READINGS]

        self.assertEqual(held, [tiles.TILE_PIXELS] * len(check.READINGS))

    def test_every_reading_answers_colours_the_depth_can_hold(self) -> None:
        raw = _stripes()

        outside = [name for name, read in check.READINGS if max(read(raw)) >= 1 << check.DEPTH]

        self.assertEqual(outside, [])

    def test_the_three_readings_are_not_the_same_reading(self) -> None:
        raw = _stripes()

        held = {tuple(read(raw)) for _, read in check.READINGS}

        self.assertEqual(len(held), len(check.READINGS))


class StructureTest(unittest.TestCase):
    def test_one_colour_everywhere_scores_the_most_there_is(self) -> None:
        held = check.structure([3] * tiles.TILE_PIXELS)

        self.assertEqual(held, 64.0)

    def test_a_different_colour_every_pixel_scores_the_least(self) -> None:
        held = check.structure([at % 16 for at in range(tiles.TILE_PIXELS)])

        self.assertEqual(held, 8.0)

    def test_renaming_the_colours_does_not_move_it(self) -> None:
        pixels = [0, 0, 1, 1, 2, 2, 3, 3] * 8
        renamed = [(one + 5) % 16 for one in pixels]

        self.assertEqual(check.structure(pixels), check.structure(renamed))


class RegionTest(unittest.TestCase):
    def test_a_region_of_one_repeated_byte_is_passed_over(self) -> None:
        held = list(check.regions(bytes(check.LIMIT)))

        self.assertEqual(held, [])

    def test_an_image_too_short_to_hold_one_yields_nothing(self) -> None:
        held = list(check.regions(bytes(check.FIRST)))

        self.assertEqual(held, [])

    def test_a_tail_too_short_to_hold_one_ends_the_walk(self) -> None:
        image = bytearray(check.FIRST + check.STRIDE + 10)
        image[check.FIRST : check.FIRST + check.REGION_BYTES] = _pictures()

        held = list(check.regions(bytes(image)))

        self.assertEqual(len(held), 1)

    def test_a_region_with_enough_in_it_is_judged(self) -> None:
        image = bytearray(check.FIRST + check.REGION_BYTES)
        image[check.FIRST :] = _pictures()

        held = list(check.regions(bytes(image)))

        self.assertEqual(len(held), 1)


class WinsTest(unittest.TestCase):
    def test_a_region_the_published_layout_reads_best_goes_to_it(self) -> None:
        held = check.wins(_pictures())

        self.assertEqual(held, "documented")

    def test_and_it_wins_on_the_merits_rather_than_on_a_tie(self) -> None:
        scored = {name: check.structure(read(PICTURE)) for name, read in check.READINGS}

        self.assertGreater(
            scored["documented"], max(v for k, v in scored.items() if k != "documented")
        )

    def test_a_region_built_for_another_reading_does_not(self) -> None:
        """Bytes laid out two pixels to a byte, which is one of the other two."""
        block = bytes([0x11] * check.TILE_BYTES) * check.TILES_PER_REGION

        self.assertNotEqual(check.wins(block), "contiguous planes")


class WhereTest(unittest.TestCase):
    def test_a_named_directory_is_looked_at_first(self) -> None:
        held = check.directories({check.DIRECTORY_VARIABLE: "/somewhere"})

        self.assertEqual(held[0], Path("/somewhere"))

    def test_naming_nothing_still_leaves_the_two_this_project_knows(self) -> None:
        held = check.directories({})

        self.assertEqual(held, (check.ALONGSIDE, check.DEFAULT_DIRECTORY))

    def test_images_are_found_in_the_named_directory(self) -> None:
        where = Path(self.enterContext(tempfile.TemporaryDirectory()))
        (where / "b.sfc").write_bytes(b"")
        (where / "a.smc").write_bytes(b"")

        held = check.every({check.DIRECTORY_VARIABLE: str(where)})

        self.assertEqual([one.name for one in held], ["a.smc", "b.sfc"])

    def test_a_directory_holding_nothing_of_the_kind_answers_nothing(self) -> None:
        where = Path(self.enterContext(tempfile.TemporaryDirectory()))
        (where / "notes.txt").write_text("")

        self.assertEqual(check.every({check.DIRECTORY_VARIABLE: str(where)}), [])

    def test_a_directory_that_is_not_there_is_stepped_over(self) -> None:
        self.assertEqual(check.every({check.DIRECTORY_VARIABLE: "/nowhere-at-all"}), [])

    def test_with_nothing_named_the_first_place_that_is_there_is_read(self) -> None:
        where = Path(self.enterContext(tempfile.TemporaryDirectory()))

        held = check.where_to_look({}, places=(Path("/nowhere-at-all"), where))

        self.assertEqual(held, where)

    def test_and_when_no_place_is_there_it_answers_nothing(self) -> None:
        held = check.where_to_look({}, places=(Path("/nowhere-at-all"),))

        self.assertIsNone(held)


class ChosenTest(unittest.TestCase):
    def test_a_library_smaller_than_the_sample_is_taken_whole(self) -> None:
        found = [Path(f"{at}.sfc") for at in range(5)]

        self.assertEqual(check.chosen(found, how_many=10), found)

    def test_a_bigger_one_is_cut_to_size(self) -> None:
        found = [Path(f"{at}.sfc") for at in range(50)]

        self.assertEqual(len(check.chosen(found, how_many=10)), 10)

    def test_and_the_same_cut_on_every_machine(self) -> None:
        found = [Path(f"{at}.sfc") for at in range(50)]

        self.assertEqual(check.chosen(found, how_many=10), check.chosen(found, how_many=10))


class JudgeTest(unittest.TestCase):
    def test_it_counts_every_region_it_judged(self) -> None:
        where = Path(self.enterContext(tempfile.TemporaryDirectory()))
        image = bytearray(check.FIRST + check.REGION_BYTES)
        image[check.FIRST :] = _pictures()
        (where / "a.sfc").write_bytes(bytes(image))

        held = check.judge([where / "a.sfc"])

        self.assertEqual(held["regions"], 1)

    def test_and_the_reading_that_won_it(self) -> None:
        where = Path(self.enterContext(tempfile.TemporaryDirectory()))
        image = bytearray(check.FIRST + check.REGION_BYTES)
        image[check.FIRST :] = _pictures()
        (where / "a.sfc").write_bytes(bytes(image))

        held = check.judge([where / "a.sfc"])

        self.assertEqual(held["wins"]["documented"], 1)

    def test_the_floor_it_publishes_is_one_reading_in_three(self) -> None:
        held = check.judge([])

        self.assertAlmostEqual(held["floor"], 1 / len(check.READINGS))


class RecordTest(unittest.TestCase):
    @override
    def setUp(self) -> None:
        self.held = check.declared()

    def test_it_says_the_images_are_not_carried(self) -> None:
        self.assertFalse(self.held["carried"])

    def test_the_floor_it_records_is_the_one_the_code_publishes(self) -> None:
        self.assertAlmostEqual(self.held["floor"], 1 / len(check.READINGS), places=3)

    def test_the_readings_it_names_are_the_ones_that_ran(self) -> None:
        self.assertEqual(self.held["readings"], [name for name, _ in check.READINGS])

    def test_the_wins_it_records_add_up_to_the_regions_it_records(self) -> None:
        self.assertEqual(sum(self.held["wins"].values()), self.held["regions"])

    def test_the_published_layout_beat_the_floor(self) -> None:
        self.assertGreater(self.held["documentedShare"], self.held["floor"])

    def test_and_by_enough_to_be_worth_saying(self) -> None:
        self.assertGreater(self.held["documentedShare"], self.held["floor"] * 1.4)

    def test_it_says_what_it_does_not_cover(self) -> None:
        self.assertIn("still held to", self.held["howToSettleIt"])

    def test_a_record_can_be_read_from_somewhere_else(self) -> None:
        where = Path(self.enterContext(tempfile.TemporaryDirectory())) / "r.json"
        where.write_text(json.dumps({"regions": 0}))

        self.assertEqual(check.declared(where)["regions"], 0)


class RunTest(unittest.TestCase):
    def _look(self, documented: int, regions: int) -> Any:
        rest = regions - documented
        return lambda _images: {
            "regions": regions,
            "wins": {
                "documented": documented,
                "contiguous planes": rest,
                "two pixels per byte": 0,
            },
            "corpusDigest": "",
            "floor": 1 / len(check.READINGS),
        }

    def test_a_machine_holding_no_images_checks_nothing(self) -> None:
        said: list[str] = []

        code = check.main(say=said.append, find=list)

        self.assertEqual(code, check.NOTHING_CHECKED)

    def test_and_names_the_variable_that_would_point_at_them(self) -> None:
        said: list[str] = []

        check.main(say=said.append, find=list)

        self.assertIn(check.DIRECTORY_VARIABLE, said[0])

    def test_images_holding_no_region_worth_judging_check_nothing(self) -> None:
        said: list[str] = []

        code = check.main(say=said.append, find=lambda: [Path("a.sfc")], look=self._look(0, 0))

        self.assertEqual(code, check.NOTHING_CHECKED)

    def test_a_layout_that_beats_the_floor_passes(self) -> None:
        said: list[str] = []

        code = check.main(say=said.append, find=lambda: [Path("a.sfc")], look=self._look(60, 100))

        self.assertEqual(code, 0)

    def test_and_says_by_how_much(self) -> None:
        said: list[str] = []

        check.main(say=said.append, find=lambda: [Path("a.sfc")], look=self._look(60, 100))

        self.assertIn("60.0% against a floor of 33.3%", said[-1])

    def test_a_layout_that_does_no_better_than_chance_fails(self) -> None:
        """The check has been watched failing, on the only input that should fail it."""
        said: list[str] = []

        code = check.main(say=said.append, find=lambda: [Path("a.sfc")], look=self._look(33, 100))

        self.assertEqual(code, 1)

    def test_and_says_so_rather_than_reporting_a_number(self) -> None:
        said: list[str] = []

        check.main(say=said.append, find=lambda: [Path("a.sfc")], look=self._look(33, 100))

        self.assertIn("no better than chance", said[-1])


class SharedDirectoryRuleTest(unittest.TestCase):
    """The rule every member of this family uses to find a file it does not carry.

    Byte-identical in all of them, so these check the behaviour that identity is
    supposed to guarantee rather than the text of one copy.
    """

    def test_the_project_above_is_looked_at_before_the_package_itself(self) -> None:
        """Vendored, the parent owns the library, which is what ALONGSIDE is for."""
        found = check.directories({})

        self.assertLess(found.index(check.ALONGSIDE), found.index(check.DEFAULT_DIRECTORY))

    def test_a_named_directory_is_looked_at_before_either(self) -> None:
        found = check.directories({check.DIRECTORY_VARIABLE: "/x"})

        self.assertEqual(found[0], Path("/x"))

    def test_more_than_one_can_be_named_at_once(self) -> None:
        found = check.directories({check.DIRECTORY_VARIABLE: f"/x{os.pathsep}/y"})

        self.assertEqual(found[:2], (Path("/x"), Path("/y")))

    def test_an_empty_entry_between_two_names_is_passed_over(self) -> None:
        found = check.directories({check.DIRECTORY_VARIABLE: f"/x{os.pathsep}{os.pathsep}/y"})

        self.assertEqual(found[:2], (Path("/x"), Path("/y")))

    def test_no_directory_appears_twice(self) -> None:
        found = check.directories({check.DIRECTORY_VARIABLE: str(check.DEFAULT_DIRECTORY)})

        self.assertEqual(len(found), len(set(found)))


if __name__ == "__main__":
    unittest.main()
