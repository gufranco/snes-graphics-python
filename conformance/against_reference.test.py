import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from conformance import against_reference as against  # noqa: E402
from snesgfx import palette, tilemap, tiles  # noqa: E402


class Answering:
    """A reference that answers whatever it is told to, without a process."""

    def __init__(self, answers: dict[str, str] | None = None, wrong: bool = False) -> None:
        self.answers = answers or {}
        self.wrong = wrong
        self.asked: list[str] = []

    def ask(self, question: str) -> str:
        self.asked.append(question)
        if question in self.answers:
            return self.answers[question]
        return "DEAD" if self.wrong else self.correct(question)

    def correct(self, question: str) -> str:
        verb, rest = question.split(" ", 1)
        if verb == "tile":
            depth, held = rest.split(" ")
            return "".join(f"{one:02X}" for one in tiles.decode(bytes.fromhex(held), int(depth)))
        if verb == "colour":
            packed = int(rest)
            red = (packed & 0x1F) << 3
            green = ((packed >> 8) & 0x1F) << 3
            blue = ((packed >> 16) & 0x1F) << 3
            return palette.encode([(red, green, blue)]).hex().upper()
        tile, block, horizontal, vertical = (int(one) for one in rest.split(" "))
        return (
            tilemap.encode(
                [
                    tilemap.Entry(
                        tile=tile,
                        block=block,
                        horizontal_flip=bool(horizontal),
                        vertical_flip=bool(vertical),
                    )
                ]
            )
            .hex()
            .upper()
        )


class OneBitTileTest(unittest.TestCase):
    def test_every_bit_of_a_two_bit_tile_is_tried_once(self) -> None:
        held = list(against.one_bit_tiles(2))

        self.assertEqual(len(held), 16 * 8)

    def test_and_each_case_sets_exactly_one_bit(self) -> None:
        for _, data in against.one_bit_tiles(4):
            self.assertEqual(sum(bin(one).count("1") for one in data), 1)

    def test_the_tile_is_the_width_the_depth_calls_for(self) -> None:
        for depth, width in against.BYTES_FOR_DEPTH.items():
            _, data = next(iter(against.one_bit_tiles(depth)))

            self.assertEqual(len(data), width, depth)

    def test_the_bits_are_walked_from_the_first_byte_onward(self) -> None:
        held = [at for at, _ in against.one_bit_tiles(2)]

        self.assertEqual(held, sorted(held))


class DisagreementTest(unittest.TestCase):
    def test_a_reference_that_agrees_reports_nothing_for_tiles(self) -> None:
        self.assertEqual(against.tile_disagreements(Answering()), [])

    def test_and_one_that_does_not_is_reported_for_every_case(self) -> None:
        held = against.tile_disagreements(Answering(wrong=True))

        self.assertEqual(len(held), sum(one * 8 for one in against.BYTES_FOR_DEPTH.values()))

    def test_a_reference_that_agrees_reports_nothing_for_colours(self) -> None:
        self.assertEqual(against.colour_disagreements(Answering()), [])

    def test_and_a_single_wrong_colour_is_named(self) -> None:
        held = against.colour_disagreements(Answering({"colour 0": "FFFF"}))

        self.assertEqual(len(held), 1)

    def test_and_the_report_names_both_answers(self) -> None:
        held = against.colour_disagreements(Answering({"colour 0": "FFFF"}))

        self.assertIn("FFFF", held[0])

    def test_a_reference_that_agrees_reports_nothing_for_entries(self) -> None:
        self.assertEqual(against.entry_disagreements(Answering()), [])

    def test_and_a_single_wrong_entry_is_named(self) -> None:
        held = against.entry_disagreements(Answering({"entry 0 0 0 0": "FFFF"}))

        self.assertEqual(len(held), 1)

    def test_the_walk_asks_about_both_flips_and_neither_and_both(self) -> None:
        reference = Answering()

        against.entry_disagreements(reference)

        self.assertEqual(
            sorted({one.rsplit(" ", 2)[-2] + one[-2:] for one in reference.asked[:4]}),
            ["0 0", "0 1", "1 0", "1 1"],
        )


