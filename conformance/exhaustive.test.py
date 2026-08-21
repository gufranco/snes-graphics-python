import importlib
import sys
import unittest
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

exhaustive: Any = importlib.import_module("exhaustive")


class CheckTest(unittest.TestCase):
    def test_every_check_reports_how_many_cases_it_settled(self) -> None:
        for check in exhaustive.CHECKS:
            found = check.run()

            self.assertGreater(found.cases, 0, check.name)

    def test_every_check_passes(self) -> None:
        for check in exhaustive.CHECKS:
            self.assertEqual(check.run().failures, [], check.name)

    def test_every_check_says_what_it_settles(self) -> None:
        for check in exhaustive.CHECKS:
            self.assertTrue(check.summary.strip())

    def test_the_checks_between_them_settle_six_figures_of_cases(self) -> None:
        total = sum(check.run().cases for check in exhaustive.CHECKS)

        self.assertGreater(total, 150_000)


class ResultTest(unittest.TestCase):
    def test_a_result_prints_as_the_name_and_the_count(self) -> None:
        found = exhaustive.Result(name="thing", cases=5, failures=[])

        self.assertIn("thing", repr(found))
        self.assertIn("5", repr(found))

    def test_a_result_with_failures_is_not_clean(self) -> None:
        self.assertFalse(exhaustive.Result(name="x", cases=1, failures=["bad"]).clean)

    def test_and_one_without_them_is(self) -> None:
        self.assertTrue(exhaustive.Result(name="x", cases=1, failures=[]).clean)


class RunTest(unittest.TestCase):
    def test_a_full_run_reports_clean(self) -> None:
        self.assertEqual(exhaustive.run([]), 0)

    def test_naming_one_check_runs_only_that_one(self) -> None:
        self.assertEqual(exhaustive.run(["--only", exhaustive.CHECKS[0].name]), 0)

    def test_naming_a_check_that_does_not_exist_is_refused(self) -> None:
        self.assertEqual(exhaustive.run(["--only", "nothing"]), 2)

    def test_an_option_it_does_not_know_is_refused(self) -> None:
        with self.assertRaises(exhaustive.Usage):
            exhaustive.options(["--nonsense"])

    def test_an_option_with_no_value_is_refused(self) -> None:
        with self.assertRaises(exhaustive.Usage):
            exhaustive.options(["--only"])

    def test_the_default_is_to_run_them_all(self) -> None:
        self.assertIsNone(exhaustive.options([]).only)


class CatchesDefectsTest(unittest.TestCase):
    """A check that cannot fail proves nothing, so each one is shown to fail."""

    def broken(self, name: str, module: Any, attribute: str, replacement: Any) -> Any:
        original = getattr(module, attribute)
        setattr(module, attribute, replacement)
        try:
            return next(check for check in exhaustive.CHECKS if check.name == name).run()
        finally:
            setattr(module, attribute, original)

    def test_a_tile_that_does_not_round_trip_is_caught(self) -> None:
        found = self.broken(
            "tiles-2bpp", exhaustive.tiles, "encode", lambda pixels, depth: b"\x00" * 16
        )

        self.assertFalse(found.clean)

    def test_a_plane_reaching_the_wrong_bit_is_caught(self) -> None:
        found = self.broken(
            "tiles-planes", exhaustive.tiles, "decode", lambda data, depth: [0] * 64
        )

        self.assertFalse(found.clean)

    def test_a_colour_that_does_not_narrow_back_is_caught(self) -> None:
        found = self.broken("palette", exhaustive.palette, "to_word", lambda r, g, b: 0)

        self.assertFalse(found.clean)

    def test_a_map_entry_that_does_not_round_trip_is_caught(self) -> None:
        found = self.broken(
            "tilemap",
            exhaustive.tilemap,
            "Entry",
            type("E", (), {"from_word": staticmethod(lambda word: type("W", (), {"word": 0})())}),
        )

        self.assertFalse(found.clean)

    def test_a_sprite_slot_read_from_the_wrong_place_is_caught(self) -> None:
        found = self.broken(
            "oam-high",
            exhaustive.oam,
            "decode",
            lambda data: [exhaustive.oam.Sprite(x=0x100, large=True) for _ in range(128)],
        )

        self.assertFalse(found.clean)

    def test_a_sprite_slot_that_disturbs_a_neighbour_is_caught(self) -> None:
        found = self.broken(
            "oam-high",
            exhaustive.oam,
            "decode",
            lambda data: [exhaustive.oam.Sprite(x=0x100 if at == 127 else 0) for at in range(128)],
        )

        self.assertTrue(any("neighbour" in failure for failure in found.failures))

    def test_a_run_with_a_broken_check_reports_the_failure(self) -> None:
        original = exhaustive.palette.to_word
        exhaustive.palette.to_word = lambda r, g, b: 0
        try:
            self.assertEqual(exhaustive.run(["--only", "palette"]), 1)
        finally:
            exhaustive.palette.to_word = original


class EntryTest(unittest.TestCase):
    def test_a_run_from_the_command_line_returns_what_the_run_returned(self) -> None:
        self.assertEqual(exhaustive.main(["--only", exhaustive.CHECKS[0].name]), 0)

    def test_an_option_it_does_not_know_is_reported(self) -> None:
        self.assertEqual(exhaustive.main(["--nonsense"]), 2)


if __name__ == "__main__":
    unittest.main()
