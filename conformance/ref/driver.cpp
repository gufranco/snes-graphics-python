// A harness around somebody else's decoder, so this package can be held to it.
//
// The three functions this compiles are not written here. They are lifted, at a
// pinned commit, out of a converter whose whole job is these formats, and they
// are the only independent reading of Nintendo's figures this package has.
//
// Everything else in this file exists to give those functions something to run
// against: the handful of types they name, and a line protocol on stdin so a
// Python process can ask them what a byte means.
//
// The types below are the smallest thing that satisfies the lifted code. They
// are not the converter's own: reproducing its headers would be carrying
// somebody else's work rather than calling it.

#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <stdexcept>
#include <string>
#include <vector>

typedef std::vector<uint8_t> byte_vec_t;
typedef std::vector<uint8_t> index_vec_t;
typedef uint32_t rgba_t;

// Every mode the lifted code names, so its switch statements compile. Only
// `snes` is ever passed in. The rest are here because a switch that does not
// handle a value the enum declares is a warning somewhere, and because taking
// only the SNES arm would mean editing somebody else's function rather than
// calling it.
enum class Mode { none, snes, snes_mode7, gb, gbc, gg, sms, ws, wsc, wsc_packed,
                  pce, pce_sprite, gba, gba_affine, md, ngp, ngpc };

struct Mapentry {
  int tile_index = 0;
  int palette_index = 0;
  bool flip_h = false;
  bool flip_v = false;
};

namespace sfc {
inline std::string mode(Mode) { return "snes"; }
}

namespace fmt {
template <typename... Args> inline std::string format(const char *what, Args...) {
  return std::string(what);
}
}

#include "bodies.inc"

// One line in, one line out. The verbs are the three questions worth asking:
// what pixels are in these bytes, what bytes hold this colour, and what bytes
// hold this map entry.
int main(void) {
  char line[512];

  while (fgets(line, sizeof(line), stdin)) {
    char verb[16];
    if (sscanf(line, "%15s", verb) < 1) continue;

    if (!strcmp(verb, "tile")) {
      unsigned bpp = 0;
      char hex[256];
      if (sscanf(line, "%*s %u %255s", &bpp, hex) < 2) continue;
      byte_vec_t data;
      for (size_t at = 0; hex[at] && hex[at + 1]; at += 2) {
        char pair[3] = {hex[at], hex[at + 1], 0};
        data.push_back((uint8_t)strtoul(pair, nullptr, 16));
      }
      index_vec_t held = unpack_native_tile(data, Mode::snes, bpp, 8, 8);
      for (size_t at = 0; at < held.size(); at++) printf("%02X", held[at]);
      printf("\n");

    } else if (!strcmp(verb, "colour")) {
      unsigned long rgba = 0;
      if (sscanf(line, "%*s %lu", &rgba) < 1) continue;
      byte_vec_t held = pack_native_color((rgba_t)rgba, Mode::snes);
      for (size_t at = 0; at < held.size(); at++) printf("%02X", held[at]);
      printf("\n");

    } else if (!strcmp(verb, "entry")) {
      int tile = 0, palette = 0, flip_h = 0, flip_v = 0;
      if (sscanf(line, "%*s %d %d %d %d", &tile, &palette, &flip_h, &flip_v) < 4) continue;
      Mapentry entry;
      entry.tile_index = tile;
      entry.palette_index = palette;
      entry.flip_h = flip_h != 0;
      entry.flip_v = flip_v != 0;
      byte_vec_t held = pack_native_mapentry(entry, Mode::snes);
      for (size_t at = 0; at < held.size(); at++) printf("%02X", held[at]);
      printf("\n");
    }
    fflush(stdout);
  }
  return 0;
}
