# sangha.nyc

Website for the young adult sangha of the New York Insight Meditation Center.

Single-page static site (`index.html`), deployed to GitHub Pages via GitHub Actions
on every push to `main`. Served at [sangha.nyc](https://sangha.nyc/) — the custom
domain is set by the `CNAME` file.


## Local preview

Serve the directory (don't just open the file — `file://` blocks the font loads):

```
python3 -m http.server 8000
```


## Layout

```
index.html            the whole site: markup, styles and scripts in one file
404.html              branded not-found page, served by GitHub Pages
assets/fonts/         self-hosted webfont subsets (see below)
assets/               logo, favicons, social share image
robots.txt            crawler rules
sitemap.xml           bump <lastmod> when the content changes meaningfully
tools/build-fonts.py  regenerates assets/fonts/
```


## Editing the events section

Each event carries `data-expires="YYYY-MM-DD"` (New York time). On and after that
date a script silently removes it and strips it from the JSON-LD, so past events
never linger. When no events remain, the "no upcoming events" panel takes over.

Adding an event means adding the `<article class="event">` block **and** a matching
`Event` node in the JSON-LD near the top of the file.


## Fonts

Newsreader and Figtree are self-hosted rather than loaded from Google Fonts, which
drops two third-party connections and a render-blocking stylesheet. The files in
`assets/fonts/` are Latin-only subsets with the weight axis trimmed to what the
stylesheet uses, split by `unicode-range` so the accented-Latin files only download
when a page actually needs them.

To regenerate them (after changing weights, or to pick up an upstream release):

```
pip install fonttools brotli
python3 tools/build-fonts.py
```

If you add a font weight in the CSS, add it to `SOURCES` in that script too —
otherwise the browser will fake the weight instead of rendering it.


## Theme

The site follows, in order of precedence: an explicit choice saved by the nav
toggle, then the visitor's OS dark-mode setting, then the local clock (dark from
7pm to 7am). The `theme-color` meta tag is kept in sync by the same script.
