"""Bruce's Windows: the one interactive demo (title-bar drag, "Got it"
closes the dialog) and the reference implementation for this project's
Windows 3.1-style chrome -- see `docs/bruces-windows.md` for the overview
and `docs/pixel-archaeology.md` for method.

`images/WINDOW1.png` (200x200) is a single coherent screenshot, unlike
Title/Dooley/CD Player's source images -- no bundled calibration bands to
untangle. Every text label (the window title, the dialog's own title,
its two body lines, the button label, and the status bar text) is
pixel-verified: extracted as the literal set of black pixels within its
tight bounding box, not a decomposed reusable font -- there's no reason to
decompose into letters here, since every label in this demo is fixed
content, not `--text`-overridable. `STATUS_TEXT_ROWS` keeps a genuine
source quirk: it reads "This is a status a bar...", not "This is a status
bar..." as the original terse spec paraphrased it -- an extra "a", kept
verbatim rather than "corrected."

The window chrome uses four distinct border styles, not one generic
bevel -- caught on review (2026-08-25) after the first pass collapsed them
all into a single helper and got the bevel direction backwards in the
process. Each is now measured by sampling its edge profile (background ->
border colours -> content) outside-in on all four sides, the same
"verify programmatically" bar `docs/pixel-archaeology.md` sets, rather
than eyeballed:
- **Outer frame**: 1px black, 1px white, a 2px background margin, then
  either a corner-box bevel or a plain sunken bevel framing each title bar
  (see below), depending on x/y.
- **Simple bevel** (`_bevel_rect`): a single 1px line -- white on top/left
  + grey on bottom/right for "raised" (the corner boxes; the first pass
  had this direction backwards), grey/white swapped for "sunken" (the
  frame around both cyan title bars, main and dialog).
- **Ring frame** (`_ring_frame`, the "Got it" button): three concentric
  1px outlines, grey/black/white from the outside in, uniformly on all
  four sides -- not a directional bevel at all, just three nested rules.
- **Double rule** (`_double_rule_rect`, the status text field and the
  icon-grid box): a single grey line and a single white line, white
  outermost, with background gaps on both sides and before the content --
  not a touching two-tone bevel.

The status bar's own green/red icon grid (12x4 cells, 2px squares on a
3px pitch) *is* pixel-verified, since its exact pattern is content, not
just a border.

Dragging needs `framework/runtime.py`'s new mouse-coordinate rescaling
(added the same day this demo was built, see its own docstring) -- the
first demo that needed mouse events at all.
"""

from __future__ import annotations

import pygame

from retrodemos.framework.demo import Demo

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BEZEL_DARK = (128, 128, 128)
PANEL = (192, 192, 192)
TITLE_CYAN = (0, 191, 191)
GREEN_ON = (0, 255, 0)
RED_ON = (191, 0, 0)
DESKTOP_BG = (0, 128, 128)  # invented -- WINDOW1.png shows only the window itself, no desktop backdrop

WINDOW_SIZE = (200, 200)
CANVAS_SIZE = (320, 240)

# --- Pixel-verified text labels: each is the literal set of black pixels
# within its tight bounding box in WINDOW1.png, at (origin) within the
# 200x200 window surface. ---

WINDOW_TITLE_ORIGIN = (60, 7)
WINDOW_TITLE_ROWS = (
    "##...###...##.##..............##........................########.##......##........",
    "##...###...##.##..............##...........................##....##...#..##........",
    ".##..###..##..................##...........................##........##..##........",
    ".##.##.##.##..##..##.##....##.##...####..##...#...##.......##....##.####.##...####.",
    ".##.##.##.##..##..###.##..##.###..##..##.##..###..##.......##....##..##..##..##..##",
    ".##.##.##.##..##..##..##..##..##..##..##..##.###.##........##....##..##..##..##..##",
    ".##.##.##.##..##..##..##..##..##..##..##..##.#.#.##........##....##..##..##..######",
    "..###...###...##..##..##..##..##..##..##..####.####........##....##..##..##..##....",
    "..###...###...##..##..##..##.###..##..##...###.###.........##....##..##..##..##..##",
    "..###...###...##..##..##...##.##...####....##...##.........##....##...##.##...####.",
)

