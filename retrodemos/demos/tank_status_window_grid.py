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
for the explosion/burst topology in the phases module,
`framework/pixel_font.py`'s A-Z alphabet for the secondary strip's status
text (`led_grid.DOT_FONT` is the same cell size and would have fit the
strip's ROWS=9 just as well, but it's digits/space/hyphen only -- built
for LED II's numeric marquee, no letters), and
`framework/window_chrome.py`'s `bevel_rect`/`black_ring` for the button
row and the dropdown box, which use that exact black-ring-plus-raised-
bevel combination in the source (confirmed by direct pixel inspection --
the minimize box, by contrast, is flush flat panel with no bevel of its
own, bounded only by the surrounding structural divider lines).

The outer frame, title bar, and grid-bevel widths below are simplified to
tidy round numbers anchored on the real measurements (e.g. the source's
border is BORDER-1/BORDER+1px on top vs. right/bottom -- asymmetric in
ways not worth preserving exactly) rather than reconstructed byte-exact;
what *is* pixel-exact: the overall window size, both grids' dot counts
(83x84 and 83x9), the dot pitch/size/colour, the button count (11), and
the literal pixel masks below for the title text and both title-bar icons
(extracted the same tight-bounding-box way Bruce's Windows' fixed labels
were, since none of this is arbitrary/generated content).
"""

from __future__ import annotations

import pygame

from retrodemos.framework.led_grid import DOT_LIT, lerp_color
from retrodemos.framework.pixel_font import GLYPH_H, text_cells
from retrodemos.framework.window_chrome import BEZEL_DARK, BLACK, PANEL, WHITE, bevel_rect, black_ring

# ---- Frame/window geometry (measured, simplified -- see module docstring) ----
WINDOW_W, WINDOW_H = 273, 350
FRAME_RED = (255, 0, 0)
BORDER = 4  # 1px black hairline + 2px red + 1px black divider, all four sides

TITLE_H = 18
BOX = 18  # minimize/dropdown box size
DIVIDER = 1

CONTENT_X0 = BORDER
CONTENT_X1 = WINDOW_W - BORDER
CONTENT_W = CONTENT_X1 - CONTENT_X0
BODY_Y0 = BORDER + TITLE_H + DIVIDER
BODY_Y1 = WINDOW_H - BORDER

MIN_BOX_RECT = (CONTENT_X0, BORDER, BOX, BOX)
DROPDOWN_BOX_RECT = (CONTENT_X1 - BOX, BORDER, BOX, BOX)
TITLE_TEXT_RECT = (
    CONTENT_X0 + BOX + DIVIDER,
    BORDER,
    CONTENT_W - 2 * (BOX + DIVIDER),
    TITLE_H,
)

# ---- Dot grids (measured, exact -- see module docstring) ----
DOT_SIZE = 2
PITCH = 3  # DOT_SIZE + 1px gap, same as led_grid.DotMatrixDisplay's own
DOT_UNLIT = (0, 0, 0)  # WIN1.png's own test pattern never shows an unlit dot in the gaps between lit ones -- plain black, unlike LED II's dim-red-when-off

MAIN_COLS, MAIN_ROWS = 83, 84
SEC_COLS, SEC_ROWS = 83, 9

GRID_INSET_X = 7  # body-panel edge to first dot column (measured)
GRID_INSET_Y = 5  # body-panel edge to first dot row (measured)
GRID_GAP = 9  # between the main grid's bottom bevel and the secondary strip's top bevel
BUTTON_ROW_GAP = 6  # between the secondary strip's bottom bevel and the button row

MAIN_GRID_X0 = CONTENT_X0 + GRID_INSET_X
MAIN_GRID_Y0 = BODY_Y0 + GRID_INSET_Y
MAIN_GRID_W = MAIN_COLS * PITCH - 1
MAIN_GRID_H = MAIN_ROWS * PITCH - 1

SEC_GRID_X0 = MAIN_GRID_X0
SEC_GRID_Y0 = MAIN_GRID_Y0 + MAIN_GRID_H + GRID_GAP
SEC_GRID_W = SEC_COLS * PITCH - 1
SEC_GRID_H = SEC_ROWS * PITCH - 1

GRID_BEVEL = 3  # sunken frame thickness around each grid, drawn via bevel_rect(raised=False)

# ---- Button row (measured: 11 blank buttons, pitch 23, reusing
# window_chrome's black_ring + bevel_rect -- the source's own button
# chrome is exactly that combination) ----
BUTTON_COUNT = 11
BUTTON_MARGIN = 4  # body edge to the first button's own border
BUTTON_PITCH = 23
BUTTON_SIZE = 22
BUTTON_ROW_Y0 = SEC_GRID_Y0 + SEC_GRID_H + GRID_BEVEL * 2 + BUTTON_ROW_GAP
BUTTON_ROW_X0 = CONTENT_X0 + BUTTON_MARGIN

# ---- Title text: literal pixel mask, extracted as the tight bounding box
# of black pixels in WIN1.png's title bar (fixed content -- not a font,
# same method Bruce's Windows' own fixed labels used). 120x10.
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
    "...#.....##.#..#...#..#...#.......#####...##...##.#..##...##.#...###.........#.....#....#..#...#..#...##...###....#...#..",
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


def _draw_frame(surface: pygame.Surface) -> None:
    surface.fill(BLACK)
    pygame.draw.rect(surface, FRAME_RED, (1, 1, WINDOW_W - 2, WINDOW_H - 2))
    pygame.draw.rect(surface, PANEL, (BORDER, BORDER, WINDOW_W - 2 * BORDER, WINDOW_H - 2 * BORDER))


def _draw_minimize_icon(surface: pygame.Surface, box: tuple[int, int, int, int]) -> None:
    bx, by, bw, bh = box
    icon_w, icon_h = 13, 3
    ix = bx + (bw - icon_w) // 2
    iy = by + (bh - icon_h) // 2
    surface.fill(BEZEL_DARK, (ix + 1, iy + 1, icon_w, icon_h))  # drop shadow, drawn first
    pygame.draw.rect(surface, BLACK, (ix, iy, icon_w, icon_h))
    surface.fill(WHITE, (ix + 1, iy + 1, icon_w - 2, icon_h - 2))


def _draw_dropdown_box(surface: pygame.Surface, box: tuple[int, int, int, int]) -> None:
    black_ring(surface, box)
    inner = (box[0] + 1, box[1] + 1, box[2] - 2, box[3] - 2)
    bevel_rect(surface, inner, raised=True)
    mw, mh = len(DROPDOWN_ARROW_MASK[0]), len(DROPDOWN_ARROW_MASK)
    mx = box[0] + (box[2] - mw) // 2
    my = box[1] + (box[3] - mh) // 2
    for dy, row in enumerate(DROPDOWN_ARROW_MASK):
        for dx, ch in enumerate(row):
            if ch == "#":
                surface.set_at((mx + dx, my + dy), BLACK)


def _draw_title_text(surface: pygame.Surface, rect: tuple[int, int, int, int]) -> None:
    rx, ry, rw, rh = rect
    mw, mh = len(TITLE_TEXT_MASK[0]), len(TITLE_TEXT_MASK)
    tx = rx + (rw - mw) // 2
    ty = ry + (rh - mh) // 2
    for dy, row in enumerate(TITLE_TEXT_MASK):
        for dx, ch in enumerate(row):
            if ch == "#":
                surface.set_at((tx + dx, ty + dy), BLACK)


def _draw_title_bar(surface: pygame.Surface) -> None:
    pygame.draw.rect(surface, BEZEL_DARK, (CONTENT_X0, BORDER, CONTENT_W, TITLE_H))
    pygame.draw.rect(surface, PANEL, MIN_BOX_RECT)
    pygame.draw.line(surface, BLACK, (CONTENT_X0 + BOX, BORDER), (CONTENT_X0 + BOX, BORDER + TITLE_H - 1))
    pygame.draw.line(
        surface,
        BLACK,
        (CONTENT_X1 - BOX - DIVIDER, BORDER),
        (CONTENT_X1 - BOX - DIVIDER, BORDER + TITLE_H - 1),
    )
    _draw_minimize_icon(surface, MIN_BOX_RECT)
    _draw_dropdown_box(surface, DROPDOWN_BOX_RECT)
    _draw_title_text(surface, TITLE_TEXT_RECT)


def _draw_grid_bevel(surface: pygame.Surface, x0: int, y0: int, w: int, h: int) -> None:
    b = GRID_BEVEL
    bevel_rect(surface, (x0 - b, y0 - b, w + 2 * b, h + 2 * b), raised=False)


def _draw_dots(
    surface: pygame.Surface,
    x0: int,
    y0: int,
    cols: int,
    rows: int,
    cells: dict[tuple[int, int], float] | set[tuple[int, int]] | None,
) -> None:
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


def _draw_button_row(surface: pygame.Surface) -> None:
    for i in range(BUTTON_COUNT):
        x = BUTTON_ROW_X0 + i * BUTTON_PITCH
        rect = (x, BUTTON_ROW_Y0, BUTTON_SIZE, BUTTON_SIZE)
        black_ring(surface, rect)
        inner = (rect[0] + 1, rect[1] + 1, rect[2] - 2, rect[3] - 2)
        bevel_rect(surface, inner, raised=True)


class TankDisplay:
    """The shared render target `PatrolPhase`/`EngagePhase`/`ResetPhase`
    drive. `main_cells`/`secondary_cells` are either a set of lit
    (col, row) cells or a dict mapping cell to 0..1 intensity (for a
    Burst's fading embers); each phase owns the fields it writes to."""

    def __init__(self) -> None:
        self.main_cells: dict[tuple[int, int], float] | set[tuple[int, int]] = set()
        self.secondary_cells: dict[tuple[int, int], float] | set[tuple[int, int]] = set()

    def draw(self, surface: pygame.Surface) -> None:
        _draw_frame(surface)
        _draw_title_bar(surface)
        pygame.draw.rect(surface, PANEL, (CONTENT_X0, BODY_Y0, CONTENT_W, BODY_Y1 - BODY_Y0))
        _draw_grid_bevel(surface, MAIN_GRID_X0, MAIN_GRID_Y0, MAIN_GRID_W, MAIN_GRID_H)
        _draw_dots(surface, MAIN_GRID_X0, MAIN_GRID_Y0, MAIN_COLS, MAIN_ROWS, self.main_cells)
        _draw_grid_bevel(surface, SEC_GRID_X0, SEC_GRID_Y0, SEC_GRID_W, SEC_GRID_H)
        _draw_dots(surface, SEC_GRID_X0, SEC_GRID_Y0, SEC_COLS, SEC_ROWS, self.secondary_cells)
        _draw_button_row(surface)


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
