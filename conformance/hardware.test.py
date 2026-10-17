import json
import sys
import unittest
from pathlib import Path
from typing import Any, override

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from snesgfx import palette, tilemap, tiles

HERE = Path(__file__).resolve().parent


def declared(name: str) -> dict[str, Any]:
    held = json.loads((HERE / name).read_text())
    assert isinstance(held, dict), f"{name} does not hold an object"
    return held


FIGURES = declared("hardware.json")

FULL = 0xFF

FULL_CHANNEL = 0xFF

ROWS = range(8)

RGB = ("red", "green", "blue")

ENTRY_ATTRIBUTES = {
    "NAME": "tile",
    "COLOR": "block",
    "BG Pri.": "priority",
    "H": "horizontal_flip",
    "V": "vertical_flip",
}


def two_characters(depth: dict[str, Any]) -> bytes:
    size: int = depth["bytes"]
    return bytes(size) + bytes([FULL]) * size


def all_in_plane(plane: int) -> list[int]:
    return [1 << plane] * (len(ROWS) * len(ROWS))


def written_bytes(data: bytes) -> list[int]:
    return [at for at, byte in enumerate(data) if byte]


def field_value(field: dict[str, Any]) -> int:
    shift: int = field.get("shift", 0)
    return int(field["mask"], 16) << shift


def full(field: dict[str, Any]) -> int | bool:
    mask = int(field["mask"], 16)
    return mask if mask & 1 else True


def empty(field: dict[str, Any]) -> int | bool:
    return 0 if int(field["mask"], 16) & 1 else False


def entry_with(field: dict[str, Any]) -> tilemap.Entry:
    options: dict[str, Any] = {ENTRY_ATTRIBUTES[field["name"]]: full(field)}
    return tilemap.Entry(**options)


def entry_fields(entry: tilemap.Entry) -> dict[str, Any]:
    return {name: getattr(entry, attribute) for name, attribute in ENTRY_ATTRIBUTES.items()}


def bits_named(span: str) -> int:
    high, low = sorted((int(word[1:]) for word in span.split() if word[1:].isdigit()), reverse=True)
    return ((1 << (high - low + 1)) - 1) << low


class DocumentTest(unittest.TestCase):
    @override
    def setUp(self) -> None:
        self.declared = declared("hardware.json")

    def test_the_document_is_pinned_by_digest(self) -> None:
        document = self.declared["documents"]["developmentManual"]

        self.assertEqual(len(document["sha256"]), 64)

    def test_every_figure_names_the_page_it_was_read_from(self) -> None:
        sections = ("characterData", "tilemapEntry", "colour")

        missing = [name for name in sections if not self.declared[name].get("manualPage")]

        self.assertEqual(missing, [])

    def test_what_the_figures_do_not_state_is_recorded(self) -> None:
        stated = self.declared["notStated"]

        self.assertGreaterEqual(len(stated), 4)


class CharacterTest(unittest.TestCase):
    @override
    def setUp(self) -> None:
        self.figure: dict[str, Any] = declared("hardware.json")["characterData"]
        self.depths: list[dict[str, Any]] = self.figure["depths"]

    def test_a_character_is_the_size_the_figure_draws(self) -> None:
        drawn = (self.figure["rows"], self.figure["columns"])

        self.assertEqual(drawn, (tiles.TILE_WIDTH, tiles.TILE_WIDTH))

    def test_and_its_pixel_count_follows_from_that(self) -> None:
        self.assertEqual(self.figure["rows"] * self.figure["columns"], tiles.TILE_PIXELS)

    def test_every_depth_the_figure_draws_is_one_this_package_knows(self) -> None:
        drawn = [row["bitsPerDot"] for row in self.depths]

        self.assertEqual(tuple(drawn), tiles.DEPTHS)

    def test_every_printed_byte_count_is_what_this_package_uses(self) -> None:
        wrong = [
            (row["bitsPerDot"], row["bytes"], tiles.tile_bytes(row["bitsPerDot"]))
            for row in self.depths
            if row["bytes"] != tiles.tile_bytes(row["bitsPerDot"])
        ]

        self.assertEqual(wrong, [])

    def test_and_every_printed_word_count_is_half_of_it(self) -> None:
        wrong = [row["bitsPerDot"] for row in self.depths if row["words"] * 2 != row["bytes"]]

        self.assertEqual(wrong, [])

    def test_the_pairs_start_where_the_figure_puts_them(self) -> None:
        wrong = [
            (row["bitsPerDot"], row["pairOffsets"])
            for row in self.depths
            if [offset * 2 for offset in row["pairOffsets"]]
            != [tiles._plane_offset(plane * 2) for plane in range(row["planePairs"])]
        ]

        self.assertEqual(wrong, [])

    def test_each_depth_has_half_as_many_pairs_as_planes(self) -> None:
        wrong = [
            row["bitsPerDot"] for row in self.depths if row["planePairs"] * 2 != row["bitsPerDot"]
        ]

        self.assertEqual(wrong, [])

    def test_the_two_bytes_of_a_pair_are_adjacent(self) -> None:
        first, second = tiles._plane_offset(0), tiles._plane_offset(1)

        self.assertEqual(second - first, 1)


