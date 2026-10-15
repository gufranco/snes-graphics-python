import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import override

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from snesgfx import oam, palette, tilemap, tiles

USAGE = "usage: exhaustive.py [--only NAME]"

FAILURE_LIMIT = 5


class Usage(Exception):
    pass


class Options:
    def __init__(self, only: str | None = None) -> None:
        self.only = only


class Result:
    def __init__(self, name: str, cases: int, failures: Sequence[str]) -> None:
        self.name = name
        self.cases = cases
        self.failures = failures

    @property
    def clean(self) -> bool:
        return not self.failures

    @override
    def __repr__(self) -> str:
        return f"<Result {self.name}: {self.cases} cases, {len(self.failures)} failures>"


class Check:
    def __init__(self, name: str, summary: str, walk: Callable[[], tuple[int, list[str]]]) -> None:
        self.name = name
        self.summary = summary
        self.walk = walk

    def run(self) -> "Result":
        cases, failures = self.walk()
        return Result(self.name, cases, failures)


def _every_two_bit_tile() -> tuple[int, list[str]]:
    failures = []
    cases = 0
    for low in range(256):
        for high in range(256):
            data = bytes([low, high] + [0] * 14)
            cases += 1
            if tiles.encode(tiles.decode(data, 2), 2) != data:
                failures.append(f"{low:02X} {high:02X}")
                if len(failures) >= FAILURE_LIMIT:
                    return cases, failures
    return cases, failures


def _every_plane_reaches_its_own_bit() -> tuple[int, list[str]]:
    failures = []
    cases = 0
    for depth in tiles.DEPTHS:
        size = tiles.tile_bytes(depth)
        for plane in range(depth):
            for pixel in range(tiles.TILE_PIXELS):
                row, column = divmod(pixel, tiles.TILE_WIDTH)
                data = bytearray(size)
                data[(plane // 2) * tiles.PLANE_PAIR_BYTES + (plane % 2) + row * 2] = 0x80 >> column
                cases += 1
                found = tiles.decode(bytes(data), depth)
                wanted = [0] * tiles.TILE_PIXELS
                wanted[pixel] = 1 << plane
                if found != wanted:
                    failures.append(f"{depth}bpp plane {plane} pixel {pixel}")
                    if len(failures) >= FAILURE_LIMIT:
                        return cases, failures
    return cases, failures


def _every_colour() -> tuple[int, list[str]]:
    failures = []
    cases = 0
    for word in range(0x8000):
        cases += 1
        if palette.to_word(*palette.to_rgb(word)) != word:
            failures.append(f"{word:04X}")
            if len(failures) >= FAILURE_LIMIT:
                return cases, failures
    return cases, failures


def _every_map_entry() -> tuple[int, list[str]]:
    failures = []
    cases = 0
    for word in range(0x10000):
        cases += 1
        if tilemap.Entry.from_word(word).word != word:
            failures.append(f"{word:04X}")
            if len(failures) >= FAILURE_LIMIT:
                return cases, failures
    return cases, failures


def _every_sprite_slot() -> tuple[int, list[str]]:
    failures = []
    cases = 0
    for index in range(oam.SPRITES):
        for bits in range(4):
            data = bytearray(oam.TABLE_BYTES)
            data[oam.LOW_TABLE_BYTES + index // 4] = bits << ((index % 4) * 2)
            cases += 1
            found = oam.decode(bytes(data))
            wanted_x = (bits & 0x01) << 8
            wanted_large = bool(bits & 0x02)
            if found[index].x != wanted_x or found[index].large != wanted_large:
                failures.append(f"sprite {index} bits {bits}")
                if len(failures) >= FAILURE_LIMIT:
                    return cases, failures
            neighbours = [other for at, other in enumerate(found) if at != index]
            if any(other.x or other.large for other in neighbours):
                failures.append(f"sprite {index} bits {bits} disturbed a neighbour")
                if len(failures) >= FAILURE_LIMIT:
                    return cases, failures
    return cases, failures


CHECKS = (
    Check(
        "tiles-2bpp",
        "Every two bit tile that can exist, round tripped through both directions.",
        _every_two_bit_tile,
    ),
    Check(
        "tiles-planes",
        "Every plane of every depth against every pixel, in isolation.",
        _every_plane_reaches_its_own_bit,
    ),
    Check(
        "palette",
        "Every colour the hardware can name, widened to bytes and narrowed back.",
        _every_colour,
    ),
    Check(
        "tilemap",
        "Every map entry word, decoded into fields and re-encoded.",
        _every_map_entry,
    ),
    Check(
        "oam-high",
        "Every sprite's two bits in the second table, without disturbing its neighbours.",
        _every_sprite_slot,
    ),
)


def options(argv: Sequence[str]) -> "Options":
    chosen = Options()
    rest = list(argv)
    while rest:
        item = rest.pop(0)
        if item != "--only":
            raise Usage(USAGE)
        if not rest:
            raise Usage(USAGE)
        chosen.only = rest.pop(0)
    return chosen


def run(argv: Sequence[str]) -> int:
    chosen = options(argv)
    wanted = [check for check in CHECKS if chosen.only in (None, check.name)]
    if not wanted:
        print(f"no check called {chosen.only}; there are {', '.join(c.name for c in CHECKS)}")
        return 2

    total = 0
    failed = 0
    for check in wanted:
        found = check.run()
        total += found.cases
        if found.clean:
            print(f"  {found.name}: {found.cases:,} cases settled")
            continue
        failed += 1
        print(f"  {found.name}: {len(found.failures)} failures, first {found.failures[0]}")

    print(f"{total:,} cases, {failed} checks failed")
    return 1 if failed else 0


def main(argv: Sequence[str]) -> int:
    try:
        return run(argv)
    except Usage as error:
        print(error)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
