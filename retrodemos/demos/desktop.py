"""The desktop shell: the root interface of `retrodemos` itself
(`PLAN.md`'s "Future: the unified desktop"). One icon per demo; click to
open it as its own draggable/closable window, reusing
`framework/window_chrome.py`'s generic wrapper around that demo's own
`Demo.draw()` output.

New content throughout -- there's no source screenshot for a desktop full
of icons, unlike every other demo in this project (see
`framework/pixel_font.py`'s and `framework/window_chrome.py`'s own
docstrings for the same point about their own pieces). The icon glyphs
were mocked up and confirmed with Bruce before wiring in (2026-08-25),
same workflow CD Player's prototype pass and Bruce's Windows' pixel
archaeology got, just without a source image to measure against.

One instance per demo at a time. An open demo's icon doesn't disappear
(2026-08-25: that "is weird") -- it stays put and dims, same as any
other disabled control, and clicking it does nothing while its window is
open. `bruces_windows` is disabled outright regardless of open state, in
`_PERMANENTLY_DISABLED`: a demo *of* windowing reads as redundant now
that the desktop itself is a real windowing system, so it's parked
rather than removed -- see that set's own comment. Every open demo keeps
running its own `update(dt)` even when not focused, the same "several
little utility programs left open together" attract-mode feel `PLAN.md`
describes. Background windows aren't paused.

Most demos get exactly one window through the generic chrome wrapper
above. CD Player is the exception (2026-08-25 playtesting: "should get
real windows, not appear in another window"): its main and equalizer
panels already draw their own complete chrome (see
`cd_player.py`'s module docstring), so wrapping them in a *second*,
generic chrome read as a window inside a window. `_OpenWindow` supports
a `chrome=False` mode for exactly this -- no generic wrapper, and
close/drag hit-testing reads `close_rect`/`button_rects` straight off
the demo instance instead of a chrome-supplied rect dict. Opening CD
Player's icon opens only its main window; the equalizer starts hidden
and is revealed by clicking the main window's body, both special-cased
in `_open_cd_player_main`/`_reveal_cd_player_eq` rather than
generalized -- the only demo that needs multi-window treatment so far.

A macOS-style top menu bar (2026-08-25, new content -- no source image
for this either) sits above every window: white, exactly tall enough for
one line of `pixel_font` text plus 2px padding on each side, the command
glyph at the left, and the focused window's title (or "HELP" with
nothing focused) after it. Both render bold (`_draw_bold`: every lit
cell gets a second one a column to its right, a cheap way to thicken a
1px-stroke font that has no separate bold weight) -- an earlier
drop-shadow version was dropped in favour of this once seen live. It's
functional, not decorative: the command icon opens a dropdown with About
(a small info panel), Close All Windows, and Quit; the "HELP" text
itself, while nothing is focused, opens a panel of condensed `README.md`
content (`_HELP_LINES` -- paraphrased, since `pixel_font` has no
punctuation beyond an apostrophe). Quit needed one small framework
addition -- `Demo.want_quit`, a poll-based flag `runtime.run()` checks
each frame, since until now only Esc/Q (handled before any demo ever
sees the event) could end a run. Windows are clamped below the bar; they
can never be dragged underneath it.
"""

from __future__ import annotations

import pygame

from retrodemos.demos.bruces_windows import BruceWindowsDemo
from retrodemos.demos.cd_player import CDPlayerEqualizerWindow, CDPlayerMainWindow
from retrodemos.demos.led import LedDemo
from retrodemos.demos.led_ii import LedIIDemo
from retrodemos.demos.title import TitleDemo
from retrodemos.framework.demo import Demo
from retrodemos.framework.pixel_font import GLYPH_GAP, GLYPH_H, text_cells
from retrodemos.framework.window_chrome import BEZEL_DARK, render_window_chrome

DESKTOP_BG = (0, 128, 128)  # invented -- matches the teal Bruce's Windows itself used to use as its own backdrop
ICON_FG = (255, 255, 255)
ICON_DISABLED_FG = (0, 96, 96)  # dimmed toward DESKTOP_BG, not hidden -- still visibly present, just inert
NATIVE_SIZE = (1024, 576)

