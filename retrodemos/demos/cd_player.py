"""CD Player: simulated playback, no real audio -- a numeric LED
track/time readout, a dot-matrix spectrum/level meter, transport buttons,
and a companion equalizer window with a vertical slider bank, composited
from pieces reverse-engineered from `images/CDPLAYER.png` (see
`docs/pixel-archaeology.md` for method, `docs/cd-player.md` for the demo
overview).

`CDPLAYER.png` (384x78) turned out not to be one coherent screenshot, the
same surprise Title's and Dooley's source images held: it bundles three
stacked reference bands. Band A (y0-31, x0-284) is the main player
window -- close button, "cd" logo, a wide readout box (spectrum dots,
3-digit counter, repeat/shuffle status text), and 5 transport buttons.
The companion equalizer window (x287-383, y0-53) sits beside it, own
close button, own "cd" logo, 6-band slider bank -- taller than the main
window since it isn't split at y31 the way the main window is. Band B
(y32-53, x0-247) is a sprite/reference strip below the main window, not
part of any real window -- icon and digit-shape references only, same
role Dooley's own reference material played. Band C (y56-77) is a
separate full-width level-meter strip, reference for the meter's colours
and pitch, not a UI element of its own.

A 2026-08-25 review (Bruce playtesting flagged the demo as "far from
pixel perfect") went through two passes. The first pass fixed real box
border and digit-font mistakes but still treated the whole top ~90px as
one loosely-composed panel, not the two actual windows the source shows.
The second pass (this one) rebuilt the layout around that: two window
frames side by side, each with its own close button and "cd" logo, the
big dot-matrix spectrum living *inside* the main readout box (not a
separate meter panel underneath), 5 transport buttons (not 6 -- the
extra "eject" icon only exists in Band B's reference capture, never in
the real window), and 6 sliders (not 4).

Every piece is pixel-verified against Band A directly for the main and
equalizer windows themselves (not Band B, which is reference material
only, confirmed by finding Band A's own transport buttons use a
different border style than Band B's copies of the same icons): the
outer window frames are a raised bevel (white top/left, grey
bottom/right); the readout box and the transport button sub-panel are
sunken (reversed); individual transport buttons are a light 3-sided
highlight (top/left/right) sitting inside that sunken well. The dot-matrix
meter's own "dots" are a genuine 2px NW-SE diagonal glint, not a single
pixel -- confirmed against both the spectrum area and Band C's reference
strip, and missed by the first two passes (see _draw_dot_glint). The digit
segment geometry, all button/close icons, the slider bank's track+tick
geometry, and the "cd" logo (reused identically by both windows) are all
literal coordinate/glyph data measured from the source. The one
genuinely invented pieces are the playback simulation itself (no real
audio) and the slider levels (no thumb/handle is visible in the source,
a blank calibration state).

The main and equalizer windows are genuinely separate in the source, not
one panel wearing two close buttons -- confirmed by a second playtest
pass (2026-08-25): dragging one in the original reveals/reorders the
other, so CD Player is now interactive (the second demo to be, after
Bruce's Windows), not automated attract-mode. Each window renders onto
its own Surface (`_render_main_window`/`_render_eq_window`) and gets
blited at its own draggable position; `handle_event` tracks per-window
position and z-order the same way `desktop.py`'s `_OpenWindow` does,
just scoped to two windows instead of an open-ended set. The demo canvas
(480x180) is bigger than the two windows combined so there's room to
drag them apart; they start docked together, matching the source
screenshot's own layout.

A third playtest pass (2026-08-26) reconsidered the readout's two dot
areas. The transport icons were still visibly off-centre (the 2026-08-25
fix solved clipping but not centring -- each `icon_offset` now comes from
matching the icon's own black-pixel bounding box in `_ICON_ROWS` against
its measured bounding box in the source, not eyeballed placement). More
substantially: the big dot area (formerly a generic "spectrum meter") now
scrolls a marquee -- the current fake track's title, then "0123456789"
(a nod to LED's own `NumbersPhase` scroll, the lighter-weight version of
"run the other LED demos on it" that doesn't require hosting a whole
second Demo's update loop inside a differently-shaped display) -- and the
small dot swatch beside "1AR" (previously a static all-lit copy of the
source's own calibration pattern) now animates as a real per-column
frequency bar meter, reusing the same simulated levels the equalizer
slider bank doesn't have room to show. Both reuse Band C's measured
green-on/red-off meter colours (`GREEN_ON`/`GREEN_OFF`) rather than the
static readout's plain red, since both are now genuine meters, not
fixed text.

A fourth pass the same day (playtesting again: "buttons still off",
"colours off", "borders off", "black dot top right", "right borders
off") went back to `images/CDPLAYER.png` with the reconstruct-and-diff
rigor `tank_status_window.py` uses, rather than re-eyeballing: the
window was 3px narrower than the source (285 vs. the real 288), the
readout box 1px narrower on its own right edge, the transport sub-panel
1px short on its own bottom edge, every transport button's right/bottom
edges turned out not to exist at all (measured chrome is top+left
highlight only -- the earlier "3-sided" and "4-sided-with-shadow"
theories were both wrong, caught by scanning a face column clear of any
icon glyph instead of one that happened to clip one), the divider lines
between buttons needed their own mitered T-junctions where they meet a
button's own left edge, stop/pause both turned out to be missing their
icon's bottom shadow row, and play's own taper was truncated 2 rows
early. All of it is now covered by
`tests/test_cd_player.py::test_transport_panel_is_byte_exact_against_the_source_image`
and `test_main_window_frame_is_byte_exact_excluding_dynamic_content` --
matching every pixel except the readout/status text's own dynamic
content (never comparable to the source's fixed calibration display) and
the close-button/"cd"-logo corner, which turned out to have its own
small bevel box not yet re-measured -- a known remaining gap, not a
regression.
"""

