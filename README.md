<div align="center">

<h1>SNES Graphics Formats</h1>

<strong>The Super Nintendo graphics formats, encoded and decoded exactly, settled rather than sampled.</strong>

<br>
<br>

[![CI](https://github.com/gufranco/snes-graphics-python/actions/workflows/ci.yml/badge.svg)](https://github.com/gufranco/snes-graphics-python/actions/workflows/ci.yml)
[![Exhaustive](https://img.shields.io/badge/exhaustive-165%2C248%20cases-brightgreen)](#how-this-is-settled)
[![Coverage](https://img.shields.io/badge/coverage-100%25%20statement%20%2B%20branch-brightgreen)](#tests)
[![Python](https://img.shields.io/badge/python-3.12%20%7C%203.13%20%7C%203.14-blue)](pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

</div>

<p align="center">
  <a href="#install">Install</a> &nbsp;|&nbsp;
  <a href="#the-interface">The interface</a> &nbsp;|&nbsp;
  <a href="#the-formats">The formats</a> &nbsp;|&nbsp;
  <a href="#the-parts-people-get-wrong">The parts people get wrong</a> &nbsp;|&nbsp;
  <a href="#is-it-right">Is it right</a> &nbsp;|&nbsp;
  <a href="https://github.com/gufranco/snes-graphics-python/issues">Issues</a>
</p>

**7** formats · **165,248** cases settled by walking their whole input space, **0** failures · **412** tests · **100%** statement and branch coverage · no dependencies

```python
from snesgfx import tiles

data = bytes.fromhex("3c00423cbd7ea566a566bd7e423c3c0000000000000018001800000000000000")
pixels = tiles.decode(data, depth=4)

for row in range(8):
    print("".join(f"{pixel:x}" for pixel in pixels[row * 8 : row * 8 + 8]))
```

```
00111100
01222210
12333321
12344321
12344321
12333321
01222210
00111100
```

## Install

```bash
pip install git+https://github.com/gufranco/snes-graphics-python.git
```

Python 3.12 or newer. Nothing else.

## The interface

Each layout has a module, and a catalogue sits over them so a tool can hold bytes
and a name without knowing that each format needs a different call shape.
Reaching for a module directly is equally supported and often clearer.

| Call | Does | Returns |
|:--|:--|:--|
| `describe(name)` | The layout behind a name or an alias | a `Format` |
| `format.decode(data)` / `format.encode(...)` | The layout's own reading, whichever it is | per format |
| `tiles.decode(data, depth)` / `tiles.encode(pixels, depth)` | Bit plane tiles at two, four or eight bits | pixels / bytes |
| `palette.decode(data)` / `palette.encode(colours)` | Fifteen bit colour words | triples / bytes |
| `palette.resolve(colours, pixel, depth, block)` | Which colour a pixel number reaches | a triple |
| `tilemap.decode(data)` / `tilemap.encode(entries)` | Background entries, quadrants included | entries / bytes |
| `oam.decode(low, high)` / `oam.encode(sprites)` | The sprite table, both halves of it | sprites / bytes |
| `mode7.decode(vram)` / `mode7.transform(...)` | The interleaved map and the fixed point matrix | names and pixels |

Everything the package raises lives in [`snesgfx/errors.py`](snesgfx/errors.py)
and nowhere else: `Truncated`, `OutOfRange`, `UnknownDepth` and `UnknownFormat`.
All four are published, because `except` takes a name and one that cannot be
imported can only be handled by catching everything.

### Read a tile

```python
from snesgfx import tiles

data = bytes.fromhex("3c00423cbd7ea566a566bd7e423c3c0000000000000018001800000000000000")
pixels = tiles.decode(data, depth=4)

print(len(pixels))
print(pixels[:8])
```

```
64
[0, 0, 1, 1, 1, 1, 0, 0]
```

### Put the colours on it

```python
from snesgfx import palette, tiles

data = bytes.fromhex("3c00423cbd7ea566a566bd7e423c3c0000000000000018001800000000000000")
pixels = tiles.decode(data, depth=4)
colours = palette.decode(bytes(512))

print(palette.resolve(colours, pixels[0], depth=4, block=2))
```

```
(0, 0, 0)
```

`resolve` is not a lookup by index. Which sixteen colours a four bit tile can
reach depends on the palette block the tilemap or sprite entry names, so the
block is part of the question.

## The formats

| Name | What it is | Also answers to |
|:-----|:-----------|:----------------|
| `2bpp` | Two planes, four colours, sixteen bytes a tile | `4-colour`, `2bit` |
| `4bpp` | Four planes, sixteen colours, thirty two bytes a tile | `16-colour`, `4bit` |
| `8bpp` | Eight planes, two hundred and fifty six colours, sixty four bytes | `256-colour`, `8bit` |
| `mode7` | The rotating background, a pixel to a byte, map and pixels interleaved | `mode-7`, `m7` |
| `palette` | Fifteen bit colour, two bytes each, blue highest | `cgram`, `colours`, `colors` |
| `tilemap` | The background map, sixteen bits an entry, stored in quadrants | `map`, `screen`, `bg` |
| `oam` | The sprite table, four bytes each plus two more bits elsewhere | `sprites`, `objects`, `obj` |

Each is reached by its name or by any of those:

```python
from snesgfx import describe

print(describe("2bpp").name)
print(describe("4bpp").name)
print(describe("8bpp").name)
print(describe("mode7").name)
print(describe("palette").name)
print(describe("tilemap").name)
print(describe("oam").name)

print(describe("16-colour").name)
print(describe("Mode-7").name)
```

```
2bpp
4bpp
8bpp
mode7
palette
tilemap
oam
4bpp
mode7
```

Case, spaces and separators do not matter. Six bits per pixel is not here,
because the hardware does not have it however many tools offer it.

## The parts people get wrong

**Tiles are not stored as pixels.** Each bit of a pixel's colour number lives in
a different plane, and the planes are paired and interleaved by row. So a four
bit tile is two interleaved pairs one after the other, not four planes in a row,
and the first sixteen bytes of one are a complete two bit tile.

**The leftmost pixel comes from the highest bit.** That is the opposite of the
order the bytes are numbered in, and it is where most mirroring bugs come from.

**Five bit colour does not widen by shifting.** Shifting left by three leaves the
brightest colour the hardware can name three steps short of white, so a palette
that should reach white does not. Repeating the value's own high bits into the
gap maps the top of one range onto the top of the other, which is why every one
of the 32,768 colours here survives a round trip and a shift-based conversion
does not.

**A background map is not a rectangle.** It is up to four blocks of thirty two by
thirty two stored one after another, so a position in the right half is a whole
block further along than its column suggests. Getting it wrong draws the correct
tiles in the wrong quadrant, which reads as a scrolling bug.

**A sprite's data is in two places.** Nine bits of position and a size flag do not
fit in four bytes, so two bits per sprite live in a second table, four sprites to
a byte. The ninth bit of the position is a sign rather than a magnitude: a sprite
at `0x1F0` is sixteen pixels off the left of the screen, not far to the right.

**Mode 7 throws away the low six bits of every product.** The multiplier
truncates before the terms are added, so a matrix entry small enough that its
product falls under sixty four contributes nothing at all. A very slow rotation
does not creep; it stays exactly still and then jumps. Software tuned on hardware
looks broken on a model that keeps the full product.

## Is it right

There is no chip to compare against and there does not need to be. These are
layouts, and several of them have input spaces small enough to walk from end to
end. The claim is therefore not that this agrees with a reference on the cases
somebody thought to try; it is that there is no case left.

| Check | Cases | What it settles |
|:------|------:|:----------------|
| `tiles-2bpp` | 65,536 | Every two bit tile that can exist, round tripped both ways |
| `tilemap` | 65,536 | Every map entry word, decoded into fields and re-encoded |
| `palette` | 32,768 | Every colour the hardware can name, widened to bytes and narrowed back |
| `tiles-planes` | 896 | Every plane of every depth against every one of the sixty four pixels |
| `oam-high` | 512 | Every sprite's two bits in the second table, without disturbing its neighbours |

```bash
python3 -m conformance.exhaustive
```

```
  tiles-2bpp: 65,536 cases settled
  tiles-planes: 896 cases settled
  palette: 32,768 cases settled
  tilemap: 65,536 cases settled
  oam-high: 512 cases settled
165,248 cases, 0 checks failed
```

The depths above two bits cannot be walked; a four bit tile has more states than
is worth counting. What can be walked for those is each plane separately against
each pixel, which is the property that actually matters: a plane must reach its
own bit of every pixel and no other bit of anything.

A check that cannot fail proves nothing, so each one is also shown to fail. The
tests break each format deliberately and confirm the walk catches it.

### When something is wrong

```bash
python3 -m snesgfx.doctor
```

It looks at this machine and prints what is actually there, and every line is
something it looked at just now rather than something that ought to be true. A
check that fails says what it saw. A check that itself throws is reported as what
it threw rather than taking the report down with it. Paste all of it into an
issue.

## Working on it

### Running the tests

Each module has its test file beside it, named after it.

```bash
python -m coverage erase
for file in $(find snesgfx conformance -name '*.test.py' | sort); do
  python -m coverage run -a "$file"
done
python -m coverage report
```

Coverage is a gate, not a report: the build fails below 100% of statements and
branches.

### Project conventions

| Convention | Source |
|:-----------|:-------|
| Commit format | [Conventional Commits](https://www.conventionalcommits.org/) |
| Format and lint | [ruff](https://docs.astral.sh/ruff/), configured in [pyproject.toml](pyproject.toml) |
| Releases | [semantic-release](https://semantic-release.gitbook.io/), from the commit history |
| Test naming | A sentence stating the behaviour, not the function name |

### Non-obvious decisions

- Nothing here reads or writes an image file. Turning pixels into a PNG is a
  different problem with existing answers, and pulling one in would make a
  package with no dependencies into one with several.
- Mode 7 keeps the hardware's truncation rather than the mathematically correct
  product. A model that is more accurate than the hardware is wrong.
- The catalogue exists so a tool can hold bytes and a name without knowing that
  each format needs a different call shape. Reaching for a module directly is
  equally supported and often clearer.
- There is no six bit depth, no matter how many tools list one.

### Layout

| File | Holds |
|:-----|:------|
| [`snesgfx/tiles.py`](snesgfx/tiles.py) | Bit plane tiles at every depth, and the mirroring an entry can ask for |
| [`snesgfx/palette.py`](snesgfx/palette.py) | The fifteen bit colour word, and the blocks each depth reaches |
| [`snesgfx/tilemap.py`](snesgfx/tilemap.py) | The background entry, and the quadrants a map is stored in |
| [`snesgfx/oam.py`](snesgfx/oam.py) | The sprite table, including the bits kept in a second one |
| [`snesgfx/mode7.py`](snesgfx/mode7.py) | The matrix, in the fixed point the hardware applies it in |
| [`snesgfx/models.py`](snesgfx/models.py) | The format named at construction |
| [`conformance/exhaustive.py`](conformance/exhaustive.py) | The walks that settle a format rather than sampling it |

### Contributing

Measurements first. [CONTRIBUTING.md](CONTRIBUTING.md) has the gates a change is
expected to pass, [SECURITY.md](SECURITY.md) says what belongs in a private
report, and the [Code of Conduct](CODE_OF_CONDUCT.md) applies wherever this
project is discussed.

Never attach a copyrighted file, and never link to somewhere one can be
downloaded. A digest identifies a file without carrying it.

## References

This repository carries no documents and no cartridges, and nothing here is
compared against an emulator. These are layouts: a layout is right or wrong, and
where the input space is small enough it is walked from end to end rather than
sampled.

That leaves nothing to cite for most of it, and one thing that is worth naming.
The truncation Mode 7 performs is a property of the multiplier rather than of a
format, so it is a claim about hardware in a package that otherwise makes none:
[`conformance/hardware.json`](conformance/hardware.json) holds it with where it
came from, and [`conformance/divergences.json`](conformance/divergences.json)
holds what a model that kept the full product would get wrong.

## Citing this

[CITATION.cff](CITATION.cff) is kept in step with the released version by the
same script that stamps the package, so the version it names is the version that
shipped.

## License

[MIT](LICENSE).
