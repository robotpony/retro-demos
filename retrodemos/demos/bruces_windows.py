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

The window chrome is now reconstructed byte-exact against
`images/WINDOW1.png` (verified in `_render_window`'s own reconstruct-and-
diff test, `tests/test_bruces_windows.py`) -- two review passes were
needed to get there (2026-08-25), each catching mistakes a first
eyeballed pass had made, not just imprecision:

1. First pass: one generic raised/sunken-rect helper, approximated, bevel
   direction backwards (dark top/left instead of light top/left for
   "raised").
2. Second pass: measured every element's edge profile outside-in on all
   four sides (`docs/pixel-archaeology.md`'s "verify programmatically"
   bar) instead of eyeballing, which found the whole chrome is actually
   built from just **two** primitives, not the four this pass first
   guessed:
   - **`_bevel_rect`**: a single 1px line, white top/left + grey
     bottom/right for "raised", swapped for "sunken". Used everywhere --
     the outer window edge (raised, closest to the viewer), the body
     panel (sunken, the content sits inside it), both title bars
     (sunken), the corner boxes (raised), the status text field and
     icon-grid box (sunken, not the "double rule with a gap" this pass
     first guessed -- it's the exact same touching bevel as everything
     else), and both the Dialog and the "Got it" button, which each
     nest a **raised** bevel just inside a **sunken** one (the dialog
     floats above the body; the button is a raised control sitting in a
     sunken well) with a black ring sandwiched between -- not the
     uniform grey/black/white "ring frame" this pass first guessed.
   - **`_black_ring`**: a plain 1px black divider, used only between the
     Dialog's/button's two opposite-direction bevels.
   A third finding: every 1px outline is **mitered, not closed** -- the
   two corners where its two colours would collide (top-right,
   bottom-left) are left unset, showing whatever's underneath, while the
   other two corners (each touched by only one colour) are filled
   normally. A naive closed rectangle gets every corner wrong.

