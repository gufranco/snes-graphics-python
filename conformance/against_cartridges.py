"""Hold the tile layout to what cartridges actually contain.

Everything else in this directory proves the code agrees with a record, with a
second reading of the same manual, and with itself over the whole input space.
None of that can tell a correct reading of the manual from a plausible one,
because a decoder that is consistently wrong agrees with itself perfectly and
with a record written from the same misreading.

What separates them is data nobody here wrote. A cartridge holds pictures, and a
picture read with the right layout looks like a picture: pixels next to each
other are usually the same colour. Read with the wrong layout it looks like
noise. So the layout can be measured rather than agreed upon, by reading the same
bytes three ways and asking which reading finds the most structure.

The two other readings are not strawmen. Contiguous planes is how several other
consoles of the period store the same kind of tile, and two pixels to a byte is
the obvious way to store sixteen colours. Both are what somebody misreading the
manual would plausibly build.

Two things make the answer mean something. The regions are chosen without
consulting the statistic, so the reading under test gets no help from selection.
And all three readings see exactly the same regions, so the only thing that
varies is the layout. A reading with no information in it would win a third of
the regions, and that floor is published beside the result rather than left for a
reader to work out.

Nothing here is carried. Cartridge images belong to whoever made them, and this
reads whatever is on the machine it runs on.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable, Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(ROOT))

from snesgfx import tiles  # noqa: E402

RECORD = Path(__file__).resolve().parent / "cartridges.json"

DIRECTORY_VARIABLE = "SNES_CARTRIDGE_DIR"

DEFAULT_DIRECTORY = ROOT / "cartridges"

ALONGSIDE = ROOT.parent / "snes-roms"

SUFFIXES = (".sfc", ".smc")

DEPTH = 4

TILE_BYTES = 32

TILES_PER_REGION = 64

REGION_BYTES = TILE_BYTES * TILES_PER_REGION

STRIDE = 0x8000

FIRST = 0x8000

LIMIT = 0x200000

DISTINCT_BYTES = 8
"""A region with fewer distinct bytes than this is padding, not a picture."""

CARTRIDGES = 300

SEED = 11

NOTHING_CHECKED = 2


DIRECTORY_VARIABLES = (DIRECTORY_VARIABLE,)
"""Every variable naming a directory, most specific first.