class CompareTest(unittest.TestCase):
    def test_a_clean_comparison_finds_nothing(self) -> None:
        _, found = against.compare(Answering())

        self.assertEqual(found, [])

    def test_and_counts_every_case_it_asked_about(self) -> None:
        reference = Answering()

        asked, _ = against.compare(reference)

        self.assertEqual(asked, len(reference.asked))

    def test_a_broken_reference_disagrees_about_everything(self) -> None:
        asked, found = against.compare(Answering(wrong=True))

        self.assertEqual(len(found), asked)


class ReportTest(unittest.TestCase):
    def test_a_clean_run_says_how_much_it_compared(self) -> None:
        lines = against.report(66432, [])

        self.assertIn("66,432", lines[0])

    def test_and_says_nothing_disagreed(self) -> None:
        lines = against.report(10, [])

        self.assertIn("none disagreed", lines[0])

    def test_a_dirty_run_counts_them(self) -> None:
        lines = against.report(10, ["one", "two"])

        self.assertIn("2 of 10", lines[0])

    def test_and_names_them(self) -> None:
        lines = against.report(10, ["a disagreement"])

        self.assertIn("a disagreement", lines[1])

    def test_a_flood_is_cut_so_a_log_stays_readable(self) -> None:
        lines = against.report(100, [f"one {at}" for at in range(50)])

        self.assertEqual(len(lines), 21)


class ReferenceTest(unittest.TestCase):
    def test_a_driver_that_is_not_built_is_refused_by_name(self) -> None:
        where = Path(tempfile.mkdtemp()) / "driver"

        with self.assertRaises(against.Missing):
            against.Reference(where)

    def test_and_the_refusal_says_how_to_build_it(self) -> None:
        where = Path(tempfile.mkdtemp()) / "driver"

        with self.assertRaises(against.Missing) as caught:
            against.Reference(where)

        self.assertIn("conformance.build", str(caught.exception))

    def test_it_speaks_to_a_process_a_line_at_a_time(self) -> None:
        with (
            unittest.mock.patch.object(Path, "exists", lambda _: True),
            unittest.mock.patch.object(subprocess, "Popen") as opened,
        ):
            opened.return_value.stdout.readline.return_value = "BEEF\n"
            reference = against.Reference(Path("anywhere"))

            self.assertEqual(reference.ask("colour 0"), "BEEF")

    def test_and_closes_the_process_when_it_is_done(self) -> None:
        with (
            unittest.mock.patch.object(Path, "exists", lambda _: True),
            unittest.mock.patch.object(subprocess, "Popen") as opened,
        ):
            with against.Reference(Path("anywhere")):
                pass

            opened.return_value.wait.assert_called_once()

    def test_a_process_with_no_input_stream_is_closed_without_raising(self) -> None:
        with (
            unittest.mock.patch.object(Path, "exists", lambda _: True),
            unittest.mock.patch.object(subprocess, "Popen") as opened,
        ):
            opened.return_value.stdin = None

            against.Reference(Path("anywhere")).close()

            opened.return_value.wait.assert_called_once()


class MainTest(unittest.TestCase):
    def test_a_machine_without_the_reference_says_so_and_does_not_fail(self) -> None:
        said: list[str] = []

        def refuse(*_: Any, **__: Any) -> Any:
            raise against.Missing("not built")

        with unittest.mock.patch.object(against, "Reference", refuse):
            code = against.main((), said.append)

        self.assertEqual(code, 0)

    def test_and_the_line_it_prints_names_what_is_absent(self) -> None:
        said: list[str] = []

        def refuse(*_: Any, **__: Any) -> Any:
            raise against.Missing("not built")

        with unittest.mock.patch.object(against, "Reference", refuse):
            against.main((), said.append)

        self.assertIn("not built", said[0])

    def test_a_clean_comparison_exits_zero(self) -> None:
        said: list[str] = []

        with unittest.mock.patch.object(against, "Reference", lambda: _Held(Answering())):
            code = against.main((), said.append)

        self.assertEqual(code, 0)

    def test_and_a_disagreement_exits_one(self) -> None:
        said: list[str] = []

        with unittest.mock.patch.object(against, "Reference", lambda: _Held(Answering(wrong=True))):
            code = against.main((), said.append)

        self.assertEqual(code, 1)


class _Held:
    """A stand-in that satisfies the context manager without a process."""

    def __init__(self, answering: Answering) -> None:
        self.answering = answering

    def __enter__(self) -> Answering:
        return self.answering

    def __exit__(self, *_: object) -> None:
        return None


if __name__ == "__main__":
    unittest.main()
