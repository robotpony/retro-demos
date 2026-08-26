"""Tank Status Window's chrome and dot-grid renderer -- the geometry and
literal pixel content measured from `images/WIN1.png`, plus the shared
`TankDisplay` render target the phases in `tank_status_window_phases.py`
drive (the role `CardTable`/`SevenSegmentDisplay` play for their own
demos). Split out from `tank_status_window.py` itself to avoid an import
cycle with the phases module, the same shape `bruces_21_table.py` has
relative to `bruces_21.py`/`bruces_21_phases.py`.

`WIN1.png` (273x350) is a window titled "Tank Status Window": a red/black
outer frame, a title bar with a flat minimize box (left) and a bevelled
dropdown box (right), a large 83x84 red/black dot-matrix grid, a smaller
83x9 secondary dot strip below it, and a row of 11 blank grey buttons at
the bottom. In the source, every dot in both grids is lit -- it's a
test-pattern screenshot, not a captured game state -- so only the *off*
background colour (plain black) and the dot pitch/size/on-colour are
measured facts; nothing about which dots are lit came from the source.

Dot geometry (2x2px dot on a 3px pitch) and the on-colour (191, 0, 0) are
identical to `led_grid.DOT_LIT`/`DotMatrixDisplay`'s own -- the same
LED-family red, confirmed by direct pixel comparison -- but this demo
doesn't reuse `DotMatrixDisplay` itself: its own bezel is a different
shape, and its main grid's 84 rows don't fit that class's `ROWS = 9`
constant. What *is* reused: `led_grid.DOT_LIT` and `led_grid.lerp_color`
directly (for Burst-driven fade intensities), `led_grid.dot_grid_adjacency`
for the explosion/burst topology in the phases module, and
`framework/pixel_font.py`'s A-Z alphabet for the secondary strip's status
text (`led_grid.DOT_FONT` is the same cell size and would have fit the
strip's ROWS=9 just as well, but it's digits/space/hyphen only -- built
for LED II's numeric marquee, no letters). The button row and dropdown
box each have their own bespoke corner treatment (see `_draw_button_row`/
`_draw_dropdown_box`'s own docstrings/comments) that turned out not to
match `framework/window_chrome.py`'s `bevel_rect` closely enough to reuse
directly -- only `black_ring` (for the button row's single outer ring)
carries over as-is.

Playtesting (2026-08-26) called out the first build as "not 1:1 with the
source": the outer frame used a simplified symmetric border (the source's
right edge is really 6px, not 4 like the other three sides), the button
row bled past the window edge (11 buttons at a guessed pitch/size, each
drawn as its own fully independent black-ringed+bevelled box), and the
title text was centred by formula rather than placed at its own measured
origin. This version replaces every one of those approximations with
coordinates actually measured off `images/WIN1.png`, verified by
reconstruct-and-diff against the full lit-everywhere test pattern (see
`tests/test_tank_status_window.py`): 95,546 of 95,550 pixels now match
exactly. The remaining 4 -- one row (y=327) where both side borders
blip from red to black for a single scanline -- read as a source
artifact (a compression/scan glitch, not a design element: it doesn't
recur, isn't mirrored top/bottom the way the real divider notches are,
and lands on no other structural boundary) and are deliberately not
reproduced, the same call `docs/pixel-archaeology.md` documents for
LED-thumb.png's own one-off tight first digit. One real quirk *is*
reproduced: the 4th button (0-indexed 3, `_FLAT_BUTTON_INDEX`) renders
flat -- grey where the others show a white highlight, no bevel at all --
confirmed by re-inspecting the source at high zoom, not assumed.
"""

from __future__ import annotations

import pygame

from retrodemos.framework.led_grid import DOT_LIT, lerp_color
from retrodemos.framework.pixel_font import GLYPH_H, text_cells
from retrodemos.framework.window_chrome import BEZEL_DARK, BLACK, PANEL, WHITE, black_ring