One here, and a tuple anyway, because this is the shared rule below and a member
that grows a second variable should not have to change the rule to get it.
"""


def directories(environment: Mapping[str, str] | None = None) -> tuple[Path, ...]:
    """Every place an image is looked for, in the order they are looked at.

    Whatever was named comes first, then the project this package sits inside if
    it is a submodule of one, then this package itself. More than one can be
    named at once, separated the way the operating system separates a path.

    `DIRECTORY_VARIABLES` is read in order, so a member that shares a variable
    with a sibling reads its own name first and the shared one after it. A
    caller who has set only the shared name keeps working; a caller who sets
    both points the two members at different directories, which is the whole
    reason the member's own name exists.

    This function is one rule with a copy in every member that reads a file it
    does not carry, because no package is a dependency of all of them. The
    copies are byte-identical below the constants and are meant to stay that
    way, so a diff against a sibling is the check:

        cut='/^def directories/,/^    return tuple(seen)/p'
        diff <(sed -n "$cut" mine/thing.py) <(sed -n "$cut" theirs/thing.py)
    """
    held = environment if environment is not None else os.environ
    wanted = [
        Path(where)
        for variable in DIRECTORY_VARIABLES
        for where in held.get(variable, "").split(os.pathsep)
        if where
    ]
    wanted += [ALONGSIDE, DEFAULT_DIRECTORY]
    seen: list[Path] = []
    for where in wanted:
        if where not in seen:
            seen.append(where)
    return tuple(seen)


def where_to_look(
    environment: Mapping[str, str] | None = None, places: Iterable[Path] | None = None
) -> Path | None:
    """The one directory to read, or nothing when there is none.

    A named directory wins even when it is empty or missing. Falling back from a
    path somebody typed turns their typo into a run that reads a different
    library and reports success, which is the failure this whole file exists to
    avoid.
    """
    named = (environment if environment is not None else os.environ).get(DIRECTORY_VARIABLE)
    if named:
        return Path(named)
    for place in places if places is not None else (DEFAULT_DIRECTORY, ALONGSIDE):
        if place.is_dir():
            return place
    return None


def every(environment: Mapping[str, str] | None = None) -> list[Path]:
    """Every image in that directory, in one order whatever the filesystem says."""
    where = where_to_look(environment)
    if where is None or not where.is_dir():
        return []
    return sorted(
        one for one in where.rglob("*") if one.suffix.lower() in SUFFIXES and one.is_file()
    )


def chosen(found: Sequence[Path], how_many: int = CARTRIDGES, seed: int = SEED) -> list[Path]:
    """A sample drawn the same way on every machine that holds the same library."""
    if len(found) <= how_many:
        return list(found)
    return sorted(random.Random(seed).sample(list(found), how_many))


def documented(raw: bytes) -> list[int]:
    """The layout this package publishes, which is the reading under test."""
    return tiles.decode(raw, DEPTH)


def contiguous_planes(raw: bytes) -> list[int]:
    """Four planes of eight bytes each, the way other consoles of the day stored them."""
    return [
        sum(((raw[plane * 8 + row] >> (7 - column)) & 1) << plane for plane in range(4))
        for row in range(8)
        for column in range(8)
    ]


def two_pixels_per_byte(raw: bytes) -> list[int]:
    """Sixteen colours packed two to a byte, read straight through."""
    out: list[int] = []
    for byte in raw[:TILE_BYTES]:
        out.append(byte >> 4)
        out.append(byte & 0x0F)
    return out[: tiles.TILE_PIXELS]


READINGS: tuple[tuple[str, Callable[[bytes], list[int]]], ...] = (
    ("documented", documented),
    ("contiguous planes", contiguous_planes),
    ("two pixels per byte", two_pixels_per_byte),
)


def structure(pixels: Sequence[int]) -> float:
    """How long a run of one colour lasts across a row, summed over the tile.

    A picture has neighbours that match. Noise does not. Nothing about this
    favours one layout: it counts whether adjacent pixels are equal and never
    looks at which colour they are, so relabelling the colours cannot move it.
    That is deliberate, because a layout difference that only relabels colours is
    not a layout difference anybody can see.
    """
    total = 0.0
    for row in range(8):
        line = pixels[row * 8 : row * 8 + 8]
        changes = sum(1 for at in range(1, 8) if line[at] != line[at - 1])
        total += 8 / (1 + changes)
    return total


def regions(image: bytes) -> Iterable[bytes]:
    """Blocks to judge, picked by where they sit rather than by what is in them."""
    for at in range(FIRST, min(len(image), LIMIT), STRIDE):
        block = image[at : at + REGION_BYTES]
        if len(block) < REGION_BYTES:
            return
        if len(set(block)) < DISTINCT_BYTES:
            continue
        yield block


def wins(block: bytes) -> str:
    """Which reading finds the most structure in one region."""
    scored = [
        (
            sum(
                structure(read(block[at * TILE_BYTES : (at + 1) * TILE_BYTES]))
                for at in range(TILES_PER_REGION)
            ),
            name,
        )
        for name, read in READINGS
    ]
    return max(scored)[1]


def judge(images: Iterable[Path]) -> dict[str, Any]:
    """Every region of every image, and which reading won each."""
    tally = {name: 0 for name, _ in READINGS}
    seen = 0
    digest = hashlib.sha256()
    for one in images:
        raw = one.read_bytes()
        digest.update(hashlib.sha256(raw).digest())
        for block in regions(raw):
            tally[wins(block)] += 1
            seen += 1
    return {
        "regions": seen,
        "wins": tally,
        "corpusDigest": digest.hexdigest(),
        "floor": 1 / len(READINGS),
    }


def declared(path: Path | str | None = None) -> dict[str, Any]:
    held: dict[str, Any] = json.loads(Path(path or RECORD).read_text())
    return held


def main(
    say: Callable[[str], None] = print,
    find: Callable[[], list[Path]] = every,
    look: Callable[[Iterable[Path]], dict[str, Any]] = judge,
) -> int:
    found = find()
    if not found:
        say(
            "nothing was checked: no cartridge images are on this machine. They are"
            f" not carried here; name a directory in {DIRECTORY_VARIABLE}"
        )
        return NOTHING_CHECKED
    held = look(chosen(found))
    if not held["regions"]:
        say("nothing was checked: no region in those images held enough to judge")
        return NOTHING_CHECKED
    share = held["wins"]["documented"] / held["regions"]
    for name, _ in READINGS:
        count = held["wins"][name]
        say(
            f"  {name:<22} won {count:>6} of {held['regions']} ({100 * count / held['regions']:.1f}%)"
        )
    say(f"  a reading with nothing in it would win {100 * held['floor']:.1f}%")
    if share <= held["floor"]:
        say("the published layout did no better than chance")
        return 1
    say(
        f"the published layout won {100 * share:.1f}% against a floor of {100 * held['floor']:.1f}%"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
