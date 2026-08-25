"""CD Player: simulated playback, no real audio -- a numeric LED
track/time readout, transport buttons, a green/red dot-matrix level meter,
and a vertical slider bank, composited from pieces reverse-engineered from
`images/CDPLAYER.png` (see `docs/pixel-archaeology.md` for method,
`docs/cd-player.md` for the demo overview).

`CDPLAYER.png` (384x78) turned out not to be one coherent screenshot, the
same surprise Title's and Dooley's source images held: it bundles three
stacked reference bands rather than a single window. Band A (y0-28) and
Band B (y30-53) are two differently-sized captures of the same widget
vocabulary (transport buttons, a "cd" logo, a slider bank); Band C (y56-77)
is a separate full-width level-meter strip. Built around Band B (confirmed
with Bruce, 2026-08-24) since it's the larger, more detailed of the two and
its long readout doubles as a segment-font calibration strip (see
DIGIT_SEGMENTS below).

Every piece below is pixel-verified against Band B directly (not
approximated the way Dooley's RGB-spinner/grid area was): the digit
segment geometry, all six button/close icons, the slider bank's
track+tick geometry, and the "cd" logo are all literal coordinate/glyph
data measured from the source, not guessed shapes. The one exception is
overall panel layout (where each piece sits relative to the others) --
Band B's own pieces aren't laid out as one coherent window (see above),
so composing them into a single CD Player face is this file's own design
call, not a measurement.

A 2026-08-25 re-verification (connected-component style, the same method
that caught Bruce's Windows' bevel bugs) found two real mistakes in the
first pass, both now fixed:

- Every widget border in the source -- the readout box, the level-meter
  box, the transport buttons -- is a flat single-tone grey outline
  (BEZEL_DARK), not a two-tone raised/sunken bevel. There is no bevel
  anywhere in CDPLAYER.png outside the outer window frame; the earlier
  `_raised_rect` helper invented one. `_flat_box` replaces it.
- The digit segments were mis-measured: what looked like a calibration
  strip spelling "0123456789" is actually a segment-test pattern with
  *every* segment lit (matching Band A's own all-lit "888"), just
  alternating red/green per position for visibility. There is no source
  data for individual digit shapes, so the invented "6 has no top bar, 9
  has no bottom bar" quirks were fabricated, not measured -- DIGIT_SEGMENTS
  now uses the standard closed 6/9 forms instead. The segment *geometry*
  (each segment's exact tapered pixel shape) came from that same all-lit
  pattern and is real -- see _draw_digit.

No PhaseSequence: unlike LED/LED II/Title, there's no scripted narrative
here (no power-up flicker, snake, or fireworks fits "simulated CD
playback") -- same reasoning Dooley's continuous design used. Playback is
one continuous loop: the time counter increments, wraps to the next track
after TRACK_LENGTH seconds (wrapping the track number after TRACK_COUNT),
occasionally pauses for a few seconds (transport buttons pick out which
control is "active" to match), and the level meter fakes a waveform that
goes quiet while paused.
"""

from __future__ import annotations

import math

import pygame

from retrodemos.framework.demo import Demo
from retrodemos.framework.ticker import Ticker

BG = (0, 0, 0)
PANEL = (192, 192, 192)
BEZEL_DARK = (128, 128, 128)
BEZEL_LIGHT = (255, 255, 255)

# Measured directly from Band A's "888" readout: (191, 0, 0). The source
# never shows an unlit segment next to a lit one -- an "off" segment is
# simply not drawn, same as the panel's own black background -- so there's
# no separate off-colour to measure or invent.
SEG_ON = (191, 0, 0)
GREEN_ON = (0, 255, 0)
GREEN_OFF = (191, 0, 0)  # measured -- Band C's own "unlit" colour, not invented

# Segments: a=top, b=top-right, c=bottom-right, d=bottom, e=bottom-left,
# f=top-left, g=middle. What looked like a calibration strip spelling
# "0123456789" is actually a segment-test pattern with every segment lit
# (see module docstring) -- there's no source data for individual digit
# shapes, so this is the standard closed 6/9 form, not measured content.
DIGIT_SEGMENTS = {
    "0": "abcdef", "1": "bc", "2": "abdeg", "3": "abcdg", "4": "bcfg",
    "5": "acdfg", "6": "acdefg", "7": "abc", "8": "abcdefg", "9": "abcdfg",
    " ": "",
}
CELL_W, CELL_H = 11, 21