# Top menu bar, macOS-style (2026-08-25): white strip across the full
# width, the desktop's own teal used for its text/glyphs, bolded (see
# _draw_bold) rather than shadowed -- an earlier drop-shadow version was
# dropped in favour of a heavier weight instead. Height is exactly 2px
# padding + one line of `pixel_font` text + 2px padding, so the bar is
# only ever as tall as it needs to be for whatever font the rest of the
# chrome uses.
MENU_BAR_BG = (255, 255, 255)
MENU_TEXT = DESKTOP_BG
MENU_PADDING = 2
MENU_BAR_HEIGHT = MENU_PADDING + GLYPH_H + MENU_PADDING
MENU_SIDE_MARGIN = 4
# _draw_bold thickens each glyph by one column to its right -- laid out
# at the font's own default 1px gap, that thickened column runs straight
# into the next glyph with no visible space at all. Every bold text_cells
# call on the bar/dropdown/panels uses this wider gap instead.
_BOLD_GAP = GLYPH_GAP + 1

ICON_SCALE = 3  # icon glyph pixel scale; labels render at the font's own native 1px
ICON_SLOT_W = 110
ICON_SLOT_H = 70
ICON_ORIGIN = (30, MENU_BAR_HEIGHT + 19)  # 19px gap below the bar, same gap the bar itself replaced
ICON_GRID_ROWS = 6  # icons per column before wrapping to a new column, classic desktop-style
LABEL_GAP = 5  # px between an icon's glyph and its label, at ICON_SCALE

# Icon glyphs: new pixel art, "#"=lit, not archaeology -- see module
# docstring. Each evokes its own demo's actual on-screen content.
_ICON_GLYPHS: dict[str, tuple[str, ...]] = {
    "led": (
        ".####.",
        "#....#",
        "#....#",
        ".####.",
        "#....#",
        "#....#",
        ".####.",
    ),
    "led_ii": (
        "#.#.#.#",
        ".......",
        "#.#.#.#",
        ".......",
        "#.#.#.#",
        ".......",
        "#.#.#.#",
    ),
    "title": (
        "########",
        "#.#.#.#.",
        "########",
        "........",
        "########",
        ".#.#.#.#",
        "########",
    ),
    "cd_player": (
        "..###..",
        ".#####.",
        "##...##",
        "##.#.##",
        "##...##",
        ".#####.",
        "..###..",
    ),
    "bruces_windows": (
        "#########",
        "#########",
        "#.......#",
        "#.......#",
        "#.......#",
        "#.......#",
        "#########",
    ),
}

# (module key, display title, Demo class) -- a curated, fixed list, not a
# generic directory scan like __main__.py's -- the desktop only ever shows
# these five icons, in this order. cd_player's class slot is None: it
# doesn't open through the generic single-window path at all (see
# _open_cd_player_main below) -- its icon and cascade position still come
# from this table, but opening it is special-cased.
_DEMO_ENTRIES: list[tuple[str, str, type[Demo] | None]] = [
    ("led", "LED", LedDemo),
    ("led_ii", "LED II", LedIIDemo),
    ("title", "TITLE", TitleDemo),
    ("cd_player", "CD PLAYER", None),
    ("bruces_windows", "WINDOWS", BruceWindowsDemo),
]

# cd_player's icon represents two independently-opened windows, not one
# -- the icon should disable once its main window is open, whether or
# not the equalizer has been revealed alongside it (see module docstring
# on CDPlayerMainWindow/CDPlayerEqualizerWindow for why they're separate).
_ICON_OPEN_KEY = {"cd_player": "cd_player_main"}

# Disabled outright, regardless of open state -- greyed out and inert,
# still visible rather than removed. Bruce's Windows started as the
# demo that validated the desktop's own window-chrome pattern, but a
# demo *of* windowing inside a real windowing system now reads as
# redundant; parked here rather than removed since a use for it may
# still turn up (2026-08-25).
_PERMANENTLY_DISABLED = {"bruces_windows"}

