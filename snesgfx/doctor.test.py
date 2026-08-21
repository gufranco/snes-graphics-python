import sys
import unittest
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from snesgfx import doctor


class Complaint(Exception):
    pass


def a_finding(
    name: str = "something", ok: bool = True, detail: str = "detail", advice: str | None = None
) -> Any:
    return doctor.Finding(name, ok, detail, advice)


class FindingTest(unittest.TestCase):
    def test_a_finding_says_what_was_checked(self) -> None:
        self.assertEqual(a_finding(name="the palette").name, "the palette")

    def test_and_whether_it_was_well(self) -> None:
        self.assertTrue(a_finding(ok=True).ok)
        self.assertFalse(a_finding(ok=False).ok)

    def test_a_healthy_finding_prints_with_a_mark_that_says_so(self) -> None:
        self.assertIn("ok", a_finding(ok=True).line)

    def test_and_an_unhealthy_one_prints_differently(self) -> None:
        self.assertNotIn("ok", a_finding(ok=False).line)

    def test_every_finding_carries_what_it_actually_saw(self) -> None:
        self.assertIn("64 pixels", a_finding(detail="64 pixels").line)

    def test_an_unhealthy_finding_says_what_to_do_about_it(self) -> None:
        self.assertIn("go and look", a_finding(ok=False, advice="go and look").report)

    def test_a_healthy_one_carries_no_advice(self) -> None:
        self.assertEqual(a_finding(ok=True, advice="x").report, a_finding(ok=True).line)

    def test_a_finding_prints_as_itself(self) -> None:
        self.assertIn("something", repr(a_finding()))


class ExamineTest(unittest.TestCase):
    def test_the_examination_produces_findings(self) -> None:
        self.assertTrue(doctor.examine())

    def test_it_reports_the_python_it_is_running_on(self) -> None:
        self.assertIn("python", [one.name for one in doctor.examine()])

    def test_and_the_version_of_this_package(self) -> None:
        self.assertIn("snesgfx", [one.name for one in doctor.examine()])

    def test_and_one_finding_per_layout_it_covers(self) -> None:
        from snesgfx import models

        names = [one.name for one in doctor.examine()]

        for layout in models.FORMATS:
            self.assertIn(layout, names, layout)

    def test_every_finding_carries_a_detail(self) -> None:
        for one in doctor.examine():
            self.assertTrue(one.detail, one.name)

    def test_a_layout_that_will_not_decode_is_reported_rather_than_hidden(self) -> None:
        def boom(_name: str, _data: Any) -> Any:
            raise Complaint("the decoder exploded")

        self.assertTrue(any(not one.ok for one in doctor.examine(decode=boom)))

    def test_and_the_report_carries_what_it_said_and_what_kind(self) -> None:
        def boom(_name: str, _data: Any) -> Any:
            raise Complaint("the decoder exploded")

        text = "\n".join(one.report for one in doctor.examine(decode=boom))

        self.assertIn("the decoder exploded", text)
        self.assertIn("Complaint", text)

    def test_a_layout_that_decodes_says_how_much_came_out(self) -> None:
        for one in doctor.examine():
            if one.name == "4bpp":
                self.assertIn("decoded", one.detail)


class RoundTripTest(unittest.TestCase):
    """The one property worth the most here: what goes in comes back out."""

    def test_the_report_says_whether_a_tile_survives_the_round_trip(self) -> None:
        self.assertIn("round trip", [one.name for one in doctor.examine()])

    def test_a_tile_that_survives_is_reported_as_well(self) -> None:
        for one in doctor.examine():
            if one.name == "round trip":
                self.assertTrue(one.ok)

    def test_one_that_comes_back_different_is_a_failure(self) -> None:
        found = doctor._round_trip(
            lambda _name, data: data, lambda _name, _sheet: b"something else"
        )

        self.assertFalse(found.ok)

    def test_and_the_report_says_how_many_bytes_came_back(self) -> None:
        found = doctor._round_trip(lambda _name, data: data, lambda _name, _sheet: b"\x00")

        self.assertIn("1 byte", found.detail)

    def test_a_round_trip_that_throws_is_reported_rather_than_swallowed(self) -> None:
        def boom(_name: str, _data: Any) -> Any:
            raise Complaint("nothing encodes")

        found = doctor._round_trip(lambda _name, data: data, boom)

        self.assertFalse(found.ok)
        self.assertIn("nothing encodes", found.detail)


class ExhaustiveTest(unittest.TestCase):
    def test_the_report_names_what_is_settled_exhaustively(self) -> None:
        self.assertIn("settled exhaustively", [one.name for one in doctor.examine()])

    def test_and_lists_the_checks_by_name(self) -> None:
        found = doctor.examine()

        self.assertIn("palette", " ".join(one.detail for one in found))

    def test_a_conformance_module_that_cannot_be_read_is_reported(self) -> None:
        def boom() -> Any:
            raise Complaint("no checks at all")

        found = doctor._exhaustive(boom)

        self.assertFalse(found.ok)
        self.assertIn("no checks at all", found.detail)

    def test_and_one_that_lists_nothing_is_a_failure(self) -> None:
        found = doctor._exhaustive(tuple)

        self.assertFalse(found.ok)


class ReportTest(unittest.TestCase):
    def test_the_report_has_a_line_for_every_finding(self) -> None:
        found = doctor.examine()

        self.assertGreaterEqual(len(doctor.report(found)), len(found))

    def test_it_opens_with_something_that_says_what_it_is(self) -> None:
        self.assertIn("snesgfx", doctor.report(doctor.examine())[0])

    def test_an_unhealthy_run_says_how_many_did_not_pass(self) -> None:
        self.assertIn("1", " ".join(doctor.report([a_finding(ok=False)])))

    def test_a_healthy_run_says_there_is_nothing_to_report(self) -> None:
        self.assertIn("nothing to report", " ".join(doctor.report([a_finding(ok=True)])))


class EntryTest(unittest.TestCase):
    def test_a_healthy_run_reports_success(self) -> None:
        self.assertEqual(
            doctor.main([], examine=lambda **_: [a_finding(ok=True)], say=lambda _: None), 0
        )

    def test_an_unhealthy_one_reports_failure(self) -> None:
        self.assertEqual(
            doctor.main([], examine=lambda **_: [a_finding(ok=False)], say=lambda _: None), 1
        )

    def test_the_report_is_printed_rather_than_kept(self) -> None:
        said: list[str] = []

        doctor.main([], examine=lambda **_: [a_finding(ok=True)], say=said.append)

        self.assertTrue(said)

    def test_a_real_run_says_something_about_this_machine(self) -> None:
        said: list[str] = []

        doctor.main([], say=said.append)

        self.assertIn("snesgfx", " ".join(said))


if __name__ == "__main__":
    unittest.main()
