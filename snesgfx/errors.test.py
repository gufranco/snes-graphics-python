from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from snesgfx import errors, mode7, oam, palette, tilemap, tiles  # noqa: E402


def reaching_back(source: str) -> list[str]:
    """Every import in that source that comes from this package rather than outside it.

    Written against text rather than against the one file it guards, so it can be
    handed something that should fail it. A reader nobody has seen report a fault
    reports a clean run whether or not there is one.

    A relative import counts however deep it goes, and an absolute one counts
    when it is the package or a module under it. The dot is required, because a
    package whose name merely begins the same way is somebody else's.
    """

    def inside(name: str) -> bool:
        return name.startswith(".") or name == "snesgfx" or name.startswith("snesgfx.")

    borrowed = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            borrowed += [alias.name for alias in node.names if inside(alias.name)]
        elif isinstance(node, ast.ImportFrom):
            name = "." * node.level + (node.module or "")
            if inside(name):
                borrowed.append(name)
    return borrowed


class OneHomeTest(unittest.TestCase):
    """That every refusal this package makes is defined here and nowhere else.

    Four modules each defined their own `Truncated` and four each defined their
    own `OutOfRange`. All eight worked, all eight were tested, and `except
    tiles.Truncated` sailed straight past the one the palette raised. That is the
    failure this module exists to make impossible rather than unlikely.
    """

    def named(self) -> list[str]:
        return [
            name
            for name, held in vars(errors).items()
            if isinstance(held, type) and issubclass(held, Exception)
        ]

    def test_the_module_defines_every_refusal_this_package_makes(self) -> None:
        self.assertEqual(
            sorted(self.named()),
            ["OutOfRange", "Truncated", "UnknownDepth", "UnknownFormat"],
        )

    def test_every_one_of_them_derives_from_exception(self) -> None:
        stray = [name for name in self.named() if not issubclass(getattr(errors, name), Exception)]

        self.assertEqual(stray, [])

    def test_and_every_one_says_what_it_means(self) -> None:
        """A refusal a caller meets and cannot look up is a refusal they guess at."""
        silent = [
            name for name in self.named() if not (getattr(errors, name).__doc__ or "").strip()
        ]

        self.assertEqual(silent, [])

    def test_none_of_them_is_a_subclass_of_another(self) -> None:
        """Or catching one would silently catch the other."""
        held = [getattr(errors, name) for name in self.named()]

        overlapping = [
            (one.__name__, other.__name__)
            for one in held
            for other in held
            if one is not other and issubclass(one, other)
        ]

        self.assertEqual(overlapping, [])


class OneClassPerNameTest(unittest.TestCase):
    """That every module reaching for a refusal reaches for the same object.

    Identity rather than name. Two classes under one name compare equal by name
    and are different objects, which is exactly why the old arrangement passed
    every test written against it.
    """

    def test_every_module_that_truncates_raises_the_one_truncated(self) -> None:
        held = {getattr(one, "Truncated") for one in (mode7, oam, palette, tilemap)}  # noqa: B009

        self.assertEqual(held, {errors.Truncated})

    def test_and_every_module_with_a_range_raises_the_one_out_of_range(self) -> None:
        held = {getattr(one, "OutOfRange") for one in (oam, palette, tilemap, tiles)}  # noqa: B009

        self.assertEqual(held, {errors.OutOfRange})

    def test_catching_the_published_name_catches_what_the_tiles_module_raises(self) -> None:
        with self.assertRaises(errors.UnknownDepth):
            tiles.decode(bytes(16), depth=6)

    def test_and_what_the_palette_module_raises(self) -> None:
        with self.assertRaises(errors.Truncated):
            palette.decode(bytes(3))


class NoCycleTest(unittest.TestCase):
    """That this module imports nothing from the package it belongs to.

    Everything here raises, so everything here imports this. An import running
    the other way closes the cycle and makes the order modules happen to load in
    decide whether the package works.
    """

    def test_it_imports_nothing_from_this_package(self) -> None:
        held = (ROOT / "snesgfx" / "errors.py").read_text()

        self.assertEqual(reaching_back(held), [])

    def test_the_reader_of_that_names_an_absolute_import_back(self) -> None:
        found = reaching_back("import snesgfx.tiles\n")

        self.assertEqual(found, ["snesgfx.tiles"])

    def test_and_a_relative_one(self) -> None:
        found = reaching_back("from . import tiles\n")

        self.assertEqual(found, ["."])

    def test_and_steps_over_one_from_outside(self) -> None:
        """The standard library and a package whose name merely starts the same."""
        found = reaching_back("from __future__ import annotations\nimport snesgfxtools\n")

        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