# What the menu bar calls each open-window key -- most come straight from
# _DEMO_ENTRIES, but CD Player's two chromeless windows (cd_player_main/
# cd_player_eq) aren't in that table under those keys, so they get their
# own two entries.
_WINDOW_TITLES: dict[str, str] = {key: title for key, title, _cls in _DEMO_ENTRIES if key != "cd_player"}
_WINDOW_TITLES["cd_player_main"] = "CD PLAYER"
_WINDOW_TITLES["cd_player_eq"] = "EQUALIZER"

# The command-key glyph, new pixel art like the icon glyphs above -- no
# source to measure. Four square "loop" corners joined by a thin bridge
# through the middle, evoking the real glyph's four connected loops
# better than a flat bracket pair did (2026-08-25: the first version
# read as "weird"). 9x9 -- doesn't need to match GLYPH_H like the app
# title text next to it does, just fit inside MENU_BAR_HEIGHT (it does,
# with a 1px margin top and bottom).
_CMD_GLYPH = (
    "###...###",
    "#.#...#.#",
    "#.#...#.#",
    "##.....##",
    "..#####..",
    "##.....##",
    "#.#...#.#",
    "#.#...#.#",
    "###...###",
)
_CMD_GLYPH_CELLS = {(x, y) for y, row in enumerate(_CMD_GLYPH) for x, ch in enumerate(row) if ch == "#"}
_CMD_GLYPH_W = len(_CMD_GLYPH[0])

# The dropdown under the command icon -- functional, not decorative: About
# shows a small info panel, Close All Windows clears every open window,
# Quit ends the whole run (via Demo.want_quit -- see runtime.py).
_MENU_ITEMS: tuple[tuple[str, str], ...] = (
    ("about", "ABOUT RETRODEMOS"),
    ("close_all", "CLOSE ALL WINDOWS"),
    ("quit", "QUIT"),
)
_MENU_ITEM_HEIGHT = MENU_PADDING + GLYPH_H + MENU_PADDING
_MENU_ITEM_PADDING_X = 6

CASCADE_STEP = 28
CASCADE_BASE = (140, 100 + MENU_BAR_HEIGHT)
CASCADE_WRAP = 8


def _icon_cells(key: str) -> set[tuple[int, int]]:
    return {(x, y) for y, row in enumerate(_ICON_GLYPHS[key]) for x, ch in enumerate(row) if ch == "#"}


def _icon_glyph_size(key: str) -> tuple[int, int]:
    rows = _ICON_GLYPHS[key]
    return max(len(row) for row in rows), len(rows)


def _icon_slot_rect(index: int) -> pygame.Rect:
    # Column-major grid, filling top-to-bottom then wrapping to a new
    # column on the right -- keeps icons pinned to the left edge and all
    # visible at once, the way a real desktop lays out its icons.
    x0, y0 = ICON_ORIGIN
    col, row = divmod(index, ICON_GRID_ROWS)
    return pygame.Rect(x0 + col * ICON_SLOT_W, y0 + row * ICON_SLOT_H, ICON_SLOT_W, ICON_SLOT_H)


def _draw_icon(surface: pygame.Surface, key: str, title: str, slot: pygame.Rect, *, disabled: bool = False) -> None:
    colour = ICON_DISABLED_FG if disabled else ICON_FG
    gw, gh = _icon_glyph_size(key)
    glyph_w_px, glyph_h_px = gw * ICON_SCALE, gh * ICON_SCALE
    gx = slot.x + (slot.width - glyph_w_px) // 2
    gy = slot.y
    for x, y in _icon_cells(key):
        surface.fill(colour, (gx + x * ICON_SCALE, gy + y * ICON_SCALE, ICON_SCALE, ICON_SCALE))

    label_cells, label_w = text_cells(title)
    lx = slot.x + (slot.width - label_w) // 2
    ly = gy + glyph_h_px + LABEL_GAP
    for x, y in label_cells:
        surface.set_at((lx + x, ly + y), colour)


