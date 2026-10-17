import platform
import re
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, override


def read_version(where: Path | None = None) -> str:
    found = re.search(
        r"""VERSION\s*[:=][^"']*["']([^"']+)["']""",
        (where or Path(__file__).resolve().parent / "version.py").read_text(),
    )
    return found.group(1) if found else "unknown"


ROOT = Path(__file__).resolve().parent.parent


def make_reachable(root: Path = ROOT, path: list[str] | None = None) -> bool:
    where = sys.path if path is None else path
    if str(root) in where:
        return False
    where.insert(0, str(root))
    return True


make_reachable()

from snesgfx import environment, models  # noqa: E402

VERSION = read_version()

OLDEST_PYTHON = (3, 12)

TILE = bytes(range(32))

SIZES = (2, 4, 8, 16, 32, 64, 128, 256, 512, 544, 1024)

WITNESS = "4bpp"


class Finding:
    def __init__(self, name: str, ok: bool, detail: str, advice: str | None = None) -> None:
        self.name = name
        self.ok = ok
        self.detail = detail
        self.advice = advice

    @property
    def line(self) -> str:
        return f"  {'ok  ' if self.ok else '   !'}  {self.name}: {self.detail}"

    @property
    def report(self) -> str:
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
    return models.format_named(name).decode(data)


def _default_encode(name: str, decoded: Any) -> bytes:
    return models.format_named(name).encode(decoded)


def _counting(size: int) -> bytes:
    return bytes(one % 256 for one in range(size))


def _layout(name: str, decode: Callable[..., Any]) -> "Finding":
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


def round_trip(decode: Callable[..., Any], encode: Callable[..., bytes]) -> "Finding":
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
    sys.path.insert(0, str(ROOT))
    from conformance import exhaustive

    return exhaustive.CHECKS


def settled_exhaustively(checks: Callable[[], Any]) -> "Finding":
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
    found = [_python(), _package()]
    found.extend(_layout(name, decode) for name in sorted(models.FORMATS))
    found.append(round_trip(decode, encode))
    found.append(settled_exhaustively(checks))
    return found


def report(found: list["Finding"]) -> list[str]:
    unwell = [one for one in found if not one.ok]
    lines = [f"snesgfx {VERSION} on {platform.python_version()}, {platform.system()}", ""]
    lines.append("  the machine")
    lines.extend(environment.lines(ROOT))
    lines.append("")
    lines.append("  this package")
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
