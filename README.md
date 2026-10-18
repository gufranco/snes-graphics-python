# SNES Graphics Formats

The Super Nintendo tile, colour, background map, sprite and Mode 7 formats in Python, with the tile, map entry and colour layouts held to Nintendo's development manual and every input space small enough to walk walked from end to end.

English | [日本語](README.ja.md) | [简体中文](README.zh-Hans.md) | [繁體中文（香港）](README.zh-HK.md)

[![CI](https://github.com/gufranco/snes-graphics-python/actions/workflows/ci.yml/badge.svg)](https://github.com/gufranco/snes-graphics-python/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/gufranco/snes-graphics-python)](https://github.com/gufranco/snes-graphics-python/releases)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

**7** formats, **165,248** cases settled by walking their whole input space, **66,432** cases compared against SuperFamiconv, **11,765** regions of real cartridge data read three ways, **0** failures, **906** tests, **100%** statement and branch coverage, no dependencies

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

The 32 bytes are one four bit tile as video memory holds it. `tiles.decode` turns them into 64 colour numbers, row by row with the leftmost pixel first. Printed in hexadecimal, the numbers draw four rings of colours 1 to 4.

## Install

| Requirement | Version |
|:--|:--|
| Python | 3.12 or newer |
| git | Any |

```bash
git clone https://github.com/gufranco/snes-graphics-python.git
cd snes-graphics-python
python3 snesgfx/doctor.py
```

The package imports nothing outside the standard library. The examples in this file run from the repository root.

The doctor reports the machine, decodes every format on the spot, round trips a tile and lists the exhaustive walks. It ends with one line. Paste its whole output into any bug report.

```
  11 checks, nothing to report
```

Releases follow [Semantic Versioning](https://semver.org/) and are cut from the commit history by semantic-release. Every release is tagged and listed on the [releases page](https://github.com/gufranco/snes-graphics-python/releases).

## The interface

The package has one module per layout and a catalogue over them. The catalogue lets a tool hold bytes and a format name without knowing each module's call shape. Every module is also imported directly.

| Module | Holds |
|:--|:--|
| [`snesgfx/tiles.py`](snesgfx/tiles.py) | Bit plane tiles at 2, 4 and 8 bits a pixel, and flipping |
| [`snesgfx/palette.py`](snesgfx/palette.py) | The fifteen bit colour word and the palette blocks each depth reaches |
| [`snesgfx/tilemap.py`](snesgfx/tilemap.py) | The background map entry and the quadrants a map is stored in |
| [`snesgfx/oam.py`](snesgfx/oam.py) | The sprite table, both the 512 byte low table and the 32 byte high table |
| [`snesgfx/mode7.py`](snesgfx/mode7.py) | The Mode 7 matrix in the hardware's fixed point, and the interleaved map and pixels |
| [`snesgfx/models.py`](snesgfx/models.py) | The catalogue |
| [`snesgfx/errors.py`](snesgfx/errors.py) | Every exception the package raises |
| [`snesgfx/doctor.py`](snesgfx/doctor.py) | The doctor |
| [`snesgfx/environment.py`](snesgfx/environment.py) | The machine checks the doctor prints |

### The catalogue

| Name | Content |
|:--|:--|
| `snesgfx.FORMATS` | The seven `Format` records, keyed by canonical name |
| `snesgfx.format_named(name)` | The `Format` a name or an alias means. Case, spaces, hyphens and underscores are ignored. Raises `UnknownFormat` for any other name, listing the seven |
| `snesgfx.Format` | A record with `name`, `aliases`, `summary`, `decode` and `encode` |
| `snesgfx.__version__` | The installed version |

`Format.decode` and `Format.encode` take a whole buffer. On the three tile formats they read and write a sheet of tiles through `tiles.decode_sheet` and `tiles.encode_sheet`. On `mode7` they split and join the interleaved words. On the other three they are the module's own `decode` and `encode`.

```python
import snesgfx
from snesgfx import format_named

for name, found in snesgfx.FORMATS.items():
    print(name, found.aliases)

print(format_named("2bpp"), format_named("4bpp"), format_named("8bpp"), format_named("mode7"))
print(format_named("palette"), format_named("tilemap"), format_named("oam"))
print(format_named("16 Colour"), format_named("Mode_7"), format_named("CGRAM"))

sheet = format_named("2bpp").decode(bytes(32))
print(len(sheet), len(sheet[0]))
print(format_named("mode7").decode(bytes([1, 2, 3, 4])))

try:
    format_named("6bpp")
except snesgfx.UnknownFormat as error:
    print(error)
```

```
2bpp ('4-colour', '2bit')
4bpp ('16-colour', '4bit')
8bpp ('256-colour', '8bit')
mode7 ('mode-7', 'm7')
palette ('cgram', 'colours', 'colors')
tilemap ('map', 'screen', 'bg')
oam ('sprites', 'objects', 'obj')
<Format 2bpp> <Format 4bpp> <Format 8bpp> <Format mode7>
<Format palette> <Format tilemap> <Format oam>
<Format 4bpp> <Format mode7> <Format palette>
2 64
(b'\x01\x03', b'\x02\x04')
6bpp is not a format this package covers; it has 2bpp, 4bpp, 8bpp, mode7, oam, palette, tilemap
```

### Tiles

| Call | Effect |
|:--|:--|
| `tiles.decode(data, depth)` | One tile of `depth` times 8 bytes to 64 colour numbers, row by row |
| `tiles.encode(pixels, depth)` | 64 colour numbers to one tile |
| `tiles.decode_sheet(data, depth)` | Consecutive tiles to a list of 64-number lists |
| `tiles.encode_sheet(sheet, depth)` | A list of tiles back to bytes |
| `tiles.flip(pixels, horizontal=False, vertical=False)` | A mirrored copy of one tile |
| `tiles.tile_bytes(depth)` | 16, 32 or 64 |
| `tiles.depth_of(name)` | The depth an integer or a name in `tiles.NAMES` means |

| Constant | Value |
|:--|:--|
| `tiles.DEPTHS` | `(2, 4, 8)` |
| `tiles.TILE_PIXELS`, `tiles.TILE_WIDTH` | 64 and 8 |
| `tiles.PLANE_PAIR_BYTES` | 16, the bytes one pair of planes takes |
| `tiles.NAMES` | `2bpp`, `4bpp`, `8bpp`, `4-colour`, `16-colour` and `256-colour`, each mapped to its depth |

```python
from snesgfx import OutOfRange, Truncated, UnknownDepth, tiles

data = bytes.fromhex("3c00423cbd7ea566a566bd7e423c3c0000000000000018001800000000000000")
pixels = tiles.decode(data, depth=4)

print(tiles.encode(pixels, depth=4) == data)
print(tiles.decode(data[:16], depth=2)[16:24])
print(tiles.flip(pixels, horizontal=True)[:8] == pixels[:8][::-1])
print(tiles.tile_bytes(2), tiles.tile_bytes(4), tiles.tile_bytes(8))
print(tiles.depth_of("16-colour"), len(tiles.decode_sheet(data * 3, 4)))

for refused in (
    lambda: tiles.decode(data, 6),
    lambda: tiles.decode(data[:31], 4),
    lambda: tiles.encode([4] * 64, 2),
):
    try:
        refused()
    except (OutOfRange, Truncated, UnknownDepth) as error:
        print(type(error).__name__, error)
```

```
True
[1, 2, 3, 3, 3, 3, 2, 1]
True
16 32 64
4 3
UnknownDepth 6 is not a depth the hardware has; it has 2, 4, 8
Truncated a 4 bit tile is 32 bytes, not 31
OutOfRange 4 does not fit in 2 bits
```

The first 16 bytes of the four bit tile decode as a complete two bit tile: its third row is the low two bits of `12333321`.

### Colour

| Call | Effect |
|:--|:--|
| `palette.decode(data)` | Little-endian colour words to `(red, green, blue)` triples of 0 to 255 |
| `palette.encode(colours)` | Triples to colour words. Each channel keeps its top five bits |
| `palette.to_rgb(word)`, `palette.to_word(red, green, blue)` | One colour each way. Bit 15 of a word is ignored |
| `palette.normalise(data)` | A copy with bit 15 of every word cleared |
| `palette.block_size(depth)` | 4, 16 or 256 colours |
| `palette.block_start(depth, block)` | The index of a block's first colour |
| `palette.resolve(table, pixel, depth, block)` | The colour a pixel number reaches through a block |
| `palette.is_transparent(pixel)` | True for colour number 0 |

| Constant | Value |
|:--|:--|
| `palette.COLOURS` | 256 |
| `palette.BYTES_PER_COLOUR` | 2 |
| `palette.WORD_MASK` | `0x7FFF` |
| `palette.CHANNEL_BITS`, `palette.CHANNEL_MASK` | 5 and `0x1F` |
| `palette.BLOCKS` | `{2: 4, 4: 16, 8: 256}` |
| `palette.TRANSPARENT` | 0 |

```python
from snesgfx import palette

print(palette.to_rgb(0x7FFF), palette.to_rgb(0x001F), palette.to_rgb(0x7C00))
print(hex(palette.to_word(255, 255, 255)), hex(palette.to_word(0, 0, 255)))
print(palette.decode(bytes.fromhex("ff7f1f00")))
print(palette.encode([(255, 255, 255), (255, 0, 0)]).hex())
print(palette.normalise(bytes.fromhex("ffff")).hex())

grey = [(index, index, index) for index in range(256)]
print(palette.block_start(4, 2), palette.resolve(grey, 5, depth=4, block=2))
print(palette.block_start(2, 7), palette.resolve(grey, 3, depth=2, block=7))
print(palette.is_transparent(0), palette.is_transparent(1))
```

```
(255, 255, 255) (255, 0, 0) (0, 0, 255)
0x7fff 0x7c00
[(255, 255, 255), (255, 0, 0)]
ff7f1f00
ff7f
32 (37, 37, 37)
28 (31, 31, 31)
True False
```

`resolve` takes the depth and the block because a pixel number alone does not name a colour. A four bit pixel 5 in block 2 is colour 37, and a two bit pixel 3 in block 7 is colour 31.

### Background maps

`tilemap.Entry(tile=0, block=0, priority=False, horizontal_flip=False, vertical_flip=False)` is one map entry.

| Call or attribute | Effect |
|:--|:--|
| `Entry.from_word(word)` | The entry a sixteen bit word holds |
| `entry.word` | The word an entry packs to. Raises `OutOfRange` for a tile above 1023 or a block above 7 |
| `tilemap.decode(data)`, `tilemap.encode(entries)` | Little-endian words each way |
| `tilemap.screen_size(size)` | The width and height in tiles of screen size setting 0 to 3 |
| `tilemap.offset_of(x, y, size)` | The entry index of a tile position, quadrants included. Positions wrap |
| `tilemap.entry_at(entries, x, y, size)` | The entry at a tile position |

| Constant | Value |
|:--|:--|
| `tilemap.SCREEN_SIZES` | `((32, 32), (64, 32), (32, 64), (64, 64))` |
| `tilemap.QUADRANT_TILES`, `tilemap.QUADRANT_ENTRIES` | 32 and 1024 |
| `tilemap.BYTES_PER_ENTRY` | 2 |
| `tilemap.TILE_MASK` | `0x03FF` |
| `tilemap.BLOCK_SHIFT`, `tilemap.BLOCK_MASK` | 10 and `0x07` |
| `tilemap.PRIORITY_BIT`, `tilemap.HORIZONTAL_BIT`, `tilemap.VERTICAL_BIT` | `0x2000`, `0x4000`, `0x8000` |

```python
from snesgfx import tilemap

entry = tilemap.Entry.from_word(0x6C05)
print(entry, entry.priority, entry.horizontal_flip, entry.vertical_flip)
print(hex(tilemap.Entry(tile=5, block=3, priority=True, horizontal_flip=True).word))
print(tilemap.decode(bytes.fromhex("056c")), tilemap.encode([entry]).hex())

print(tilemap.screen_size(0), tilemap.screen_size(3))
print(tilemap.offset_of(31, 0, 1), tilemap.offset_of(32, 0, 1))
print(tilemap.offset_of(0, 32, 2), tilemap.offset_of(0, 32, 3))

entries = [tilemap.Entry(tile=index % 1024) for index in range(4096)]
print(tilemap.entry_at(entries, 40, 2, 3))
```

```
<Entry tile 5 block 3> True True False
0x6c05
[<Entry tile 5 block 3>] 056c
(32, 32) (64, 64)
31 1024
1024 2048
<Entry tile 72 block 0>
```

Column 32 of a 64 by 32 map is entry 1024, the first entry of the second quadrant, where column 31 is entry 31.

### Sprites

`oam.Sprite(x=0, y=0, tile=0, block=0, priority=0, table=0, horizontal_flip=False, vertical_flip=False, large=False)` is one sprite.

| Call or attribute | Effect |
|:--|:--|
| `oam.decode(data)` | The 544 byte table to 128 sprites. Bit 8 of `x` and `large` come from the high table |
| `oam.encode(sprites)` | Exactly 128 sprites to 544 bytes. Raises `OutOfRange` for `x` from 512, `y` from 256, `tile` from 512, `block` from 8 or `priority` from 4 |
| `sprite.screen_x` | `x` as a screen position: from 256 up, `x` minus 512 |
| `sprite.table` | Bit 0 of the attribute byte, which is also bit 8 of `tile`. `encode` writes that bit from `tile` |
| `oam.sizes(setting)` | The small and large sizes of object size setting 0 to 7 |
| `oam.size_of(sprite, setting)` | The size one sprite takes under a setting |

| Constant | Value |
|:--|:--|
| `oam.SPRITES` | 128 |
| `oam.LOW_ENTRY_BYTES`, `oam.LOW_TABLE_BYTES` | 4 and 512 |
| `oam.HIGH_TABLE_BYTES`, `oam.TABLE_BYTES` | 32 and 544 |
| `oam.SCREEN_WIDTH` | 256 |
| `oam.SIZES` | The eight `(small, large)` pairs |

```python
from snesgfx import oam

sprites = [oam.Sprite() for _ in range(oam.SPRITES)]
sprites[5] = oam.Sprite(
    x=0x1F0, y=100, tile=0x123, block=2, priority=3, horizontal_flip=True, large=True
)
table = oam.encode(sprites)
print(len(table), table[20:24].hex(), bin(table[513]))

back = oam.decode(table)[5]
print(back, back.screen_x, back.large, back.table)
print(oam.sizes(0), oam.size_of(back, 0), oam.size_of(back, 6))
```

```
544 f0642375 0b1100
<Sprite at 496,100 tile 291 block 2> -16 True 1
((8, 8), (16, 16)) (16, 16) (32, 64)
```

Sprite 5 keeps its low four bytes at offset 20. Its two high bits sit in byte 513, bits 2 and 3, which also holds sprites 4, 6 and 7. An `x` of `0x1F0` is 16 pixels off the left edge.

### Mode 7

| Call | Effect |
|:--|:--|
| `mode7.Matrix(a, b, c, d)` | The four matrix registers. Each attribute reads as a signed sixteen bit value, 8.8 fixed point |
| `mode7.Field(matrix, centre=(0, 0), scroll=(0, 0))` | A matrix with its centre and scroll, each read as signed thirteen bit values |
| `field.at(x, y)` | The field pixel a screen pixel shows. The products with the scroll offset and with `y` lose their low six bits before the sum; the products with `x` keep them |
| `mode7.signed13(value)`, `mode7.signed16(value)` | Sign extension |
| `mode7.wrap(x, y)`, `mode7.outside(x, y)` | A position wrapped into the 1024 by 1024 field, and whether it lies outside |
| `mode7.deinterleave(vram)`, `mode7.interleave(names, pixels)` | Split the words into map bytes and pixel bytes, and join them back |
| `mode7.tile(pixels, index)` | The 64 pixels of one tile, a byte each |
| `mode7.name_at(names, x, y)` | The tile name under a field pixel |

| Constant | Value |
|:--|:--|
| `mode7.FIELD_TILES`, `mode7.TILE_WIDTH`, `mode7.FIELD_PIXELS` | 128, 8 and 1024 |
| `mode7.FRACTION_BITS` | 8 |
| `mode7.TRUNCATE` | `~0x3F` |
| `mode7.SIGN13`, `mode7.RANGE13`, `mode7.SIGN16`, `mode7.RANGE16` | `0x1000`, `0x2000`, `0x8000`, `0x10000` |

```python
from snesgfx import mode7

identity = mode7.Matrix(a=0x0100, b=0, c=0, d=0x0100)
print(mode7.Field(identity).at(10, 20))
print(mode7.Field(identity, centre=(128, 112), scroll=(64, 0)).at(10, 20))
print(mode7.Field(mode7.Matrix(a=0x0200, b=0, c=0, d=0x0200)).at(10, 20))
print(mode7.Matrix(a=0xFF00, b=0, c=0, d=0x0100))

shear = mode7.Matrix(a=0x0100, b=0x0030, c=0, d=0x0100)
print(mode7.Field(shear, scroll=(0, 1)).at(0, 5), (0x30 * 1 + 0x30 * 5) >> 8)

names, pixels = mode7.deinterleave(bytes(range(8)))
print(names.hex(), pixels.hex(), mode7.interleave(names, pixels) == bytes(range(8)))
print(mode7.tile(bytes(range(128)), 1)[:4], mode7.name_at(bytes(range(256)) * 64, 9, 8))
print(mode7.signed13(0x1FFF), mode7.wrap(-1, 1024), mode7.outside(1024, 0))
```

```
(10, 20)
(74, 20)
(20, 40)
<Matrix a=-256 b=0 c=0 d=256>
(0, 6) 1
00020406 01030507 True
[64, 65, 66, 67] 129
-1 (1023, 0) True
```

The sheared field shows column 0 although the full products, 48 and 240, add up to one whole pixel, as the second number printed says. Each product loses its low six bits first: 48 becomes 0 and 240 becomes 192, which sum to less than 256.

### Errors

Every exception lives in [`snesgfx/errors.py`](snesgfx/errors.py), and all four are exported from `snesgfx`.

| Exception | Raised when |
|:--|:--|
| `Truncated` | A buffer is the wrong length: a tile that is not 8 bytes per bit of its depth, a pixel list that is not 64 long, a sheet or colour or map buffer that does not divide evenly, a sprite table that is not 544 bytes or 128 sprites, Mode 7 words of odd length or halves of unequal length, a Mode 7 tile past the end |
| `OutOfRange` | A value does not fit its field: a pixel too large for its depth, a channel outside 0 to 255, a colour word above 16 bits, a palette block past the table, a map entry tile or block, a sprite field, a screen size or object size setting, a depth `palette.block_size` does not know |
| `UnknownDepth` | A tile depth other than 2, 4 and 8, or a name `tiles.depth_of` does not know |
| `UnknownFormat` | A name `format_named` does not know |

### The doctor

`python3 snesgfx/doctor.py` takes no arguments. It prints nine machine checks, then eleven package checks: the Python version, the package version, one decode per format, a four bit round trip and the list of exhaustive walks. It exits 0 when the eleven package checks pass and 1 when any fails. The machine checks are printed and do not change the exit code.

## The formats

| Name | What it is | Aliases |
|:--|:--|:--|
| `2bpp` | Two planes, four colours, 16 bytes a tile | `4-colour`, `2bit` |
| `4bpp` | Four planes, sixteen colours, 32 bytes a tile | `16-colour`, `4bit` |
| `8bpp` | Eight planes, 256 colours, 64 bytes a tile | `256-colour`, `8bit` |
| `mode7` | The rotating background: a byte a pixel, map and pixels interleaved word by word | `mode-7`, `m7` |
| `palette` | Fifteen bit colour, two bytes each, blue highest | `cgram`, `colours`, `colors` |
| `tilemap` | The background map, sixteen bits an entry, stored in quadrants | `map`, `screen`, `bg` |
| `oam` | The sprite table, four bytes a sprite plus two bits in a second table | `sprites`, `objects`, `obj` |

There is no six bit depth, because no background mode has one. Nothing here reads or writes an image file, which keeps the package free of dependencies.

## The parts people get wrong

**Tiles are not stored as pixels.** Each bit of a colour number lives in its own plane, and the planes are paired and interleaved by row. A four bit tile is two such pairs one after the other, so its first 16 bytes are a complete two bit tile.

**The leftmost pixel comes from the highest bit.** That is the opposite of the order the bits are numbered in.

**Five bit colour does not widen by shifting.** Shifting 31 left by three gives 248, so white decodes as `(248, 248, 248)`. Repeating the value's top bits into the gap gives 255, and all 32,768 colours survive a round trip.

**A background map is not a rectangle.** A 64 tile wide map is two 32 by 32 blocks stored one after the other, so column 32 is entry 1024 and not entry 32. Getting it wrong draws the right tiles in the wrong quadrant.

**A sprite's data is in two places.** Bit 8 of the horizontal position and the size flag live in the 32 byte high table, four sprites to a byte. That ninth bit acts as a sign: `x` of `0x1F0` is 16 pixels off the left edge.

**Mode 7 drops the low six bits of most products.** The products with the scroll offset and with the screen row are truncated before they are added, so one under 64 contributes nothing. The products with the screen column keep every bit. `field.at` does both.

## Is it right

Three figures are held to the manual: the tile layout, the map entry and the colour word. [`conformance/hardware.json`](conformance/hardware.json) carries each with its sentence, the manual page and the file page, and [`conformance/hardware.test.py`](conformance/hardware.test.py) compares them with the constants in the package. `python3 -m conformance.quotes` locates all 9 quoted sentences in the manual when it is on disk.

A complete round trip only shows that a decoder and an encoder agree. Swapping the two flip bits in the record and in the code together passes every walk and every record check, and decodes every map wrong. Two checks below rest on something this repository did not write: a second reading of the same figures, and cartridge bytes.

### Every case walked

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

| Walk | Cases | What it covers |
|:--|--:|:--|
| `tiles-2bpp` | 65,536 | Every two bit tile row pair, decoded and re-encoded |
| `tiles-planes` | 896 | Every plane of every depth against each of the 64 pixels |
| `palette` | 32,768 | Every colour word, widened and narrowed back |
| `tilemap` | 65,536 | Every map entry word, split into fields and packed back |
| `oam-high` | 512 | Both high bits of each of the 128 sprites, with no neighbour disturbed |

A four bit tile has too many states to walk. The plane walk stands in for it: each plane must reach its own bit of every pixel and nothing else. The tests break each format on purpose and confirm the walk catches it.

### Against a second reading

The reference is [SuperFamiconv](https://github.com/Optiroc/SuperFamiconv), pinned by commit in [`conformance/pinned.json`](conformance/pinned.json). It is not carried here. `conformance.build` fetches the pinned commit, lifts three functions and compiles them behind [`conformance/ref/driver.cpp`](conformance/ref/driver.cpp) with `g++`.

```bash
python3 -m conformance.build
python3 -m conformance.against_reference
```

```
  66,432 cases compared against the reference, none disagreed
```

| Figure | Cases | How the cases are chosen |
|:--|--:|:--|
| Bit plane layout | 896 | One bit set at a time, at each depth |
| Colour packing | 32,768 | Every five bit red, green and blue |
| Map entry | 32,768 | Every tile, block and pair of flips |

This package narrows eight bit channels itself, and the reference is handed the five bits the console stores.

### Against cartridges

Two readers who make the same mistake agree. Cartridge bytes separate a right reading from a plausible one, because a picture read with the right grouping has neighbours that match. [`conformance/against_cartridges.py`](conformance/against_cartridges.py) reads the same regions three ways, at four bits a pixel, and counts which reading finds the most equal neighbours in each region. Contiguous planes is how other consoles of the period stored tiles, and two pixels to a byte is the plainest way to hold sixteen colours.

```bash
SNES_CARTRIDGE_DIR=/path/to/your/images python3 -m conformance.against_cartridges
```

```
  documented             won   6178 of 11765 (52.5%)
  contiguous planes      won   3735 of 11765 (31.7%)
  two pixels per byte    won   1852 of 11765 (15.7%)
  a reading with nothing in it would win 33.3%
the published layout won 52.5% against a floor of 33.3%
```

Regions are 2,048 bytes taken every 32 KB from offset `0x8000` up to 2 MB, chosen by position and skipped only when they hold fewer than 8 distinct bytes. The statistic looks at whether neighbours are equal, never at their colour, so swapping the plane pairs scores the same. That swap only renames colours. No cartridge is carried: the run read 300 of the 7,578 images on one machine, drawn with seed 11, and [`conformance/cartridges.json`](conformance/cartridges.json) records the counts and the corpus digest. Without the variable the runner looks in `cartridges/` inside the checkout, then in a `snes-roms` directory beside it.

### The checking tools

| Command | Arguments | Exit codes |
|:--|:--|:--|
| `python3 -m conformance.exhaustive` | `--only NAME` | 0 every walk clean, 1 a walk failed, 2 an unknown name or argument |
| `python3 -m conformance.build` | `--sources DIR`, `--output PATH`, `--pinned FILE`, `--driver-source FILE` | 0 built, 1 the compiler failed, 2 a bad argument or a failed fetch |
| `python3 -m conformance.against_reference` | None | 0 no disagreement, or the driver is not built and it says so, 1 a disagreement |
| `python3 -m conformance.against_cartridges` | `SNES_CARTRIDGE_DIR` in the environment | 0 above the floor, 1 at or below it, 2 nothing to check |
| `python3 -m conformance.quotes` | None | 0 every quote located or no manual on disk, 1 a quote or citation that does not hold |
| `python3 -m conformance.documents` | `--check`, `--only SUBSTRING` | 0 every document verified, 1 a refusal, no match or a bad argument |
| `python3 -m conformance.speed` | None | 0 at least 10,000 four bit decodes a second, 1 below that |
| `python3 -m conformance.links` | None | 0, or 1 when an address in this file answers 404 or 410 |
| `python3 -m conformance.package WHEEL` | A built wheel | 0 every module and no test shipped, 1 a fault or no such file, 2 no argument |

What the manual does not settle is in [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md), and each entry is also in [`conformance/divergences.json`](conformance/divergences.json) with its status and severity.

## Working on it

| Need | Where |
|:--|:--|
| Every gate and the order to run them | [CONTRIBUTING.md](CONTRIBUTING.md) |
| The same material for a coding agent | [AGENTS.md](AGENTS.md) |
| The standard this repository shares with the rest of the family | [FAMILY.md](FAMILY.md) |
| Bug reports | [GitHub Issues](https://github.com/gufranco/snes-graphics-python/issues) |
| Security reports | [SECURITY.md](SECURITY.md) |

```bash
uvx ruff@0.16.3 format --check .
uvx ruff@0.16.3 check .
uvx --python 3.12 --with types-setuptools==84.0.0.20260812 mypy==1.14.1
pnpm install --frozen-lockfile && pnpm run format:check
cov=(uvx --python 3.12 --from coverage==7.6.10 --with setuptools==84.0.0 coverage)
"${cov[@]}" erase
for file in $(find snesgfx conformance -name '*.test.py' | sort); do
  "${cov[@]}" run -a "$file"
done
"${cov[@]}" report
```

Each module has a test file beside it, named after it, and each runs on its own, such as `python3 snesgfx/tiles.test.py`. Coverage is a hard gate at 100% statement and branch.

## References

- *SNES Development Manual, Book I*, Nintendo of America Inc., undated. Appendix A, pages A-10, A-12 and A-17. 240 pages, 21,022,582 bytes, SHA-256 `f1405241000046abba7849376d2ec53cf85f1ad2e9950d69a7c2cf1f3ff6b791`. It is not redistributable and is not in this repository. `python3 -m conformance.documents` downloads it from https://archive.org/download/SNESDevManual/book1_text.pdf into `docs/manufacturer/`, which git ignores, and refuses any other file. `python3 -m conformance.documents --check` verifies a copy already there.
- SuperFamiconv by David Lindecrantz, MIT, at commit `d903daf1b74c9ec6db7949fe62af2f0b58bdc23b`, https://github.com/Optiroc/SuperFamiconv, for an independent reading of the bit plane, colour and map entry figures. `unpack_native_tile`, `pack_native_color` and `pack_native_mapentry` are compiled at build time and never committed.

## Citing this

[CITATION.cff](CITATION.cff) is updated with each release by the script that stamps the package version.

## License

MIT. See [LICENSE](LICENSE).
