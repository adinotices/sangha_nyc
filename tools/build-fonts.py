#!/usr/bin/env python3
"""Rebuild the self-hosted webfonts in assets/fonts/.

The site self-hosts Newsreader and Figtree instead of loading them from Google
Fonts, which removes two third-party connections and the render-blocking
stylesheet Google injects. This script regenerates those files from the
upstream originals.

    pip install fonttools brotli
    python3 tools/build-fonts.py

What it does to each font:
  * subsets to Latin (the site has no other scripts; emoji come from the OS)
  * trims the weight axis to the weights the stylesheet actually asks for
  * keeps Newsreader's optical-size axis -- the site sets it from 12.5px to
    72px, and opsz is what keeps the large hero type looking refined
  * splits each family in two by unicode-range, so the accented-Latin file is
    only downloaded if some character on the page needs it

If you change which weights index.html uses, update WEIGHTS below to match,
otherwise the browser will synthesise the missing weight.
"""

import os
import sys
import urllib.request

try:
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    from fontTools.subset import Subsetter, Options
except ImportError:
    sys.exit("missing deps -- run: pip install fonttools brotli")

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts")

# Upstream latin-subset variable fonts, as served by Google Fonts.
# Re-copy these URLs from the css2 API if Google bumps a version.
SOURCES = {
    "newsreader": (
        "https://fonts.gstatic.com/s/newsreader/v26/cY9AfjOCX1hbuyalUrK4397yjA.woff2",
        {"wght": (300, 400, 500), "opsz": (12, 18, 72)},
    ),
    "newsreader-italic": (
        "https://fonts.gstatic.com/s/newsreader/v26/cY9CfjOCX1hbuyalUrK439vCjohC.woff2",
        {"wght": (300, 400), "opsz": (12, 18, 72)},
    ),
    "figtree": (
        "https://fonts.gstatic.com/s/figtree/v9/_Xms-HUzqDCFdgfMm4S9DQ.woff2",
        {"wght": (400, 500, 600)},
    ),
}

# Must stay in sync with the unicode-range values in index.html / 404.html.
BASIC = list(range(0x0020, 0x007F)) + [0x00A0, 0x2013, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D, 0x2026]
EXT = list(range(0x00A1, 0x0100)) + [
    0x2010, 0x2011, 0x2012, 0x2015, 0x201A, 0x201B, 0x201E, 0x201F,
    0x2030, 0x2032, 0x2033, 0x2039, 0x203A, 0x20AC, 0x2122, 0x2212,
]

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"


def fetch(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req) as r, open(dest, "wb") as f:
        f.write(r.read())


def build(src, dest, axes, unicodes):
    font = TTFont(src)
    opts = Options()
    opts.layout_features = ["kern", "liga", "clig", "calt", "ccmp", "locl", "rlig", "mark", "mkmk"]
    opts.name_IDs = ["*"]
    opts.name_legacy = True
    opts.notdef_outline = True
    opts.drop_tables += ["DSIG"]

    # Subset before instancing: instancing can leave gvar without an entry for
    # glyphs that lost all their deltas, which the subsetter then trips over.
    sub = Subsetter(options=opts)
    sub.populate(unicodes=unicodes)
    sub.subset(font)

    if axes:
        font = instancer.instantiateVariableFont(font, axes, inplace=True, updateFontNames=False)

    font.flavor = "woff2"
    font.save(dest)
    return os.path.getsize(dest)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    tmp = os.path.join(OUT_DIR, ".upstream.woff2")
    initial = 0
    for name, (url, axes) in SOURCES.items():
        print(f"{name}: fetching upstream…")
        fetch(url, tmp)
        basic = build(tmp, os.path.join(OUT_DIR, f"{name}.woff2"), axes, BASIC)
        ext = build(tmp, os.path.join(OUT_DIR, f"{name}-ext.woff2"), axes, EXT)
        initial += basic
        print(f"  {name}.woff2 {basic/1024:6.1f}K   {name}-ext.woff2 {ext/1024:6.1f}K")
    os.remove(tmp)
    print(f"\nDownloaded by a visitor on a page with no accented characters: {initial/1024:.1f}K")


if __name__ == "__main__":
    main()