class TilemapTest(unittest.TestCase):
    @override
    def setUp(self) -> None:
        figure: dict[str, Any] = declared("hardware.json")["tilemapEntry"]
        self.figure = figure
        self.fields = {row["name"]: row for row in figure["fields"]}

    def test_an_entry_is_the_number_of_bytes_the_figure_gives(self) -> None:
        self.assertEqual(self.figure["bytes"], tilemap.BYTES_PER_ENTRY)

    def test_the_character_code_occupies_the_bits_the_figure_names(self) -> None:
        name = self.fields["NAME"]

        self.assertEqual(int(name["mask"], 16), tilemap.TILE_MASK)

    def test_and_the_range_it_prints_is_what_that_mask_holds(self) -> None:
        name = self.fields["NAME"]

        self.assertEqual(name["range"], f"{0:03X}H~{tilemap.TILE_MASK:03X}H")

    def test_the_palette_field_sits_where_the_figure_puts_it(self) -> None:
        colour = self.fields["COLOR"]

        self.assertEqual(
            (colour["shift"], int(colour["mask"], 16)), (tilemap.BLOCK_SHIFT, tilemap.BLOCK_MASK)
        )

    def test_and_the_figure_says_eight_palettes_which_is_what_it_holds(self) -> None:
        colour = self.fields["COLOR"]

        self.assertEqual(
            ("8-Palettes" in colour["meaningQuote"], tilemap.BLOCK_MASK + 1), (True, 8)
        )

    def test_the_priority_bit_is_the_one_the_figure_names(self) -> None:
        priority = self.fields["BG Pri."]

        self.assertEqual(int(priority["mask"], 16), tilemap.PRIORITY_BIT)

    def test_the_two_flip_bits_are_the_ones_the_figure_names(self) -> None:
        found = (int(self.fields["H"]["mask"], 16), int(self.fields["V"]["mask"], 16))

        self.assertEqual(found, (tilemap.HORIZONTAL_BIT, tilemap.VERTICAL_BIT))

    def test_the_five_fields_cover_the_whole_word_without_overlapping(self) -> None:
        masks = [int(row["mask"], 16) for row in self.figure["fields"]]

        covered = 0
        for mask in masks:
            covered |= mask << (self.fields["COLOR"]["shift"] if mask == 0x07 else 0)

        self.assertEqual(covered, 0xFFFF)

    def test_an_entry_built_from_the_figure_reads_back_the_same_way(self) -> None:
        entry = tilemap.Entry(
            tile=tilemap.TILE_MASK,
            block=tilemap.BLOCK_MASK,
            priority=True,
            horizontal_flip=True,
            vertical_flip=True,
        )

        self.assertEqual(entry.word, 0xFFFF)


class ColourTest(unittest.TestCase):
    @override
    def setUp(self) -> None:
        self.figure: dict[str, Any] = declared("hardware.json")["colour"]

    def test_a_colour_is_the_number_of_bytes_the_manual_gives(self) -> None:
        self.assertEqual(self.figure["bytesPerColour"], palette.BYTES_PER_COLOUR)

    def test_the_first_colour_of_a_palette_is_the_transparent_one(self) -> None:
        transparent = self.figure["transparent"]

        self.assertEqual(transparent["index"], palette.TRANSPARENT)

    def test_and_the_manual_says_so_rather_than_this_package_deciding(self) -> None:
        transparent = self.figure["transparent"]

        self.assertIn("is transparent", transparent["quote"])

    def test_three_channels_share_the_word_the_package_masks_to(self) -> None:
        channels = len(self.figure["channelOrder"])

        self.assertEqual(channels * palette.CHANNEL_BITS, palette.WORD_MASK.bit_length())

    def test_and_a_channel_holds_what_its_width_allows(self) -> None:
        self.assertEqual(palette.CHANNEL_MASK, (1 << palette.CHANNEL_BITS) - 1)


