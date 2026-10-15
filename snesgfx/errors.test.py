from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from snesgfx import errors, mode7, oam, palette, tilemap, tiles  # noqa: E402


def reaching_back(source: str) -> list[str]:

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

    def test_none_of_them_is_a_subclass_of_another(self) -> None:
        held = [getattr(errors, name) for name in self.named()]

        overlapping = [
            (one.__name__, other.__name__)
            for one in held
            for other in held
            if one is not other and issubclass(one, other)
        ]

        self.assertEqual(overlapping, [])


class OneClassPerNameTest(unittest.TestCase):
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
        found = reaching_back("from __future__ import annotations\nimport snesgfxtools\n")

        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