DIALOG_TITLE_ORIGIN = (86, 65)
DIALOG_TITLE_ROWS = (
    "#####...##........##..............",
    "##..##............##..............",
    "##...##.##..####..##..####...##.##",
    "##...##.##.#...##.##.##..##.##.###",
    "##...##.##...####.##.##..##.##..##",
    "##...##.##..##.##.##.##..##.##..##",
    "##...##.##.##..##.##.##..##.##..##",
    "##..##..##.##..##.##.##..##.##.###",
    "#####...##..#####.##..####...##.##",
    "............................#...##",
    ".............................####.",
)

WELCOME_LINE1_ORIGIN = (68, 90)
WELCOME_LINE1_ROWS = (
    "#.....#.....#........#...............................................",
    "#....#.#....#........#......................................#........",
    ".#...#.#...#.........#......................................#........",
    ".#...#.#...#...###...#...###....###...#.##..##....###......###...###.",
    ".#...#.#...#..#...#..#..#...#..#...#..##..##..#..#...#......#...#...#",
    "..#.#...#.#...#...#..#..#......#...#..#...#...#..#...#......#...#...#",
    "..#.#...#.#...#####..#..#......#...#..#...#...#..#####......#...#...#",
    "..#.#...#.#...#......#..#......#...#..#...#...#..#..........#...#...#",
    "...#.....#....#...#..#..#...#..#...#..#...#...#..#...#......#...#...#",
    "...#.....#.....###...#...###....###...#...#...#...###.......##...###.",
)

WELCOME_LINE2_ORIGIN = (56, 108)
WELCOME_LINE2_ROWS = (
    "######............................#...........#.....#.....#.#.............#.......................",
    "#.....#...........................#...........#....#.#....#...............#.......................",
    "#.....#...........................#............#...#.#...#................#.......................",
    "#.....#..#.#.#...#...###....###......###.......#...#.#...#..#..#.##....##.#...###..#...#...#..###.",
    "######...##..#...#..#...#..#...#....#...#......#...#.#...#..#..##..#..#..##..#...#.#...#...#.#...#",
    "#.....#..#...#...#..#......#...#....#...........#.#...#.#...#..#...#..#...#..#...#..#.#.#.#..#....",
    "#.....#..#...#...#..#......#####.....###........#.#...#.#...#..#...#..#...#..#...#..#.#.#.#...###.",
    "#.....#..#...#...#..#......#............#.......#.#...#.#...#..#...#..#...#..#...#..#.#.#.#......#",
    "#.....#..#...#..##..#...#..#...#....#...#........#.....#....#..#...#..#..##..#...#...#...#...#...#",
    "######...#....##.#...###....###......###.........#.....#....#..#...#...##.#...###....#...#....###.",
)

GOT_IT_ORIGIN = (89, 134)
GOT_IT_ROWS = (
    "..###...........#.....#..#.",
    ".#...#..........#........#.",
    "#.....#...###..###....#.###",
    "#........#...#..#.....#..#.",
    "#...###..#...#..#.....#..#.",
    "#.....#..#...#..#.....#..#.",
    "#.....#..#...#..#.....#..#.",
    ".#...#...#...#..#.....#..#.",
    "..###.....###...##....#..##",
)

STATUS_TEXT_ORIGIN = (7, 184)
STATUS_TEXT_ROWS = (  # genuine source quirk: "a status a bar", not "a status bar" -- see module docstring
    "#######.#......#............#.............................#.........#.............................#........................",
    "...#....#.................................................#.........#.............................#........................",
    "...#....#.##...#...###......#...###.......###.......###..###..###..###.#...#...###.......###......#.##....###...#.#........",
    "...#....##..#..#..#...#.....#..#...#.....#...#.....#...#..#..#...#..#..#...#..#...#.....#...#.....##..#..#...#..##.........",
    "...#....#...#..#..#.........#..#.............#.....#......#......#..#..#...#..#.............#.....#...#......#..#..........",
    "...#....#...#..#...###......#...###.......####......###...#...####..#..#...#...###.......####.....#...#...####..#..........",
    "...#....#...#..#......#.....#......#.....#...#.........#..#..#...#..#..#...#......#.....#...#.....#...#..#...#..#..........",
    "...#....#...#..#..#...#.....#..#...#.....#..##.....#...#..#..#..##..#..#..##..#...#.....#..##.....##..#..#..##..#..........",
    "...#....#...#..#...###......#...###.......##.#......###...##..##.#..##..##.#...###.......##.#.....#.##....##.#..#...#..#..#",
)


def _draw_glyph(surface: pygame.Surface, origin: tuple[int, int], rows: tuple[str, ...], colour: tuple[int, int, int]) -> None:
    x0, y0 = origin
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch == "#":
                surface.set_at((x0 + dx, y0 + dy), colour)