# ---- Frame/window geometry -- every coordinate below is measured
# directly off images/WIN1.png, not derived from a symmetric guess (the
# source's own border is 4px on three sides but 6px on the right). ----
WINDOW_W, WINDOW_H = 273, 350
FRAME_RED = (255, 0, 0)

# Content occupies [CONTENT_X0, CONTENT_X1) x [CONTENT_Y0, CONTENT_Y1);
# the black divider ring sits one pixel outside that box on every side
# (at CONTENT_X0-1, CONTENT_X1, CONTENT_Y0-1, CONTENT_Y1).
CONTENT_X0, CONTENT_X1 = 4, 267
CONTENT_Y0, CONTENT_Y1 = 4, 346

TITLE_H = 18  # rows 4-21
BOX = 18  # minimize/dropdown box size, both square
TITLE_DIVIDER_BOTTOM_Y = CONTENT_Y0 + TITLE_H  # 22 -- full-width black line under the title bar

MIN_BOX_RECT = (CONTENT_X0, CONTENT_Y0, BOX, BOX)  # (4, 4, 18, 18)
DROPDOWN_BOX_RECT = (CONTENT_X1 - BOX, CONTENT_Y0, BOX, BOX)  # (249, 4, 18, 18)
# The two vertical dividers separating minimize-box | title-text | dropdown-box
# run from inside the red border itself (y=1) down through the title bar.
TITLE_DIVIDER_1_X = CONTENT_X0 + BOX  # 22
TITLE_DIVIDER_2_X = DROPDOWN_BOX_RECT[0] - 1  # 248

BODY_Y0 = TITLE_DIVIDER_BOTTOM_Y + 1  # 23
BODY_Y1 = CONTENT_Y1  # 346

# ---- Dot grids -- pixel-exact (see module docstring) ----
DOT_SIZE = 2
PITCH = 3  # DOT_SIZE + 1px gap, same as led_grid.DotMatrixDisplay's own
DOT_UNLIT = (0, 0, 0)  # WIN1.png's own test pattern never shows an unlit dot in the gaps between lit ones -- plain black, unlike LED II's dim-red-when-off

MAIN_COLS, MAIN_ROWS = 83, 84
SEC_COLS, SEC_ROWS = 83, 9

GRID_X0 = 11  # first dot column, both grids (measured, identical for each)
MAIN_GRID_Y0 = 28
SEC_GRID_Y0 = 289

# Every content row (dot or gap) shares the same left/right margin
# pattern: white highlight, a 2px black shadow line, the dots themselves,
# then a mirrored (but not colour-mirrored) black/grey shadow on the
# right. GRID_X0-3/-2 is the left shadow; GRID_X0 + cols*PITCH-1 is the
# last dot column, +1/+2 the right shadow, +3 the single grey highlight.
GRID_WHITE_X = GRID_X0 - 3  # 8
GRID_LEFT_BLACK_X0 = GRID_X0 - 2  # 9 (2px: 9-10)


def _grid_right_edge(cols: int) -> tuple[int, int, int]:
    """(last content column, black_x0, grey_x) for a grid `cols` wide --
    the right-side mirror of GRID_WHITE_X/GRID_LEFT_BLACK_X0, but the
    black shadow there is 2px (not the left edge's implicit single
    column), so it's a function of `cols` rather than a flat constant."""
    last_content = GRID_X0 + cols * PITCH - 2  # 258 for the 83-col grids
    return last_content, last_content + 1, last_content + 3  # black spans black_x0..black_x0+1


