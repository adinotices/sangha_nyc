#!/usr/bin/env python3
"""Regenerate assets/social-card.png, the image link previews use.

    pip install playwright pillow && playwright install chromium
    python3 tools/build-social-card.py

Design notes, since they are easy to undo by accident:

WhatsApp does not show this at 1200x630. It letterboxes the whole image into a
small square thumbnail, so a 1200x630 card becomes roughly 100x53 actual pixels
next to the title text. Two things follow:

  * Fill the frame. Generous margins are invisible at full size and fatal at
    thumbnail size -- the previous card used about 55% of the canvas and turned
    to mush.
  * Do not repeat the title or description. WhatsApp already prints both beside
    the thumbnail. The image earns its place by being recognisable, not by
    restating text, so this is the mark plus the name and nothing else.

The lotus is rendered from the SVG rather than assets/logo.png, which is only
96x96 and would be upscaled roughly 4x. Rendering happens at 2x and is then
downsampled, which keeps the type crisp.

Changing the card means changing OUT_NAME too: previews are cached per image
URL, so reusing a filename can leave old thumbnails in place indefinitely.
Update the og:image / twitter:image tags and the JSON-LD nodes to match.
"""

import os
import sys

try:
    from playwright.sync_api import sync_playwright
    from PIL import Image
except ImportError:
    sys.exit("missing deps -- run: pip install playwright pillow")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_NAME = "social-card.png"
OUT = os.path.join(ROOT, "assets", OUT_NAME)
CHROMIUM = "/opt/pw-browsers/chromium"

# Light palette, matching the site's default (daytime) theme. To switch the card
# to the dark theme, swap in: ink #f1efe2, accent #9fc28f, bg #171b10, and
# lighten the ring colours.
HTML = """
<!doctype html><meta charset="utf-8">
<style>
  @font-face{font-family:Newsreader;font-style:normal;font-weight:300 500;
    src:url(fonts/newsreader.woff2) format('woff2');}
  @font-face{font-family:Newsreader;font-style:italic;font-weight:300 400;
    src:url(fonts/newsreader-italic.woff2) format('woff2');}
  *{margin:0;box-sizing:border-box}
  .card{width:1200px;height:630px;background:#f2efe4;position:relative;
    overflow:hidden;display:flex;align-items:center;justify-content:center;}
  .rings{position:absolute;top:50%;left:50%;width:1060px;height:1060px;
    transform:translate(-50%,-50%);}
  .rings i{position:absolute;inset:0;border-radius:50%;
    border:1.5px solid rgba(127,154,114,.30);}
  .rings i:nth-child(2){inset:13%;border-color:rgba(127,154,114,.20)}
  .rings i:nth-child(3){inset:26%;border-color:rgba(194,149,63,.30)}
  .rings i:nth-child(4){inset:39%;border-color:rgba(127,154,114,.20)}
  .in{position:relative;z-index:2;display:flex;align-items:center;gap:56px;}
  img{width:360px;height:360px;display:block;flex:none;}
  .name{font-family:Newsreader;font-weight:400;line-height:1.02;
    letter-spacing:-.015em;font-size:100px;color:#212a20;}
  .sub{font-family:Newsreader;font-style:italic;font-weight:300;
    font-size:52px;margin-top:18px;color:#55694e;}
</style>
<div class="card">
  <div class="rings"><i></i><i></i><i></i><i></i></div>
  <div class="in">
    <img src="logo.svg" alt="">
    <div>
      <div class="name">Young&nbsp;Adult<br>Sangha</div>
      <div class="sub">of New York Insight</div>
    </div>
  </div>
</div>
"""


def main():
    assets = os.path.join(ROOT, "assets")
    tmp_html = os.path.join(assets, ".social-card.html")
    with open(tmp_html, "w", encoding="utf-8") as f:
        f.write(HTML)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                executable_path=CHROMIUM if os.path.exists(CHROMIUM) else None
            )
            page = browser.new_page(
                viewport={"width": 1200, "height": 630}, device_scale_factor=2
            )
            page.goto("file://" + tmp_html)
            page.wait_for_timeout(1200)
            page.locator(".card").screenshot(path=OUT)
            browser.close()
        # rendered at 2x, so bring it back down for a crisper 1200x630, then
        # quantise -- the card is flat colour plus one gradient, so 256 colours
        # is visually identical and roughly halves the file
        card = Image.open(OUT).convert("RGB").resize((1200, 630), Image.LANCZOS)
        card.quantize(colors=256, method=Image.MEDIANCUT,
                      dither=Image.FLOYDSTEINBERG).save(OUT, optimize=True)
    finally:
        if os.path.exists(tmp_html):
            os.remove(tmp_html)
    print(f"wrote assets/{OUT_NAME}  ({os.path.getsize(OUT)/1024:.1f}K)")
    print("remember: og:image / twitter:image / JSON-LD must use this filename")


if __name__ == "__main__":
    main()
