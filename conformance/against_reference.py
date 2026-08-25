"""Hold every figure this package read to somebody else's reading of the same one.

The gap this closes is narrow and was invisible. Every layout here was read off a
rendered page of Nintendo's manual by one person and written into
`hardware.json`. `hardware.test.py` holds the code to that record, and
`exhaustive.py` walks the whole input space and proves the code round-trips. None
of that can see a misreading: swap the two flip bits in the record and in the
code together and all of it still passes, because a consistently wrong decoder
agrees with itself perfectly.

What catches that is a second reading, and this is one. The reference is a
converter whose whole job is these formats, pinned by commit in `pinned.json` and
built by `build.py`. It is not carried here: only the harness in `ref/` belongs
to this repository.

The spaces below are chosen to pin a layout exactly rather than to sample it.

For a tile, one bit at a time. A bitplane layout is a map from a bit in the bytes
to a bit in a pixel, so setting exactly one byte-bit and asking where it lands
determines the whole map with no case left over. Every bit of every depth is
tried, which is 128, 256 and 512 cases.

For a colour and for a map entry, the whole space. Thirty-two thousand each,
which is small enough to walk and leaves nothing to argue about.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Iterator, Sequence

ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(ROOT))

from snesgfx import palette, tilemap, tiles  # noqa: E402

DRIVER = ROOT / "conformance" / "ref" / "driver"

DEPTHS = (2, 4, 8)

BYTES_FOR_DEPTH = {2: 16, 4: 32, 8: 64}

CHANNELS = 1 << palette.CHANNEL_BITS

TILES = 1 << 10

BLOCKS = 8


class Asks(Protocol):
    """Anything that answers a question, which is all the comparison needs.

    Written out so the walks below can be handed something other than a process.
    Their own tests drive them against an implementation that answers from this
    package, which is how a walk is shown to report a disagreement that is really
    there and to stay quiet when there is none.
    """

    def ask(self, question: str) -> str: ...


class Missing(Exception):
    """The reference is not built, which is not the same as a disagreement."""


class Reference:
    """The other implementation, kept open and asked one question at a time."""

    __slots__ = ("process",)

    def __init__(self, where: Path | str = DRIVER) -> None:
        if not Path(where).exists():
            raise Missing(
                f"{where} is not built. Run `python3 -m conformance.build` first;"
                " it fetches the reference at the commit pinned in pinned.json."
            )
        self.process = subprocess.Popen(
            [str(where)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

    def ask(self, question: str) -> str:
        assert self.process.stdin is not None
        assert self.process.stdout is not None
        self.process.stdin.write(question + "\n")
        self.process.stdin.flush()
        return self.process.stdout.readline().strip()

    def close(self) -> None:
        if self.process.stdin is not None:
            self.process.stdin.close()
        self.process.wait(timeout=30)

    def __enter__(self) -> Reference:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def one_bit_tiles(depth: int) -> Iterator[tuple[int, bytes]]:
    """Every tile with exactly one bit set, which pins the whole layout."""
    width = BYTES_FOR_DEPTH[depth]
    for at in range(width * 8):
        held = bytearray(width)
        held[at // 8] = 1 << (7 - (at % 8))
        yield at, bytes(held)


def tile_disagreements(reference: Asks) -> list[str]:
    """Where the two readings of the bitplane figure differ."""
    found = []
    for depth in DEPTHS:
        for at, data in one_bit_tiles(depth):
            theirs = reference.ask(f"tile {depth} {data.hex().upper()}")
            ours = "".join(f"{one:02X}" for one in tiles.decode(data, depth))
            if ours != theirs:
                found.append(f"{depth}bpp bit {at}: this package {ours}, the reference {theirs}")
    return found


def colour_disagreements(reference: Asks) -> list[str]:
    """Where the two readings of the colour figure differ, over every colour.

    The two sides take their channels in different units, and the walk has to
    speak each one's. This package takes the eight bits an image carries and
    narrows them itself, refusing anything above 255. The reference takes the
    five the console stores, one channel per byte, and packs from there. Handing
    either one the other's units makes them disagree about almost every colour,
    which is a fault in the question rather than in either answer. Two earlier
    versions of this file did exactly that, in opposite directions.

    So the walk is over the five-bit space the hardware actually has, and each
    side is asked in the units it documents.
    """
    found = []
    for red in range(CHANNELS):
        for green in range(CHANNELS):
            for blue in range(CHANNELS):
                eight = (red << 3, green << 3, blue << 3)
                ours = palette.encode([eight]).hex().upper()
                rgba = red | (green << 8) | (blue << 16)
                theirs = reference.ask(f"colour {rgba}")
                if ours != theirs:
                    found.append(
                        f"colour {red},{green},{blue}: this package {ours}, the reference {theirs}"
                    )
    return found


def entry_disagreements(reference: Asks) -> list[str]:
    """Where the two readings of the map entry figure differ, over every entry."""
    found = []
    for tile in range(TILES):
        for block in range(BLOCKS):
            for flips in range(4):
                horizontal = bool(flips & 1)
                vertical = bool(flips & 2)
                ours = (
                    tilemap.encode(
                        [
                            tilemap.Entry(
                                tile=tile,
                                block=block,
                                horizontal_flip=horizontal,
                                vertical_flip=vertical,
                            )
                        ]
                    )
                    .hex()
                    .upper()
                )
                theirs = reference.ask(f"entry {tile} {block} {int(horizontal)} {int(vertical)}")
                if ours != theirs:
                    found.append(
                        f"entry tile={tile} block={block} h={horizontal} v={vertical}:"
                        f" this package {ours}, the reference {theirs}"
                    )
    return found


def compare(reference: Asks) -> tuple[int, list[str]]:
    """Every space, walked, with what disagreed and how much was asked."""
    found: list[str] = []
    found += tile_disagreements(reference)
    found += colour_disagreements(reference)
    found += entry_disagreements(reference)
    asked = sum(BYTES_FOR_DEPTH[one] * 8 for one in DEPTHS)
    asked += CHANNELS**3
    asked += TILES * BLOCKS * 4
    return asked, found


def report(asked: int, found: Sequence[str]) -> list[str]:
    if not found:
        return [f"  {asked:,} cases compared against the reference, none disagreed"]
    return [f"  {len(found)} of {asked:,} disagreed", *(f"    {one}" for one in found[:20])]


def main(argv: Sequence[str] = (), say: Any = print) -> int:
    try:
        with Reference() as reference:
            asked, found = compare(reference)
    except Missing as trouble:
        say(f"  {trouble}")
        return 0
    for line in report(asked, found):
        say(line)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