from __future__ import annotations

import math

import pygame

from retrodemos.framework.demo import Demo
from retrodemos.framework.pixel_font import text_cells
from retrodemos.framework.ticker import Ticker
from retrodemos.framework.window_chrome import bevel_rect

BG = (0, 0, 0)
PANEL = (192, 192, 192)
BEZEL_DARK = (128, 128, 128)
BEZEL_LIGHT = (255, 255, 255)

# Measured directly from Band A's readout: (191, 0, 0). The source never
# shows an unlit segment next to a lit one -- an "off" segment is simply
# not drawn, same as the panel's own black background -- so there's no
# separate off-colour to measure or invent.
SEG_ON = (191, 0, 0)
GREEN_ON = (0, 255, 0)
GREEN_OFF = (191, 0, 0)  # measured -- Band C's own "unlit" colour, not invented

# Segments: a=top, b=top-right, c=bottom-right, d=bottom, e=bottom-left,
# f=top-left, g=middle. What looked like a calibration strip spelling
# "0123456789" is actually a segment-test pattern with every segment lit
# -- there's no source data for individual digit shapes, so this is the
# standard closed 6/9 form, not measured content. Band A's own "888"
# counter reuses this same font at the same 12px pitch (confirmed by
# measuring its digit cells directly), just 3 digits instead of 17.
DIGIT_SEGMENTS = {
    "0": "abcdef", "1": "bc", "2": "abdeg", "3": "abcdg", "4": "bcfg",
    "5": "acdfg", "6": "acdefg", "7": "abc", "8": "abcdefg", "9": "abcdfg",
    " ": "",
}
CELL_W, CELL_H = 11, 21

# Each segment's exact pixel shape, measured from an all-lit test cell:
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


def _draw_digits(surface: pygame.Surface, x0: int, y0: int, text: str, *, pitch: int = CELL_W) -> None:
    for i, ch in enumerate(text):
        _draw_digit(surface, x0 + i * pitch, y0, ch, SEG_ON)


