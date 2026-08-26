"""Cinqtris: an attract-mode title screen -- an animated "CINQTRIS"
wordmark over an 8-bar cascading equalizer, with one interactive touch: a
click anywhere slides a "MADMAX" logo across the screen and off the far
edge. See `docs/cinqtris.md` for the demo overview.

`CT_ANI.png` (128x145) turned out to be a sprite sheet, not a screenshot
of the finished title screen -- same surprise every other demo's source
image has held. It bundles three separate animation strips, stacked
vertically for storage:

- **Wordmark** (y0-47): three 128x16 frames of the full "CINQTRIS"
  wordmark (8 letters x 16px). Each letter's *shape* is identical across
  all three frames -- only a 3-colour band (yellow/olive/green, each 4px
  tall within the 16-row cell) cycles per frame, scrolling upward with
  wraparound. `WORD_LETTERS` holds the shared shape once; `WORD_BAND_COLORS`
  plus the frame index reproduce the cycle (see `_draw_wordmark`).
- **Equalizer** (y48-141, minus the last 2 columns of the second row):
  14 frames of a single bar rising from all-red (quiet) to all-green
  (loud) over frames 0-7, then falling back over frames 8-13 -- a
  symmetric rise-and-fall, not 14 independent bars. `EQ_FRAMES` holds
  all 14; the demo cycles `EQ_BARS` (8) bars through them with a 1-frame
  stagger per bar for the cascading-wave look `docs/cinqtris.md` calls
  for. Genuinely bordered in the source: a sunken bevel (grey top/left,
  white bottom/right, 2px each) frames the whole strip, with a white+grey
  2px/2px divider between columns -- easy to miss (an early pass did)
  since it reads as background chrome, not part of "the bars" themselves.
- **MADMAX** (the last 2 of row 2's 8 column slots, x96-127 y98-141): a
  2x3 grid reading "MAD" (left column) over "MAX" (right column), in two
  colour-swapped frames (red-on-olive / olive-on-red) -- not separate
  hover/press art, just a colour-flash pair. The source lays it out as a
  stacked 2x3 block; this demo instead lays the same 4 unique letter
  shapes (M, A, D, X) out in one horizontal row "MADMAX" (M-A-D-M-A-X, 6
  cells), since a left-to-right slide needs a horizontal strip -- the one
  real adaptation here, not a straight lift like everything else.

Design proposed 2026-08-25 and refined over several rounds with Bruce
before building: vertical stack (wordmark above equalizer, not the
horizontal 3-cells-across layout `docs/cinqtris.md` originally sketched),
both rendered at the same pixel scale since they're both 128 native px
wide in the source and meant to line up exactly; the wordmark cropped to
exactly 1px of padding above and below its own glyphs (not the source's
full 2px margin) with that tight treatment kept local to the wordmark,
not applied elsewhere; the equalizer's real bevel border restored after
briefly (and wrongly) stripping it out; both elements explicitly centred.
MADMAX starts off-screen and is invisible until triggered.

No `Phase`/`PhaseSequence`: like CD Player, nothing about this attract
loop suggested discrete narrative beats -- it's one continuous loop
(wordmark cycle, equalizer cascade) plus a one-shot triggered animation
(the slide), not a scripted sequence of stages.
"""

from __future__ import annotations

import pygame

from retrodemos.framework.demo import Demo
from retrodemos.framework.ticker import Ticker

BG = (0, 0, 0)

# ---- Wordmark: exact letter shapes measured from CT_ANI.png (16x16 per
# cell, y0-47 band) -- identical across all 3 sampled colour frames, only
# the row-banding colour cycles. See module docstring. ----
WORD_LETTERS: tuple[tuple[str, ...], ...] = (
    ("................", "................", "....##########..", "....##########..", "..####..........", "..####..........", "..####..........", "..####..........", "..####..........", "..####..........", "..############..", "..############..", "....##########..", "....##########..", "................", "................"),
    ("................", "................", "..############..", "..############..", "......####......", "......####......", "......####......", "......####......", "......####......", "......####......", "..############..", "..############..", "..############..", "..############..", "................", "................"),
    ("................", "................", "..####....####..", "..####....####..", "..######..####..", "..######..####..", "..############..", "..############..", "..####..######..", "..####..######..", "..####....####..", "..####....####..", "..####....####..", "..####....####..", "................", "................"),
    ("................", "................", "....########....", "....########....", "..####....####..", "..####....####..", "..####....####..", "..####....####..", "..####..######..", "..####..######..", "..############..", "..############..", "....##########..", "....##########..", "................", "................"),
    ("................", "................", "..############..", "..############..", "......####......", "......####......", "......####......", "......####......", "......####......", "......####......", "......####......", "......####......", "......####......", "......####......", "................", "................"),
    ("................", "................", "..##########....", "..##########....", "..####....####..", "..####....####..", "..##########....", "..##########....", "..####....####..", "..####....####..", "..####....####..", "..####....####..", "..####....####..", "..####....####..", "................", "................"),
    ("................", "................", "..############..", "..############..", "......####......", "......####......", "......####......", "......####......", "......####......", "......####......", "..############..", "..############..", "..############..", "..############..", "................", "................"),
    ("................", "................", "....##########..", "....##########..", "..####..........", "..####..........", "....########....", "....########....", "..........####..", "..........####..", "..############..", "..############..", "..##########....", "..##########....", "................", "................"),
)
WORD_BAND_COLORS: tuple[tuple[int, int, int], ...] = ((255, 255, 0), (191, 191, 0), (0, 191, 0))  # yellow, olive, green
LETTER_W = LETTER_H = 16
LETTER_CONTENT_TOP, LETTER_CONTENT_BOTTOM = 2, 13  # inclusive -- rows 0-1/14-15 are always blank margin
WORD_PAD = 1  # kept above/below the glyphs; NOT the source's own 2px margin, and not used elsewhere
WORD_RENDER_H = WORD_PAD + (LETTER_CONTENT_BOTTOM - LETTER_CONTENT_TOP + 1) + WORD_PAD  # 14