# Each segment's exact pixel shape, measured from the all-lit test cell:
# horizontal bars (a, g, d) are a 2-row trapezoid (8px then 6px, tapering
# toward the verticals); verticals (f, b, e, c) are 1px at the row
# touching a bar and 2px everywhere else -- the hexagonal "cut corner" cut
# real LED segments have, not a plain rectangle.
_SEG_CELLS = {
    "a": [(dx, 1) for dx in range(1, 9)] + [(dx, 2) for dx in range(2, 8)],
    "g": [(dx, dy) for dy in (10, 11) for dx in range(2, 8)],
    "d": [(dx, 19) for dx in range(2, 8)] + [(dx, 20) for dx in range(1, 9)],
    "f": [(0, 3)] + [(dx, dy) for dy in range(4, 9) for dx in (0, 1)] + [(0, 9)],
    "b": [(9, 3)] + [(dx, dy) for dy in range(4, 9) for dx in (8, 9)] + [(9, 9)],
    "e": [(0, 12)] + [(dx, dy) for dy in range(13, 18) for dx in (0, 1)] + [(0, 18)],
    "c": [(9, 12)] + [(dx, dy) for dy in range(13, 18) for dx in (8, 9)] + [(9, 18)],
}


def _draw_digit(surface: pygame.Surface, x0: int, y0: int, ch: str, on: tuple[int, int, int]) -> None:
    lit = set(DIGIT_SEGMENTS.get(ch, ""))
    for name in lit:
        for dx, dy in _SEG_CELLS[name]:
            surface.set_at((x0 + dx, y0 + dy), on)


def _draw_readout(surface: pygame.Surface, x0: int, y0: int, text: str) -> None:
    for i, ch in enumerate(text):
        _draw_digit(surface, x0 + i * CELL_W, y0, ch, SEG_ON)


# Button/close icons: pixel-verified glyphs from Band B (o=white highlight,
# #=black fill, -=grey shadow -- the source's own beveled-icon shading).
_ICON_ROWS = {
    "prev": (
        "......oo.oo.oo.",
        ".....o##-o#-o#-",
        "....o###-o#-o#-",
        "...o####-o#-o#-",
        "....-###-o#-o#-",
        ".....-##-o#-o#-",
        "......---.--.--",
    ),
    "next": (
        "..oo.oo..oo....",
        "..o#-o#-o##o...",
        "..o#-o#-o###o..",
        "..o#-o#-o####o.",
        "..o#-o#-o###-..",
        "..o#-o#-o##-...",
        "...--.--.--....",
    ),
    "stop": (
        "...ooooo...",
        "...o####-..",
        "...o####-..",
        "...o####-..",
        "...o####-..",
        "...o####-..",
    ),
    "pause": (
        "..oo.oo...",
        "..o#-o#-..",
        "..o#-o#-..",
        "..o#-o#-..",
        "..o#-o#-..",
        "..o#-o#-..",
    ),
    "play": (
        "..o........",
        ".o#o.......",
        ".o##o......",
        ".o###o.....",
        ".o####o....",
        ".o###-.....",
        ".o##-......",
    ),
    "close": (
        "...o...o.....",
        "..-#o.o#-....",
        "...-#o#-.....",
        "....-#-......",
        "...o#-##o....",
        "..o##.-###o..",
        ".o##-..-#-...",
        "..-#....-....",
        "...-.........",
    ),
}
_ICON_COLOUR = {"o": BEZEL_LIGHT, "#": BG, "-": BEZEL_DARK}


def _draw_icon(surface: pygame.Surface, x0: int, y0: int, name: str, *, active: bool = False) -> None:
    colours = _ICON_COLOUR if not active else {**_ICON_COLOUR, "#": (191, 0, 0)}
    for dy, row in enumerate(_ICON_ROWS[name]):
        for dx, ch in enumerate(row):
            if ch != ".":
                surface.set_at((x0 + dx, y0 + dy), colours[ch])


# Every box in the source -- readout, meter, buttons -- is a flat 1px grey
# outline, not a bevel; see the module docstring's 2026-08-25 note.
def _flat_box(surface: pygame.Surface, x: int, y: int, w: int, h: int, *, fill: tuple[int, int, int] = PANEL) -> None:
    pygame.draw.rect(surface, fill, (x, y, w, h))
    pygame.draw.rect(surface, BEZEL_DARK, (x, y, w, h), width=1)


def _draw_transport(surface: pygame.Surface, x0: int, y0: int, active: str) -> None:
    _flat_box(surface, x0, y0, 18, 11)
    _draw_icon(surface, x0 + 3, y0 + 2, "prev", active=active == "prev")
    _flat_box(surface, x0 + 19, y0, 17, 11)
    _draw_icon(surface, x0 + 21, y0 + 2, "next", active=active == "next")
    _draw_icon(surface, x0 + 39, y0 + 2, "close")
    _flat_box(surface, x0, y0 + 12, 12, 10)
    _draw_icon(surface, x0 + 3, y0 + 15, "stop", active=active == "stop")
    _flat_box(surface, x0 + 13, y0 + 12, 12, 10)
    _draw_icon(surface, x0 + 16, y0 + 15, "pause", active=active == "pause")
    _flat_box(surface, x0 + 26, y0 + 12, 12, 10)
    _draw_icon(surface, x0 + 28, y0 + 15, "play", active=active == "play")