# ---- Button row -- measured as one black_ring around the whole strip
# (not 11 separate rings; 2026-08-26 playtesting: the original per-button
# black-ringed version bled past the window's right edge because its
# guessed button size/pitch didn't match the source), with each of the
# 11 cells then getting its own small raised bevel inside that ring --
# see _draw_button_row's own docstring for the exact recipe.
BUTTON_COUNT = 11
BUTTON_PITCH = 23  # measured: consecutive divider positions are exactly 23px apart
BUTTON_ROW_X0 = 8
BUTTON_ROW_Y0 = 321
BUTTON_ROW_W = BUTTON_COUNT * BUTTON_PITCH + 1  # 254 -- spans to the measured right edge at x=261
BUTTON_ROW_H = 22  # measured: top border y=321, bottom border y=342
_FLAT_BUTTON_INDEX = 3  # measured: the 4th button (0-indexed) is a flat black-ringed panel, not raised -- a genuine source quirk, not a bug

# ---- Title text: literal pixel mask, extracted as the tight bounding box
# of black pixels in WIN1.png's title bar (fixed content -- not a font,
# same method Bruce's Windows' own fixed labels used). 120x10, placed at
# its own measured origin rather than re-centred by formula -- the
# source text isn't dead-centre in its bar, and playtesting (2026-08-26)
# called out the formula-centred version as visibly off.
TITLE_TEXT_ORIGIN = (72, 8)
TITLE_TEXT_MASK: tuple[str, ...] = (
    "#######...............#...........#####...................................#.....#.....#.#.............#.................",
    "...#..................#..........#.....#..#..........#....................#....#.#....#...............#.................",
    "...#..................#..........#.....#..#..........#.....................#...#.#...#................#.................",
    "...#.....###...#.##...#...#......#.......###...###..###..#...#...###.......#...#.#...#..#..#.##....##.#...###..#...#...#",
    "...#....#...#..##..#..#..#........###.....#...#...#..#...#...#..#...#......#...#.#...#..#..##..#..#..##..#...#.#...#...#",
    "...#........#..#...#..#.#............##...#.......#..#...#...#..#...........#.#...#.#...#..#...#..#...#..#...#..#.#.#.#.",
    "...#.....####..#...#..###..............#..#....####..#...#...#...###........#.#...#.#...#..#...#..#...#..#...#..#.#.#.#.",
    "...#....#...#..#...#..#..#.......#.....#..#...#...#..#...#...#......#.......#.#...#.#...#..#...#..#...#..#...#..#.#.#.#.",
    "...#....#..##..#...#..#..#.......#.....#..#...#..##..#...#..##..#...#........#.....#....#..#...#..#..##..#...#...#...#..",
    "...#.....##.#..#...#..#...#.......#####...##...##.#..##...##.#...###.........#.....#....#..#...#...##.#...###....#...#..",
)

# ---- Dropdown arrow glyph: literal 7x4 triangle mask, extracted the same
# way. The minimize icon (a raised white bar) is drawn as two rects
# instead of a mask -- see _draw_minimize_icon.
DROPDOWN_ARROW_MASK: tuple[str, ...] = (
    "#######",
    ".#####.",
    "..###..",
    "...#...",
)


# Measured off WIN1.png, the right-side outer black hairline is 3px wide
# (270-272) rather than mirroring the left/top/bottom sides' 1px -- a real
# source asymmetry, kept faithfully through the 2026-08-26 reconstruct-
# and-diff pass. A later playtesting round on the built demo called it out
# as reading like a stray extra black line rather than a border, so this
# is now a deliberate departure from the source: RED_X1 extends 2px
# further, leaving a symmetric 1px hairline on all four sides.
RED_X1 = WINDOW_W - 1  # exclusive -- 272, matching the left/top/bottom border width


