"""Tests for the Bruce's Windows demo: a plain static render of
WINDOW1.png, with "Got it" closing the dialog. Dragging and window-within-
a-window canvas logic moved to framework/window_chrome.py's generic
wrapper (see bruces_windows.py's module docstring) -- covered in
tests/test_window_chrome.py instead. runtime.py's mouse coordinate
rescaling is covered directly in tests/test_smoke.py.

Unlike the other LED-family renderers' tests, this file's reconstruct-and-
diff check runs live against images/WINDOW1.png rather than being noted as
"done interactively" -- the image is tracked in the repo and the path
resolves fine from the project root pytest is always run from (see
CLAUDE.md's Commands section), so there's no reason not to guard the
byte-exact match (achieved 2026-08-25, after a review found the first
build's bevel geometry had real bugs, not just imprecision) with a real
test."""

from __future__ import annotations

import pygame

from retrodemos.demos.bruces_windows import (
    BUTTON_OUTER_BEVEL_RECT,
    GOT_IT_ROWS,
    STATUS_TEXT_ROWS,
    WINDOW_SIZE,
    WINDOW_TITLE_ROWS,
    BruceWindowsDemo,
    _render_window,
)


def test_native_size_is_the_window():
    demo = BruceWindowsDemo()
    assert demo.NATIVE_SIZE == WINDOW_SIZE


def test_dialog_starts_open():
    demo = BruceWindowsDemo()
    assert demo._dialog_open is True


def test_demo_runs_for_many_frames_without_raising():
    demo = BruceWindowsDemo()
    surface = pygame.Surface(demo.NATIVE_SIZE)
    for _ in range(100):
        demo.update(0.05)
        demo.draw(surface)


def test_clicking_got_it_closes_the_dialog():
    demo = BruceWindowsDemo()
    button = pygame.Rect(*BUTTON_OUTER_BEVEL_RECT)
    demo.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=button.center, button=1))
    assert demo._dialog_open is False


def test_got_it_does_nothing_once_the_dialog_is_already_closed():
    demo = BruceWindowsDemo()
    button = pygame.Rect(*BUTTON_OUTER_BEVEL_RECT)
    demo.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=button.center, button=1))
    assert demo._dialog_open is False
    # clicking the same spot again (now empty window body, dialog gone)
    # must not raise or reopen the dialog
    demo.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=button.center, button=1))
    assert demo._dialog_open is False


def test_clicking_outside_the_button_does_nothing():
    demo = BruceWindowsDemo()
    demo.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(5, 5), button=1))
    assert demo._dialog_open is True


def test_reset_reopens_the_dialog():
    demo = BruceWindowsDemo()
    button = pygame.Rect(*BUTTON_OUTER_BEVEL_RECT)
    demo.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=button.center, button=1))
    assert demo._dialog_open is False
    demo.reset()
    assert demo._dialog_open is True


def test_window_title_glyph_reads_as_actual_letters_not_noise():
    # Sanity check the text-glyph tables are real pixel data, same
    # "verify programmatically" bar the LED-family fonts got: every row
    # must be the same width (a ragged table would mean a copy/paste slip)
    # and at least one row must have more than a couple of lit pixels.
    widths = {len(row) for row in WINDOW_TITLE_ROWS}
    assert len(widths) == 1
    assert any(row.count("#") > 5 for row in WINDOW_TITLE_ROWS)


def test_got_it_and_status_text_glyphs_are_rectangular_tables():
    for rows in (GOT_IT_ROWS, STATUS_TEXT_ROWS):
        widths = {len(row) for row in rows}
        assert len(widths) == 1


def test_render_window_is_byte_exact_against_the_source_image():
    src = pygame.image.load("images/WINDOW1.png")  # no convert_alpha needed, just reading pixels
    mine = _render_window(dialog_open=True)
    w, h = src.get_size()
    assert mine.get_size() == (w, h)
    mismatches = [
        (x, y)
        for y in range(h)
        for x in range(w)
        if src.get_at((x, y))[:3] != mine.get_at((x, y))[:3]
    ]
    assert mismatches == []