def _draw_bold(surface: pygame.Surface, cells: set[tuple[int, int]], x0: int, y0: int) -> None:
    """A cheap "bold" for a 1px-stroke font: every lit cell gets a second
    lit cell one column to its right, thickening each vertical stroke
    without redrawing the glyph at a different weight (there isn't one --
    see pixel_font.py's own docstring). Plain MENU_TEXT, no shadow."""
    for x, y in cells:
        surface.set_at((x0 + x, y0 + y), MENU_TEXT)
        surface.set_at((x0 + x + 1, y0 + y), MENU_TEXT)


def _cmd_icon_rect() -> pygame.Rect:
    # Wider than the glyph itself so the click target isn't a fiddly 7px
    # square -- the whole left end of the bar, same idea as a real menu
    # bar's Apple-menu hit zone being bigger than the logo glyph.
    return pygame.Rect(0, 0, MENU_SIDE_MARGIN * 2 + _CMD_GLYPH_W + 12, MENU_BAR_HEIGHT)


def _menu_item_rects() -> list[pygame.Rect]:
    width = max(text_cells(label, gap=_BOLD_GAP)[1] for _id, label in _MENU_ITEMS) + _MENU_ITEM_PADDING_X * 2
    return [pygame.Rect(0, MENU_BAR_HEIGHT + i * _MENU_ITEM_HEIGHT, width, _MENU_ITEM_HEIGHT) for i in range(len(_MENU_ITEMS))]


def _draw_menu_bar(surface: pygame.Surface, app_title: str) -> None:
    width = surface.get_width()
    surface.fill(MENU_BAR_BG, (0, 0, width, MENU_BAR_HEIGHT))
    gy = (MENU_BAR_HEIGHT - len(_CMD_GLYPH)) // 2
    _draw_bold(surface, _CMD_GLYPH_CELLS, MENU_SIDE_MARGIN, gy)

    title_cells, _title_w = text_cells(app_title, gap=_BOLD_GAP)
    tx = MENU_SIDE_MARGIN * 2 + _CMD_GLYPH_W + 8
    ty = MENU_PADDING
    _draw_bold(surface, title_cells, tx, ty)


def _app_title_rect(app_title: str) -> pygame.Rect:
    """Where `_draw_menu_bar` puts the app-name text -- used to hit-test
    a click on it (only meaningful while it reads "HELP", see
    DesktopDemo._handle_click)."""
    _cells, width = text_cells(app_title, gap=_BOLD_GAP)
    x = MENU_SIDE_MARGIN * 2 + _CMD_GLYPH_W + 8
    return pygame.Rect(x, 0, width + 1, MENU_BAR_HEIGHT)  # +1: _draw_bold's own thickening


def _draw_dropdown(surface: pygame.Surface) -> None:
    rects = _menu_item_rects()
    outline = rects[0].unionall(rects[1:])
    pygame.draw.rect(surface, MENU_BAR_BG, outline)
    pygame.draw.rect(surface, BEZEL_DARK, outline, width=1)
    for (item_id, label), rect in zip(_MENU_ITEMS, rects):
        cells, _w = text_cells(label, gap=_BOLD_GAP)
        _draw_bold(surface, cells, rect.x + _MENU_ITEM_PADDING_X, rect.y + MENU_PADDING)
        if rect is not rects[-1]:
            pygame.draw.line(surface, BEZEL_DARK, (rect.left, rect.bottom - 1), (rect.right - 1, rect.bottom - 1))


# Both overlay panels (About, Help) are the same shape: a centred white
# box, one pixel_font line per row. Content only differs in which lines
# they hold, so one pair of helpers draws both.
_ABOUT_LINES = ("RETRODEMOS", "", "RECREATIONS OF BRUCE'S EARLY", "1990S DEMO PROGRAMS")

