[English](README.md) | 日本語 | [简体中文](README.zh-Hans.md) | [繁體中文（香港）](README.zh-HK.md)

# SNESグラフィックフォーマット

Super Nintendoのタイル、カラー、背景マップ、スプライト、Mode 7の各フォーマットをPythonで実装したものです。タイル、マップエントリ、カラーのレイアウトはNintendoの開発マニュアルに合わせてあり、端から端まで走査できるほど小さな入力空間はすべて走査しています。

[![CI](https://github.com/gufranco/snes-graphics-python/actions/workflows/ci.yml/badge.svg)](https://github.com/gufranco/snes-graphics-python/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/gufranco/snes-graphics-python)](https://github.com/gufranco/snes-graphics-python/releases)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

**7**種類のフォーマット、入力空間全体の走査で確定した**165,248**ケース、SuperFamiconvと比較した**66,432**ケース、3通りに読んだ実カートリッジデータの**11,765**領域、失敗**0**件、テスト**859**件、ステートメントとブランチのカバレッジ**100%**、依存関係なし

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

この32バイトは、ビデオメモリに置かれた形の4ビットタイル1枚です。`tiles.decode`はこれを64個のカラー番号に変換します。順序は行ごとで、各行は左端のピクセルから始まります。16進数で表示すると、これらの番号はカラー1から4までの4重の輪を描きます。

## インストール

| 要件 | バージョン |
|:--|:--|
| Python | 3.12以降 |
| git | 任意 |

```bash
git clone https://github.com/gufranco/snes-graphics-python.git
cd snes-graphics-python
python3 snesgfx/doctor.py
```

このパッケージは標準ライブラリ以外を何もインポートしません。このファイルの例はリポジトリのルートから実行します。

ドクターはマシンの情報を報告し、その場ですべてのフォーマットをデコードし、タイル1枚の往復変換を行い、網羅的な走査の一覧を表示します。最後は1行で終わります。バグ報告には出力全体を貼り付けてください。

```
  11 checks, nothing to report
```

リリースは[Semantic Versioning](https://semver.org/)に従い、semantic-releaseがコミット履歴から作成します。すべてのリリースにはタグが付き、[リリースページ](https://github.com/gufranco/snes-graphics-python/releases)に掲載されます。

## インターフェース

このパッケージはレイアウトごとに1つのモジュールを持ち、それらをまとめるカタログを1つ持ちます。カタログを使うと、ツールは各モジュールの呼び出し形式を知らなくても、バイト列とフォーマット名だけで扱えます。各モジュールは直接インポートすることもできます。

| モジュール | 内容 |
|:--|:--|
| [`snesgfx/tiles.py`](snesgfx/tiles.py) | 1ピクセルあたり2、4、8ビットのビットプレーンタイルと反転 |
| [`snesgfx/palette.py`](snesgfx/palette.py) | 15ビットのカラーワードと、各深度が参照するパレットブロック |
| [`snesgfx/tilemap.py`](snesgfx/tilemap.py) | 背景マップのエントリと、マップを格納する象限 |
| [`snesgfx/oam.py`](snesgfx/oam.py) | スプライトテーブル。512バイトの下位テーブルと32バイトの上位テーブルの両方 |
| [`snesgfx/mode7.py`](snesgfx/mode7.py) | ハードウェアの固定小数点によるMode 7の行列と、インターリーブされたマップとピクセル |
| [`snesgfx/models.py`](snesgfx/models.py) | カタログ |
| [`snesgfx/errors.py`](snesgfx/errors.py) | パッケージが送出するすべての例外 |
| [`snesgfx/doctor.py`](snesgfx/doctor.py) | ドクター |
| [`snesgfx/environment.py`](snesgfx/environment.py) | ドクターが表示するマシンのチェック |

### カタログ

| 名前 | 内容 |
|:--|:--|
| `snesgfx.FORMATS` | 7つの`Format`レコード。正式名をキーとします |
| `snesgfx.format_named(name)` | 名前または別名が指す`Format`。大文字と小文字、空白、ハイフン、アンダースコアは無視します。それ以外の名前には`UnknownFormat`を送出し、7つの名前を列挙します |
| `snesgfx.Format` | `name`、`aliases`、`summary`、`decode`、`encode`を持つレコード |
| `snesgfx.__version__` | インストールされているバージョン |

`Format.decode`と`Format.encode`はバッファ全体を受け取ります。3つのタイルフォーマットでは、`tiles.decode_sheet`と`tiles.encode_sheet`を通じてタイルのシートを読み書きします。`mode7`では、インターリーブされたワードを分割・結合します。残りの3つでは、そのモジュール自身の`decode`と`encode`です。

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

### タイル

| 呼び出し | 効果 |
|:--|:--|
| `tiles.decode(data, depth)` | `depth`の8倍のバイト数のタイル1枚を、行ごとに64個のカラー番号へ変換 |
| `tiles.encode(pixels, depth)` | 64個のカラー番号をタイル1枚へ変換 |
| `tiles.decode_sheet(data, depth)` | 連続したタイルを、64個の番号のリストのリストへ変換 |
| `tiles.encode_sheet(sheet, depth)` | タイルのリストをバイト列へ戻す |
| `tiles.flip(pixels, horizontal=False, vertical=False)` | タイル1枚の反転したコピー |
| `tiles.tile_bytes(depth)` | 16、32、64のいずれか |
| `tiles.depth_of(name)` | 整数または`tiles.NAMES`にある名前が指す深度 |

| 定数 | 値 |
|:--|:--|
| `tiles.DEPTHS` | `(2, 4, 8)` |
| `tiles.TILE_PIXELS`, `tiles.TILE_WIDTH` | 64と8 |
| `tiles.PLANE_PAIR_BYTES` | 16。プレーン1組が占めるバイト数 |
| `tiles.NAMES` | `2bpp`、`4bpp`、`8bpp`、`4-colour`、`16-colour`、`256-colour`。それぞれ対応する深度に対応付けられます |

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

4ビットタイルの先頭16バイトは、それだけで完全な2ビットタイルとしてデコードされます。その3行目は`12333321`の下位2ビットです。

### カラー

| 呼び出し | 効果 |
|:--|:--|
| `palette.decode(data)` | リトルエンディアンのカラーワードを、0から255の`(red, green, blue)`の3つ組へ変換 |
| `palette.encode(colours)` | 3つ組をカラーワードへ変換。各チャンネルは上位5ビットを保持します |
| `palette.to_rgb(word)`, `palette.to_word(red, green, blue)` | 1色をそれぞれの方向へ変換。ワードのビット15は無視します |
| `palette.normalise(data)` | すべてのワードのビット15をクリアしたコピー |
| `palette.block_size(depth)` | 4、16、256色のいずれか |
| `palette.block_start(depth, block)` | ブロックの最初の色のインデックス |
| `palette.resolve(table, pixel, depth, block)` | ピクセル番号がブロックを通じて参照する色 |
| `palette.is_transparent(pixel)` | カラー番号0ならTrue |

| 定数 | 値 |
|:--|:--|
| `palette.COLOURS` | 256 |
| `palette.BYTES_PER_COLOUR` | 2 |
| `palette.WORD_MASK` | `0x7FFF` |
| `palette.CHANNEL_BITS`, `palette.CHANNEL_MASK` | 5と`0x1F` |
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

ピクセル番号だけでは色が決まらないため、`resolve`は深度とブロックを受け取ります。ブロック2の4ビットピクセル5はカラー37で、ブロック7の2ビットピクセル3はカラー31です。

### 背景マップ

`tilemap.Entry(tile=0, block=0, priority=False, horizontal_flip=False, vertical_flip=False)`はマップエントリ1つです。

| 呼び出しまたは属性 | 効果 |
|:--|:--|
| `Entry.from_word(word)` | 16ビットワードが表すエントリ |
| `entry.word` | エントリをパックしたワード。タイルが1023を超えるか、ブロックが7を超えると`OutOfRange`を送出します |
| `tilemap.decode(data)`, `tilemap.encode(entries)` | リトルエンディアンのワードをそれぞれの方向へ変換 |
| `tilemap.screen_size(size)` | 画面サイズ設定0から3の、タイル単位の幅と高さ |
| `tilemap.offset_of(x, y, size)` | タイル位置のエントリインデックス。象限も考慮します。位置は折り返します |
| `tilemap.entry_at(entries, x, y, size)` | タイル位置にあるエントリ |

| 定数 | 値 |
|:--|:--|
| `tilemap.SCREEN_SIZES` | `((32, 32), (64, 32), (32, 64), (64, 64))` |
| `tilemap.QUADRANT_TILES`, `tilemap.QUADRANT_ENTRIES` | 32と1024 |
| `tilemap.BYTES_PER_ENTRY` | 2 |
| `tilemap.TILE_MASK` | `0x03FF` |
| `tilemap.BLOCK_SHIFT`, `tilemap.BLOCK_MASK` | 10と`0x07` |
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

64×32のマップの列32はエントリ1024で、2番目の象限の最初のエントリです。一方、列31はエントリ31です。

### スプライト

`oam.Sprite(x=0, y=0, tile=0, block=0, priority=0, table=0, horizontal_flip=False, vertical_flip=False, large=False)`はスプライト1つです。

| 呼び出しまたは属性 | 効果 |
|:--|:--|
| `oam.decode(data)` | 544バイトのテーブルを128個のスプライトへ変換。`x`のビット8と`large`は上位テーブルから取ります |
| `oam.encode(sprites)` | ちょうど128個のスプライトを544バイトへ変換。`x`が512以上、`y`が256以上、`tile`が512以上、`block`が8以上、`priority`が4以上のときは`OutOfRange`を送出します |
| `sprite.screen_x` | 画面上の位置としての`x`。256以上では`x`から512を引いた値 |
| `sprite.table` | 属性バイトのビット0。これは`tile`のビット8でもあります。`encode`はこのビットを`tile`から書き込みます |
| `oam.sizes(setting)` | オブジェクトサイズ設定0から7の小サイズと大サイズ |
| `oam.size_of(sprite, setting)` | ある設定のもとでスプライト1つが取るサイズ |

| 定数 | 値 |
|:--|:--|
| `oam.SPRITES` | 128 |
| `oam.LOW_ENTRY_BYTES`, `oam.LOW_TABLE_BYTES` | 4と512 |
| `oam.HIGH_TABLE_BYTES`, `oam.TABLE_BYTES` | 32と544 |
| `oam.SCREEN_WIDTH` | 256 |
| `oam.SIZES` | 8組の`(small, large)` |

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

スプライト5の下位4バイトはオフセット20にあります。上位の2ビットはバイト513のビット2と3にあり、このバイトにはスプライト4、6、7も入っています。`0x1F0`の`x`は左端から16ピクセル外側です。

### Mode 7

| 呼び出し | 効果 |
|:--|:--|
| `mode7.Matrix(a, b, c, d)` | 4つの行列レジスタ。各属性は符号付き16ビット値、8.8固定小数点として読みます |
| `mode7.Field(matrix, centre=(0, 0), scroll=(0, 0))` | 中心とスクロールを伴う行列。中心とスクロールはそれぞれ符号付き13ビット値として読みます |
| `field.at(x, y)` | 画面ピクセルが表示するフィールドピクセル。スクロールオフセットとの積と`y`との積は、加算の前に下位6ビットを失います。`x`との積は下位6ビットを保持します |
| `mode7.signed13(value)`, `mode7.signed16(value)` | 符号拡張 |
| `mode7.wrap(x, y)`, `mode7.outside(x, y)` | 1024×1024のフィールド内に折り返した位置と、その位置がフィールドの外にあるかどうか |
| `mode7.deinterleave(vram)`, `mode7.interleave(names, pixels)` | ワードをマップのバイトとピクセルのバイトに分割し、また結合します |
| `mode7.tile(pixels, index)` | タイル1枚の64ピクセル。1ピクセル1バイト |
| `mode7.name_at(names, x, y)` | フィールドピクセルの下にあるタイル名 |

| 定数 | 値 |
|:--|:--|
| `mode7.FIELD_TILES`, `mode7.TILE_WIDTH`, `mode7.FIELD_PIXELS` | 128、8、1024 |
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

完全な積である48と240を足すとちょうど1ピクセルになり、2番目に表示される数値がそれを示していますが、シアーをかけたフィールドは列0を表示します。各積は先に下位6ビットを失うため、48は0に、240は192になり、その合計は256に届きません。

### エラー

すべての例外は[`snesgfx/errors.py`](snesgfx/errors.py)にあり、4つとも`snesgfx`からエクスポートされています。

| 例外 | 送出される条件 |
|:--|:--|
| `Truncated` | バッファの長さが正しくない場合。深度1ビットあたり8バイトでないタイル、長さが64でないピクセルリスト、割り切れないシート、カラー、マップのバッファ、544バイトまたは128スプライトでないスプライトテーブル、奇数長のMode 7ワードまたは長さの異なる半分、末尾を越えたMode 7タイル |
| `OutOfRange` | 値がそのフィールドに収まらない場合。深度に対して大きすぎるピクセル、0から255の範囲外のチャンネル、16ビットを超えるカラーワード、テーブルを越えたパレットブロック、マップエントリのタイルまたはブロック、スプライトのフィールド、画面サイズ設定またはオブジェクトサイズ設定、`palette.block_size`が知らない深度 |
| `UnknownDepth` | 2、4、8以外のタイル深度、または`tiles.depth_of`が知らない名前 |
| `UnknownFormat` | `format_named`が知らない名前 |

### ドクター

`python3 snesgfx/doctor.py`は引数を取りません。9つのマシンチェックを表示し、続いて11のパッケージチェックを表示します。パッケージチェックは、Pythonのバージョン、パッケージのバージョン、フォーマットごとに1回のデコード、4ビットの往復変換、網羅的な走査の一覧です。11のパッケージチェックがすべて通れば0で、いずれかが失敗すれば1で終了します。マシンチェックは表示されるだけで、終了コードには影響しません。

## フォーマット

| 名前 | 内容 | 別名 |
|:--|:--|:--|
| `2bpp` | 2プレーン、4色、1タイル16バイト | `4-colour`, `2bit` |
| `4bpp` | 4プレーン、16色、1タイル32バイト | `16-colour`, `4bit` |
| `8bpp` | 8プレーン、256色、1タイル64バイト | `256-colour`, `8bit` |
| `mode7` | 回転する背景。1ピクセル1バイトで、マップとピクセルがワード単位でインターリーブされます | `mode-7`, `m7` |
| `palette` | 15ビットカラー。1色2バイトで、青が最上位です | `cgram`, `colours`, `colors` |
| `tilemap` | 背景マップ。1エントリ16ビットで、象限ごとに格納されます | `map`, `screen`, `bg` |
| `oam` | スプライトテーブル。1スプライト4バイトに加え、2つ目のテーブルに2ビット | `sprites`, `objects`, `obj` |

6ビットの深度はありません。その深度を持つ背景モードがないためです。ここには画像ファイルを読み書きするものは何もなく、そのためパッケージは依存関係を持ちません。

## 間違えやすい点

**タイルはピクセルとして格納されていません**。カラー番号の各ビットはそれぞれ専用のプレーンにあり、プレーンは2枚ずつ組になって行ごとにインターリーブされます。4ビットタイルはこの組が2つ続いたものなので、先頭16バイトはそれだけで完全な2ビットタイルです。

**左端のピクセルは最上位ビットから取ります**。これはビットに番号が振られている順序とは逆です。

**5ビットカラーはシフトでは正しく広がりません**。31を3ビット左にシフトすると248になるため、白は`(248, 248, 248)`としてデコードされます。値の上位ビットを空いたビットに繰り返し入れると255になり、32,768色すべてが往復変換で保たれます。

**背景マップは長方形ではありません**。幅64タイルのマップは32×32のブロック2つを続けて格納したものなので、列32はエントリ32ではなくエントリ1024です。これを間違えると、正しいタイルが間違った象限に描かれます。

**スプライトのデータは2か所にあります**。水平位置のビット8とサイズフラグは32バイトの上位テーブルにあり、1バイトに4スプライト分が入っています。この9番目のビットは符号として働きます。`0x1F0`の`x`は左端から16ピクセル外側です。

**Mode 7はほとんどの積の下位6ビットを捨てます**。スクロールオフセットとの積と画面の行との積は、加算の前に切り捨てられるため、64未満の値は何も寄与しません。画面の列との積はすべてのビットを保持します。`field.at`はこの両方を行います。

## 正しいか

マニュアルに照らしているのは3つの図表、タイルレイアウト、マップエントリ、カラーワードです。[`conformance/hardware.json`](conformance/hardware.json)はそれぞれについて、該当する文、マニュアルのページ、ファイルのページを保持し、[`conformance/hardware.test.py`](conformance/hardware.test.py)はそれらをパッケージの定数と比較します。マニュアルがディスク上にあれば、`python3 -m conformance.quotes`は引用した9つの文すべてをマニュアル内で見つけます。

往復変換が完全に通っても、デコーダとエンコーダが一致していることしか示せません。レコードとコードの両方で2つの反転ビットを入れ替えると、すべての走査とすべてのレコードチェックに通りながら、すべてのマップを誤ってデコードします。以下の2つのチェックは、このリポジトリが書いたものではないものに基づいています。同じ図表の2つ目の読み方と、カートリッジのバイト列です。

### すべてのケースを走査

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

| 走査 | ケース数 | 対象 |
|:--|--:|:--|
| `tiles-2bpp` | 65,536 | 2ビットタイルのすべての行の組を、デコードして再エンコード |
| `tiles-planes` | 896 | すべての深度のすべてのプレーンを、64ピクセルそれぞれに対して |
| `palette` | 32,768 | すべてのカラーワードを、広げてから狭め直す |
| `tilemap` | 65,536 | すべてのマップエントリワードを、フィールドに分割してパックし直す |
| `oam-high` | 512 | 128スプライトそれぞれの上位2ビットを、隣接するスプライトを乱さずに |

4ビットタイルは状態が多すぎて走査できません。代わりにプレーンの走査を使います。各プレーンは、すべてのピクセルの自分のビットにだけ届き、それ以外には届いてはなりません。テストは各フォーマットを意図的に壊し、走査がそれを検出することを確認します。

### 2つ目の読み方との比較

参照実装は[SuperFamiconv](https://github.com/Optiroc/SuperFamiconv)で、[`conformance/pinned.json`](conformance/pinned.json)でコミットを固定しています。このリポジトリには含めていません。`conformance.build`は固定したコミットを取得し、3つの関数を取り出して、[`conformance/ref/driver.cpp`](conformance/ref/driver.cpp)の背後で`g++`によりコンパイルします。

```bash
python3 -m conformance.build
python3 -m conformance.against_reference
```

```
  66,432 cases compared against the reference, none disagreed
```

| 図表 | ケース数 | ケースの選び方 |
|:--|--:|:--|
| ビットプレーンのレイアウト | 896 | 各深度で、1度に1ビットだけを立てる |
| カラーのパッキング | 32,768 | 5ビットの赤、緑、青のすべて |
| マップエントリ | 32,768 | すべてのタイル、ブロック、反転の組 |

このパッケージは8ビットのチャンネルを自分で狭め、参照実装にはコンソールが格納する5ビットを渡します。

### カートリッジとの比較

同じ間違いをする2つの読み手は一致してしまいます。カートリッジのバイト列は、正しい読み方ともっともらしい読み方を区別します。正しいまとまりで読んだ絵は、隣接するピクセルが一致するからです。[`conformance/against_cartridges.py`](conformance/against_cartridges.py)は同じ領域を1ピクセル4ビットで3通りに読み、各領域でどの読み方が等しい隣接ピクセルを最も多く見つけるかを数えます。連続したプレーンは同時代の他のコンソールがタイルを格納していた方法で、1バイトに2ピクセルは16色を保持する最も単純な方法です。

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

領域はオフセット`0x8000`から2 MBまで32 KBごとに取った2,048バイトで、位置で選び、異なるバイトが8種類未満の場合にだけスキップします。この統計は隣接ピクセルが等しいかどうかだけを見て、その色は見ないため、プレーンの組を入れ替えても同じスコアになります。その入れ替えは色の名前を付け替えるだけです。カートリッジは含めていません。この実行では1台のマシン上の7,578個のイメージのうち300個をシード11で抽出して読み、[`conformance/cartridges.json`](conformance/cartridges.json)がその件数とコーパスのダイジェストを記録しています。環境変数がない場合、ランナーはチェックアウト内の`cartridges/`を探し、次にその隣の`snes-roms`ディレクトリを探します。

### チェック用ツール

| コマンド | 引数 | 終了コード |
|:--|:--|:--|
| `python3 -m conformance.exhaustive` | `--only NAME` | 0はすべての走査が正常、1は走査が失敗、2は不明な名前または引数 |
| `python3 -m conformance.build` | `--sources DIR`, `--output PATH`, `--pinned FILE`, `--driver-source FILE` | 0はビルド成功、1はコンパイラの失敗、2は不正な引数または取得の失敗 |
| `python3 -m conformance.against_reference` | なし | 0は不一致なし、またはドライバが未ビルドでその旨を表示、1は不一致あり |
| `python3 -m conformance.against_cartridges` | 環境変数の`SNES_CARTRIDGE_DIR` | 0は下限を上回った、1は下限以下、2はチェック対象なし |
| `python3 -m conformance.quotes` | なし | 0はすべての引用を発見、またはディスク上にマニュアルなし、1は成り立たない引用または出典 |
| `python3 -m conformance.documents` | `--check`, `--only SUBSTRING` | 0はすべての文書を検証済み、1は拒否、一致なし、または不正な引数 |
| `python3 -m conformance.speed` | なし | 0は毎秒10,000回以上の4ビットデコード、1はそれ未満 |
| `python3 -m conformance.links` | なし | 0、またはこのファイル内のアドレスが404か410を返したときは1 |
| `python3 -m conformance.package WHEEL` | ビルド済みのwheel | 0はすべてのモジュールを含みテストを含まない、1は不具合またはファイルなし、2は引数なし |

マニュアルで決まらない点は[OPEN-QUESTIONS.md](OPEN-QUESTIONS.md)にあり、各項目は状態と重大度とともに[`conformance/divergences.json`](conformance/divergences.json)にも載っています。

## 開発に参加する

| 必要なもの | 場所 |
|:--|:--|
| すべてのゲートと実行順序 | [CONTRIBUTING.md](CONTRIBUTING.md) |
| コーディングエージェント向けの同じ内容 | [AGENTS.md](AGENTS.md) |
| このリポジトリがファミリーの他のリポジトリと共有する標準 | [FAMILY.md](FAMILY.md) |
| バグ報告 | [GitHub Issues](https://github.com/gufranco/snes-graphics-python/issues) |
| セキュリティ報告 | [SECURITY.md](SECURITY.md) |

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

各モジュールには、そのモジュールにちなんだ名前のテストファイルが隣にあり、`python3 snesgfx/tiles.test.py`のようにそれぞれ単独で実行できます。カバレッジはステートメントとブランチで100%を必須のゲートとしています。

## 参考文献

- *SNES Development Manual, Book I*、Nintendo of America Inc.、日付なし。Appendix A、A-10、A-12、A-17ページ。240ページ、21,022,582バイト、SHA-256 `f1405241000046abba7849376d2ec53cf85f1ad2e9950d69a7c2cf1f3ff6b791`。再配布できないため、このリポジトリには含まれていません。`python3 -m conformance.documents`はこれを https://archive.org/download/SNESDevManual/book1_text.pdf から、gitが無視する`docs/manufacturer/`にダウンロードし、それ以外のファイルは拒否します。`python3 -m conformance.documents --check`は既にあるコピーを検証します。
- David LindecrantzによるSuperFamiconv、MIT、コミット`d903daf1b74c9ec6db7949fe62af2f0b58bdc23b`、https://github.com/Optiroc/SuperFamiconv 。ビットプレーン、カラー、マップエントリの図表を独立に読むために使います。`unpack_native_tile`、`pack_native_color`、`pack_native_mapentry`はビルド時にコンパイルされ、コミットされることはありません。

## 引用

[CITATION.cff](CITATION.cff)は、パッケージのバージョンを書き込むスクリプトによってリリースごとに更新されます。

## ライセンス

MIT。[LICENSE](LICENSE)を参照してください。