# Slider bank: 2px track (dark+light), 2px ticks every 6px, 12px pitch --
# all measured from Band B. No thumb/handle is visible in the source
# (a blank calibration state), so SLIDER_LEVELS below (one per slider,
# 0..1) is this file's own invented content, not measured.
def _draw_sliders(surface: pygame.Surface, x0: int, y0: int, count: int, height: int, levels: list[float]) -> None:
    for i in range(count):
        sx = x0 + i * 12
        for dy in range(height):
            surface.set_at((sx, y0 + dy), BEZEL_DARK)
            surface.set_at((sx + 1, y0 + dy), BEZEL_LIGHT)
        for ty in range(0, height, 6):
            surface.set_at((sx + 5, y0 + ty), BEZEL_LIGHT)
            surface.set_at((sx + 6, y0 + ty), BEZEL_LIGHT)
            surface.set_at((sx + 5, y0 + ty + 1), BEZEL_DARK)
            surface.set_at((sx + 6, y0 + ty + 1), BEZEL_DARK)
        thumb_y = y0 + int((1 - levels[i % len(levels)]) * (height - 3))
        pygame.draw.rect(surface, BEZEL_DARK, (sx - 3, thumb_y, 9, 3))


# "cd" logo, pixel-verified from Band B (re-measured 2026-08-25 -- the
# first pass was off by a column and missing the "d"'s ascender tip).
_CD_ROWS = (
    "..........-#o",
    "..........-#o",
    "..---...---#o",
    ".-###o.-####o",
    "-#oooo-#oo.#o",
    "-#o...-#o.-#o",
    "-#.--.-#.--#o",
    ".o###o.-####o",
    "..oooo..ooooo",
)


def _draw_cd_logo(surface: pygame.Surface, x0: int, y0: int) -> None:
    for dy, row in enumerate(_CD_ROWS):
        for dx, ch in enumerate(row):
            if ch != ".":
                surface.set_at((x0 + dx, y0 + dy), _ICON_COLOUR[ch])


def _draw_meter(surface: pygame.Surface, x0: int, y0: int, cols: int, rows: int, levels: list[float]) -> None:
    for col in range(cols):
        lit_rows = round(levels[col % len(levels)] * rows)
        for row in range(rows):
            lit = row >= rows - lit_rows
            surface.set_at((x0 + col * 3, y0 + row * 3), GREEN_ON if lit else GREEN_OFF)


WIDTH, HEIGHT = 340, 90

# Playback simulation constants -- all invented content, not measured.
TRACK_LENGTH = 180.0  # seconds per fake track
TRACK_COUNT = 12
PAUSE_EVERY = 25.0  # seconds of play between pauses
PAUSE_DURATION = 3.0
METER_COLS = 84
METER_ROWS = 12
METER_TICK = 0.06


class CDPlayerDemo(Demo):
    NATIVE_SIZE = (WIDTH, HEIGHT)

    def __init__(self, *, text: str | None = None, **_ignored) -> None:
        self.reset()

    def reset(self) -> None:
        self._elapsed = 0.0
        self._track = 1
        self._play_elapsed = 0.0  # time since the last pause ended
        self._paused = False
        self._pause_elapsed = 0.0
        self._meter_ticker = Ticker(METER_TICK)
        self._meter_phase = 0.0
        self._levels = [0.0] * METER_COLS

    def update(self, dt: float) -> None:
        if self._paused:
            self._pause_elapsed += dt
            if self._pause_elapsed >= PAUSE_DURATION:
                self._paused = False
                self._play_elapsed = 0.0
        else:
            self._elapsed += dt
            self._play_elapsed += dt
            if self._elapsed >= TRACK_LENGTH:
                self._elapsed = 0.0
                self._track = self._track % TRACK_COUNT + 1
            if self._play_elapsed >= PAUSE_EVERY:
                self._paused = True
                self._pause_elapsed = 0.0

        for _ in range(self._meter_ticker.advance(dt)):
            self._meter_phase += 1
            self._update_levels()

    def _update_levels(self) -> None:
        if self._paused:
            self._levels = [0.0] * METER_COLS
            return
        t = self._meter_phase * 0.3
        self._levels = [
            0.4 + 0.35 * math.sin(t + col * 0.5) + 0.2 * math.sin(t * 2.3 + col * 0.9)
            for col in range(METER_COLS)
        ]
        self._levels = [max(0.05, min(1.0, level)) for level in self._levels]

    def _active_button(self) -> str:
        return "pause" if self._paused else "play"

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(PANEL)

        _flat_box(surface, 6, 6, 150, 25, fill=BG)
        minutes, seconds = divmod(int(self._elapsed), 60)
        readout = f"{self._track:2d}  {minutes:1d} {seconds:02d}"
        _draw_readout(surface, 12, 10, readout)

        _draw_transport(surface, 165, 8, self._active_button())

        _flat_box(surface, 6, 40, 258, 44, fill=BG)
        _draw_meter(surface, 10, 44, METER_COLS, METER_ROWS, self._levels)

        _flat_box(surface, 270, 40, 64, 44)
        _draw_cd_logo(surface, 273, 42)
        _draw_sliders(surface, 273, 60, 4, 18, [0.6, 0.4, 0.7, 0.5])


DEMO_CLASS = CDPlayerDemo
