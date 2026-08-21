# Working in this repository

This file is for a coding agent. A person reading it will not be harmed, but
[README.md](README.md) is the document written for them.

## What this project is, in one paragraph

The Super Nintendo's graphics layouts, both directions: characters at two, four
and eight bits per dot, tilemap entries, sprite tables, colours, and Mode 7. It
converts between bytes and pixels. It draws nothing, models no chip, and knows
nothing about time.

## The authority ladder

1. **`conformance/hardware.json`**, which is Appendix A of Nintendo's SNES
   Development Manual: the CHR DATA CONSTRUCTION figure on page A-12 and the BG
   SC DATA figure on page A-10, plus the manual's statement about the
   transparent colour. It decides every layout.
2. **Nothing else.** There is no reference implementation here and no corpus.

## The thing to understand before changing anything

`conformance/exhaustive.py` walks every value each format can hold, decodes it,
re-encodes it, and checks that nothing changed. 165,248 cases, no sampling.

**That proves this package round-trips itself and nothing more.** A decoder and
an encoder wrong in exactly opposite ways pass every one of those cases, and for
a long time nothing here compared a layout against a figure Nintendo printed.

`conformance/hardware.test.py` is what closes that gap, and it is the file to
extend when adding a format. A format with an exhaustive walk and no figure
behind it is back in the position described above.

## Read the page, never the text layer

The manual is a scan whose OCR interleaves the columns of a table. Every figure
was read off a rendered page:

```bash
pdftoppm -r 200 -png -f 205 -l 207 book1.pdf pages/p
```

BG SC DATA is PDF page 205, CHR DATA CONSTRUCTION is 207.

## Every gate, in the order to run them

```bash
ruff format --check .                     # formatting
ruff check .                              # lint, zero warnings
mypy                                      # types, strict
pnpm run format:check                     # every JSON file
for f in snesgfx/*.test.py conformance/*.test.py; do python3 "$f"; done
python3 -m coverage report                # fails below 100%

python3 conformance/exhaustive.py         # every value of every space
python3 -m snesgfx.doctor                 # what is missing on this machine
```

Everything runs on any machine. Nothing here needs a cartridge, a corpus or a
network.

## Things that will bite you

**Planes are paired, not sequential.** The two planes of a pair share the two
bytes of one word, and the next pair starts eight words later. A four bit
character is not two planes then two more; it is a pair at word zero and a pair
at word eight.

**A tilemap entry's five fields cover the word exactly.** Ten bits of character
code, three of palette, one of priority, two of flip. If a change leaves a gap,
one of the masks is wrong.

**The channel width is arithmetic, not a figure.** Fifteen bits over three
channels gives five each. Nintendo prints the field order for register 2132H and
does not print the width, so it is recorded in `conformance/divergences.json`
rather than quoted as though it were printed.

**Nothing here knows about time.** These are layouts in memory.

## Conventions

| Thing | Rule |
|:------|:-----|
| Language | Python only |
| Comments | None in source. Docstrings carry the reasoning, and say why rather than what |
| Test layout | `<module>.test.py` beside the module it covers |
| Test structure | Arrange, blank line, one act, blank line, assert. No section labels |
| Package manager for tooling | pnpm, never npm |
| Commits | Conventional Commits |
| A new format | Needs a figure in `hardware.json` and a check in `hardware.test.py`, not only an exhaustive walk |