The status bar's own green/red icon grid (12x4 cells, 2px squares on a
3px pitch) and the resize grip (`RESIZE_GRIP_ROWS`) are both pixel-verified
glyphs too, same as the text.

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
    the bottom+right edges, mitered rather than closed -- measured against
    the source (2026-08-25): the top-right and bottom-left corners (where
    the two colours would otherwise collide) are left unset, showing
    whatever's underneath, while the top-left and bottom-right corners
    (each touched by only one colour) are filled in normally."""
    x, y, w, h = rect
    pygame.draw.line(surface, top_left, (x, y), (x + w - 2, y))
    pygame.draw.line(surface, top_left, (x, y), (x, y + h - 2))
    pygame.draw.line(surface, bottom_right, (x + w - 1, y + 1), (x + w - 1, y + h - 1))
    pygame.draw.line(surface, bottom_right, (x + 1, y + h - 1), (x + w - 1, y + h - 1))


def _bevel_rect(surface: pygame.Surface, rect: tuple[int, int, int, int], *, raised: bool = True) -> None:
    """A simple 1px bevel: white top/left + grey bottom/right for raised
    (the corner boxes), swapped for sunken. Filled with PANEL first."""
    pygame.draw.rect(surface, PANEL, rect)
    tl, br = (WHITE, BEZEL_DARK) if raised else (BEZEL_DARK, WHITE)
    _rect_outline(surface, rect, tl, br)


def _black_ring(surface: pygame.Surface, rect: tuple[int, int, int, int]) -> None:
    """A plain 1px black outline, uniform on all four sides -- the divider
    the Dialog and the "Got it" button each sandwich between two opposite-
    direction bevels. All four corners are left unset (matching the
    source, same mitered-corner finding as `_rect_outline`), not closed
    the way a plain `pygame.draw.rect(..., width=1)` would."""
    x, y, w, h = rect
    pygame.draw.line(surface, BLACK, (x + 1, y), (x + w - 2, y))
    pygame.draw.line(surface, BLACK, (x + 1, y + h - 1), (x + w - 2, y + h - 1))
    pygame.draw.line(surface, BLACK, (x, y + 1), (x, y + h - 2))
    pygame.draw.line(surface, BLACK, (x + w - 1, y + 1), (x + w - 1, y + h - 2))


# --- Chrome geometry (measured edge-by-edge -- see module docstring for
# which border style each element uses) ---

TITLE_BAR_RECT = (24, 5, 152, 15)
TITLE_BAR_BEVEL_RECT = (23, 4, 154, 17)  # sunken bevel (grey TL, white BR) framing the cyan bar
LEFT_CORNER_RECT = (4, 4, 17, 17)
RIGHT_CORNER_RECT = (179, 4, 17, 17)
OUTER_BEVEL_RECT = (1, 1, 198, 198)  # raised bevel just inside the black window border
BODY_BEVEL_RECT = (4, 23, 192, 155)  # sunken bevel framing the space between title bar and status row
DIALOG_OUTLINE_RECT = (43, 57, 119, 101)  # black ring around the dialog
DIALOG_BEVEL_RECT = (44, 58, 117, 99)  # raised bevel just inside that ring
DIALOG_TITLE_BAR_RECT = (48, 62, 109, 15)
DIALOG_TITLE_BAR_BEVEL_RECT = (47, 61, 111, 17)  # sunken bevel, same style as the main title bar's
BUTTON_OUTLINE_RECT = (77, 129, 54, 19)  # black ring between the button's two bevels
BUTTON_OUTER_BEVEL_RECT = (76, 128, 56, 21)  # sunken -- the well the button sits in
BUTTON_INNER_BEVEL_RECT = (78, 130, 52, 17)  # raised -- the button itself
STATUS_TEXT_BOX_RECT = (4, 180, 130, 17)  # sunken bevel, same style as the body/title bars
ICON_BOX_RECT = (136, 180, 41, 17)  # sunken bevel, same style

# Icon grid: pixel-verified (12 cols: 6 green + 6 red, 4 rows, 2px squares
# on a 3px pitch), origin at the grid's own top-left cell.
ICON_GRID_ORIGIN = (139, 183)
ICON_GRID_COLS = 12
ICON_GRID_ROWS = 4
ICON_GRID_GREEN_COLS = 6

# Resize grip: pixel-verified glyph (o=white, -=grey, #=black), same
# convention as the icon glyphs above.
RESIZE_GRIP_ORIGIN = (178, 176)
RESIZE_GRIP_ROWS = (
    ".................o..-#",
    "oooooooooooooooooo..-#",
    "....................-#",
    "....................-#",
    "................-...-#",
    "...............-o...-#",
    "..............-o....-#",
    ".............-o.-...-#",
    "............-o.-o...-#",
    "...........-o.-o....-#",
    "..........-o.-o.-...-#",
    ".........-o.-o.-o...-#",
    "........-o.-o.-o....-#",
    ".......-o.-o.-o.-...-#",
    "......-o.-o.-o.-o...-#",
    ".....-o.-o.-o.-o....-#",
    "....-o.-o.-o.-o.-...-#",
    "...-o.-o.-o.-o.-o...-#",
    "..-o.-o.-o.-o.-o....-#",
    ".-o.-o.-o.-o.-o.....-#",
    "....................-#",
    "....................-#",
    "---------------------#",
    "#######################",
)
_GRIP_COLOUR = {"o": WHITE, "-": BEZEL_DARK, "#": BLACK}


def _draw_resize_grip(surface: pygame.Surface) -> None:
    x0, y0 = RESIZE_GRIP_ORIGIN
    for dy, row in enumerate(RESIZE_GRIP_ROWS):
        for dx, ch in enumerate(row):
            if ch != ".":
                surface.set_at((x0 + dx, y0 + dy), _GRIP_COLOUR[ch])


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
    _bevel_rect(surf, OUTER_BEVEL_RECT)  # raised -- the window's own edge, closest to the viewer
    _bevel_rect(surf, BODY_BEVEL_RECT, raised=False)  # sunken -- the content sits inside this

    _bevel_rect(surf, LEFT_CORNER_RECT)
    _bevel_rect(surf, RIGHT_CORNER_RECT)
    _bevel_rect(surf, TITLE_BAR_BEVEL_RECT, raised=False)
    surf.fill(TITLE_CYAN, TITLE_BAR_RECT)
    _draw_glyph(surf, WINDOW_TITLE_ORIGIN, WINDOW_TITLE_ROWS, BLACK)

    if dialog_open:
        _bevel_rect(surf, DIALOG_BEVEL_RECT)  # raised -- the dialog floats above the body
        _black_ring(surf, DIALOG_OUTLINE_RECT)
        _bevel_rect(surf, DIALOG_TITLE_BAR_BEVEL_RECT, raised=False)
        surf.fill(TITLE_CYAN, DIALOG_TITLE_BAR_RECT)
        _draw_glyph(surf, DIALOG_TITLE_ORIGIN, DIALOG_TITLE_ROWS, BLACK)
        _draw_glyph(surf, WELCOME_LINE1_ORIGIN, WELCOME_LINE1_ROWS, BLACK)
        _draw_glyph(surf, WELCOME_LINE2_ORIGIN, WELCOME_LINE2_ROWS, BLACK)
        _bevel_rect(surf, BUTTON_OUTER_BEVEL_RECT, raised=False)  # the well
        _black_ring(surf, BUTTON_OUTLINE_RECT)
        _bevel_rect(surf, BUTTON_INNER_BEVEL_RECT)  # the button itself, raised out of the well
        _draw_glyph(surf, GOT_IT_ORIGIN, GOT_IT_ROWS, BLACK)

    _bevel_rect(surf, STATUS_TEXT_BOX_RECT, raised=False)
    _draw_glyph(surf, STATUS_TEXT_ORIGIN, STATUS_TEXT_ROWS, BLACK)
    _bevel_rect(surf, ICON_BOX_RECT, raised=False)
    _draw_icon_grid(surf)
    _draw_resize_grip(surf)
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
        x, y, w, h = BUTTON_OUTER_BEVEL_RECT
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
