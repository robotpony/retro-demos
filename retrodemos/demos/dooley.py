"""Dooley: a Windows 3.1-style colour-picker dialog, recreated as an
automated attract-mode demo -- three regions built from
`framework/led_grid.py`'s `BevelCellDisplay` and a bit of direct drawing,
composited onto one canvas the size of `images/DOOLEY1.png` (256x128). See
`docs/dooley.md` for the full pixel-archaeology findings and the scope
decisions (confirmed with Bruce, 2026-08-24) behind what follows.

**LED strip** (33x6 `BevelCellDisplay` cells, top-left): shown fully lit in
the source, same "calibration image" pattern as LED/LED II's own source
images, so its content is invented here -- a compact 3x5 digit font
(`DIGIT_FONT` below; DOT_FONT in led_grid.py is 5x7 and doesn't fit this
display's 6 rows) scrolling the digits, same idea as LED II's marquee.

**Colour palette** (two 3x7 `BevelCellDisplay`s stacked with a 1px gap, left
edge): a fixed, mirrored dark/dither/bright rainbow reference chart,
verified byte-exact against DOOLEY1.png (see
tests/test_led_grid_bevel_cell.py's module docstring). Palette-cycles:
the 7 hues rotate through the 7 row positions on a timer, mirrored the same
way top/bottom halves mirror in the source.

**RGB-spinner/grid area** (right of the palette): approximated, not
pixel-verified the way the other two regions are -- it's decorative
backdrop, not carried content, so it doesn't need the same reconstruct-and-
diff bar. 11 columns of raised-bevel cells, the first 3 topped with an
up/down spinner-arrow pair; idle animation rotates which spinner reads as
"active" (drawn sunken) so the window doesn't look frozen.

Unlike LED/LED II/Title, Dooley isn't built as a `Phase`/`PhaseSequence`
script. Every other demo's source image describes a narrative with distinct
beats (power-up, content, snake, fireworks, credit); DOOLEY1.png is a
screenshot of a tool's UI, not an LED program with a script of its own, and
nothing about it suggests discrete stages -- it's one continuous behaviour
(scroll + cycle + idle) for as long as the demo runs. `Phase`/`PhaseSequence`
stay available if a later revision of this demo turns out to want one.
"""

from __future__ import annotations

import random

import pygame

from retrodemos.framework.demo import Demo
from retrodemos.framework.led_grid import BEZEL_CORNER, BEZEL_DARK, BEZEL_LIGHT, BevelCellDisplay, CellFill
from retrodemos.framework.ticker import Ticker

NATIVE_SIZE = (256, 128)  # matches images/DOOLEY1.png

# --- LED strip -------------------------------------------------------------

STRIP_COLS = 33
STRIP_ROWS = 6
STRIP_ORIGIN = (4, 4)  # measured position within DOOLEY1.png

# Measured (191, 191, 0) is DOOLEY1.png's only lit-strip colour (verified
# byte-exact across all 198 cells -- see test_led_grid_bevel_cell.py). The
# strip's unlit colour has no ground truth (source only ever shows it fully
# lit), so it's invented here at the same ~0.25 dimness ratio LED's own
# invented UNLIT and LED II's DOT_UNLIT both use below their LIT colours.
STRIP_LIT = (191, 191, 0)
STRIP_UNLIT = (48, 48, 0)

# A compact 3-wide x5-tall digit font, invented for this display -- DOT_FONT
# (led_grid.py, 5x7) doesn't fit the LED strip's 6 rows. Same "#"/"."
# row-string convention DOT_FONT's own source table uses.
_DIGIT_GLYPH_ROWS: dict[str, tuple[str, ...]] = {
    "0": ("###", "#.#", "#.#", "#.#", "###"),
    "1": (".#.", "##.", ".#.", ".#.", "###"),
    "2": ("###", "..#", "###", "#..", "###"),
    "3": ("###", "..#", "###", "..#", "###"),
    "4": ("#.#", "#.#", "###", "..#", "..#"),
    "5": ("###", "#..", "###", "..#", "###"),
    "6": ("###", "#..", "###", "#.#", "###"),
    "7": ("###", "..#", "..#", "..#", "..#"),
    "8": ("###", "#.#", "###", "#.#", "###"),
    "9": ("###", "#.#", "###", "..#", "###"),
    "-": ("...", "...", "###", "...", "..."),
    " ": ("...", "...", "...", "...", "..."),
}
DIGIT_GLYPH_W = 3
DIGIT_GLYPH_H = 5
DIGIT_GLYPH_GAP = 1
DIGIT_FONT: dict[str, set[tuple[int, int]]] = {
    ch: {(x, y) for y, row in enumerate(rows) for x, pixel in enumerate(row) if pixel == "#"}
    for ch, rows in _DIGIT_GLYPH_ROWS.items()
}

