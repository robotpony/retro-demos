"""Reusable Windows 3.1-style window chrome, extracted from
`retrodemos/demos/bruces_windows.py` (2026-08-25) once the desktop shell
(`PLAN.md`'s "Future: the unified desktop") became a second real caller for
the same border primitives -- see `bruces_windows.py`'s module docstring
for the full pixel-archaeology history behind `_bevel_rect`/`_black_ring`
themselves (measured against `images/WINDOW1.png`, byte-exact).

`render_window_chrome` itself is new, not archaeology: WINDOW1.png's own
Dialog archetype has no close control at all, and needs a title that can
be any demo's name, not the fixed strings "Window Title"/"Dialog" the
source shows. It reuses the *verified* primitives (colours, bevel
direction, mitered corners) but composes them into a generic wrapper --
see `framework/pixel_font.py` for the same "new design, built consistent
with everything measured" reasoning applied to the title text.
"""

from __future__ import annotations

import pygame

from .pixel_font import GLYPH_GAP, GLYPH_H, text_cells

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BEZEL_DARK = (128, 128, 128)
PANEL = (192, 192, 192)
TITLE_CYAN = (0, 191, 191)

BORDER = 2  # 1px black ring + 1px bevel line, on every side
MARGIN = 2  # background gap between the border/title bar and their neighbours
TITLE_TEXT_PADDING = 2  # above and below the title glyphs, inside the cyan bar
CLOSE_BUTTON_SIZE = 11


def _rect_outline(surface: pygame.Surface, rect: tuple[int, int, int, int], top_left: tuple[int, int, int], bottom_right: tuple[int, int, int]) -> None:
    """One 1px outline: `top_left` on the top+left edges, `bottom_right` on
    the bottom+right edges, mitered rather than closed -- the top-right and
    bottom-left corners (where the two colours would collide) are left
    unset, matching what WINDOW1.png's own borders actually do (see
    `bruces_windows.py`'s module docstring)."""
    x, y, w, h = rect
    pygame.draw.line(surface, top_left, (x, y), (x + w - 2, y))
    pygame.draw.line(surface, top_left, (x, y), (x, y + h - 2))
    pygame.draw.line(surface, bottom_right, (x + w - 1, y + 1), (x + w - 1, y + h - 1))
    pygame.draw.line(surface, bottom_right, (x + 1, y + h - 1), (x + w - 1, y + h - 1))


def bevel_rect(surface: pygame.Surface, rect: tuple[int, int, int, int], *, raised: bool = True) -> None:
    """A simple 1px bevel: white top/left + grey bottom/right for raised,
    swapped for sunken. Filled with PANEL first."""
    pygame.draw.rect(surface, PANEL, rect)
    tl, br = (WHITE, BEZEL_DARK) if raised else (BEZEL_DARK, WHITE)
    _rect_outline(surface, rect, tl, br)


def black_ring(surface: pygame.Surface, rect: tuple[int, int, int, int]) -> None:
    """A plain 1px black outline, mitered the same way `bevel_rect` is --
    all four corners left unset, not closed."""
    x, y, w, h = rect
    pygame.draw.line(surface, BLACK, (x + 1, y), (x + w - 2, y))
    pygame.draw.line(surface, BLACK, (x + 1, y + h - 1), (x + w - 2, y + h - 1))
    pygame.draw.line(surface, BLACK, (x, y + 1), (x, y + h - 2))
    pygame.draw.line(surface, BLACK, (x + w - 1, y + 1), (x + w - 1, y + h - 2))


# A 7x7 close-button glyph (o=white highlight, #=black, -=grey shadow),
# the same beveled-icon convention CD Player's own button icons use
# (`cd_player.py`'s _ICON_ROWS) -- new content, no source to match, but
# built in that established visual language rather than inventing a
# different one.
_CLOSE_X_ROWS = (
    "o.....#",
    ".o...#.",
    "..o.#..",
    "...#...",
    "..#.o..",
    ".#...o.",
    "#.....o",
)
_CLOSE_X_COLOUR = {"o": WHITE, "#": BLACK}


def _draw_close_glyph(surface: pygame.Surface, x0: int, y0: int) -> None:
    for dy, row in enumerate(_CLOSE_X_ROWS):
        for dx, ch in enumerate(row):
            if ch != ".":
                surface.set_at((x0 + dx, y0 + dy), _CLOSE_X_COLOUR[ch])


def render_window_chrome(content: pygame.Surface, title: str) -> tuple[pygame.Surface, dict[str, pygame.Rect]]:
    """Wrap `content` in a generic draggable/closable window: a black ring
    + raised bevel border (WINDOW1.png's Dialog archetype -- no corner
    boxes, no status bar, no resize grip; see `bruces_windows.py`'s module
    docstring for why that's the right weight for an arbitrary demo's
    window) around a sunken-bevel cyan title bar, plus a close button
    grafted onto the title bar's right end (the source's own Dialog has no
    close control at all -- new, not measured).

    Returns the composed surface and a dict of rects in that surface's own
    local coordinates -- `"title_bar"` (drag hit-test), `"close_button"`
    (click hit-test), and `"content"` (where `content` itself landed, for
    translating an event's position into the wrapped demo's own native
    space) -- for the caller to translate into screen space by adding
    wherever the window itself is positioned.
    """
    title_cells, title_width = text_cells(title.upper())
    title_bar_h = GLYPH_H + 2 * TITLE_TEXT_PADDING
    title_bar_bevel_h = title_bar_h + 2
    inner_w = max(content.get_width(), title_width + CLOSE_BUTTON_SIZE + 3 * MARGIN)

    width = inner_w + 2 * (BORDER + MARGIN)
    top_chrome_h = BORDER + MARGIN + title_bar_bevel_h + MARGIN
    height = top_chrome_h + content.get_height() + BORDER + MARGIN

    surf = pygame.Surface((width, height))
    surf.fill(PANEL)

    outline_rect = (0, 0, width, height)
    border_rect = (1, 1, width - 2, height - 2)
    bevel_rect(surf, border_rect)
    black_ring(surf, outline_rect)

    title_bevel_rect = (BORDER, BORDER, width - 2 * BORDER, title_bar_bevel_h)
    bevel_rect(surf, title_bevel_rect, raised=False)
    title_fill_rect = pygame.Rect(BORDER + 1, BORDER + 1, width - 2 * BORDER - 2, title_bar_bevel_h - 2)
    surf.fill(TITLE_CYAN, title_fill_rect)
    for x, y in title_cells:
        surf.set_at((title_fill_rect.x + MARGIN + x, title_fill_rect.y + TITLE_TEXT_PADDING + y), BLACK)

    close_rect = pygame.Rect(
        title_fill_rect.right - MARGIN - CLOSE_BUTTON_SIZE,
        title_fill_rect.y + (title_fill_rect.height - CLOSE_BUTTON_SIZE) // 2,
        CLOSE_BUTTON_SIZE,
        CLOSE_BUTTON_SIZE,
    )
    bevel_rect(surf, close_rect)
    _draw_close_glyph(surf, close_rect.x + 2, close_rect.y + 2)

    content_pos = (BORDER + MARGIN, top_chrome_h)
    surf.blit(content, content_pos)

    return surf, {
        "title_bar": pygame.Rect(*title_bevel_rect),
        "close_button": close_rect,
        "content": pygame.Rect(content_pos, content.get_size()),
    }