def _rect_outline(surface: pygame.Surface, rect: tuple[int, int, int, int], top_left: tuple[int, int, int], bottom_right: tuple[int, int, int]) -> None:
    """One 1px outline: `top_left` on the top+left edges, `bottom_right` on
    the bottom+right edges. The shared primitive `_bevel_rect` and
    `_ring_frame` both draw with, at different insets."""
    x, y, w, h = rect
    pygame.draw.line(surface, top_left, (x, y), (x + w - 1, y))
    pygame.draw.line(surface, top_left, (x, y), (x, y + h - 1))
    pygame.draw.line(surface, bottom_right, (x + w - 1, y), (x + w - 1, y + h - 1))
    pygame.draw.line(surface, bottom_right, (x, y + h - 1), (x + w - 1, y + h - 1))


def _bevel_rect(surface: pygame.Surface, rect: tuple[int, int, int, int], *, raised: bool = True) -> None:
    """A simple 1px bevel: white top/left + grey bottom/right for raised
    (the corner boxes), swapped for sunken. Filled with PANEL first."""
    pygame.draw.rect(surface, PANEL, rect)
    tl, br = (WHITE, BEZEL_DARK) if raised else (BEZEL_DARK, WHITE)
    _rect_outline(surface, rect, tl, br)


def _ring_frame(surface: pygame.Surface, rect: tuple[int, int, int, int]) -> None:
    """Three concentric 1px outlines -- grey, then black, then white, from
    the outside in -- uniformly on all four sides. The "Got it" button's
    own style, not a directional bevel. `rect` is the outermost (grey)
    edge; PANEL fill starts 3px in from every side."""
    x, y, w, h = rect
    _rect_outline(surface, rect, BEZEL_DARK, BEZEL_DARK)
    _rect_outline(surface, (x + 1, y + 1, w - 2, h - 2), BLACK, BLACK)
    _rect_outline(surface, (x + 2, y + 2, w - 4, h - 4), WHITE, WHITE)
    pygame.draw.rect(surface, PANEL, (x + 3, y + 3, w - 6, h - 6))


def _double_rule_rect(surface: pygame.Surface, rect: tuple[int, int, int, int]) -> None:
    """A single grey line and a single white line, white outermost, with a
    1px background gap on both sides of each and before the content --
    the status text field's and icon-grid box's own style, not a touching
    two-tone bevel. `rect` is the outer (white) edge."""
    x, y, w, h = rect
    _rect_outline(surface, rect, WHITE, WHITE)
    _rect_outline(surface, (x + 2, y + 2, w - 4, h - 4), BEZEL_DARK, BEZEL_DARK)


# --- Chrome geometry (measured edge-by-edge -- see module docstring for
# which border style each element uses) ---

TITLE_BAR_RECT = (24, 5, 152, 15)
TITLE_BAR_BEVEL_RECT = (23, 4, 154, 17)  # sunken bevel (grey TL, white BR) framing the cyan bar
LEFT_CORNER_RECT = (4, 4, 20, 17)
RIGHT_CORNER_RECT = (176, 4, 20, 17)
DIALOG_RECT = (43, 57, 118, 100)
DIALOG_TITLE_BAR_RECT = (48, 62, 109, 15)
DIALOG_TITLE_BAR_BEVEL_RECT = (47, 61, 111, 17)  # same sunken bevel, dialog's own title bar
BUTTON_RECT = (76, 128, 56, 21)  # outer (grey) edge of the button's ring frame
STATUS_TEXT_BOX_RECT = (2, 180, 133, 17)  # outer (white) edge
ICON_BOX_RECT = (133, 176, 46, 22)  # outer (white) edge
RESIZE_GRIP_RECT = (180, 178, 18, 18)

# Icon grid: pixel-verified (12 cols: 6 green + 6 red, 4 rows, 2px squares
# on a 3px pitch), origin at the grid's own top-left cell.
ICON_GRID_ORIGIN = (139, 183)
ICON_GRID_COLS = 12
ICON_GRID_ROWS = 4
ICON_GRID_GREEN_COLS = 6


def _draw_resize_grip(surface: pygame.Surface, rect: tuple[int, int, int, int]) -> None:
    x0, y0, w, h = rect
    for i in range(0, max(w, h), 3):
        pygame.draw.line(surface, WHITE, (x0 + w - 1 - i, y0 + h - 1), (x0 + w - 1, y0 + h - 1 - i))
        pygame.draw.line(surface, BEZEL_DARK, (x0 + w - 1 - i - 1, y0 + h - 1), (x0 + w - 1, y0 + h - 1 - i - 1))