def _draw_wordmark(surface: pygame.Surface, frame: int, x0: int, y0: int) -> None:
    content_y0 = y0 + (WORD_PAD - LETTER_CONTENT_TOP)
    for i, mask in enumerate(WORD_LETTERS):
        lx = x0 + i * LETTER_W
        for band in range(3):
            colour = WORD_BAND_COLORS[(band - frame) % 3]
            for dy in range(2 + band * 4, 2 + band * 4 + 4):
                row = mask[dy]
                for dx, ch in enumerate(row):
                    if ch == "#":
                        surface.set_at((lx + dx, content_y0 + dy), colour)


# ---- Equalizer: 14-frame rise/fall sequence, 7 segments per bar,
# measured from CT_ANI.png (y50-93, one column per frame). Border
# colours measured the same way: sunken bevel + column dividers. ----
EQ_FRAMES: tuple[str, ...] = ("RRRRRRR", "RRRRRRG", "RRRRRGG", "RRRRGGG", "RRRGGGG", "RRGGGGG", "RGGGGGG", "GGGGGGG", "GGGGGGR", "GGGGGRR", "GGGGRRR", "GGGRRRR", "GGRRRRR", "GRRRRRR")
EQ_COLOR = {"R": (191, 0, 0), "G": (0, 255, 0)}
EQ_BARS = 8
SEG_H, SEG_GAP, SEG_W = 4, 2, 10
EQ_BAR_PITCH = 16  # native px per column -- matches the wordmark's own letter pitch
EQ_BORDER = 2
EQ_BORDER_TL = (128, 128, 128)  # grey -- top/left, sunken
EQ_BORDER_BR = (255, 255, 255)  # white -- bottom/right, sunken
EQ_W = EQ_BARS * EQ_BAR_PITCH  # 128 -- same native width as the wordmark, deliberately (see module docstring)
EQ_H = EQ_BORDER + 7 * (SEG_H + SEG_GAP) + EQ_BORDER


def _draw_equalizer(surface: pygame.Surface, phase: int, x0: int, y0: int) -> None:
    w, h, b = EQ_W, EQ_H, EQ_BORDER
    pygame.draw.rect(surface, EQ_BORDER_TL, (x0, y0, w, b))
    pygame.draw.rect(surface, EQ_BORDER_TL, (x0, y0, b, h))
    pygame.draw.rect(surface, EQ_BORDER_BR, (x0, y0 + h - b, w, b))
    pygame.draw.rect(surface, EQ_BORDER_BR, (x0 + w - b, y0, b, h))
    pygame.draw.rect(surface, BG, (x0 + b, y0 + b, w - 2 * b, h - 2 * b))

    for bar in range(EQ_BARS):
        pattern = EQ_FRAMES[(phase + bar) % len(EQ_FRAMES)]
        bx = x0 + EQ_BORDER + bar * EQ_BAR_PITCH
        for s, ch in enumerate(pattern):
            sy = y0 + EQ_BORDER + s * (SEG_H + SEG_GAP)
            pygame.draw.rect(surface, EQ_COLOR[ch], (bx, sy, SEG_W, SEG_H))
        if bar < EQ_BARS - 1:
            dx = x0 + EQ_BORDER + bar * EQ_BAR_PITCH + SEG_W
            pygame.draw.rect(surface, EQ_BORDER_BR, (dx, y0 + b, 2, h - 2 * b))
            pygame.draw.rect(surface, EQ_BORDER_TL, (dx + 2, y0 + b, 2, h - 2 * b))