# Condensed from README.md -- pixel_font only has A-Z/0-9/'/space (see its
# own docstring), so this paraphrases rather than quoting verbatim;
# punctuation the font can't render (periods, parens, backticks) is
# dropped rather than showing as gaps.
_HELP_LINES = (
    "RETRO DEMOS",
    "",
    "DEMOS BASED ON PROGRAMS WRITTEN IN THE",
    "EARLY 1990S FOR THE ATARI ST AND EARLY",
    "WINDOWS MACHINES",
    "",
    "CLICK AN ICON TO OPEN A DEMO AS A WINDOW",
    "DRAG A WINDOW TO MOVE IT",
    "CLICK ITS CLOSE BUTTON TO SHUT IT",
    "",
    "CONTROLS",
    "ESC OR Q QUIT",
    "SPACE PAUSE OR RESUME",
    "R RESTART",
)


def _panel_rect(lines: tuple[str, ...]) -> pygame.Rect:
    width = max(text_cells(line, gap=_BOLD_GAP)[1] for line in lines) + 24
    height = len(lines) * (GLYPH_H + 3) + 20
    x = (NATIVE_SIZE[0] - width) // 2
    y = (NATIVE_SIZE[1] - height) // 2
    return pygame.Rect(x, y, width, height)


def _draw_panel(surface: pygame.Surface, lines: tuple[str, ...]) -> None:
    rect = _panel_rect(lines)
    pygame.draw.rect(surface, MENU_BAR_BG, rect)
    pygame.draw.rect(surface, BEZEL_DARK, rect, width=1)
    for i, line in enumerate(lines):
        cells, _w = text_cells(line, gap=_BOLD_GAP)
        _draw_bold(surface, cells, rect.x + 12, rect.y + 10 + i * (GLYPH_H + 3))


class _OpenWindow:
    def __init__(self, key: str, title: str, demo: Demo, pos: tuple[int, int], *, chrome: bool = True) -> None:
        self.key = key
        self.title = title
        self.demo = demo
        self.pos = list(pos)
        self.chrome = chrome
        self._content_surface = pygame.Surface(demo.NATIVE_SIZE)
        if chrome:
            # Chrome geometry (window size, title bar/close/content rects)
            # only depends on content size + title, both fixed once a
            # window is open -- compute once here rather than every
            # draw() call.
            surf, self.local_rects = render_window_chrome(self._content_surface, title)
            self.size = surf.get_size()
        else:
            # No generic wrapper: the demo draws its own complete chrome
            # (own border, own close button) -- CD Player's two windows,
            # so far the only case (2026-08-25, "should get real windows,
            # not appear in another window"). Hit-testing for close/drag
            # reads close_rect/button_rects straight off the demo
            # instance instead of a chrome-supplied rect dict.
            self.local_rects = {}
            self.size = demo.NATIVE_SIZE

    def screen_rect(self) -> pygame.Rect:
        return pygame.Rect(self.pos, self.size)

    def title_bar_screen_rect(self) -> pygame.Rect:
        r = self.local_rects["title_bar"]
        return pygame.Rect(self.pos[0] + r.x, self.pos[1] + r.y, r.width, r.height)

    def close_button_screen_rect(self) -> pygame.Rect:
        r = self.local_rects["close_button"]
        return pygame.Rect(self.pos[0] + r.x, self.pos[1] + r.y, r.width, r.height)

    def content_screen_rect(self) -> pygame.Rect:
        if not self.chrome:
            return self.screen_rect()
        r = self.local_rects["content"]
        return pygame.Rect(self.pos[0] + r.x, self.pos[1] + r.y, r.width, r.height)

    def to_content_local(self, screen_pos: tuple[int, int]) -> tuple[int, int]:
        content = self.content_screen_rect()
        return (screen_pos[0] - content.x, screen_pos[1] - content.y)

    def render(self) -> pygame.Surface:
        self.demo.draw(self._content_surface)
        if not self.chrome:
            return self._content_surface
        surf, _ = render_window_chrome(self._content_surface, self.title)
        return surf