def _draw_frame(surface: pygame.Surface) -> None:
    surface.fill(BLACK)
    pygame.draw.rect(surface, FRAME_RED, (1, 1, RED_X1 - 1, WINDOW_H - 2))
    pygame.draw.rect(
        surface,
        BLACK,
        (CONTENT_X0 - 1, CONTENT_Y0 - 1, CONTENT_X1 - CONTENT_X0 + 2, CONTENT_Y1 - CONTENT_Y0 + 2),
    )
    pygame.draw.rect(surface, PANEL, (CONTENT_X0, CONTENT_Y0, CONTENT_X1 - CONTENT_X0, CONTENT_Y1 - CONTENT_Y0))
    # The title bar's two dividers reappear as a 1px notch through the
    # bottom border's own red band too (measured) -- not through the
    # grid in between, where the same columns just happen to land on the
    # dot pattern's own natural gaps instead.
    surface.set_at((TITLE_DIVIDER_1_X, WINDOW_H - 3), BLACK)
    surface.set_at((TITLE_DIVIDER_1_X, WINDOW_H - 2), BLACK)
    surface.set_at((TITLE_DIVIDER_2_X, WINDOW_H - 3), BLACK)
    surface.set_at((TITLE_DIVIDER_2_X, WINDOW_H - 2), BLACK)


def _draw_minimize_icon(surface: pygame.Surface, box: tuple[int, int, int, int]) -> None:
    bx, by, bw, bh = box
    icon_w, icon_h = 13, 3
    ix = bx + (bw - icon_w) // 2
    iy = by + (bh - icon_h) // 2
    surface.fill(BEZEL_DARK, (ix + 1, iy + 1, icon_w, icon_h))  # drop shadow, drawn first
    pygame.draw.rect(surface, BLACK, (ix, iy, icon_w, icon_h))
    surface.fill(WHITE, (ix + 1, iy + 1, icon_w - 2, icon_h - 2))


def _draw_dropdown_box(surface: pygame.Surface, box: tuple[int, int, int, int]) -> None:
    # No black_ring, and not framework/window_chrome.py's bevel_rect
    # either -- this box's own corner convention is the opposite of that
    # helper's (grey claims the top-right AND bottom-left corners, not
    # just bottom-right; white only gets the top-left), so it's drawn
    # directly rather than forced through a shape that doesn't match.
    x, y, w, h = box
    pygame.draw.rect(surface, PANEL, box)
    surface.fill(BEZEL_DARK, (x + w - 2, y, 2, h))  # right columns (2px), full height
    surface.fill(BEZEL_DARK, (x, y + h - 2, w, 2))  # bottom rows (2px), full width
    # White drawn after grey, so it wins the corners it overlaps
    # (measured: the top row's highlight reaches all the way to the
    # second-to-last column, and the left column's reaches down to the
    # first of the two bottom-shadow rows -- only the very last column
    # and very last row stay pure grey).
    surface.fill(WHITE, (x, y, w - 1, 1))  # top row, short of only the rightmost column
    surface.fill(WHITE, (x, y + 1, 1, h - 2))  # left column, short of the top row and the last shadow row
    mw, mh = len(DROPDOWN_ARROW_MASK[0]), len(DROPDOWN_ARROW_MASK)
    mx = box[0] + (box[2] - mw) // 2
    my = box[1] + (box[3] - mh) // 2
    for dy, row in enumerate(DROPDOWN_ARROW_MASK):
        for dx, ch in enumerate(row):
            if ch == "#":
                surface.set_at((mx + dx, my + dy), BLACK)


def _draw_title_text(surface: pygame.Surface) -> None:
    tx, ty = TITLE_TEXT_ORIGIN
    for dy, row in enumerate(TITLE_TEXT_MASK):
        for dx, ch in enumerate(row):
            if ch == "#":
                surface.set_at((tx + dx, ty + dy), BLACK)