# Button/close icons: pixel-verified glyphs (o=white highlight, #=black
# fill, -=grey shadow -- the source's own beveled-icon shading). "close"
# is the X glyph both windows' own corner close buttons use, not a 6th
# transport button -- Band A's real transport cluster only has 5 (see
# module docstring).
_ICON_ROWS = {
    # Re-extracted 2026-08-26 as each icon's own tight bounding box within
    # its button (playtesting: stop/pause were both missing their bottom
    # shadow row entirely -- the icon reads as one row shorter than the
    # source's -- and play's taper was truncated 2 rows early). Masks are
    # tight now (no padding baked in); _TRANSPORT_BUTTONS' own icon_offset
    # is each one's measured (bbox_x - button_x, bbox_y - button_y).
    "prev": (
        "...oo.oo.oo.",
        "..o##-o#-o#-",
        ".o###-o#-o#-",
        "o####-o#-o#-",
        ".-###-o#-o#-",
        "..-##-o#-o#-",
        "...---.--.--",
    ),
    "next": (
        "oo.oo..oo...",
        "o#-o#-o##o..",
        "o#-o#-o###o.",
        "o#-o#-o####o",
        "o#-o#-o###-.",
        "o#-o#-o##-..",
        ".--.--.--...",
    ),
    "stop": (
        "ooooo.",
        "o####-",
        "o####-",
        "o####-",
        "o####-",
        "o####-",
        ".-----",
    ),
    "pause": (
        "oo.oo.",
        "o#-o#-",
        "o#-o#-",
        "o#-o#-",
        "o#-o#-",
        "o#-o#-",
        ".--.--",
    ),
    "play": (
        ".o....",
        "o#o...",
        "o##o..",
        "o###o.",
        "o####o",
        "o###-.",
        "o##-..",
        "o#-...",
        ".-....",
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


# The small status cluster right of the "888" counter -- a repeat/shuffle
# icon plus "1AR" text. No pixel font was built for this text; it's
# copied verbatim as a lit/unlit mask (x209-241, y2-11 in the source),
# the same approach the "cd" logo and button icons use for one-off
# glyphs. The dense (2px pitch) dot-matrix swatch that sits below it in
# the source is no longer part of this fixed mask -- playtesting
# (2026-08-26) repurposed it into an animated frequency bar meter (see
# EQ_BAR_* / _draw_eq_bars below), since the source's own all-lit test
# pattern there was never meant to be copied as static content, the same
# reasoning that turned the big meter into a marquee.
_STATUS_TEXT_ROWS = (
    "                                 ",
    "                                 ",
    "                                 ",
    "                                 ",
    "           #      #   ##  ###    ",
    "    #####.####   ##  #  # #  #   ",
    "   #.......#..#   #..#..#.#..#   ",
    "   #..#.......#   #..####.###    ",
    "    ####.#####    #..#..#.#..#   ",
    "      #..........###.#..#.#..#   ",
)


def _draw_status_text(surface: pygame.Surface, x0: int, y0: int) -> None:
    for dy, row in enumerate(_STATUS_TEXT_ROWS):
        for dx, ch in enumerate(row):
            if ch == "#":
                surface.set_at((x0 + dx, y0 + dy), SEG_ON)


# Small EQ swatch, measured the same 2px pitch/14x7 layout the source's
# own static dot pattern used (see _STATUS_TEXT_ROWS' comment) -- now
# driven by simulated levels instead of always-lit. Column/row origins
# are relative to STATUS_ORIGIN, matching where the old static rows sat.
EQ_BAR_X0 = 3
EQ_BAR_Y0 = 11
EQ_BAR_COLS = 14
EQ_BAR_ROWS = 7
EQ_BAR_PITCH = 2


def _draw_eq_bars(surface: pygame.Surface, x0: int, y0: int, levels: list[float]) -> None:
    for col in range(EQ_BAR_COLS):
        level = levels[col % len(levels)]
        lit_rows = round(level * EQ_BAR_ROWS)
        for row in range(EQ_BAR_ROWS):
            lit = row >= EQ_BAR_ROWS - lit_rows
            colour = GREEN_ON if lit else GREEN_OFF
            surface.set_at((x0 + EQ_BAR_X0 + col * EQ_BAR_PITCH, y0 + EQ_BAR_Y0 + row * EQ_BAR_PITCH), colour)


def _sunken_box(surface: pygame.Surface, rect: tuple[int, int, int, int], *, fill: tuple[int, int, int] = PANEL) -> None:
    """A sunken bevel (grey top/left, white bottom/right), mitered the
    same way `framework.window_chrome.bevel_rect` is. That helper always
    fills PANEL first, which doesn't fit the readout box's black
    interior, so this is its own small sibling rather than a reuse.
    The two mitered corners (top-right, bottom-left) always read as the
    surrounding window's own PANEL, regardless of `fill` -- with a black
    `fill` (the readout box) that corner pixel was otherwise left black
    instead of unset, a real bug (playtesting, 2026-08-26: "black dot top
    right of CD display") transport's own PANEL-on-PANEL fill happened to
    hide."""
    x, y, w, h = rect
    pygame.draw.rect(surface, fill, rect)
    pygame.draw.line(surface, BEZEL_DARK, (x, y), (x + w - 2, y))
    pygame.draw.line(surface, BEZEL_DARK, (x, y), (x, y + h - 2))
    pygame.draw.line(surface, BEZEL_LIGHT, (x + w - 1, y + 1), (x + w - 1, y + h - 1))
    pygame.draw.line(surface, BEZEL_LIGHT, (x + 1, y + h - 1), (x + w - 1, y + h - 1))
    surface.set_at((x + w - 1, y), PANEL)
    surface.set_at((x, y + h - 1), PANEL)


# Transport sub-panel: measured directly from Band A (x247-283, y3-28),
# not Band B -- Band A's own buttons turned out to use a different border
# style than Band B's copies of the same icons (light 3-sided highlight
# here vs. Band B's flat grey), so Band B was reference for icon shapes
# only, never for chrome. 5 buttons: prev/next on top, stop/pause/play
# below -- there is no 6th "eject" button in the real window.
_TRANSPORT_RECT = (247, 3, 38, 26)
# icon_offset re-measured again 2026-08-26 (playtesting: still visibly
# off-centre against the source, bleeding past the button edges) -- the
# 2026-08-25 pass fixed the vertical clipping but never actually solved
# for the offset that lands each icon's own black-pixel bounding box on
# top of the source's, which is what these values are now: found by
# comparing each button's measured black bbox in images/CDPLAYER.png
# against the same bbox within `_ICON_ROWS`' own mask, not eyeballed.
_TRANSPORT_BUTTONS = (
    ("prev", (248, 4, 17, 10), (3, 2)),
    ("next", (266, 4, 17, 10), (3, 2)),
    ("stop", (248, 15, 11, 12), (3, 3)),
    ("pause", (260, 15, 11, 12), (3, 3)),
    ("play", (272, 15, 11, 12), (3, 2)),
)


def _button_highlight(surface: pygame.Surface, rect: tuple[int, int, int, int], *, pressed: bool = False) -> None:
    """Each transport button is a highlight on 2 sides only -- top and
    left, full length on each -- re-measured 2026-08-26 (playtesting:
    still visibly off) after two false leads: it does NOT have its own
    right or bottom edge line at all (a clean column/row scan away from
    any icon glyph -- which has its own 'o'/'-' shading that a scan
    closer to one had been misread as chrome -- shows plain panel colour
    the entire face, no shadow). The separating lines between buttons
    (see `_TRANSPORT_DIVIDERS`) are a shared structure, not owned by
    either neighbour. `pressed` swaps highlight for shadow, an invented
    press animation (no source data exists for a pressed state)."""
    x, y, w, h = rect
    colour = BEZEL_DARK if pressed else BEZEL_LIGHT
    pygame.draw.line(surface, colour, (x, y), (x + w - 1, y))
    pygame.draw.line(surface, colour, (x, y), (x, y + h - 1))


# Dividers between adjacent buttons, and between the last button in each
# row and the panel's own right edge -- measured the same session as the
# button rects: each spans from just below its row's own top-highlight
# row through the shared horizontal divider row that closes that row out
# (y=14 for the prev/next row, y=27 for stop/pause/play's).
_TRANSPORT_DIVIDERS = (
    (265, 5, 14), (283, 5, 14),  # prev|next, next|panel-edge
    (259, 16, 27), (271, 16, 27), (283, 16, 27),  # stop|pause, pause|play, play|panel-edge
)
# Each row-divider line, plus the x-positions it must leave alone --
# mitered the same "leave the T-junction unset" way `black_ring` leaves
# its own corners (see tank_status_window_grid.py for the same idea):
# wherever a button's own left-highlight column crosses this row, the
# highlight wins and the divider colour doesn't show. y=27's line also
# reaches one column further left than y=14's, into the panel's own left
# edge -- _sunken_box's own left edge stops one row short of it.
_TRANSPORT_ROW_DIVIDERS = (
    (14, 248, 283, (248, 266)),
    (27, 247, 283, (248, 260, 272)),
)


def _draw_transport(surface: pygame.Surface, active: str, *, pressed: str | None = None) -> None:
    _sunken_box(surface, _TRANSPORT_RECT)
    for y, x0, x1, skip_x in _TRANSPORT_ROW_DIVIDERS:
        pygame.draw.line(surface, BEZEL_DARK, (x0, y), (x1, y))
        for x in skip_x:
            surface.set_at((x, y), PANEL)
    for x, y0, y1 in _TRANSPORT_DIVIDERS:
        pygame.draw.line(surface, BEZEL_DARK, (x, y0), (x, y1))
    for name, rect, icon_offset in _TRANSPORT_BUTTONS:
        is_pressed = name == pressed
        _button_highlight(surface, rect, pressed=is_pressed)
        # pressed buttons nudge their icon 1px down/right, reading as
        # physically pushed in -- same invented-animation reasoning as
        # the highlight inversion above.
        nudge = 1 if is_pressed else 0
        _draw_icon(surface, rect[0] + icon_offset[0] + nudge, rect[1] + icon_offset[1] + nudge, name, active=active == name)


# Slider bank: 2px track (dark+light), 2px ticks every 6px, 12px pitch,
# 6 sliders -- all measured from the equalizer window directly. No
# thumb/handle is visible in the source (a blank calibration state), so
# the demo's slider levels and thumb positions are invented content.
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


# "cd" logo, pixel-verified -- both windows show the literal same glyph
# (re-measured 2026-08-25 against both instances to confirm).
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


# Each "dot" isn't a single pixel -- it's a 2px NW-SE diagonal glint,
# confirmed both in the readout and in Band C's own reference strip (row
# y: one pixel; row y+1: the next pixel over). Missed in the first two
# passes, which drew a single set_at() per dot. Kept as the shared style
# for the title marquee below -- still a dot-matrix display, just
# scrolling text instead of a generic level meter now (2026-08-26
# playtesting: "the left is a display for track titles").
def _draw_dot_glint(surface: pygame.Surface, x: int, y: int, colour: tuple[int, int, int]) -> None:
    surface.set_at((x, y), colour)
    surface.set_at((x + 1, y + 1), colour)


def _draw_title_marquee(surface: pygame.Surface, x0: int, y0: int, cols: int, cells: set[tuple[int, int]]) -> None:
    for col, row in cells:
        if 0 <= col < cols:
            _draw_dot_glint(surface, x0 + col * 3, y0 + row * 3, GREEN_ON)


# Window frames -- measured from Band A/the equalizer window directly:
# both are a raised bevel (white top/left, grey bottom/right), no black
# ring around them the way Bruce's Windows has. reuses
# framework.window_chrome.bevel_rect, settling PLAN.md's open question
# of whether CD Player should route its chrome through that module --
# its own inner controls (readout, buttons) still don't, since those are
# a different border style (sunken, or the 3-sided highlight above).
# Both rects are window-local (each window renders onto its own Surface,
# sized to its rect, at (0,0)) -- see _render_main_window/_render_eq_window.
# The two are truly separate windows in the source, not one panel: each
# has its own close button, can be dragged independently, and clicking
# either brings it in front of the other (2026-08-25, playtesting).
MAIN_WINDOW_RECT = (0, 0, 288, 32)
EQ_WINDOW_RECT = (0, 0, 97, 54)
READOUT_RECT = (19, 3, 224, 26)
TITLE_ORIGIN = (21, 6)
DIGITS_ORIGIN = (174, 5)
STATUS_ORIGIN = (209, 2)
CLOSE_ICON_OFFSET = (2, 2)
CD_LOGO_OFFSET = (3, 18)
EQ_CLOSE_OFFSET = (2, 1)
EQ_DIVIDER_Y = 12
EQ_CD_LOGO_POS = (7, 44)
EQ_SLIDER_ORIGIN = (26, 18)
EQ_SLIDER_HEIGHT = 36
EQ_SLIDER_COUNT = 6

# The demo canvas is bigger than the two windows themselves so there's
# room to drag them apart -- they start docked together, matching the
# source screenshot's own layout.
WIDTH, HEIGHT = 480, 180
DESK_BG = (72, 76, 78)  # invented -- a neutral backdrop for the floating windows
MAIN_START_POS = (40, 24)
EQ_START_POS = (40 + MAIN_WINDOW_RECT[2] + 2, 24)

# Playback simulation constants -- all invented content, not measured.
TRACK_LENGTH = 180.0  # seconds per fake track
TRACK_COUNT = 12
PAUSE_EVERY = 25.0  # seconds of play between pauses
PAUSE_DURATION = 3.0
TITLE_COLS = 50  # (168 - 21) // 3 + 1, matching the measured spectrum area
TITLE_ROWS = 7  # == pixel_font.GLYPH_H, so marquee text needs no row offset
TITLE_SCROLL_SPEED = 10.0  # dot-columns/sec, invented
EQ_TICK = 0.06
SLIDER_LEVELS = [0.6, 0.4, 0.7, 0.5, 0.55, 0.45]  # invented -- no thumb visible in the source


class CDPlayerMainWindow(Demo):
    """The main player window, standalone: readout, transport, its own
    close button and "cd" logo. Draws its own complete chrome (see
    module docstring), so a host -- the desktop shell, or `CDPlayerDemo`
    below for standalone launches -- reads `close_rect`/`button_rects`
    directly off this instance to know where its controls are, rather
    than this window being wrapped in someone else's generic chrome.

    `reveal_equalizer` is a flag, not a callback: it's set True by a
    body click (not on a button or the close control) and left for
    whoever owns this window to notice and clear next frame -- avoids
    this window needing to know anything about how its host manages a
    second window. `closed` works the same way for the close button.
    """

    NATIVE_SIZE = MAIN_WINDOW_RECT[2:]

    def __init__(self, *, text: str | None = None, **_ignored) -> None:
        self.close_rect = pygame.Rect(0, 0, 14, 13)
        self.button_rects = {name: pygame.Rect(*rect) for name, rect, _offset in _TRANSPORT_BUTTONS}
        self.reset()

    def reset(self) -> None:
        self._elapsed = 0.0
        self._track = 1
        self._play_elapsed = 0.0  # time since the last pause ended
        self._paused = False
        self._pause_elapsed = 0.0
        self._eq_ticker = Ticker(EQ_TICK)
        self._eq_phase = 0.0
        self._levels = [0.0] * EQ_BAR_COLS
        self._pressed: str | None = None
        self.reveal_equalizer = False
        self.closed = False
        self._marquee_mode = "title"
        self._marquee_offset = 0.0
        self._marquee_cells, self._marquee_width = self._marquee_content()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.close_rect.collidepoint(event.pos):
                self.closed = True
                return
            for name, rect in self.button_rects.items():
                if rect.collidepoint(event.pos):
                    self._pressed = name
                    return
            self.reveal_equalizer = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._pressed = None

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

        for _ in range(self._eq_ticker.advance(dt)):
            self._eq_phase += 1
            self._update_levels()

        self._marquee_offset += TITLE_SCROLL_SPEED * dt
        if self._marquee_offset >= self._marquee_width + TITLE_COLS:
            self._marquee_offset = 0.0
            self._marquee_mode = "numbers" if self._marquee_mode == "title" else "title"
            self._marquee_cells, self._marquee_width = self._marquee_content()

    def _marquee_content(self) -> tuple[set[tuple[int, int]], int]:
        # "title" is an invented placeholder ("TRACK 01", no real track
        # metadata exists to show -- see module docstring); "numbers"
        # scrolls "0123456789", the lighter-weight nod to LED's own
        # NumbersPhase this demo borrows instead of hosting a second Demo.
        text = f"TRACK {self._track:02d}" if self._marquee_mode == "title" else "0123456789"
        return text_cells(text)

    def _update_levels(self) -> None:
        if self._paused:
            self._levels = [0.0] * EQ_BAR_COLS
            return
        t = self._eq_phase * 0.3
        self._levels = [
            0.4 + 0.35 * math.sin(t + col * 0.5) + 0.2 * math.sin(t * 2.3 + col * 0.9)
            for col in range(EQ_BAR_COLS)
        ]
        self._levels = [max(0.05, min(1.0, level)) for level in self._levels]

    def _active_button(self) -> str:
        return "pause" if self._paused else "play"

    def draw(self, surface: pygame.Surface) -> None:
        bevel_rect(surface, (0, 0, *self.NATIVE_SIZE), raised=True)
        cx, cy = CLOSE_ICON_OFFSET
        _draw_icon(surface, cx, cy, "close")
        lx, ly = CD_LOGO_OFFSET
        _draw_cd_logo(surface, lx, ly)

        _sunken_box(surface, READOUT_RECT, fill=BG)
        mx, my = TITLE_ORIGIN
        offset = int(self._marquee_offset)
        visible_cells = {(TITLE_COLS + cx - offset, cy) for cx, cy in self._marquee_cells}
        _draw_title_marquee(surface, mx, my, TITLE_COLS, visible_cells)
        minutes, seconds = divmod(int(self._elapsed), 60)
        readout = f"{min(minutes, 9)}{seconds:02d}"
        dx, dy = DIGITS_ORIGIN
        _draw_digits(surface, dx, dy, readout, pitch=12)
        sx, sy = STATUS_ORIGIN
        _draw_status_text(surface, sx, sy)
        _draw_eq_bars(surface, sx, sy, self._levels)

        _draw_transport(surface, self._active_button(), pressed=self._pressed)


class CDPlayerEqualizerWindow(Demo):
    """The companion equalizer window, standalone: its own close button,
    "cd" logo, and the 6-slider bank. No functional sliders yet (no
    thumb/handle exists in the source to know how one should look while
    being dragged, see module docstring) -- just the close control."""

    NATIVE_SIZE = EQ_WINDOW_RECT[2:]

    def __init__(self, *, text: str | None = None, **_ignored) -> None:
        cx, cy = EQ_CLOSE_OFFSET
        self.close_rect = pygame.Rect(cx - 2, cy - 1, 14, 13)
        self.reset()

    def reset(self) -> None:
        self.closed = False

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.close_rect.collidepoint(event.pos):
            self.closed = True

    def draw(self, surface: pygame.Surface) -> None:
        ew, eh = self.NATIVE_SIZE
        bevel_rect(surface, (0, 0, ew, eh), raised=True)
        ecx, ecy = EQ_CLOSE_OFFSET
        _draw_icon(surface, ecx, ecy, "close")
        pygame.draw.line(surface, BEZEL_DARK, (1, EQ_DIVIDER_Y), (ew - 2, EQ_DIVIDER_Y))
        pygame.draw.line(surface, BEZEL_LIGHT, (1, EQ_DIVIDER_Y + 1), (ew - 2, EQ_DIVIDER_Y + 1))
        _draw_cd_logo(surface, *EQ_CD_LOGO_POS)
        sx0, sy0 = EQ_SLIDER_ORIGIN
        _draw_sliders(surface, sx0, sy0, EQ_SLIDER_COUNT, EQ_SLIDER_HEIGHT, SLIDER_LEVELS)


class CDPlayerDemo(Demo):
    """Standalone combo view -- both windows on one canvas, for
    `python -m retrodemos cd_player` (a single Demo, no desktop shell
    around it to host two independent windows). The desktop shell itself
    does *not* use this class: it opens `CDPlayerMainWindow` and
    `CDPlayerEqualizerWindow` directly as two independent top-level
    windows instead (see `desktop.py`'s own CD Player handling) --
    nesting them inside a third wrapper window looked wrong once seen on
    the real desktop (2026-08-25 playtesting: "should get real windows,
    not appear in another window"). This class re-implements that same
    per-window position/z-order/reveal/close bookkeeping at a smaller
    scale so the standalone view keeps working the same way.

    The equalizer starts hidden, same as on the desktop -- clicking the
    main window's body (not a button, not its close control) reveals it.
    """

    NATIVE_SIZE = (WIDTH, HEIGHT)

    def __init__(self, *, text: str | None = None, **_ignored) -> None:
        self.reset()

    def reset(self) -> None:
        self.main = CDPlayerMainWindow()
        self.eq = CDPlayerEqualizerWindow()
        self._win_pos = {"main": list(MAIN_START_POS), "eq": list(EQ_START_POS)}
        self._order: list[str] = ["main"]  # equalizer hidden until revealed
        self._dragging: str | None = None
        self._drag_offset = (0, 0)
        self._mouse_down_key: str | None = None

    def _demo(self, key: str) -> Demo:
        return self.main if key == "main" else self.eq

    def _window_rect(self, key: str) -> pygame.Rect:
        return pygame.Rect(self._win_pos[key], self._demo(key).NATIVE_SIZE)

    def _window_at(self, pos: tuple[int, int]) -> str | None:
        for key in reversed(self._order):
            if self._window_rect(key).collidepoint(pos):
                return key
        return None

    def _focus(self, key: str) -> None:
        self._order.remove(key)
        self._order.append(key)

    def _reveal_equalizer(self) -> None:
        if "eq" not in self._order:
            self._order.append("eq")
        else:
            self._focus("eq")

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            key = self._window_at(event.pos)
            if key is None:
                return
            self._focus(key)
            self._mouse_down_key = key
            demo = self._demo(key)
            wx, wy = self._win_pos[key]
            local_pos = (event.pos[0] - wx, event.pos[1] - wy)
            demo.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=local_pos, button=1))
            if demo.closed:
                demo.closed = False
                self._order.remove(key)
                return
            if key == "main" and self.main.reveal_equalizer:
                self.main.reveal_equalizer = False
                self._reveal_equalizer()
            hit_control = demo.close_rect.collidepoint(local_pos) or any(
                r.collidepoint(local_pos) for r in getattr(demo, "button_rects", {}).values()
            )
            if not hit_control:
                self._dragging = key
                self._drag_offset = (event.pos[0] - wx, event.pos[1] - wy)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._mouse_down_key is not None and self._mouse_down_key in self._order:
                demo = self._demo(self._mouse_down_key)
                wx, wy = self._win_pos[self._mouse_down_key]
                local_pos = (event.pos[0] - wx, event.pos[1] - wy)
                demo.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=local_pos, button=1))
            self._dragging = None
            self._mouse_down_key = None
        elif event.type == pygame.MOUSEMOTION and self._dragging is not None:
            ox, oy = self._drag_offset
            self._win_pos[self._dragging] = [event.pos[0] - ox, event.pos[1] - oy]

    def update(self, dt: float) -> None:
        for key in self._order:
            self._demo(key).update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(DESK_BG)
        for key in self._order:  # back to front, so the focused window ends up on top
            demo = self._demo(key)
            content = pygame.Surface(demo.NATIVE_SIZE)
            demo.draw(content)
            surface.blit(content, self._win_pos[key])


DEMO_CLASS = CDPlayerDemo