DEFAULT_TEXT = "0123456789"  # same default content LED II's marquee uses
STRIP_GAP = "   "  # blank columns between repeats
STRIP_SCROLL_INTERVAL = 0.05


def _text_dots(text: str) -> tuple[dict[int, set[int]], int]:
    """Lay out `text` in DIGIT_FONT, natural width, unclipped -- the LED
    strip's own version of DotMatrixDisplay.text_dots. Returns lit dots
    grouped by column (for per-column scrolling) plus the total width."""
    row_offset = (STRIP_ROWS - DIGIT_GLYPH_H) // 2
    by_col: dict[int, set[int]] = {}
    for i, ch in enumerate(text):
        glyph = DIGIT_FONT.get(ch, DIGIT_FONT[" "])
        col_offset = i * (DIGIT_GLYPH_W + DIGIT_GLYPH_GAP)
        for gx, gy in glyph:
            by_col.setdefault(col_offset + gx, set()).add(row_offset + gy)
    width = max(len(text) * (DIGIT_GLYPH_W + DIGIT_GLYPH_GAP) - DIGIT_GLYPH_GAP, 1)
    return by_col, width


# --- Colour palette ----------------------------------------------------------

PALETTE_ORIGIN = (0, 32)
PALETTE_GAP = 1  # 1px background row between the raised and sunken halves

# The 7 hues the palette cycles through, each (dark, bright) -- black has no
# bright pair (there's no "bright black" in this 16-colour set), matching
# DOOLEY1.png's own black/grey row exactly (see docs/dooley.md).
PALETTE_HUES: list[tuple[tuple[int, int, int], tuple[int, int, int] | None]] = [
    ((0, 0, 0), None),
    ((191, 0, 0), (255, 0, 0)),
    ((0, 191, 0), (0, 255, 0)),
    ((191, 191, 0), (255, 255, 0)),
    ((0, 0, 191), (0, 0, 255)),
    ((191, 0, 191), (255, 0, 255)),
    ((0, 191, 191), (0, 255, 255)),
]
PALETTE_CYCLE_INTERVAL = 0.5  # seconds per one-row rotation step


def _palette_row_cells(dark: tuple[int, int, int], bright: tuple[int, int, int] | None, reversed_: bool) -> list[CellFill]:
    """The 3 swatches for one hue row: solid dark, a dark/bright dither, and
    solid bright -- reversed (bright, dither, dark) for the mirrored bottom
    half. A hue with no bright pair (black) leaves the bright slot blank and
    dithers against the background instead -- both measured exactly this
    way in DOOLEY1.png (see test_led_grid_bevel_cell.py)."""
    solid_dark = CellFill(dark)
    dither = CellFill(dark, bright if bright is not None else BEZEL_CORNER)
    solid_bright = CellFill(bright) if bright is not None else CellFill()
    return [solid_bright, dither, solid_dark] if reversed_ else [solid_dark, dither, solid_bright]


# --- RGB-spinner/grid area (approximated, not pixel-verified) --------------

GRID_ORIGIN = (14, 31)
GRID_COLS = 11
GRID_COL_W = 22
GRID_BAND1_H = 65  # tall band -- 3 of its columns carry a spinner
GRID_DIVIDER_H = 2
GRID_BAND2_H = 21
GRID_SPINNER_COLS = 3
GRID_SPINNER_CYCLE_INTERVAL = 0.8  # how long each spinner reads as "active"


def _raised_rect(surface: pygame.Surface, x: int, y: int, w: int, h: int, *, sunken: bool = False) -> None:
    lo, hi = (BEZEL_LIGHT, BEZEL_DARK) if sunken else (BEZEL_DARK, BEZEL_LIGHT)
    pygame.draw.rect(surface, BEZEL_CORNER, (x, y, w, h))
    pygame.draw.line(surface, lo, (x, y), (x + w - 1, y))
    pygame.draw.line(surface, lo, (x, y), (x, y + h - 1))
    pygame.draw.line(surface, hi, (x + w - 1, y), (x + w - 1, y + h - 1))
    pygame.draw.line(surface, hi, (x, y + h - 1), (x + w - 1, y + h - 1))