def _draw_title_bar(surface: pygame.Surface) -> None:
    pygame.draw.rect(surface, BEZEL_DARK, (CONTENT_X0, CONTENT_Y0, CONTENT_X1 - CONTENT_X0, TITLE_H))
    pygame.draw.rect(surface, PANEL, MIN_BOX_RECT)
    # The two dividers cut through the red border itself (from y=1), not
    # just the title bar -- measured, not a stylistic flourish.
    pygame.draw.line(surface, BLACK, (TITLE_DIVIDER_1_X, 1), (TITLE_DIVIDER_1_X, CONTENT_Y0 + TITLE_H - 1))
    pygame.draw.line(surface, BLACK, (TITLE_DIVIDER_2_X, 1), (TITLE_DIVIDER_2_X, CONTENT_Y0 + TITLE_H - 1))
    pygame.draw.line(surface, BLACK, (0, TITLE_DIVIDER_BOTTOM_Y), (WINDOW_W - 1, TITLE_DIVIDER_BOTTOM_Y))
    _draw_minimize_icon(surface, MIN_BOX_RECT)
    _draw_dropdown_box(surface, DROPDOWN_BOX_RECT)
    _draw_title_text(surface)


# ---- Grid frame rows, measured (see module docstring). Every row from a
# grid's own top black-cap line through its last content row shares the
# same left/right margin; a handful of rows above/between/below the two
# grids are their own fixed bands rather than part of that per-row
# pattern. Listed here as data instead of inline magic numbers so the
# draw function is just "for each row, do what the label says." ----
_BLACK_CAP_ROWS = (27, 279, 280, 287, 288, 315, 316)  # white(8) + black(9..right-black) + grey(right-grey)
_GREY_BAND_ROWS = (26, 286)  # grey(9..right-grey), one wider than the black-cap rows
_WHITE_RIDGE_ROWS = (281, 317)  # white(8..right-black), no separate grey column


def _draw_grid_frames(surface: pygame.Surface) -> None:
    _last_content, black_x0, grey_x = _grid_right_edge(MAIN_COLS)  # both grids share this column layout

    for y in _GREY_BAND_ROWS:
        surface.fill(BEZEL_DARK, (GRID_LEFT_BLACK_X0, y, grey_x - GRID_LEFT_BLACK_X0 + 1, 1))
    for y in _BLACK_CAP_ROWS:
        surface.set_at((GRID_WHITE_X, y), WHITE)
        surface.fill(BLACK, (GRID_LEFT_BLACK_X0, y, black_x0 + 1 - GRID_LEFT_BLACK_X0 + 1, 1))
        surface.set_at((grey_x, y), BEZEL_DARK)
    for y in _WHITE_RIDGE_ROWS:
        surface.fill(WHITE, (GRID_WHITE_X, y, black_x0 + 1 - GRID_WHITE_X + 1, 1))


def _draw_dots(
    surface: pygame.Surface,
    x0: int,
    y0: int,
    cols: int,
    rows: int,
    cells: dict[tuple[int, int], float] | set[tuple[int, int]] | None,
) -> None:
    _last_content, black_x0, grey_x = _grid_right_edge(cols)
    grid_h = rows * PITCH - 1  # every pixel row of the grid, not just one per dot pitch
    surface.fill(WHITE, (GRID_WHITE_X, y0, 1, grid_h))
    surface.fill(BLACK, (GRID_LEFT_BLACK_X0, y0, x0 - GRID_LEFT_BLACK_X0, grid_h))
    surface.fill(BLACK, (black_x0, y0, 2, grid_h))
    surface.fill(BEZEL_DARK, (grey_x, y0, 1, grid_h))

    intensity: dict[tuple[int, int], float]
    if cells is None:
        intensity = {}
    elif isinstance(cells, dict):
        intensity = cells
    else:
        intensity = {cell: 1.0 for cell in cells}
    surface.fill(DOT_UNLIT, (x0, y0, cols * PITCH - 1, rows * PITCH - 1))
    for (col, row), t in intensity.items():
        if not (0 <= col < cols and 0 <= row < rows) or t <= 0:
            continue
        colour = lerp_color(DOT_UNLIT, DOT_LIT, t)
        surface.fill(colour, (x0 + col * PITCH, y0 + row * PITCH, DOT_SIZE, DOT_SIZE))