class DesktopDemo(Demo):
    NATIVE_SIZE = NATIVE_SIZE

    def __init__(self, *, text: str | None = None, **_ignored) -> None:
        self.reset()

    def reset(self) -> None:
        self._open: dict[str, _OpenWindow] = {}
        self._order: list[str] = []  # z-order, back to front; last = focused/topmost
        self._dragging: str | None = None
        self._mouse_down_key: str | None = None
        self._menu_open = False
        self._about_open = False
        self._help_open = False
        self.want_quit = False  # polled by runtime.run() -- see its own comment

    def _open_demo(self, key: str, title: str, demo_cls: type[Demo]) -> None:
        if key in self._open:
            self._focus(key)
            return
        self._open[key] = _OpenWindow(key, title, demo_cls(text=None), self._next_cascade_pos())
        self._order.append(key)

    def _next_cascade_pos(self) -> tuple[int, int]:
        n = len(self._order)
        return (
            CASCADE_BASE[0] + (n % CASCADE_WRAP) * CASCADE_STEP,
            CASCADE_BASE[1] + (n % CASCADE_WRAP) * CASCADE_STEP,
        )

    def _open_cd_player_main(self) -> None:
        # CD Player's two windows are opened directly as top-level desktop
        # windows (chrome=False -- they draw their own complete chrome),
        # not through _open_demo's single-window path. The equalizer
        # isn't opened here at all -- it starts hidden, matching the
        # source (see CDPlayerMainWindow's own docstring); clicking the
        # main window's body reveals it (_handle_click below).
        if "cd_player_main" in self._open:
            self._focus("cd_player_main")
            return
        self._open["cd_player_main"] = _OpenWindow(
            "cd_player_main", "", CDPlayerMainWindow(text=None), self._next_cascade_pos(), chrome=False
        )
        self._order.append("cd_player_main")

    def _reveal_cd_player_eq(self) -> None:
        if "cd_player_eq" in self._open:
            self._focus("cd_player_eq")
            return
        main_pos = self._open["cd_player_main"].pos
        main_w = self._open["cd_player_main"].size[0]
        pos = (main_pos[0] + main_w + 4, main_pos[1])
        self._open["cd_player_eq"] = _OpenWindow(
            "cd_player_eq", "", CDPlayerEqualizerWindow(text=None), pos, chrome=False
        )
        self._order.append("cd_player_eq")

    def _focus(self, key: str) -> None:
        if key in self._order:
            self._order.remove(key)
            self._order.append(key)

    def _close(self, key: str) -> None:
        self._open.pop(key, None)
        if key in self._order:
            self._order.remove(key)
        if self._dragging == key:
            self._dragging = None

    def _window_at(self, pos: tuple[int, int]) -> str | None:
        for key in reversed(self._order):
            if self._open[key].screen_rect().collidepoint(pos):
                return key
        return None

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_click(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            # Chromeless windows (CD Player's own) need the release too --
            # a transport button's press animation clears on mouse-up, not
            # just on the next mouse-down (see CDPlayerMainWindow).
            if self._mouse_down_key is not None:
                win = self._open.get(self._mouse_down_key)
                if win is not None and not win.chrome:
                    local_pos = win.to_content_local(event.pos)
                    win.demo.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=local_pos, button=1))
            self._mouse_down_key = None
            self._dragging = None
        elif event.type == pygame.MOUSEMOTION and self._dragging is not None:
            win = self._open.get(self._dragging)
            if win is not None:
                win.pos[0] += event.rel[0]
                win.pos[1] += event.rel[1]
                max_x = NATIVE_SIZE[0] - win.size[0]
                max_y = NATIVE_SIZE[1] - win.size[1]
                win.pos[0] = max(0, min(max_x, win.pos[0]))
                # Clamped below the menu bar, not the desktop's own top
                # edge -- a window can't be dragged up under it.
                win.pos[1] = max(MENU_BAR_HEIGHT, min(max_y, win.pos[1]))

    def _focused_app_title(self) -> str:
        if not self._order:
            return "HELP"
        title = _WINDOW_TITLES.get(self._order[-1], self._order[-1].upper())
        return f"{title} demo"

    def _handle_click(self, pos: tuple[int, int]) -> None:
        # The menu bar sits above every window, so its own hit-testing
        # (and whatever overlay it has open) comes first.
        if self._about_open:
            self._about_open = False  # any click anywhere dismisses it
            return
        if self._help_open:
            self._help_open = False  # same -- any click dismisses it
            return
        if self._menu_open:
            self._menu_open = False
            for (item_id, _label), rect in zip(_MENU_ITEMS, _menu_item_rects()):
                if rect.collidepoint(pos):
                    if item_id == "about":
                        self._about_open = True
                    elif item_id == "close_all":
                        self._open.clear()
                        self._order.clear()
                        self._dragging = None
                        self._mouse_down_key = None
                    elif item_id == "quit":
                        self.want_quit = True
                    break
            return
        if _cmd_icon_rect().collidepoint(pos):
            self._menu_open = True
            return
        app_title = self._focused_app_title()
        if app_title == "HELP" and _app_title_rect(app_title).collidepoint(pos):
            self._help_open = True
            return

        key = self._window_at(pos)
        if key is not None:
            win = self._open[key]
            if win.chrome:
                if win.close_button_screen_rect().collidepoint(pos):
                    self._close(key)
                    return
                self._focus(key)
                if win.title_bar_screen_rect().collidepoint(pos):
                    self._dragging = key
                    return
                if win.content_screen_rect().collidepoint(pos):
                    local_pos = win.to_content_local(pos)
                    win.demo.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=local_pos, button=1))
                return

            # Chromeless: the demo drew its own close button and any other
            # controls, so ask it directly (close_rect/button_rects)
            # rather than a chrome-supplied rect dict. Any other body
            # click both starts a drag and gets forwarded to the demo --
            # CD Player's main window uses that to reveal the equalizer.
            self._focus(key)
            self._mouse_down_key = key
            local_pos = win.to_content_local(pos)
            win.demo.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=local_pos, button=1))
            if getattr(win.demo, "closed", False):
                self._close(key)
                return
            if key == "cd_player_main" and getattr(win.demo, "reveal_equalizer", False):
                win.demo.reveal_equalizer = False
                self._reveal_cd_player_eq()
            close_rect = getattr(win.demo, "close_rect", None)
            button_rects = getattr(win.demo, "button_rects", {})
            hit_control = (close_rect is not None and close_rect.collidepoint(local_pos)) or any(
                r.collidepoint(local_pos) for r in button_rects.values()
            )
            if not hit_control:
                self._dragging = key
            return

        for i, (demo_key, title, demo_cls) in enumerate(_DEMO_ENTRIES):
            if self._icon_disabled(demo_key):
                continue
            if _icon_slot_rect(i).collidepoint(pos):
                if demo_key == "cd_player":
                    self._open_cd_player_main()
                else:
                    self._open_demo(demo_key, title, demo_cls)
                return

    def _icon_disabled(self, demo_key: str) -> bool:
        if demo_key in _PERMANENTLY_DISABLED:
            return True
        open_key = _ICON_OPEN_KEY.get(demo_key, demo_key)
        return open_key in self._open

    def update(self, dt: float) -> None:
        for key in self._order:
            self._open[key].demo.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(DESKTOP_BG)
        # Every icon stays visible always -- an open (or permanently
        # disabled) demo's icon just goes inert and dims, rather than
        # disappearing (2026-08-25: disappearing "is weird").
        for i, (key, title, _demo_cls) in enumerate(_DEMO_ENTRIES):
            _draw_icon(surface, key, title, _icon_slot_rect(i), disabled=self._icon_disabled(key))
        for key in self._order:
            win = self._open[key]
            surface.blit(win.render(), win.pos)

        # Menu bar and its overlays always sit on top of every window.
        _draw_menu_bar(surface, self._focused_app_title())
        if self._menu_open:
            _draw_dropdown(surface)
        if self._about_open:
            _draw_panel(surface, _ABOUT_LINES)
        if self._help_open:
            _draw_panel(surface, _HELP_LINES)


DEMO_CLASS = DesktopDemo
