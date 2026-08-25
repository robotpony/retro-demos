"""Tests for framework/window_chrome.py -- the generic draggable/closable
window wrapper the desktop shell (PLAN.md's "Future: the unified desktop")
uses to open any demo as its own window. bevel_rect/black_ring themselves
were extracted from bruces_windows.py, already verified byte-exact there
(tests/test_bruces_windows.py); this file covers render_window_chrome's
own composition and hit-test rects."""

from __future__ import annotations

import pygame

from retrodemos.framework.window_chrome import CLOSE_BUTTON_SIZE, PANEL, render_window_chrome


def _content(w=40, h=20, colour=(255, 0, 0)):
    surf = pygame.Surface((w, h))
    surf.fill(colour)
    return surf


def test_window_is_bigger_than_its_content_on_every_side():
    content = _content(40, 20)
    win, _ = render_window_chrome(content, "TEST")
    assert win.get_width() > content.get_width()
    assert win.get_height() > content.get_height()


def test_content_is_blitted_into_the_composed_window_unmodified():
    content = _content(40, 20, colour=(255, 0, 0))
    win, _ = render_window_chrome(content, "TEST")
    # scan for the content's own colour somewhere in the composed window
    found = any(
        win.get_at((x, y))[:3] == (255, 0, 0)
        for x in range(win.get_width())
        for y in range(win.get_height())
    )
    assert found


def test_returns_title_bar_close_button_and_content_rects():
    content = _content()
    _, rects = render_window_chrome(content, "TEST")
    for key in ("title_bar", "close_button", "content"):
        assert key in rects
        assert isinstance(rects[key], pygame.Rect)


def test_content_rect_matches_the_content_surfaces_own_size_and_position():
    content = _content(40, 20)
    win, rects = render_window_chrome(content, "TEST")
    assert rects["content"].size == (40, 20)
    sub = win.subsurface(rects["content"])
    assert sub.get_at((0, 0))[:3] == (255, 0, 0)
    assert sub.get_at((39, 19))[:3] == (255, 0, 0)


def test_close_button_sits_within_the_title_bar_and_is_the_expected_size():
    content = _content()
    _, rects = render_window_chrome(content, "TEST")
    assert rects["close_button"].width == CLOSE_BUTTON_SIZE
    assert rects["close_button"].height == CLOSE_BUTTON_SIZE
    assert rects["title_bar"].contains(rects["close_button"])


def test_widens_to_fit_a_long_title_even_with_narrow_content():
    narrow = _content(10, 10)
    win_short, _ = render_window_chrome(narrow, "A")
    win_long, _ = render_window_chrome(narrow, "A VERY LONG DEMO NAME")
    assert win_long.get_width() > win_short.get_width()


def test_window_widens_to_fit_wide_content_too():
    narrow = _content(10, 10)
    wide = _content(300, 10)
    win_narrow, _ = render_window_chrome(narrow, "X")
    win_wide, _ = render_window_chrome(wide, "X")
    assert win_wide.get_width() > win_narrow.get_width()


def test_background_outside_content_is_panel_coloured():
    content = _content(20, 10, colour=(0, 255, 0))
    win, rects = render_window_chrome(content, "TEST")
    # a pixel just below the title bar, left margin, should be PANEL (or
    # border colours) -- not background bleed-through / a crash
    x, y = 0, win.get_height() - 1
    assert win.get_at((x, y))[:3] in (PANEL, (0, 0, 0), (255, 255, 255), (128, 128, 128))
