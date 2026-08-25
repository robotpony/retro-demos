# Dooley

**Source:** `DOOLEY1.png`
**Mode:** Automated attract-mode
**Build:** Done (`retrodemos/demos/dooley.py`)

## What it shows

`DOOLEY1.png` is a 256x128 screenshot of a larger app window than the terse
original spec implied: a Windows 3.1-style colour-picker dialog, not just
"LED display + colour column". Scoped down with Bruce (2026-08-24) after a
zoomed look, then measured pixel-by-pixel (`docs/pixel-archaeology.md`'s
reconstruct-and-diff method) before building:

- **LED-style bevelled strip** (top-left, x4-136 y4-28): a 33x6 grid of
  individually-bevelled 4x4 cells, all 198 byte-identical and fully lit
  `(191,191,0)` in the source -- same "calibration image" pattern as
  LED-thumb.png/LED-II-thumb.png, so its actual content/font is invented at
  build time the same way LED II's was.
- **Colour palette column** (left edge, x0-11 y32-88): not the "11-row x
  3-column swatch grid" the original terse spec guessed -- measurement
  found a mirrored 14-row rainbow reference chart instead: 7 hues (black,
  red, green, yellow, blue, magenta, cyan) each shown as 3 swatches (solid
  dark, a dark/bright dither checkerboard, solid bright), raised-bevel, then
  the same 7 hues in reverse order and reversed swatch order, sunken-bevel,
  with a 1px background gap between the two halves.
- **RGB-spinner/grid area** (right of the palette, x14-256 y31-119): 11
  columns on a 22px pitch, two row-bands (a tall ~65px one and a shorter
  ~20px one, not the ~5-row grid a low-res glance suggested), the first 3
  columns of the tall band topped with an up/down spinner-arrow pair.
- **Top-right toolbar** (spinner button, an icon button, two blank buttons,
  an X close button): **out of scope** -- window chrome for a UI Dooley
  doesn't need to simulate, same reasoning `PLAN.md`'s "Window chrome"
  section gives for not sharing chrome between demos.

## Renderer

The LED strip and the palette column turned out to share one pixel model
once measured -- both are grids of individually-bevelled 4x4 cells (a 1px
bevel border on all four sides, a 2x2 fill centre), unlike `DotMatrixDisplay`
(dots on one shared bezel) or `BitColumnDisplay` (no bezel at all). One new
renderer, `framework/led_grid.py`'s `BevelCellDisplay`, covers both; see its
docstring and `tests/test_led_grid_bevel_cell.py`'s module docstring for the
reconstruct-and-diff verification (LED strip: 0/3168 mismatches; palette:
0/684 mismatches).

The RGB-spinner/grid area is **not** pixel-verified the same way -- it's
decorative backdrop, not carried content, so `dooley.py` approximates it
with plain drawing (bordered rectangles, procedural triangle arrows) rather
than measuring it to the same byte-exact bar. Worth a tighter pass later if
it ever needs to look pixel-perfect.

## Behaviour

- The LED strip scrolls digits (`DEFAULT_TEXT = "0123456789"`, same default
  LED II's marquee uses) through a compact invented 3x5 font
  (`dooley.py`'s `DIGIT_FONT` -- `led_grid.DOT_FONT` is 5x7 and doesn't fit
  this display's 6 rows).
- The palette column palette-cycles: the 7 hues rotate through the 7 row
  positions on a timer (`PALETTE_CYCLE_INTERVAL`), mirrored top/bottom the
  same way the source's own two halves mirror each other. Independent of
  the scrolling text's content -- no source evidence either way, so treated
  as independent per the original open question.
- The RGB-spinner/grid area idles: which of the 3 spinner columns reads as
  "active" (drawn sunken, arrows picked out in red) rotates on a timer
  (`GRID_SPINNER_CYCLE_INTERVAL`), so the window doesn't look frozen.

Unlike LED/LED II/Title, Dooley isn't a `Phase`/`PhaseSequence` script --
see `dooley.py`'s module docstring for why (short version: nothing about
`DOOLEY1.png`, a tool's UI rather than an LED program, suggests distinct
narrative beats the way the other three demos' source images do).

## Interaction

None beyond the shared quit/pause controls.

## Assets

Shares `framework/led_grid.py`'s `BevelCellDisplay` (new, built for this
demo) and `BEZEL_DARK`/`BEZEL_LIGHT`/`BEZEL_CORNER` colour constants
(already shared by the other three renderers). Doesn't reuse
`DotMatrixDisplay`/`BitColumnDisplay`/`DOT_FONT` -- checked against
`DOOLEY1.png` directly rather than assumed, per `PLAN.md`'s "LED grid
module" history.

## Open questions

- Whether the palette cycling should react to the scrolling text's content
  is still unresolved -- built independent, per the original call.
- The RGB-spinner/grid area's exact pixel geometry (border colours at every
  seam, whether band1/band2's uneven heights are really right) isn't
  independently re-verified beyond the rough measurements above -- fine for
  a backdrop, worth tightening if this area ever needs to be pixel-exact.