# Purely decorative icon glyphs for the button row (2026-08-26
# playtesting: the buttons "should get icons (black)" and "should be
# pressable, but ultimately do nothing other than animate") -- no source
# data exists for what these 11 blank buttons ever did (WIN1.png shows
# them blank), so these are invented pictograms, not measured content.
# Cycled across the 11 buttons by index so neighbours read as distinct
# controls rather than 11 copies of one icon.
_BUTTON_ICONS: tuple[tuple[str, ...], ...] = (
    (
        "...#...",
        "...#...",
        "...#...",
        "#######",
        "...#...",
        "...#...",
        "...#...",
    ),
    (
        "#.....#",
        ".#...#.",
        "..#.#..",
        "...#...",
        "..#.#..",
        ".#...#.",
        "#.....#",
    ),
    (
        "....#..",
        "...##..",
        "..###..",
        ".####..",
        "..###..",
        "...##..",
        "....#..",
    ),
    (
        "..#....",
        "..##...",
        "..###..",
        "..####.",
        "..###..",
        "..##...",
        "..#....",
    ),
    (
        ".......",
        ".#####.",
        ".#...#.",
        ".#...#.",
        ".#...#.",
        ".#####.",
        ".......",
    ),
    (
        "...#...",
        "..###..",
        ".#####.",
        "#######",
        ".#####.",
        "..###..",
        "...#...",
    ),
)


def _draw_button_icon(surface: pygame.Surface, cell_x0: int, inner_y0: int, cell_w: int, inner_h: int, index: int, nudge: int) -> None:
    glyph = _BUTTON_ICONS[index % len(_BUTTON_ICONS)]
    gw, gh = len(glyph[0]), len(glyph)
    gx = cell_x0 + (cell_w - gw) // 2 + nudge
    gy = inner_y0 + (inner_h - gh) // 2 + nudge
    for dy, row in enumerate(glyph):
        for dx, ch in enumerate(row):
            if ch == "#":
                surface.set_at((gx + dx, gy + dy), BLACK)


def _draw_button_row(surface: pygame.Surface, pressed: int | None = None) -> None:
    """One black_ring around the whole row (measured: its top/bottom
    border rows are solid black, mitered at the row's own 4 corners the
    same way every black_ring is -- no per-button ring). Each of the 11
    cells is its own little raised bevel (22x20): a 2px grey shadow on
    the right and bottom, a white highlight on the top row and left
    column -- drawn shadow-first so the highlight wins the top-right
    corner it overlaps, the opposite priority from `_draw_dropdown_box`'s
    own corners (measured, not a shared convention -- each was checked
    against the source independently).

    `pressed` (2026-08-26 playtesting) is an ambient, non-functional press
    animation index: that button's bevel inverts (grey top/left instead
    of white) and its icon nudges 1px, the same "invert + nudge" pressed
    look `cd_player.py`'s transport buttons use -- decorative only, not
    driven by any real click here."""
    rect = (BUTTON_ROW_X0, BUTTON_ROW_Y0, BUTTON_ROW_W, BUTTON_ROW_H)
    black_ring(surface, rect)
    inner_y0 = BUTTON_ROW_Y0 + 1
    inner_h = BUTTON_ROW_H - 2  # 20
    cell_w = BUTTON_PITCH - 1  # 22
    for i in range(1, BUTTON_COUNT):
        x = BUTTON_ROW_X0 + i * BUTTON_PITCH
        pygame.draw.line(surface, BLACK, (x, inner_y0), (x, inner_y0 + inner_h - 1))
        # Mitered T-junction: measured, the row's own top/bottom border
        # leaves a 1px background notch exactly where an internal divider
        # meets it, the same "leave the corner unset" idea black_ring
        # already applies to its own 4 corners.
        surface.set_at((x, BUTTON_ROW_Y0), PANEL)
        surface.set_at((x, BUTTON_ROW_Y0 + BUTTON_ROW_H - 1), PANEL)
    for i in range(BUTTON_COUNT):
        x0 = BUTTON_ROW_X0 + i * BUTTON_PITCH + 1
        is_pressed = i == pressed
        if i == _FLAT_BUTTON_INDEX:
            # No bevel at all -- flat panel, except grey (not the usual
            # white) exactly where a normal button's highlight sits: its
            # top row and left column. See the constant's own comment.
            surface.fill(BEZEL_DARK, (x0, inner_y0, cell_w, 1))
            surface.fill(BEZEL_DARK, (x0, inner_y0 + 1, 1, inner_h - 1))
            _draw_button_icon(surface, x0, inner_y0, cell_w, inner_h, i, 1 if is_pressed else 0)
            continue
        top_left, bottom_right = (BEZEL_DARK, WHITE) if is_pressed else (WHITE, BEZEL_DARK)
        surface.fill(bottom_right, (x0 + cell_w - 2, inner_y0, 2, inner_h))  # right shadow, full height
        surface.fill(bottom_right, (x0, inner_y0 + inner_h - 2, cell_w, 2))  # bottom shadow, full width
        surface.fill(top_left, (x0, inner_y0, cell_w - 1, 1))  # top highlight, short of the right shadow
        surface.fill(top_left, (x0, inner_y0, 1, inner_h - 1))  # left highlight, short of the bottom shadow
        _draw_button_icon(surface, x0, inner_y0, cell_w, inner_h, i, 1 if is_pressed else 0)


