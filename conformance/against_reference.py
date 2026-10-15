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
    def ask(self, question: str) -> str: ...


class Missing(Exception): ...


class Reference:
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
    width = BYTES_FOR_DEPTH[depth]
    for at in range(width * 8):
        held = bytearray(width)
        held[at // 8] = 1 << (7 - (at % 8))
        yield at, bytes(held)


def tile_disagreements(reference: Asks) -> list[str]:
    found = []
    for depth in DEPTHS:
        for at, data in one_bit_tiles(depth):
            theirs = reference.ask(f"tile {depth} {data.hex().upper()}")
            ours = "".join(f"{one:02X}" for one in tiles.decode(data, depth))
            if ours != theirs:
                found.append(f"{depth}bpp bit {at}: this package {ours}, the reference {theirs}")
    return found


def colour_disagreements(reference: Asks) -> list[str]:
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