def _draw_grid_area(surface: pygame.Surface, active_spinner: int) -> None:
    x0, y0 = GRID_ORIGIN
    for col in range(GRID_COLS):
        cx = x0 + col * GRID_COL_W
        sunken = col < GRID_SPINNER_COLS and col == active_spinner
        _raised_rect(surface, cx, y0, GRID_COL_W, GRID_BAND1_H, sunken=sunken)
        _raised_rect(surface, cx, y0 + GRID_BAND1_H + GRID_DIVIDER_H, GRID_COL_W, GRID_BAND2_H)
        if col < GRID_SPINNER_COLS:
            _draw_spinner(surface, cx + GRID_COL_W // 2, y0 + 8, active=col == active_spinner)


def _draw_spinner(surface: pygame.Surface, cx: int, cy: int, *, active: bool) -> None:
    colour = (191, 0, 0) if active else (0, 0, 0)  # active spinner's arrows pick out in red
    pygame.draw.polygon(surface, colour, [(cx - 4, cy + 4), (cx + 4, cy + 4), (cx, cy - 4)])  # up
    dy = 11
    pygame.draw.polygon(surface, colour, [(cx - 4, cy + dy - 4), (cx + 4, cy + dy - 4), (cx, cy + dy + 4)])  # down


class DooleyDemo(Demo):
    NATIVE_SIZE = NATIVE_SIZE

    def __init__(self, *, text: str | None = None, **_ignored) -> None:
        self._text = text or DEFAULT_TEXT
        self._strip = BevelCellDisplay(STRIP_COLS, STRIP_ROWS)
        self._strip_surface = pygame.Surface((self._strip.width, self._strip.height))
        self._palette_top = BevelCellDisplay(3, len(PALETTE_HUES))
        self._palette_bottom = BevelCellDisplay(3, len(PALETTE_HUES))
        self._palette_surface = pygame.Surface(
            (self._palette_top.width, self._palette_top.height + PALETTE_GAP + self._palette_bottom.height)
        )
        self._rng = random.Random()
        self.reset()

    def reset(self) -> None:
        self._by_col, self._text_width = _text_dots(self._text + STRIP_GAP)
        self._scroll_offset = 0
        self._scroll_ticker = Ticker(STRIP_SCROLL_INTERVAL)
        self._palette_offset = 0
        self._palette_ticker = Ticker(PALETTE_CYCLE_INTERVAL)
        self._active_spinner = 0
        self._spinner_ticker = Ticker(GRID_SPINNER_CYCLE_INTERVAL)

    def update(self, dt: float) -> None:
        for _ in range(self._scroll_ticker.advance(dt)):
            self._scroll_offset = (self._scroll_offset + 1) % self._text_width
        for _ in range(self._palette_ticker.advance(dt)):
            self._palette_offset = (self._palette_offset + 1) % len(PALETTE_HUES)
        for _ in range(self._spinner_ticker.advance(dt)):
            self._active_spinner = (self._active_spinner + 1) % GRID_SPINNER_COLS

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(BEZEL_CORNER)
        self._draw_strip()
        surface.blit(self._strip_surface, STRIP_ORIGIN)
        self._draw_palette()
        surface.blit(self._palette_surface, PALETTE_ORIGIN)
        _draw_grid_area(surface, self._active_spinner)

    def _draw_strip(self) -> None:
        fills = {}
        for col in range(STRIP_COLS):
            source_col = (col + self._scroll_offset) % self._text_width
            lit_rows = self._by_col.get(source_col, set())
            for row in range(STRIP_ROWS):
                fills[(col, row)] = CellFill(STRIP_LIT if row in lit_rows else STRIP_UNLIT)
        self._strip.render_raw(self._strip_surface, fills)

    def _draw_palette(self) -> None:
        self._palette_surface.fill(BEZEL_CORNER)  # the 1px gap row between halves shows through this
        n = len(PALETTE_HUES)
        top_fills, bottom_fills = {}, {}
        for row in range(n):
            dark, bright = PALETTE_HUES[(row + self._palette_offset) % n]
            for c, cell in enumerate(_palette_row_cells(dark, bright, False)):
                top_fills[(c, row)] = cell
        for row in range(n):
            dark, bright = PALETTE_HUES[(n - 1 - row + self._palette_offset) % n]
            for c, cell in enumerate(_palette_row_cells(dark, bright, True)):
                bottom_fills[(c, row)] = CellFill(cell.primary, cell.secondary, sunken=True)
        self._palette_top.render_raw(
            self._palette_surface.subsurface((0, 0, self._palette_top.width, self._palette_top.height)), top_fills
        )
        self._palette_bottom.render_raw(
            self._palette_surface.subsurface(
                (0, self._palette_top.height + PALETTE_GAP, self._palette_bottom.width, self._palette_bottom.height)
            ),
            bottom_fills,
        )


DEMO_CLASS = DooleyDemo