class TankDisplay:
    """The shared render target `PatrolPhase`/`EngagePhase`/`ResetPhase`
    drive. `main_cells`/`secondary_cells` are either a set of lit
    (col, row) cells or a dict mapping cell to 0..1 intensity (for a
    Burst's fading embers); each phase owns the fields it writes to.
    `pressed_button` (2026-08-26) is owned by the demo itself, not any
    one phase -- see `tank_status_window.py`'s `_ButtonRowAnimator` --
    since the ambient button animation keeps running across phase
    transitions, unlike the tanks/status text those phases reseed."""

    def __init__(self) -> None:
        self.main_cells: dict[tuple[int, int], float] | set[tuple[int, int]] = set()
        self.secondary_cells: dict[tuple[int, int], float] | set[tuple[int, int]] = set()
        self.pressed_button: int | None = None

    def draw(self, surface: pygame.Surface) -> None:
        _draw_frame(surface)
        _draw_title_bar(surface)
        pygame.draw.rect(surface, PANEL, (CONTENT_X0, BODY_Y0, CONTENT_X1 - CONTENT_X0, BODY_Y1 - BODY_Y0))
        _draw_grid_frames(surface)
        _draw_dots(surface, GRID_X0, MAIN_GRID_Y0, MAIN_COLS, MAIN_ROWS, self.main_cells)
        _draw_dots(surface, GRID_X0, SEC_GRID_Y0, SEC_COLS, SEC_ROWS, self.secondary_cells)
        _draw_button_row(surface, self.pressed_button)


NATIVE_SIZE = (WINDOW_W, WINDOW_H)


def status_text_cells(text: str) -> set[tuple[int, int]]:
    """Lay out `text` centred in the secondary strip, reusing
    `pixel_font.text_cells` -- `led_grid.DOT_FONT` was the other
    candidate (same 5x7 cell size, same secondary-strip ROWS=9 fit) but
    it only has digits/space/hyphen (built for LED II's numeric marquee),
    no letters; `pixel_font`'s A-Z alphabet (built for the desktop
    shell's window titles) is what actually has "PATROL"/"ENGAGE"/"RESET".
    Not a DotMatrixDisplay call: that class always renders at its own
    bezel/colour, and this strip already has both drawn by
    `TankDisplay.draw` itself."""
    row_offset = (SEC_ROWS - GLYPH_H) // 2
    cells, width = text_cells(text)
    x0 = (SEC_COLS - width) // 2
    return {(x0 + x, row_offset + y) for x, y in cells}