class PrintedBehaviourTest(unittest.TestCase):
    def test_each_character_takes_the_printed_number_of_words_in_a_sheet(self) -> None:
        # Arrange
        depths = FIGURES["characterData"]["depths"]

        # Act
        decoded = [tiles.decode_sheet(two_characters(row), row["bitsPerDot"]) for row in depths]

        # Assert
        self.assertEqual(
            decoded,
            [[[0] * 64, [(1 << row["bitsPerDot"]) - 1] * 64] for row in depths],
        )

    def test_each_plane_pair_is_written_at_the_word_the_figure_puts_it(self) -> None:
        # Arrange
        depths = FIGURES["characterData"]["depths"]

        # Act
        written = [
            [
                written_bytes(tiles.encode(all_in_plane(pair * 2), row["bitsPerDot"]))
                for pair in range(row["planePairs"])
            ]
            for row in depths
        ]

        # Assert
        self.assertEqual(
            written,
            [
                [[(offset + line) * 2 for line in ROWS] for offset in row["pairOffsets"]]
                for row in depths
            ],
        )

    def test_a_map_entry_reads_each_printed_field_from_its_own_bits(self) -> None:
        # Arrange
        fields = FIGURES["tilemapEntry"]["fields"]

        # Act
        read = [entry_fields(tilemap.Entry.from_word(field_value(field))) for field in fields]

        # Assert
        self.assertEqual(
            read,
            [
                {other["name"]: full(other) if other is field else empty(other) for other in fields}
                for field in fields
            ],
        )

    def test_a_map_entry_writes_each_printed_field_into_its_own_bits(self) -> None:
        # Arrange
        fields = FIGURES["tilemapEntry"]["fields"]

        # Act
        words = [entry_with(field).word for field in fields]

        # Assert
        self.assertEqual(words, [field_value(field) for field in fields])

    def test_each_colour_channel_is_read_from_the_bits_the_figure_gives_it(self) -> None:
        # Arrange
        colour = FIGURES["colour"]

        # Act
        read = [
            palette.to_rgb(bits_named(colour["channelBits"][name]))
            for name in colour["channelOrder"]
        ]

        # Assert
        self.assertEqual(
            read,
            [
                tuple(FULL_CHANNEL if channel == name else 0 for channel in RGB)
                for name in colour["channelOrder"]
            ],
        )

    def test_the_printed_transparent_colour_is_the_one_the_package_treats_so(self) -> None:
        # Arrange
        transparent = FIGURES["colour"]["transparent"]

        # Act
        found = [pixel for pixel in range(16) if palette.is_transparent(pixel)]

        # Assert
        self.assertEqual(found, [transparent["index"]])


class DivergenceTest(unittest.TestCase):
    @override
    def setUp(self) -> None:
        self.entries: list[dict[str, Any]] = declared("divergences.json")["divergences"]

    def test_each_entry_says_which_source_the_package_follows(self) -> None:
        allowed = {"document", "reference", "neither"}

        self.assertEqual({entry["packageFollows"] for entry in self.entries} - allowed, set())

    def test_each_entry_says_what_would_settle_or_reopen_it(self) -> None:
        missing = [
            entry["id"]
            for entry in self.entries
            if not (entry.get("wouldSettleIt") or entry.get("wouldReopenIt"))
        ]

        self.assertEqual(missing, [])

    def test_the_limit_of_an_exhaustive_walk_is_recorded(self) -> None:
        entry = next(
            item for item in self.entries if item["id"] == "exhaustion-proves-round-trip-not-layout"
        )

        self.assertIn("opposite ways", entry["reasoning"])

    def test_and_it_names_what_would_reopen_it(self) -> None:
        entry = next(
            item for item in self.entries if item["id"] == "exhaustion-proves-round-trip-not-layout"
        )

        self.assertIn("Removing the comparison", entry["wouldReopenIt"])

    def test_the_channel_width_being_arithmetic_is_recorded(self) -> None:
        named = {entry["id"] for entry in self.entries}

        self.assertIn("the-channel-width-is-arithmetic", named)


if __name__ == "__main__":
    unittest.main(verbosity=1)
