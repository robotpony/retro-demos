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

One instance per demo at a time (opening an already-open demo's icon just
focuses its existing window instead of spawning a second one); every open
demo keeps running its own `update(dt)` even when not focused, the same
"several little utility programs left open together" attract-mode feel
`PLAN.md` describes. Background windows aren't paused.

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
"""

from __future__ import annotations

import pygame

from retrodemos.demos.bruces_windows import BruceWindowsDemo
from retrodemos.demos.cd_player import CDPlayerEqualizerWindow, CDPlayerMainWindow
from retrodemos.demos.led import LedDemo
from retrodemos.demos.led_ii import LedIIDemo
from retrodemos.demos.title import TitleDemo
from retrodemos.framework.demo import Demo
from retrodemos.framework.pixel_font import text_cells
from retrodemos.framework.window_chrome import render_window_chrome

DESKTOP_BG = (0, 128, 128)  # invented -- matches the teal Bruce's Windows itself used to use as its own backdrop
ICON_FG = (255, 255, 255)
NATIVE_SIZE = (1024, 576)

ICON_SCALE = 3  # icon glyph pixel scale; labels render at the font's own native 1px
ICON_SLOT_W = 110
ICON_SLOT_H = 70
ICON_ORIGIN = (30, 30)
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
# -- the icon should hide once its main window is open, whether or not
# the equalizer has been revealed alongside it (see module docstring on
# CDPlayerMainWindow/CDPlayerEqualizerWindow for why they're separate).
_ICON_OPEN_KEY = {"cd_player": "cd_player_main"}

CASCADE_STEP = 28
CASCADE_BASE = (140, 100)
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


def _draw_icon(surface: pygame.Surface, key: str, title: str, slot: pygame.Rect) -> None:
    gw, gh = _icon_glyph_size(key)
    glyph_w_px, glyph_h_px = gw * ICON_SCALE, gh * ICON_SCALE
    gx = slot.x + (slot.width - glyph_w_px) // 2
    gy = slot.y
    for x, y in _icon_cells(key):
        surface.fill(ICON_FG, (gx + x * ICON_SCALE, gy + y * ICON_SCALE, ICON_SCALE, ICON_SCALE))

    label_cells, label_w = text_cells(title)
    lx = slot.x + (slot.width - label_w) // 2
    ly = gy + glyph_h_px + LABEL_GAP
    for x, y in label_cells:
        surface.set_at((lx + x, ly + y), ICON_FG)


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
                win.pos[1] = max(0, min(max_y, win.pos[1]))

    def _handle_click(self, pos: tuple[int, int]) -> None:
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
            open_key = _ICON_OPEN_KEY.get(demo_key, demo_key)
            if open_key in self._open:
                continue
            if _icon_slot_rect(i).collidepoint(pos):
                if demo_key == "cd_player":
                    self._open_cd_player_main()
                else:
                    self._open_demo(demo_key, title, demo_cls)
                return

    def update(self, dt: float) -> None:
        for key in self._order:
            self._open[key].demo.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(DESKTOP_BG)
        for i, (key, title, _demo_cls) in enumerate(_DEMO_ENTRIES):
            open_key = _ICON_OPEN_KEY.get(key, key)
            if open_key not in self._open:
                _draw_icon(surface, key, title, _icon_slot_rect(i))
        for key in self._order:
            win = self._open[key]
            surface.blit(win.render(), win.pos)


DEMO_CLASS = DesktopDemo
