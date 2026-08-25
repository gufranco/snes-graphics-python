# Working in this repository

This file is for a coding agent. A person reading it will not be harmed, but
[README.md](README.md) is the document written for them.

## What this project is, in one paragraph

The Super Nintendo graphics formats, encoded and decoded exactly: bit plane tiles
at three depths, fifteen bit colour, the background map with its quadrants, the
sprite table with the two bits it keeps somewhere else, and the Mode 7 matrix in
the fixed point the hardware applies it in. These are layouts rather than parts,
so there is no silicon to be faithful to and nothing to measure. Where a layout's
input space is small enough it is walked from end to end rather than sampled:
165,248 cases with no failures. Each layout is separately held against the figure
Nintendo printed, which is what stops a walk being self-consistency.

## The interface a caller drives

Each layout has a module, and a catalogue sits over them so a tool can hold bytes
and a name without knowing that each format needs a different call shape.
Reaching for a module directly is equally supported and often clearer.

- `describe(name)` finds a format by any spelling: case, spaces and separators do
  not matter.
- `tiles.decode(data, depth)` and `tiles.encode(pixels, depth)` for the three
  depths that exist. There is no six bit depth however many tools list one.
- `palette.decode`, `palette.encode` and `palette.resolve(colours, pixel, depth,
  block)`. The last is not a lookup by index: which sixteen colours a four bit
  tile can reach depends on the block the tilemap or sprite entry names, so the
  block is part of the question.
- `tilemap.decode` and `tilemap.encode`, quadrants included.
- `oam.decode(low, high)` and `oam.encode`, both halves of the table.
- `mode7.decode` and `mode7.transform`, in fixed point with the hardware's
  truncation.

Everything the package raises lives in [`snesgfx/errors.py`](snesgfx/errors.py)
and nowhere else, and that module imports nothing from the package so it can
never be the far end of a cycle. All four are published, because `except` takes a
name and one that cannot be imported can only be handled by catching everything.

## The authority ladder

Every factual question is answered by the highest rung that has an answer, and a
lower rung never overrules a higher one.

1. **Manufacturer documentation.** Nintendo's *SNES Development Manual, Book 1*,
   Appendix A. Every layout figure is in
   [`conformance/hardware.json`](conformance/hardware.json) with the sentence it
   came from, the manual page and the page in the file, and the file's digest.
   Every figure was read off a rendered page rather than out of the scan's text
   layer.
2. **The artifact itself.** Nothing here rests on one, and nothing needs to: a
   layout is a layout.
3. **Exhaustion.** Walking a format's whole input space. Strong, and about this
   package rather than about the hardware, which is the entry worth reading
   twice below.
4. **Anything else.** Nothing is cited from below rung three.

## What is settled and what is not

**Settled: five walks, 165,248 cases, no failures.** Every two bit tile, every
map entry word, every colour the hardware can name, every plane of every depth
against every pixel, and every sprite's two bits in the second table.

**Settled: that each layout is the one Nintendo printed.**
[`conformance/hardware.test.py`](conformance/hardware.test.py) holds the model's
own constants against the manual's figures.

**Not settled: 3 things**, each in [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md) with
what would close it. One is a figure that follows by arithmetic rather than being
printed, one is a value that cannot reach the hardware through this layout, and
one is a scope boundary listed so nobody mistakes it for a gap.

## An exhaustive walk proves a round trip, not a layout

This is the thing to hold on to here, and it is why
[`conformance/hardware.test.py`](conformance/hardware.test.py) exists.

A complete round trip over a whole space is strong evidence that the decoder and
the encoder agree with each other. It is not evidence about the hardware, because
a decoder and an encoder wrong in exactly opposite ways would pass every one of
the 165,248 cases. Before the comparison against the manual's figures existed,
the badge counted 165,248 cases of self-consistency and said nothing else.

Adding a format whose layout is not pinned to a printed figure reopens that, so a
new format needs an entry in the record before it needs a walk.

## Every gate, in the order to run them

```bash
ruff format --check .
ruff check .
mypy
pnpm run format:check
python3 -m coverage erase
for file in $(find snesgfx conformance -name '*.test.py' | sort); do
  python3 -m coverage run -a "$file"
done
python3 -m coverage report
```

Then the two that are not part of the coverage step:

```bash
python3 -m conformance.exhaustive
python3 -m conformance.speed
```

Everything under `conformance/` runs as a module. Run as a script, its own
directory goes on the import path and a file there shadows any standard library
module of the same name, which matters more here than elsewhere: the modules are
called things like `palette` and `tiles`.

## Conventions that are not negotiable