# ---- MADMAX: exact 7x7 letter shapes measured from CT_ANI.png (the
# source's 2x3 "MAD"/"MAX" grid, re-laid-out as one horizontal row for
# the slide -- see module docstring). Backgrounds alternate red/olive per
# letter, stroke is always the other colour in the pair. ----
MM_SHAPES: dict[str, tuple[str, ...]] = {
    "M": (".......", ".#...#.", ".##.##.", ".#.#.#.", ".#...#.", ".#...#.", "......."),
    "A": (".......", "..###..", ".#...#.", ".#####.", ".#...#.", ".#...#.", "......."),
    "D": (".......", ".####..", ".#...#.", ".#...#.", ".#...#.", ".####..", "......."),
    "X": (".......", ".#...#.", "..#.#..", "...#...", "..#.#..", ".#...#.", "......."),
}
MM_WORD = ("M", "A", "D", "M", "A", "X")
MM_CELL = 7  # native mask size
MM_BLOCK = 3  # px per mask cell when drawn -- bigger than the wordmark's own 1:1, for visual weight on the slide
MM_COLOR_A = (191, 191, 0)  # olive
MM_COLOR_B = (191, 0, 0)  # red
MM_LETTER_PX = MM_CELL * MM_BLOCK
MM_TOTAL_W = len(MM_WORD) * MM_LETTER_PX


def _draw_madmax(surface: pygame.Surface, x0: int, y0: int) -> None:
    for i, ch in enumerate(MM_WORD):
        bg, stroke = (MM_COLOR_A, MM_COLOR_B) if i % 2 == 0 else (MM_COLOR_B, MM_COLOR_A)
        cx = x0 + i * MM_LETTER_PX
        pygame.draw.rect(surface, bg, (cx, y0, MM_LETTER_PX, MM_LETTER_PX))
        for dy, row in enumerate(MM_SHAPES[ch]):
            for dx, mch in enumerate(row):
                if mch == "#":
                    surface.fill(stroke, (cx + dx * MM_BLOCK, y0 + dy * MM_BLOCK, MM_BLOCK, MM_BLOCK))


# ---- Layout -- new design, not measured (the source is a sprite sheet,
# not a mockup of the finished screen); see module docstring. Playtesting
# (2026-08-26) trimmed the margins to the bare minimum: 1px top, nothing
# on the other three sides -- both elements already fill CONTENT_W
# exactly, so any left/right padding was pure dead space, and the bottom
# edge reads better flush against the equalizer's own bevel.
CONTENT_W = len(WORD_LETTERS) * LETTER_W  # 128 -- wordmark and equalizer share this width exactly
PADDING = 0
TOP_MARGIN = 1
WORD_EQ_GAP = 3  # gap between title and equalizer -- ordinary spacing, NOT the title's own 1px rule
BOTTOM_MARGIN = 0

WORD_X = PADDING  # (CONTENT_W - CONTENT_W) // 2 == 0 -- both elements are the same width, so centring is a no-op
WORD_Y = TOP_MARGIN
EQ_X = PADDING
EQ_Y = WORD_Y + WORD_RENDER_H + WORD_EQ_GAP

WIDTH = CONTENT_W + PADDING * 2
HEIGHT = EQ_Y + EQ_H + BOTTOM_MARGIN

# Timing -- all invented, no timing data exists in a static sprite sheet.
WORD_INTERVAL = 0.26
EQ_INTERVAL = 0.14
MM_SPEED = 90.0  # native px/sec


class CinqtrisDemo(Demo):
    NATIVE_SIZE = (WIDTH, HEIGHT)

    def __init__(self, *, text: str | None = None, **_ignored) -> None:
        self.reset()

    def reset(self) -> None:
        self._word_frame = 0
        self._word_ticker = Ticker(WORD_INTERVAL)
        self._eq_phase = 0
        self._eq_ticker = Ticker(EQ_INTERVAL)
        self._mm_sliding = False
        self._mm_x = -MM_TOTAL_W

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._trigger_slide()

    def _trigger_slide(self) -> None:
        if self._mm_sliding:
            return
        self._mm_sliding = True
        self._mm_x = -MM_TOTAL_W

    def update(self, dt: float) -> None:
        for _ in range(self._word_ticker.advance(dt)):
            self._word_frame = (self._word_frame + 1) % len(WORD_BAND_COLORS)
        for _ in range(self._eq_ticker.advance(dt)):
            self._eq_phase = (self._eq_phase + 1) % len(EQ_FRAMES)
        if self._mm_sliding:
            self._mm_x += MM_SPEED * dt
            if self._mm_x > WIDTH:
                self._mm_sliding = False

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(BG)
        _draw_wordmark(surface, self._word_frame, WORD_X, WORD_Y)
        _draw_equalizer(surface, self._eq_phase, EQ_X, EQ_Y)
        if self._mm_sliding:
            mm_y = EQ_Y + EQ_H // 2 - MM_LETTER_PX // 2  # vertically centred over the bars
            _draw_madmax(surface, int(self._mm_x), mm_y)


DEMO_CLASS = CinqtrisDemo
