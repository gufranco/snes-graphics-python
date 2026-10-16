[English](README.md) | [日本語](README.ja.md) | [简体中文](README.zh-Hans.md) | 繁體中文（香港）

# SNES 圖形格式

以 Python 實現的超級任天堂圖塊、顏色、背景地圖、精靈及 Mode 7 格式。圖塊、地圖項目和顏色的佈局均以任天堂的開發手冊為準，每個小得足以遍歷的輸入空間都已從頭到尾遍歷。

[![CI](https://github.com/gufranco/snes-graphics-python/actions/workflows/ci.yml/badge.svg)](https://github.com/gufranco/snes-graphics-python/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/gufranco/snes-graphics-python)](https://github.com/gufranco/snes-graphics-python/releases)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

**7** 種格式，**165,248** 個案例透過遍歷整個輸入空間確定，**66,432** 個案例與 SuperFamiconv 比對，**11,765** 個真實卡帶數據區域以三種方式讀取，**0** 個失敗，**859** 個測試，**100%** 語句及分支覆蓋率，無依賴套件

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

這 32 個位元組是一個四位元圖塊在視像記憶體中的存放形式。`tiles.decode` 把它們轉換為 64 個顏色編號，逐行排列，最左邊的像素在前。以十六進制列印時，這些數字畫出顏色 1 至 4 的四個圓環。

## 安裝

| 需求 | 版本 |
|:--|:--|
| Python | 3.12 或更新 |
| git | 任何版本 |

```bash
git clone https://github.com/gufranco/snes-graphics-python.git
cd snes-graphics-python
python3 snesgfx/doctor.py
```

本套件只匯入標準程式庫內的模組。本檔案中的範例在儲存庫根目錄執行。

診斷腳本會報告機器狀況，即場解碼每種格式，對一個圖塊做來回轉換，並列出各項窮舉遍歷。它以一行作結。請把它的完整輸出貼到任何錯誤報告中。

```
  11 checks, nothing to report
```

版本發佈遵循[語義化版本](https://semver.org/)，由 semantic-release 根據提交歷史產生。每個版本都會加上標籤，並列於[發佈頁面](https://github.com/gufranco/snes-graphics-python/releases)。

## 介面

本套件每種佈局一個模組，另有一個涵蓋它們的目錄。目錄讓工具只需持有位元組和格式名稱，而無須知道每個模組的呼叫形式。每個模組亦可直接匯入。

| 模組 | 內容 |
|:--|:--|
| [`snesgfx/tiles.py`](snesgfx/tiles.py) | 每像素 2、4 及 8 位元的位元平面圖塊，以及翻轉 |
| [`snesgfx/palette.py`](snesgfx/palette.py) | 十五位元顏色字，以及每種深度可用的調色盤區塊 |
| [`snesgfx/tilemap.py`](snesgfx/tilemap.py) | 背景地圖項目，以及地圖儲存所用的象限 |
| [`snesgfx/oam.py`](snesgfx/oam.py) | 精靈表，包括 512 位元組的低表和 32 位元組的高表 |
| [`snesgfx/mode7.py`](snesgfx/mode7.py) | 以硬件定點格式表示的 Mode 7 矩陣，以及交錯存放的地圖和像素 |
| [`snesgfx/models.py`](snesgfx/models.py) | 目錄 |
| [`snesgfx/errors.py`](snesgfx/errors.py) | 本套件拋出的所有例外 |
| [`snesgfx/doctor.py`](snesgfx/doctor.py) | 診斷腳本 |
| [`snesgfx/environment.py`](snesgfx/environment.py) | 診斷腳本列印的機器檢查 |

### 目錄

| 名稱 | 內容 |
|:--|:--|
| `snesgfx.FORMATS` | 七個 `Format` 記錄，以標準名稱為鍵 |
| `snesgfx.format_named(name)` | 名稱或別名所指的 `Format`。忽略大小寫、空格、連字號和底線。其他名稱會拋出 `UnknownFormat`，並列出那七個名稱 |
| `snesgfx.Format` | 帶有 `name`、`aliases`、`summary`、`decode` 和 `encode` 的記錄 |
| `snesgfx.__version__` | 已安裝的版本 |

`Format.decode` 和 `Format.encode` 接受整個緩衝區。在三種圖塊格式上，它們透過 `tiles.decode_sheet` 和 `tiles.encode_sheet` 讀寫一整張圖塊表。在 `mode7` 上，它們拆分和合併交錯的字。在其餘三種格式上，它們就是該模組自身的 `decode` 和 `encode`。

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

### 圖塊

| 呼叫 | 作用 |
|:--|:--|
| `tiles.decode(data, depth)` | 把一個 `depth` 乘 8 位元組的圖塊轉為 64 個顏色編號，逐行排列 |
| `tiles.encode(pixels, depth)` | 把 64 個顏色編號轉為一個圖塊 |
| `tiles.decode_sheet(data, depth)` | 把連續的圖塊轉為由 64 個數字的列表組成的列表 |
| `tiles.encode_sheet(sheet, depth)` | 把圖塊列表轉回位元組 |
| `tiles.flip(pixels, horizontal=False, vertical=False)` | 一個圖塊的鏡像副本 |
| `tiles.tile_bytes(depth)` | 16、32 或 64 |
| `tiles.depth_of(name)` | 整數或 `tiles.NAMES` 中的名稱所指的深度 |

| 常數 | 值 |
|:--|:--|
| `tiles.DEPTHS` | `(2, 4, 8)` |
| `tiles.TILE_PIXELS`, `tiles.TILE_WIDTH` | 64 和 8 |
| `tiles.PLANE_PAIR_BYTES` | 16，即一對平面所佔的位元組數 |
| `tiles.NAMES` | `2bpp`、`4bpp`、`8bpp`、`4-colour`、`16-colour` 和 `256-colour`，各自對應其深度 |

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

四位元圖塊的頭 16 個位元組可解碼為一個完整的二位元圖塊：它的第三行是 `12333321` 的低兩位。

### 顏色

| 呼叫 | 作用 |
|:--|:--|
| `palette.decode(data)` | 把小端序顏色字轉為 0 至 255 的 `(red, green, blue)` 三元組 |
| `palette.encode(colours)` | 把三元組轉為顏色字。每個通道保留最高五位 |
| `palette.to_rgb(word)`, `palette.to_word(red, green, blue)` | 單一顏色的雙向轉換。字的第 15 位會被忽略 |
| `palette.normalise(data)` | 清除每個字第 15 位後的副本 |
| `palette.block_size(depth)` | 4、16 或 256 種顏色 |
| `palette.block_start(depth, block)` | 區塊第一種顏色的索引 |
| `palette.resolve(table, pixel, depth, block)` | 像素編號經由區塊所指向的顏色 |
| `palette.is_transparent(pixel)` | 顏色編號為 0 時是 True |

| 常數 | 值 |
|:--|:--|
| `palette.COLOURS` | 256 |
| `palette.BYTES_PER_COLOUR` | 2 |
| `palette.WORD_MASK` | `0x7FFF` |
| `palette.CHANNEL_BITS`, `palette.CHANNEL_MASK` | 5 和 `0x1F` |
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

`resolve` 需要深度和區塊，因為單憑像素編號無法確定顏色。區塊 2 中的四位元像素 5 是顏色 37，區塊 7 中的二位元像素 3 是顏色 31。

### 背景地圖

`tilemap.Entry(tile=0, block=0, priority=False, horizontal_flip=False, vertical_flip=False)` 是一個地圖項目。

| 呼叫或屬性 | 作用 |
|:--|:--|
| `Entry.from_word(word)` | 十六位元字所表示的項目 |
| `entry.word` | 項目打包成的字。圖塊大於 1023 或區塊大於 7 時拋出 `OutOfRange` |
| `tilemap.decode(data)`, `tilemap.encode(entries)` | 小端序字的雙向轉換 |
| `tilemap.screen_size(size)` | 螢幕大小設定 0 至 3 以圖塊計的寬度和高度 |
| `tilemap.offset_of(x, y, size)` | 圖塊位置的項目索引，已計入象限。位置會環繞 |
| `tilemap.entry_at(entries, x, y, size)` | 圖塊位置上的項目 |

| 常數 | 值 |
|:--|:--|
| `tilemap.SCREEN_SIZES` | `((32, 32), (64, 32), (32, 64), (64, 64))` |
| `tilemap.QUADRANT_TILES`, `tilemap.QUADRANT_ENTRIES` | 32 和 1024 |
| `tilemap.BYTES_PER_ENTRY` | 2 |
| `tilemap.TILE_MASK` | `0x03FF` |
| `tilemap.BLOCK_SHIFT`, `tilemap.BLOCK_MASK` | 10 和 `0x07` |
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

64 乘 32 地圖的第 32 欄是項目 1024，即第二個象限的第一個項目，而第 31 欄是項目 31。

### 精靈

`oam.Sprite(x=0, y=0, tile=0, block=0, priority=0, table=0, horizontal_flip=False, vertical_flip=False, large=False)` 是一個精靈。

| 呼叫或屬性 | 作用 |
|:--|:--|
| `oam.decode(data)` | 把 544 位元組的表轉為 128 個精靈。`x` 的第 8 位和 `large` 來自高表 |
| `oam.encode(sprites)` | 把剛好 128 個精靈轉為 544 位元組。`x` 達 512、`y` 達 256、`tile` 達 512、`block` 達 8 或 `priority` 達 4 時拋出 `OutOfRange` |
| `sprite.screen_x` | 以螢幕位置表示的 `x`：由 256 起為 `x` 減 512 |
| `sprite.table` | 屬性位元組的第 0 位，亦即 `tile` 的第 8 位。`encode` 從 `tile` 寫入該位 |
| `oam.sizes(setting)` | 物件大小設定 0 至 7 的小尺寸和大尺寸 |
| `oam.size_of(sprite, setting)` | 一個精靈在某個設定下所佔的尺寸 |

| 常數 | 值 |
|:--|:--|
| `oam.SPRITES` | 128 |
| `oam.LOW_ENTRY_BYTES`, `oam.LOW_TABLE_BYTES` | 4 和 512 |
| `oam.HIGH_TABLE_BYTES`, `oam.TABLE_BYTES` | 32 和 544 |
| `oam.SCREEN_WIDTH` | 256 |
| `oam.SIZES` | 八組 `(small, large)` 配對 |

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

精靈 5 的低四個位元組位於偏移 20。它的兩個高位位於位元組 513 的第 2 和第 3 位，該位元組亦存放精靈 4、6 和 7。`x` 為 `0x1F0` 時，位置在左邊緣外 16 像素。

### Mode 7

| 呼叫 | 作用 |
|:--|:--|
| `mode7.Matrix(a, b, c, d)` | 四個矩陣暫存器。每個屬性讀作有符號十六位元值，8.8 定點 |
| `mode7.Field(matrix, centre=(0, 0), scroll=(0, 0))` | 帶有中心點和捲動量的矩陣，兩者各讀作有符號十三位元值 |
| `field.at(x, y)` | 螢幕像素所顯示的場像素。與捲動偏移和與 `y` 的乘積在相加前失去低六位；與 `x` 的乘積則保留 |
| `mode7.signed13(value)`, `mode7.signed16(value)` | 符號擴展 |
| `mode7.wrap(x, y)`, `mode7.outside(x, y)` | 環繞到 1024 乘 1024 場內的位置，以及該位置是否在場外 |
| `mode7.deinterleave(vram)`, `mode7.interleave(names, pixels)` | 把字拆分為地圖位元組和像素位元組，以及把它們合併回去 |
| `mode7.tile(pixels, index)` | 一個圖塊的 64 個像素，每個一位元組 |
| `mode7.name_at(names, x, y)` | 場像素下方的圖塊名稱 |

| 常數 | 值 |
|:--|:--|
| `mode7.FIELD_TILES`, `mode7.TILE_WIDTH`, `mode7.FIELD_PIXELS` | 128、8 和 1024 |
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

完整乘積 48 和 240 加起來是一整個像素，列印出的第二個數字正說明這一點，剪切後的場卻顯示第 0 欄。每個乘積先失去低六位：48 變成 0，240 變成 192，兩者之和小於 256。

### 錯誤

所有例外都定義在 [`snesgfx/errors.py`](snesgfx/errors.py) 中，四個都由 `snesgfx` 匯出。

| 例外 | 拋出時機 |
|:--|:--|
| `Truncated` | 緩衝區長度錯誤：圖塊不是深度每一位對應 8 個位元組，像素列表長度不是 64，圖塊表、顏色或地圖緩衝區不能整除，精靈表不是 544 位元組或 128 個精靈，Mode 7 字的長度為奇數或兩半長度不等，Mode 7 圖塊超出末端 |
| `OutOfRange` | 值超出其欄位範圍：像素對其深度而言過大，通道超出 0 至 255，顏色字超過 16 位元，調色盤區塊超出表格，地圖項目的圖塊或區塊，精靈欄位，螢幕大小或物件大小設定，`palette.block_size` 不認識的深度 |
| `UnknownDepth` | 2、4 和 8 以外的圖塊深度，或 `tiles.depth_of` 不認識的名稱 |
| `UnknownFormat` | `format_named` 不認識的名稱 |

### 診斷腳本

`python3 snesgfx/doctor.py` 不接受參數。它先列印九項機器檢查，再列印十一項套件檢查：Python 版本、套件版本、每種格式一次解碼、一次四位元來回轉換，以及窮舉遍歷列表。十一項套件檢查全部通過時以 0 結束，任何一項失敗時以 1 結束。機器檢查只會列印，不影響結束碼。

## 格式

| 名稱 | 是甚麼 | 別名 |
|:--|:--|:--|
| `2bpp` | 兩個平面，四種顏色，每個圖塊 16 位元組 | `4-colour`, `2bit` |
| `4bpp` | 四個平面，十六種顏色，每個圖塊 32 位元組 | `16-colour`, `4bit` |
| `8bpp` | 八個平面，256 種顏色，每個圖塊 64 位元組 | `256-colour`, `8bit` |
| `mode7` | 旋轉背景：每像素一位元組，地圖和像素逐字交錯 | `mode-7`, `m7` |
| `palette` | 十五位元顏色，每種兩個位元組，藍色在最高位 | `cgram`, `colours`, `colors` |
| `tilemap` | 背景地圖，每個項目十六位元，按象限儲存 | `map`, `screen`, `bg` |
| `oam` | 精靈表，每個精靈四個位元組，另加第二個表中的兩位 | `sprites`, `objects`, `obj` |

沒有六位元深度，因為沒有任何背景模式使用它。這裡沒有任何程式碼讀寫圖像檔案，因此本套件無須依賴套件。

## 容易弄錯的地方

**圖塊並非以像素形式儲存。** 顏色編號的每一位各自存放在一個平面中，平面兩兩成對並逐行交錯。四位元圖塊是兩組這樣的配對前後相接，所以它的頭 16 個位元組就是一個完整的二位元圖塊。

**最左邊的像素來自最高位。** 這與位元編號的順序相反。

**五位元顏色不能靠移位來擴展。** 把 31 左移三位得到 248，於是白色會解碼成 `(248, 248, 248)`。把該值的最高幾位重複填入空出的位會得到 255，而且全部 32,768 種顏色都能完整來回轉換。

**背景地圖不是一個矩形。** 64 個圖塊寬的地圖是兩個 32 乘 32 的區塊前後相接儲存，所以第 32 欄是項目 1024 而非項目 32。弄錯的話，正確的圖塊會畫在錯誤的象限。

**精靈的數據分佈在兩處。** 水平位置的第 8 位和尺寸旗標存放在 32 位元組的高表中，每個位元組容納四個精靈。這第九位相當於符號位：`x` 為 `0x1F0` 時位置在左邊緣外 16 像素。

**Mode 7 會丟棄大部分乘積的低六位。** 與捲動偏移和與螢幕行的乘積在相加前被截斷，所以小於 64 的乘積沒有任何貢獻。與螢幕欄的乘積保留所有位。`field.at` 兩者都照做。

## 是否正確

有三幅圖以手冊為準：圖塊佈局、地圖項目和顏色字。[`conformance/hardware.json`](conformance/hardware.json) 記錄每一幅圖及其原句、手冊頁碼和檔案頁碼，[`conformance/hardware.test.py`](conformance/hardware.test.py) 則把它們與套件中的常數比較。手冊存在於磁碟上時，`python3 -m conformance.quotes` 會在手冊中找出全部 9 句引文。

完整的來回轉換只能證明解碼器和編碼器彼此一致。在記錄和程式碼中同時對調兩個翻轉位，仍能通過每次遍歷和每項記錄檢查，卻會把每張地圖都解碼錯。下面兩項檢查依賴並非由本儲存庫編寫的東西：對同一批圖的第二種解讀，以及卡帶位元組。

### 遍歷每個案例

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

| 遍歷 | 案例數 | 涵蓋範圍 |
|:--|--:|:--|
| `tiles-2bpp` | 65,536 | 每對二位元圖塊行，解碼後再重新編碼 |
| `tiles-planes` | 896 | 每種深度的每個平面，對照 64 個像素中的每一個 |
| `palette` | 32,768 | 每個顏色字，擴展後再收窄回去 |
| `tilemap` | 65,536 | 每個地圖項目字，拆分為欄位後再打包回去 |
| `oam-high` | 512 | 128 個精靈各自的兩個高位，且不干擾任何相鄰位 |

四位元圖塊的狀態太多，無法遍歷。平面遍歷代替它：每個平面必須到達每個像素中屬於它自己的那一位，而且不觸及其他位。測試會故意破壞每種格式，確認遍歷能捕捉到。

### 對照第二種解讀

參考實現是 [SuperFamiconv](https://github.com/Optiroc/SuperFamiconv)，以提交固定在 [`conformance/pinned.json`](conformance/pinned.json) 中。它不包含在本儲存庫內。`conformance.build` 擷取固定的提交，抽出三個函式，並以 `g++` 把它們與 [`conformance/ref/driver.cpp`](conformance/ref/driver.cpp) 一起編譯。

```bash
python3 -m conformance.build
python3 -m conformance.against_reference
```

```
  66,432 cases compared against the reference, none disagreed
```

| 圖 | 案例數 | 案例選取方式 |
|:--|--:|:--|
| 位元平面佈局 | 896 | 在每種深度下，每次只設定一位 |
| 顏色打包 | 32,768 | 每種五位元的紅、綠、藍 |
| 地圖項目 | 32,768 | 每個圖塊、區塊及翻轉組合 |

本套件自行把八位元通道收窄，而參考實現收到的是主機所儲存的五位。

### 對照卡帶

犯同一錯誤的兩個讀取器會互相一致。卡帶位元組能區分正確的解讀和看似合理的解讀，因為以正確分組讀出的圖像，其相鄰像素會相符。[`conformance/against_cartridges.py`](conformance/against_cartridges.py) 以每像素四位元、三種方式讀取相同區域，並統計在每個區域中哪種解讀找到最多相等的相鄰像素。連續平面是同期其他遊戲機儲存圖塊的方式，每位元組兩個像素則是存放十六種顏色最直接的方式。

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

區域為 2,048 位元組，從偏移 `0x8000` 起每 32 KB 取一個，直到 2 MB，按位置選取，只有在不同位元組少於 8 種時才跳過。統計量只看相鄰像素是否相等，從不看它們的顏色，所以對調平面配對的得分相同。這種對調只會改變顏色的編號。這裡不包含任何卡帶：該次執行在一部機器上的 7,578 個映像檔中讀取了 300 個，以種子 11 抽取，[`conformance/cartridges.json`](conformance/cartridges.json) 記錄了計數和語料庫摘要。未設定該變數時，執行器會先在檢出目錄內的 `cartridges/` 中尋找，再到旁邊的 `snes-roms` 目錄中尋找。

### 檢查工具

| 指令 | 參數 | 結束碼 |
|:--|:--|:--|
| `python3 -m conformance.exhaustive` | `--only NAME` | 0 所有遍歷無誤，1 有遍歷失敗，2 未知名稱或參數 |
| `python3 -m conformance.build` | `--sources DIR`, `--output PATH`, `--pinned FILE`, `--driver-source FILE` | 0 已建置，1 編譯器失敗，2 參數錯誤或擷取失敗 |
| `python3 -m conformance.against_reference` | 無 | 0 沒有分歧，或驅動程式未建置並如此說明，1 有分歧 |
| `python3 -m conformance.against_cartridges` | 環境變數 `SNES_CARTRIDGE_DIR` | 0 高於下限，1 等於或低於下限，2 沒有可檢查的內容 |
| `python3 -m conformance.quotes` | 無 | 0 每句引文都已找到或磁碟上沒有手冊，1 有引文或出處不成立 |
| `python3 -m conformance.documents` | `--check`, `--only SUBSTRING` | 0 每份文件都已驗證，1 拒絕、無匹配或參數錯誤 |
| `python3 -m conformance.speed` | 無 | 0 每秒至少 10,000 次四位元解碼，1 低於此數 |
| `python3 -m conformance.links` | 無 | 0，或本檔案中的位址回應 404 或 410 時為 1 |
| `python3 -m conformance.package WHEEL` | 一個已建置的 wheel | 0 包含每個模組且沒有附帶測試，1 有問題或沒有該檔案，2 沒有參數 |

手冊未能確定的事項見 [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md)，每個條目亦連同其狀態和嚴重程度收錄於 [`conformance/divergences.json`](conformance/divergences.json)。

## 參與開發

| 需要 | 位置 |
|:--|:--|
| 每項關卡檢查及其執行順序 | [CONTRIBUTING.md](CONTRIBUTING.md) |
| 給程式編寫代理的相同資料 | [AGENTS.md](AGENTS.md) |
| 本儲存庫與家族其他成員共用的標準 | [FAMILY.md](FAMILY.md) |
| 錯誤報告 | [GitHub Issues](https://github.com/gufranco/snes-graphics-python/issues) |
| 安全問題報告 | [SECURITY.md](SECURITY.md) |

```bash
uvx ruff@0.16.3 format --check .
uvx ruff@0.16.3 check .
uvx --python 3.12 mypy==1.14.1
pnpm install --frozen-lockfile && pnpm run format:check
python3 -m coverage erase
for file in $(find snesgfx conformance -name '*.test.py' | sort); do
  python3 -m coverage run -a "$file"
done
python3 -m coverage report
```

每個模組旁邊都有一個以其命名的測試檔案，每個都可單獨執行，例如 `python3 snesgfx/tiles.test.py`。覆蓋率是硬性關卡檢查，要求 100% 語句及分支覆蓋。

## 參考資料

- *SNES Development Manual, Book I*，Nintendo of America Inc.，無日期。附錄 A，第 A-10、A-12 及 A-17 頁。共 240 頁，21,022,582 位元組，SHA-256 `f1405241000046abba7849376d2ec53cf85f1ad2e9950d69a7c2cf1f3ff6b791`。它不可再分發，亦不在本儲存庫中。`python3 -m conformance.documents` 從 https://archive.org/download/SNESDevManual/book1_text.pdf 把它下載到 git 忽略的 `docs/manufacturer/`，並拒絕任何其他檔案。`python3 -m conformance.documents --check` 驗證已存在的副本。
- SuperFamiconv，作者 David Lindecrantz，MIT 授權，提交 `d903daf1b74c9ec6db7949fe62af2f0b58bdc23b`，https://github.com/Optiroc/SuperFamiconv ，用於對位元平面、顏色和地圖項目的圖作獨立解讀。`unpack_native_tile`、`pack_native_color` 和 `pack_native_mapentry` 於建置時編譯，從不提交。

## 引用本專案

[CITATION.cff](CITATION.cff) 會在每次發佈時由標記套件版本的腳本更新。

## 授權

MIT。見 [LICENSE](LICENSE)。
