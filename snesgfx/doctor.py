"""Look at this machine and say what is actually here, so a report can be believed.

This package needs nothing from anybody: no microcode, no cartridge, no reference
build. So what goes wrong with it is narrower than in its siblings, and it is
almost always one of two things. The Python is too old, or a layout somebody is
decoding is not the layout they think it is.

So this looks, and prints what it found in a form that can be pasted into an
issue as it stands.

Two rules shape it, and they are the whole point.

Nothing is hidden. A check that fails says what it saw, and a check that itself
throws is caught and reported as what it threw, named by its type. Swallowing
either would leave a report that says everything is fine on a machine where
something is not, which is worse than no report.

Nothing is inferred. Every line is something looked at on this machine just now,
including a tile actually decoded and encoded back to see whether it survives.
"""

import platform
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, override

from . import models
from .version import VERSION

ROOT = Path(__file__).resolve().parent.parent

OLDEST_PYTHON = (3, 12)

TILE = bytes(range(32))
"""Thirty two bytes counted up from zero: one four bit plane tile, and nobody's artwork."""

SIZES = (2, 4, 8, 16, 32, 64, 128, 256, 512, 544, 1024)
"""Input lengths tried against a layout, since each one reads a different unit.

A sprite table is 544 bytes and an eight bit plane tile is 64, so handing every
layout the same 32 would report a failure that is really this file asking the
wrong question. Finding the smallest length a layout accepts asks the right one
and says what that length is, which is worth knowing on its own.
"""

WITNESS = "4bpp"
"""The depth the round trip runs at, being the one most of a cartridge is drawn in."""


class Finding:
    """One thing that was looked at, and what was there."""

    def __init__(self, name: str, ok: bool, detail: str, advice: str | None = None) -> None:
        self.name = name
        self.ok = ok
        self.detail = detail
        self.advice = advice

    @property
    def line(self) -> str:
        """The one-line form, which is what a reader scans."""
        return f"  {'ok  ' if self.ok else '   !'}  {self.name}: {self.detail}"

    @property
    def report(self) -> str:
        """The same, with what to do about it when there is something to do."""
        if self.ok or not self.advice:
            return self.line
        return f"{self.line}\n         {self.advice}"

    @override
    def __repr__(self) -> str:
        return f"<Finding {self.name} {'ok' if self.ok else 'not ok'}>"


def _python() -> "Finding":
    return Finding(
        "python",
        sys.version_info[:2] >= OLDEST_PYTHON,
        f"{platform.python_version()} on {platform.system()} {platform.machine()}",
        f"this package needs {OLDEST_PYTHON[0]}.{OLDEST_PYTHON[1]} or newer",
    )


def _package() -> "Finding":
    return Finding("snesgfx", True, f"version {VERSION}")


def _default_decode(name: str, data: bytes | bytearray) -> Any:
    return models.describe(name).decode(data)


def _default_encode(name: str, decoded: Any) -> bytes:
    return models.describe(name).encode(decoded)


def _counting(size: int) -> bytes:
    return bytes(one % 256 for one in range(size))


def _layout(name: str, decode: Callable[..., Any]) -> "Finding":
    """The smallest input that layout accepts, and how much came out of it."""
    refused = None
    for size in SIZES:
        try:
            decoded = decode(name, _counting(size))
        except Exception as trouble:
            refused = trouble
            continue
        return Finding(name, True, f"decoded {len(decoded)} from {size} bytes")
    return Finding(
        name,
        False,
        f"{type(refused).__name__}: {refused}",
        f"nothing between {SIZES[0]} and {SIZES[-1]} bytes was accepted, so this"
        " is the layout failing to read rather than a length being wrong",
    )


def _round_trip(decode: Callable[..., Any], encode: Callable[..., bytes]) -> "Finding":
    """That what goes in comes back out, which is the property worth the most here.

    A decoder can be wrong in a way no eye catches and no exception marks: a
    plane read in the wrong order still produces a picture. Encoding the result
    back and comparing bytes catches that class in one line, and it needs
    nobody's artwork to do it.
    """
    try:
        back = encode(WITNESS, decode(WITNESS, TILE))
    except Exception as trouble:
        return Finding(
            "round trip",
            False,
            f"{type(trouble).__name__}: {trouble}",
            "reading a tile and writing it back failed, which is itself the finding",
        )
    return Finding(
        "round trip",
        back == TILE,
        f"a {WITNESS} tile came back as {len(back)} bytes"
        f"{'' if back == TILE else ', which are not the ones it went in as'}",
        "a layout that does not survive its own round trip is reading the planes"
        " in an order the hardware does not",
    )


def _default_checks() -> Any:
    """The exhaustive walks, reached through the package rather than as a script.

    Put the repository root on the path rather than the conformance directory
    itself. A directory on the path shadows any standard library module of the
    same name, and there is more than one plausible collision in a package whose
    modules are called things like `palette` and `tiles`.
    """
    sys.path.insert(0, str(ROOT))
    from conformance import exhaustive

    return exhaustive.CHECKS


def _exhaustive(checks: Callable[[], Any]) -> "Finding":
    """What this package settles by walking every case rather than by sampling.

    The input space of a tile decoder is small enough to walk in full, which is
    why there is no recorded corpus here and no reference build to install. The
    report names the walks so that a reader can see what "exhaustive" covers
    rather than take the word for it.
    """
    try:
        found = tuple(checks())
    except Exception as trouble:
        return Finding(
            "settled exhaustively",
            False,
            f"{type(trouble).__name__}: {trouble}",
            "the conformance checks could not be read, so nothing here says what is covered",
        )
    if not found:
        return Finding(
            "settled exhaustively",
            False,
            "no checks at all",
            "a package that walks nothing in full is not settled exhaustively",
        )
    return Finding(
        "settled exhaustively",
        True,
        f"{len(found)} walks: {', '.join(one.name for one in found)}",
    )


def examine(
    decode: Callable[..., Any] = _default_decode,
    encode: Callable[..., bytes] = _default_encode,
    checks: Callable[[], Any] = _default_checks,
) -> list["Finding"]:
    """Everything worth looking at on this machine, in the order a reader wants it."""
    found = [_python(), _package()]
    found.extend(_layout(name, decode) for name in sorted(models.FORMATS))
    found.append(_round_trip(decode, encode))
    found.append(_exhaustive(checks))
    return found


def report(found: list["Finding"]) -> list[str]:
    """The lines a person pastes into an issue."""
    unwell = [one for one in found if not one.ok]
    lines = [f"snesgfx {VERSION} on {platform.python_version()}, {platform.system()}", ""]
    lines.extend(one.report for one in found)
    lines.append("")
    if unwell:
        lines.append(f"  {len(unwell)} of {len(found)} checks did not pass")
    else:
        lines.append(f"  {len(found)} checks, nothing to report")
    return lines


def main(
    argv: Sequence[str] = (),
    examine: Callable[..., list["Finding"]] = examine,
    say: Callable[[str], None] = print,
) -> int:
    found = examine()
    for line in report(found):
        say(line)
    return 1 if any(not one.ok for one in found) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
