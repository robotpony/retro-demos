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

This demo used to own a bigger (320x240) canvas and its own title-bar-drag
logic, simulating a tiny one-window desktop by itself. Simplified back down
to a plain 200x200 static render (2026-08-25) once `framework/window_chrome.py`
took over dragging generically for every window the real desktop shell
opens (`PLAN.md`'s "Future: the unified desktop") -- this demo is now just
one exhibit among the desktop's windows, the same as any other, wrapped in
that shared chrome rather than building its own. `_bevel_rect`/`_black_ring`
moved there too, once the desktop became a second real caller for the same
primitives (still exposed here for the reconstruct-and-diff test, which
composes them the way this file's own screenshot layout does -- a shape
`window_chrome.render_window_chrome`'s generic wrapper doesn't reproduce,
so this file keeps `_render_window` rather than routing through it). The
"Got it" button still closes the dialog; that's this exhibit's own content,
not chrome, so it stays here.
"""

from __future__ import annotations

import pygame

from retrodemos.framework.demo import Demo
from retrodemos.framework.window_chrome import BEZEL_DARK, BLACK, PANEL, TITLE_CYAN, WHITE
from retrodemos.framework.window_chrome import bevel_rect as _bevel_rect
from retrodemos.framework.window_chrome import black_ring as _black_ring

GREEN_ON = (0, 255, 0)
RED_ON = (191, 0, 0)

WINDOW_SIZE = (200, 200)

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
    """The exhibit itself: a plain, static 200x200 render of `WINDOW1.png`,
    with only the "Got it" button live (closes the dialog). No drag, no
    window-within-a-window canvas -- see the module docstring for why that
    moved to `framework/window_chrome.py` as the desktop shell's own
    generic responsibility. Launched standalone (`python -m retrodemos
    bruces_windows`) it just sits there at native size; opened from the
    desktop it gets the same draggable/closable chrome every other demo's
    window does.
    """

    NATIVE_SIZE = WINDOW_SIZE

    def __init__(self, *, text: str | None = None, **_ignored) -> None:
        self.reset()

    def reset(self) -> None:
        self._dialog_open = True

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._dialog_open and pygame.Rect(*BUTTON_OUTER_BEVEL_RECT).collidepoint(event.pos):
                self._dialog_open = False

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(_render_window(self._dialog_open), (0, 0))


DEMO_CLASS = BruceWindowsDemo
