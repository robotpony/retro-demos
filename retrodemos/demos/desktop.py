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
"""

from __future__ import annotations

import pygame

from retrodemos.demos.bruces_windows import BruceWindowsDemo
from retrodemos.demos.cd_player import CDPlayerDemo
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
ICON_ORIGIN = (40, 30)
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
# these five icons, in this order.
_DEMO_ENTRIES: list[tuple[str, str, type[Demo]]] = [
    ("led", "LED", LedDemo),
    ("led_ii", "LED II", LedIIDemo),
    ("title", "TITLE", TitleDemo),
    ("cd_player", "CD PLAYER", CDPlayerDemo),
    ("bruces_windows", "WINDOWS", BruceWindowsDemo),
]

CASCADE_STEP = 28
CASCADE_BASE = (140, 100)
CASCADE_WRAP = 8


def _icon_cells(key: str) -> set[tuple[int, int]]:
    return {(x, y) for y, row in enumerate(_ICON_GLYPHS[key]) for x, ch in enumerate(row) if ch == "#"}


def _icon_glyph_size(key: str) -> tuple[int, int]:
    rows = _ICON_GLYPHS[key]
    return max(len(row) for row in rows), len(rows)


def _icon_slot_rect(index: int) -> pygame.Rect:
    x0, y0 = ICON_ORIGIN
    return pygame.Rect(x0 + index * ICON_SLOT_W, y0, ICON_SLOT_W, ICON_SLOT_H)


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
    def __init__(self, key: str, title: str, demo: Demo, pos: tuple[int, int]) -> None:
        self.key = key
        self.title = title
        self.demo = demo
        self.pos = list(pos)
        self._content_surface = pygame.Surface(demo.NATIVE_SIZE)
        # Chrome geometry (window size, title bar/close/content rects) only
        # depends on content size + title, both fixed once a window is
        # open -- compute once here rather than every draw() call.
        surf, self.local_rects = render_window_chrome(self._content_surface, title)
        self.size = surf.get_size()

    def screen_rect(self) -> pygame.Rect:
        return pygame.Rect(self.pos, self.size)

    def title_bar_screen_rect(self) -> pygame.Rect:
        r = self.local_rects["title_bar"]
        return pygame.Rect(self.pos[0] + r.x, self.pos[1] + r.y, r.width, r.height)

    def close_button_screen_rect(self) -> pygame.Rect:
        r = self.local_rects["close_button"]
        return pygame.Rect(self.pos[0] + r.x, self.pos[1] + r.y, r.width, r.height)

    def content_screen_rect(self) -> pygame.Rect:
        r = self.local_rects["content"]
        return pygame.Rect(self.pos[0] + r.x, self.pos[1] + r.y, r.width, r.height)

    def to_content_local(self, screen_pos: tuple[int, int]) -> tuple[int, int]:
        content = self.content_screen_rect()
        return (screen_pos[0] - content.x, screen_pos[1] - content.y)

    def render(self) -> pygame.Surface:
        self.demo.draw(self._content_surface)
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

    def _open_demo(self, key: str, title: str, demo_cls: type[Demo]) -> None:
        if key in self._open:
            self._focus(key)
            return
        n = len(self._order)
        pos = (
            CASCADE_BASE[0] + (n % CASCADE_WRAP) * CASCADE_STEP,
            CASCADE_BASE[1] + (n % CASCADE_WRAP) * CASCADE_STEP,
        )
        self._open[key] = _OpenWindow(key, title, demo_cls(text=None), pos)
        self._order.append(key)

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

        for i, (demo_key, title, demo_cls) in enumerate(_DEMO_ENTRIES):
            if demo_key in self._open:
                continue
            if _icon_slot_rect(i).collidepoint(pos):
                self._open_demo(demo_key, title, demo_cls)
                return

    def update(self, dt: float) -> None:
        for key in self._order:
            self._open[key].demo.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(DESKTOP_BG)
        for i, (key, title, _demo_cls) in enumerate(_DEMO_ENTRIES):
            if key not in self._open:
                _draw_icon(surface, key, title, _icon_slot_rect(i))
        for key in self._order:
            win = self._open[key]
            surface.blit(win.render(), win.pos)


DEMO_CLASS = DesktopDemo
