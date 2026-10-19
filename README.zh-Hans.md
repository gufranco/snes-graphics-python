# SNES 图形格式

用 Python 实现的 Super Nintendo 图块、颜色、背景地图、精灵和 Mode 7 格式。图块、地图条目、颜色、精灵表和 Mode 7 的布局以 Nintendo 的开发手册为准，凡是小到可以遍历的输入空间，都从头到尾遍历过。

[English](README.md) | [日本語](README.ja.md) | 简体中文 | [繁體中文（香港）](README.zh-HK.md)

[![CI](https://github.com/gufranco/snes-graphics-python/actions/workflows/ci.yml/badge.svg)](https://github.com/gufranco/snes-graphics-python/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/gufranco/snes-graphics-python)](https://github.com/gufranco/snes-graphics-python/releases)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

**7** 种格式，**165,248** 个用例通过遍历完整输入空间得到确认，**66,432** 个用例与 SuperFamiconv 比对，**11,765** 个真实卡带数据区域按三种方式读取，**0** 个失败，**924** 个测试，**100%** 语句和分支覆盖率，无依赖

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

这 32 个字节是显存中保存的一个四位图块。`tiles.decode` 把它们转换成 64 个颜色编号，逐行排列，每行最左边的像素在前。以十六进制打印时，这些编号画出颜色 1 到 4 的四个圆环。

## 安装

| 要求   | 版本        |
| :----- | :---------- |
| Python | 3.12 或更高 |
| git    | 任意        |

```bash
git clone https://github.com/gufranco/snes-graphics-python.git
cd snes-graphics-python
python3 snesgfx/doctor.py
```

这个包只导入标准库中的内容。本文件中的示例在仓库根目录下运行。

诊断脚本会报告机器信息，当场解码每种格式，对一个图块做往返转换，并列出穷举遍历。它以一行结束。提交 bug 报告时，请粘贴它的完整输出。

```
  11 checks, nothing to report
```

版本发布遵循 [Semantic Versioning](https://semver.org/)，由 semantic-release 根据提交历史生成。每个版本都打了标签，并列在[发布页面](https://github.com/gufranco/snes-graphics-python/releases)上。

## 接口

这个包每种布局对应一个模块，并在它们之上提供一个目录。借助目录，工具只需持有字节和格式名称，不必了解每个模块的调用方式。每个模块也可以直接导入。

| 模块                                               | 内容                                                     |
| :------------------------------------------------- | :------------------------------------------------------- |
| [`snesgfx/tiles.py`](snesgfx/tiles.py)             | 每像素 2、4、8 位的位平面图块，以及翻转                  |
| [`snesgfx/palette.py`](snesgfx/palette.py)         | 十五位颜色字，以及每种位深能用到的调色板块               |
| [`snesgfx/tilemap.py`](snesgfx/tilemap.py)         | 背景地图条目，以及地图存储所用的象限                     |
| [`snesgfx/oam.py`](snesgfx/oam.py)                 | 精灵表，包括 512 字节的低位表和 32 字节的高位表          |
| [`snesgfx/mode7.py`](snesgfx/mode7.py)             | 采用硬件定点格式的 Mode 7 矩阵，以及交错存放的地图和像素 |
| [`snesgfx/models.py`](snesgfx/models.py)           | 目录                                                     |
| [`snesgfx/errors.py`](snesgfx/errors.py)           | 这个包抛出的所有异常                                     |
| [`snesgfx/doctor.py`](snesgfx/doctor.py)           | 诊断脚本                                                 |
| [`snesgfx/environment.py`](snesgfx/environment.py) | 诊断脚本打印的机器检查                                   |

### 目录

| 名称                         | 内容                                                                                                                  |
| :--------------------------- | :-------------------------------------------------------------------------------------------------------------------- |
| `snesgfx.FORMATS`            | 七个 `Format` 记录，以规范名称为键                                                                                    |
| `snesgfx.format_named(name)` | 一个名称或别名对应的 `Format`。忽略大小写、空格、连字符和下划线。遇到其他名称时抛出 `UnknownFormat`，并列出这七个名称 |
| `snesgfx.Format`             | 一个包含 `name`、`aliases`、`summary`、`decode` 和 `encode` 的记录                                                    |
| `snesgfx.__version__`        | 已安装的版本                                                                                                          |

`Format.decode` 和 `Format.encode` 接受整个缓冲区。对于三种图块格式，它们通过 `tiles.decode_sheet` 和 `tiles.encode_sheet` 读写一整张图块表。对于 `mode7`，它们拆分和合并交错的字。对于其余三种格式，它们就是模块自身的 `decode` 和 `encode`。

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

### 图块

| 调用                                                   | 作用                                                         |
| :----------------------------------------------------- | :----------------------------------------------------------- |
| `tiles.decode(data, depth)`                            | 把一个 `depth` 乘 8 字节的图块转换成 64 个颜色编号，逐行排列 |
| `tiles.encode(pixels, depth)`                          | 把 64 个颜色编号转换成一个图块                               |
| `tiles.decode_sheet(data, depth)`                      | 把连续的图块转换成由 64 个编号的列表组成的列表               |
| `tiles.encode_sheet(sheet, depth)`                     | 把图块列表转换回字节                                         |
| `tiles.flip(pixels, horizontal=False, vertical=False)` | 一个图块的镜像副本                                           |
| `tiles.tile_bytes(depth)`                              | 16、32 或 64                                                 |
| `tiles.depth_of(name)`                                 | 一个整数或 `tiles.NAMES` 中的名称所表示的位深                |

| 常量                                    | 值                                                                                    |
| :-------------------------------------- | :------------------------------------------------------------------------------------ |
| `tiles.DEPTHS`                          | `(2, 4, 8)`                                                                           |
| `tiles.TILE_PIXELS`、`tiles.TILE_WIDTH` | 64 和 8                                                                               |
| `tiles.PLANE_PAIR_BYTES`                | 16，一对平面占用的字节数                                                              |
| `tiles.NAMES`                           | `2bpp`、`4bpp`、`8bpp`、`4-colour`、`16-colour` 和 `256-colour`，各自映射到对应的位深 |

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

四位图块的前 16 个字节可以解码为一个完整的二位图块：它的第三行是 `12333321` 的低两位。

### 颜色

| 调用                                                        | 作用                                                             |
| :---------------------------------------------------------- | :--------------------------------------------------------------- |
| `palette.decode(data)`                                      | 把小端序颜色字转换成取值 0 到 255 的 `(red, green, blue)` 三元组 |
| `palette.encode(colours)`                                   | 把三元组转换成颜色字。每个通道保留最高五位                       |
| `palette.to_rgb(word)`、`palette.to_word(red, green, blue)` | 单个颜色的双向转换。忽略字的第 15 位                             |
| `palette.normalise(data)`                                   | 一个把每个字的第 15 位清零的副本                                 |
| `palette.block_size(depth)`                                 | 4、16 或 256 种颜色                                              |
| `palette.block_start(depth, block)`                         | 一个块的第一个颜色的索引                                         |
| `palette.resolve(table, pixel, depth, block)`               | 一个像素编号通过某个块对应到的颜色                               |
| `palette.is_transparent(pixel)`                             | 颜色编号为 0 时为 True                                           |

| 常量                                           | 值                      |
| :--------------------------------------------- | :---------------------- |
| `palette.COLOURS`                              | 256                     |
| `palette.BYTES_PER_COLOUR`                     | 2                       |
| `palette.WORD_MASK`                            | `0x7FFF`                |
| `palette.CHANNEL_BITS`、`palette.CHANNEL_MASK` | 5 和 `0x1F`             |
| `palette.BLOCKS`                               | `{2: 4, 4: 16, 8: 256}` |
| `palette.TRANSPARENT`                          | 0                       |

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

`resolve` 需要位深和块，因为单凭像素编号无法确定颜色。块 2 中的四位像素 5 是颜色 37，块 7 中的二位像素 3 是颜色 31。

### 背景地图

`tilemap.Entry(tile=0, block=0, priority=False, horizontal_flip=False, vertical_flip=False)` 是一个地图条目。

| 调用或属性                                        | 作用                                                         |
| :------------------------------------------------ | :----------------------------------------------------------- |
| `Entry.from_word(word)`                           | 一个十六位字所保存的条目                                     |
| `entry.word`                                      | 条目打包成的字。图块大于 1023 或块大于 7 时抛出 `OutOfRange` |
| `tilemap.decode(data)`、`tilemap.encode(entries)` | 小端序字的双向转换                                           |
| `tilemap.screen_size(size)`                       | 屏幕尺寸设置 0 到 3 对应的以图块计的宽度和高度               |
| `tilemap.offset_of(x, y, size)`                   | 一个图块位置的条目索引，已考虑象限。位置会回绕               |
| `tilemap.entry_at(entries, x, y, size)`           | 一个图块位置上的条目                                         |

| 常量                                                                     | 值                                         |
| :----------------------------------------------------------------------- | :----------------------------------------- |
| `tilemap.SCREEN_SIZES`                                                   | `((32, 32), (64, 32), (32, 64), (64, 64))` |
| `tilemap.QUADRANT_TILES`、`tilemap.QUADRANT_ENTRIES`                     | 32 和 1024                                 |
| `tilemap.BYTES_PER_ENTRY`                                                | 2                                          |
| `tilemap.TILE_MASK`                                                      | `0x03FF`                                   |
| `tilemap.BLOCK_SHIFT`、`tilemap.BLOCK_MASK`                              | 10 和 `0x07`                               |
| `tilemap.PRIORITY_BIT`、`tilemap.HORIZONTAL_BIT`、`tilemap.VERTICAL_BIT` | `0x2000`、`0x4000`、`0x8000`               |

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

在 64 乘 32 的地图中，第 32 列是条目 1024，即第二个象限的第一个条目，而第 31 列是条目 31。

### 精灵

`oam.Sprite(x=0, y=0, tile=0, block=0, priority=0, table=0, horizontal_flip=False, vertical_flip=False, large=False)` 是一个精灵。

| 调用或属性                     | 作用                                                                                                                                   |
| :----------------------------- | :------------------------------------------------------------------------------------------------------------------------------------- |
| `oam.decode(data)`             | 把 544 字节的表转换成 128 个精灵。`x` 的第 8 位和 `large` 来自高位表                                                                   |
| `oam.encode(sprites)`          | 把恰好 128 个精灵转换成 544 字节。`x` 达到 512、`y` 达到 256、`tile` 达到 512、`block` 达到 8 或 `priority` 达到 4 时抛出 `OutOfRange` |
| `sprite.screen_x`              | 作为屏幕位置的 `x`：从 256 起取 `x` 减 512                                                                                             |
| `sprite.table`                 | 属性字节的第 0 位，它同时也是 `tile` 的第 8 位。`encode` 根据 `tile` 写入这一位                                                        |
| `oam.sizes(setting)`           | 对象尺寸设置 0 到 7 的小尺寸和大尺寸                                                                                                   |
| `oam.size_of(sprite, setting)` | 某个设置下单个精灵的尺寸                                                                                                               |

| 常量                                         | 值                       |
| :------------------------------------------- | :----------------------- |
| `oam.SPRITES`                                | 128                      |
| `oam.LOW_ENTRY_BYTES`、`oam.LOW_TABLE_BYTES` | 4 和 512                 |
| `oam.HIGH_TABLE_BYTES`、`oam.TABLE_BYTES`    | 32 和 544                |
| `oam.SCREEN_WIDTH`                           | 256                      |
| `oam.SIZES`                                  | 八个 `(small, large)` 对 |

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

精灵 5 的四个低位字节位于偏移 20。它的两个高位在字节 513 的第 2 位和第 3 位，这个字节同时保存精灵 4、6 和 7 的高位。`x` 为 `0x1F0` 时，精灵位于左边缘外 16 个像素处。

### Mode 7

| 调用                                                          | 作用                                                                                            |
| :------------------------------------------------------------ | :---------------------------------------------------------------------------------------------- |
| `mode7.Matrix(a, b, c, d)`                                    | 四个矩阵寄存器。每个属性都按有符号十六位值读取，格式为 8.8 定点                                 |
| `mode7.Field(matrix, centre=(0, 0), scroll=(0, 0))`           | 一个矩阵及其中心和滚动量，二者都按有符号十三位值读取                                            |
| `field.at(x, y)`                                              | 一个屏幕像素显示的场像素。与滚动偏移和与 `y` 的乘积在求和前丢弃低六位；与 `x` 的乘积保留低六位  |
| `mode7.signed13(value)`、`mode7.signed16(value)`              | 符号扩展                                                                                        |
| `mode7.clipped(offset)`                                       | 滚动偏移减去中心后，乘法器所接收的形式：保留低十位，以第 13 位为符号。`field.at` 对两个轴都应用 |
| `mode7.wrap(x, y)`、`mode7.outside(x, y)`                     | 回绕到 1024 乘 1024 场内的位置，以及位置是否在场外                                              |
| `mode7.deinterleave(vram)`、`mode7.interleave(names, pixels)` | 把字拆分成地图字节和像素字节，以及把它们重新合并                                                |
| `mode7.tile(pixels, index)`                                   | 一个图块的 64 个像素，每个像素一个字节                                                          |
| `mode7.name_at(names, x, y)`                                  | 一个场像素下的图块名称                                                                          |

| 常量                                                             | 值                                      |
| :--------------------------------------------------------------- | :-------------------------------------- |
| `mode7.FIELD_TILES`、`mode7.TILE_WIDTH`、`mode7.FIELD_PIXELS`    | 128、8 和 1024                          |
| `mode7.FRACTION_BITS`                                            | 8                                       |
| `mode7.TRUNCATE`                                                 | `~0x3F`                                 |
| `mode7.SIGN13`、`mode7.RANGE13`、`mode7.SIGN16`、`mode7.RANGE16` | `0x1000`、`0x2000`、`0x8000`、`0x10000` |
| `mode7.OFFSET_SIGN`、`mode7.OFFSET_MASK`                         | `0x2000`、`0x3FF`                       |

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

完整乘积 48 和 240 相加得到一个整像素，打印的第二个数字正说明了这一点，但错切后的场显示的是第 0 列。每个乘积先丢弃低六位：48 变成 0，240 变成 192，两者之和小于 256。

### 错误

所有异常都在 [`snesgfx/errors.py`](snesgfx/errors.py) 中，四个异常都从 `snesgfx` 导出。

| 异常            | 抛出条件                                                                                                                                                                                 |
| :-------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Truncated`     | 缓冲区长度错误：图块不是每位深 8 字节，像素列表长度不是 64，图块表、颜色或地图缓冲区无法整除，精灵表不是 544 字节或 128 个精灵，Mode 7 字的长度为奇数或两半长度不等，Mode 7 图块超出末尾 |
| `OutOfRange`    | 值超出其字段范围：像素对其位深而言过大，通道超出 0 到 255，颜色字超过 16 位，调色板块超出表，地图条目的图块或块，精灵字段，屏幕尺寸或对象尺寸设置，`palette.block_size` 不认识的位深     |
| `UnknownDepth`  | 2、4、8 以外的图块位深，或 `tiles.depth_of` 不认识的名称                                                                                                                                 |
| `UnknownFormat` | `format_named` 不认识的名称                                                                                                                                                              |

### 诊断脚本

`python3 snesgfx/doctor.py` 不接受参数。它先打印九项机器检查，再打印十一项包检查：Python 版本、包版本、每种格式各一次解码、一次四位往返转换，以及穷举遍历列表。十一项包检查全部通过时退出码为 0，任意一项失败时为 1。机器检查只打印，不影响退出码。

## 格式

| 名称      | 说明                                             | 别名                         |
| :-------- | :----------------------------------------------- | :--------------------------- |
| `2bpp`    | 两个平面，四种颜色，每个图块 16 字节             | `4-colour`、`2bit`           |
| `4bpp`    | 四个平面，十六种颜色，每个图块 32 字节           | `16-colour`、`4bit`          |
| `8bpp`    | 八个平面，256 种颜色，每个图块 64 字节           | `256-colour`、`8bit`         |
| `mode7`   | 可旋转的背景：每像素一个字节，地图和像素逐字交错 | `mode-7`、`m7`               |
| `palette` | 十五位颜色，每个颜色两个字节，蓝色在最高位       | `cgram`、`colours`、`colors` |
| `tilemap` | 背景地图，每个条目十六位，按象限存储             | `map`、`screen`、`bg`        |
| `oam`     | 精灵表，每个精灵四个字节，另加第二张表中的两位   | `sprites`、`objects`、`obj`  |

没有六位位深，因为没有任何背景模式使用它。这里没有任何代码读写图像文件，这让这个包保持无依赖。

## 容易弄错的地方

**图块不是按像素存储的。** 颜色编号的每一位位于各自的平面中，平面两两成对，并按行交错。四位图块是两对这样的平面先后排列，因此它的前 16 个字节就是一个完整的二位图块。

**最左边的像素来自最高位。** 这与位的编号顺序相反。

**五位颜色不能靠移位来扩展。** 把 31 左移三位得到 248，于是白色会解码为 `(248, 248, 248)`。把值的高位重复填入空出的位得到 255，并且全部 32,768 种颜色都能完整往返转换。

**背景地图不是一个矩形。** 64 个图块宽的地图是两个 32 乘 32 的块先后存储，因此第 32 列是条目 1024 而不是条目 32。弄错的话，正确的图块会画在错误的象限里。

**精灵的数据分在两个地方。** 水平位置的第 8 位和尺寸标志位于 32 字节的高位表中，每个字节保存四个精灵。这第九位相当于符号位：`x` 为 `0x1F0` 时位于左边缘外 16 个像素处。

**Mode 7 会丢弃大多数乘积的低六位。** 与滚动偏移和与屏幕行的乘积在相加前被截断，因此小于 64 的乘积没有任何贡献。与屏幕列的乘积保留所有位。`field.at` 两者都做到了。

## 是否正确

有六项数据以手册为准：图块布局、地图条目、颜色字、精灵表、对象尺寸，以及 Mode 7 的矩阵、中心和地图。[`conformance/hardware.json`](conformance/hardware.json) 为每一项记录了原文句子、手册页码和文件页码，[`conformance/hardware.test.py`](conformance/hardware.test.py)、[`conformance/hardware_sprites.test.py`](conformance/hardware_sprites.test.py) 和 [`conformance/hardware_mode7.test.py`](conformance/hardware_mode7.test.py) 把它们与包进行比较。手册在磁盘上时，`python3 -m conformance.quotes` 会在手册中定位全部 25 条引用的句子。手册没有印出的三点依从固定提交的 ares：Mode 7 滚动偏移在相乘时的宽度、哪些 Mode 7 乘积丢弃低六位，以及对象尺寸设置 6 和 7。[`conformance/divergences.json`](conformance/divergences.json) 记下每一点的文件和行号。

完整的往返转换只能说明解码器和编码器彼此一致。如果在记录和代码中同时交换两个翻转位，每次遍历和每项记录检查都会通过，但每张地图都会解码错误。下面有两项检查依赖于不是本仓库编写的东西：对同一组数据的第二种解读，以及卡带字节。

### 遍历每个用例

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

| 遍历           | 用例数 | 覆盖范围                                   |
| :------------- | -----: | :----------------------------------------- |
| `tiles-2bpp`   | 65,536 | 每一对二位图块行，解码后再重新编码         |
| `tiles-planes` |    896 | 每种位深的每个平面，对 64 个像素逐一检查   |
| `palette`      | 32,768 | 每个颜色字，扩展后再缩回                   |
| `tilemap`      | 65,536 | 每个地图条目字，拆分成字段后再打包回去     |
| `oam-high`     |    512 | 128 个精灵各自的两个高位，且不干扰相邻精灵 |

四位图块的状态太多，无法遍历。平面遍历代替了它：每个平面必须正好对应到每个像素中属于自己的那一位，不能涉及其他位。测试会故意破坏每种格式，确认遍历能发现问题。

### 与第二种解读比对

参照实现是 [SuperFamiconv](https://github.com/Optiroc/SuperFamiconv)，其提交固定在 [`conformance/pinned.json`](conformance/pinned.json) 中。它不包含在本仓库里。`conformance.build` 获取固定的提交，提取三个函数，并用 `g++` 把它们与 [`conformance/ref/driver.cpp`](conformance/ref/driver.cpp) 一起编译。

```bash
python3 -m conformance.build
python3 -m conformance.against_reference
```

```
  66,432 cases compared against the reference, none disagreed
```

| 数据       | 用例数 | 用例的选取方式             |
| :--------- | -----: | :------------------------- |
| 位平面布局 |    896 | 每种位深下，每次只置一位   |
| 颜色打包   | 32,768 | 每一种五位红、绿、蓝组合   |
| 地图条目   | 32,768 | 每个图块、块和每对翻转组合 |

这个包自己把八位通道缩减为五位，而传给参照实现的是主机实际存储的五位值。

### 与卡带比对

两个犯同样错误的读取器会彼此一致。卡带字节能把正确的解读与看似合理的解读区分开，因为按正确分组读取的图像，相邻像素会相同。[`conformance/against_cartridges.py`](conformance/against_cartridges.py) 以每像素四位，用三种方式读取同样的区域，并统计在每个区域中哪种解读找到的相同相邻像素最多。连续平面是同一时期其他主机存储图块的方式，每字节两个像素是保存十六种颜色最直接的方式。

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

区域大小为 2,048 字节，从偏移 `0x8000` 开始每隔 32 KB 取一个，直到 2 MB。区域按位置选取，只有在不同字节少于 8 种时才跳过。这个统计量只看相邻像素是否相同，从不看它们的颜色，因此交换平面对得分相同。这种交换只是给颜色重新编号。本仓库不包含任何卡带：这次运行在一台机器上的 7,578 个镜像中读取了 300 个，抽样种子为 11，[`conformance/cartridges.json`](conformance/cartridges.json) 记录了计数和语料摘要。未设置该变量时，运行器先在检出目录中的 `cartridges/` 查找，再在它旁边的 `snes-roms` 目录中查找。

### 检查工具

| 命令                                        | 参数                                                                      | 退出码                                                         |
| :------------------------------------------ | :------------------------------------------------------------------------ | :------------------------------------------------------------- |
| `python3 -m conformance.exhaustive`         | `--only NAME`                                                             | 0 所有遍历都通过，1 有遍历失败，2 未知名称或参数               |
| `python3 -m conformance.build`              | `--sources DIR`、`--output PATH`、`--pinned FILE`、`--driver-source FILE` | 0 构建成功，1 编译器失败，2 参数错误或获取失败                 |
| `python3 -m conformance.against_reference`  | 无                                                                        | 0 没有分歧，或驱动程序尚未构建并给出提示，1 存在分歧           |
| `python3 -m conformance.against_cartridges` | 环境变量中的 `SNES_CARTRIDGE_DIR`                                         | 0 高于下限，1 等于或低于下限，2 没有可检查的内容               |
| `python3 -m conformance.quotes`             | 无                                                                        | 0 所有引用都已定位或磁盘上没有手册，1 有引用或出处不成立       |
| `python3 -m conformance.documents`          | `--check`、`--only SUBSTRING`                                             | 0 所有文档都已验证，1 拒绝、无匹配或参数错误                   |
| `python3 -m conformance.speed`              | 无                                                                        | 0 每秒至少 10,000 次四位解码，1 低于该值                       |
| `python3 -m conformance.links`              | 无                                                                        | 0，或在本文件中的地址返回 404 或 410 时为 1                    |
| `python3 -m conformance.package WHEEL`      | 一个已构建的 wheel                                                        | 0 包含所有模块且未打包测试，1 存在问题或文件不存在，2 缺少参数 |

手册没有确定的内容记录在 [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md) 中，每个条目也连同其状态和严重程度记录在 [`conformance/divergences.json`](conformance/divergences.json) 中。

## 参与开发

| 需求                             | 位置                                                                     |
| :------------------------------- | :----------------------------------------------------------------------- |
| 所有门禁检查及其运行顺序         | [CONTRIBUTING.md](CONTRIBUTING.md)                                       |
| 面向编码智能体的同样内容         | [AGENTS.md](AGENTS.md)                                                   |
| 本仓库与同系列其他仓库共享的标准 | [FAMILY.md](FAMILY.md)                                                   |
| bug 报告                         | [GitHub Issues](https://github.com/gufranco/snes-graphics-python/issues) |
| 安全报告                         | [SECURITY.md](SECURITY.md)                                               |

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

每个模块旁边都有一个以它命名的测试文件，每个测试文件都可以单独运行，例如 `python3 snesgfx/tiles.test.py`。覆盖率是一道硬性门禁检查，要求语句和分支覆盖率达到 100%。

## 参考资料

- _SNES Development Manual, Book I_，Nintendo of America Inc.，未注明日期。附录 A，第 A-3、A-4、A-10、A-11、A-12 和 A-17 页，以及第 27 章第 2-27-1、2-27-9 和 2-27-10 页。共 240 页，21,022,582 字节，SHA-256 `f1405241000046abba7849376d2ec53cf85f1ad2e9950d69a7c2cf1f3ff6b791`。该手册不可再分发，不包含在本仓库中。`python3 -m conformance.documents` 从 https://archive.org/download/SNESDevManual/book1_text.pdf 下载它到 git 忽略的 `docs/manufacturer/` 中，并拒绝任何其他文件。`python3 -m conformance.documents --check` 验证已在该位置的副本。
- SuperFamiconv，作者 David Lindecrantz，MIT 许可，提交 `d903daf1b74c9ec6db7949fe62af2f0b58bdc23b`，https://github.com/Optiroc/SuperFamiconv ，用于对位平面、颜色和地图条目数据进行独立解读。`unpack_native_tile`、`pack_native_color` 和 `pack_native_mapentry` 在构建时编译，从不提交。
- ares，ISC 许可，提交 `9408cb43d4948fc3ea6e152a307a34348df3fe04`，https://github.com/ares-emulator/ares ，用于手册没有印出的部分：`ares/sfc/ppu/mode7.cpp` 第 27 至 32 行和 `ares/sfc/ppu/oam.cpp` 第 57 至 71 行。不编译也不携带其中任何内容。

## 引用本项目

[CITATION.cff](CITATION.cff) 在每次发布时由写入包版本的脚本更新。

## 许可证

MIT。参见 [LICENSE](LICENSE)。