def _draw_icon_grid(surface: pygame.Surface) -> None:
    x0, y0 = ICON_GRID_ORIGIN
    for row in range(ICON_GRID_ROWS):
        for col in range(ICON_GRID_COLS):
            colour = GREEN_ON if col < ICON_GRID_GREEN_COLS else RED_ON
            cx, cy = x0 + col * 3, y0 + row * 3
            surface.fill(colour, (cx, cy, 2, 2))


def _render_window(dialog_open: bool) -> pygame.Surface:
    surf = pygame.Surface(WINDOW_SIZE)
    surf.fill(PANEL)
    pygame.draw.rect(surf, BLACK, (0, 0, *WINDOW_SIZE), width=1)
    pygame.draw.rect(surf, WHITE, (1, 1, WINDOW_SIZE[0] - 2, WINDOW_SIZE[1] - 2), width=1)

    _bevel_rect(surf, LEFT_CORNER_RECT)
    _bevel_rect(surf, RIGHT_CORNER_RECT)
    _bevel_rect(surf, TITLE_BAR_BEVEL_RECT, raised=False)
    surf.fill(TITLE_CYAN, TITLE_BAR_RECT)
    _draw_glyph(surf, WINDOW_TITLE_ORIGIN, WINDOW_TITLE_ROWS, BLACK)

    if dialog_open:
        pygame.draw.rect(surf, BLACK, DIALOG_RECT, width=1)
        _bevel_rect(surf, DIALOG_TITLE_BAR_BEVEL_RECT, raised=False)
        surf.fill(TITLE_CYAN, DIALOG_TITLE_BAR_RECT)
        _draw_glyph(surf, DIALOG_TITLE_ORIGIN, DIALOG_TITLE_ROWS, BLACK)
        _draw_glyph(surf, WELCOME_LINE1_ORIGIN, WELCOME_LINE1_ROWS, BLACK)
        _draw_glyph(surf, WELCOME_LINE2_ORIGIN, WELCOME_LINE2_ROWS, BLACK)
        _ring_frame(surf, BUTTON_RECT)
        _draw_glyph(surf, GOT_IT_ORIGIN, GOT_IT_ROWS, BLACK)

    _double_rule_rect(surf, STATUS_TEXT_BOX_RECT)
    _draw_glyph(surf, STATUS_TEXT_ORIGIN, STATUS_TEXT_ROWS, BLACK)
    _double_rule_rect(surf, ICON_BOX_RECT)
    _draw_icon_grid(surf)
    _draw_resize_grip(surf, RESIZE_GRIP_RECT)
    return surf


class BruceWindowsDemo(Demo):
    NATIVE_SIZE = CANVAS_SIZE

    def __init__(self, *, text: str | None = None, **_ignored) -> None:
        self.reset()

    def reset(self) -> None:
        self._window_pos = [
            (CANVAS_SIZE[0] - WINDOW_SIZE[0]) // 2,
            (CANVAS_SIZE[1] - WINDOW_SIZE[1]) // 2,
        ]
        self._dialog_open = True
        self._dragging = False

    def _title_bar_screen_rect(self) -> pygame.Rect:
        x, y, w, h = TITLE_BAR_RECT
        return pygame.Rect(self._window_pos[0] + x, self._window_pos[1] + y, w, h)

    def _button_screen_rect(self) -> pygame.Rect:
        x, y, w, h = BUTTON_RECT
        return pygame.Rect(self._window_pos[0] + x, self._window_pos[1] + y, w, h)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._dialog_open and self._button_screen_rect().collidepoint(event.pos):
                self._dialog_open = False
            elif self._title_bar_screen_rect().collidepoint(event.pos):
                self._dragging = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging = False
        elif event.type == pygame.MOUSEMOTION and self._dragging:
            self._window_pos[0] += event.rel[0]
            self._window_pos[1] += event.rel[1]
            max_x = CANVAS_SIZE[0] - WINDOW_SIZE[0]
            max_y = CANVAS_SIZE[1] - WINDOW_SIZE[1]
            self._window_pos[0] = max(0, min(max_x, self._window_pos[0]))
            self._window_pos[1] = max(0, min(max_y, self._window_pos[1]))

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(DESKTOP_BG)
        surface.blit(_render_window(self._dialog_open), self._window_pos)


DEMO_CLASS = BruceWindowsDemo