| Thing | Rule |
|:------|:-----|
| Language | Python only |
| Comments | None in source. Docstrings carry the reasoning |
| Test layout | `<module>.test.py` beside the module it covers |
| Test shape | Arrange, blank line, one act, blank line, assert. No section labels |
| Coverage | 100% statements and branches, enforced |
| Types | `mypy` at strict, plus every optional error class |
| Commits | Conventional Commits, subject under 50 characters |
| Documents | Read, quoted and pinned by digest. Never committed: none is redistributable |
| Dependencies | None at runtime, which is why nothing here writes an image file |
| Fidelity | Where the hardware and convenience disagree, the hardware wins, including where the hardware is less accurate |
| Public API | This and the rest of the family present the same shape where the subject allows. See [FAMILY.md](FAMILY.md) |

## Layout

```
snesgfx/
  tiles.py       bit plane tiles at every depth, and the mirroring an entry can ask for
  palette.py     the fifteen bit colour word, and the blocks each depth reaches
  tilemap.py     the background entry, and the quadrants a map is stored in
  oam.py         the sprite table, including the bits kept in a second one
  mode7.py       the matrix, in the fixed point the hardware applies it in
  models.py      the catalogue, so a tool can hold bytes and a name
  errors.py      everything this package raises, importing nothing from it
  doctor.py      what is actually on this machine, for an issue report
  version.py     rewritten by the release job and by nothing else
conformance/
  exhaustive.py     the walks that settle a format rather than sampling it
  hardware.json     what Nintendo printed, with the sentence and the page
  hardware.test.py  the gate that holds each layout to those figures
  divergences.json  where a figure follows by arithmetic rather than being printed
  links.py          the weekly check that every cited address still answers
  speed.py          the throughput floor
```

## Things that will bite you

**Four modules each defined their own `Truncated` and four each defined their own
`OutOfRange`.** All eight worked, all eight were tested, and `except
tiles.Truncated` sailed straight past the one a palette raised, because two
classes under one name are two different objects. They live in `errors.py` now.
Do not add a refusal anywhere else.

- **Tiles are not stored as pixels.** Each bit of a pixel's colour number lives
  in a different plane, and the planes are paired and interleaved by row. A four
  bit tile is two interleaved pairs one after the other, not four planes in a
  row, and the first sixteen bytes of one are a complete two bit tile.
- **The leftmost pixel comes from the highest bit**, which is the opposite of the
  order the bytes are numbered in and where most mirroring bugs come from.
- **Five bit colour does not widen by shifting.** Shifting left by three leaves
  the brightest colour three steps short of white. Repeating the value's own high
  bits into the gap is what makes all 32,768 colours survive a round trip.
- **A background map is not a rectangle.** It is up to four blocks of thirty two
  by thirty two stored one after another, so a position in the right half is a
  whole block further along than its column suggests.
- **A sprite's ninth position bit is a sign rather than a magnitude.** A sprite at
  `0x1F0` is sixteen pixels off the left of the screen, not far to the right.
- **Mode 7 throws away the low six bits of every product**, and keeping the full
  product is a defect rather than an improvement.
- **`docs/` is not in the repository.** A test that reads from it and does not say
  so when it is absent passes here and fails everywhere else.

## Before calling anything finished

[`FAMILY.md`](FAMILY.md) carries a checklist under "What a new repository has to
have before it is a member". Every line on it was a defect found in one of these
repositories and fixed in all of them, so it is the list of things that have
actually gone wrong here rather than a list of good intentions. Read it before
adding a surface, and read it again before saying a change is done.

A change to `FAMILY.md` is a change to every member. Nothing here can catch it
being made in one of them and forgotten in the others, because a test in this
repository cannot see the others, so the check is a command rather than a suite:

```sh
shared() { sed '/^\*Everything above this line/q' "$1"; }

grep -o 'github\.com/[^/]*/\([a-z0-9-]*\))' FAMILY.md | sed 's|.*/||; s|)||' | sort -u |
while read -r member; do
  other="../$member/FAMILY.md"
  [ -f "$other" ] || { echo "not on this machine: $member"; continue; }
  cmp <(shared FAMILY.md) <(shared "$other") && echo "match: $member"
done
```

The members come from the table at the top of `FAMILY.md` rather than from a glob
over the parent directory. Several repositories beside these carry a copy of this
file because somebody started from one. Those are working notes: they bind
nothing, they are not expected to match, and a sweep that reports them as drifted
invites somebody to edit a file that was never a member.

Two rules from that file are worth repeating because they are the ones skipped
most often:

**A check nobody has seen fail is not known to work.** Every walk here is driven
against a format broken on purpose, once, deliberately, and confirmed to catch it.

**Silence and success produce the same output.** A walk that visited no case exits
zero exactly like one that visited every case, which is why each walk prints the
count it settled.

## What a change is expected to leave behind

A gate that would have caught the bug. A change to a layout also runs the
exhaustive walk and updates the record, because the walk alone would pass a
decoder and an encoder that were wrong together.
