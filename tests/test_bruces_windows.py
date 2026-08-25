"""Tests for the Bruce's Windows demo: the one interactive demo (title-bar
drag, "Got it" closes the dialog). Also exercises runtime.py's mouse
coordinate rescaling indirectly through the demo's own screen-rect
helpers; the rescaling itself is covered directly in tests/test_smoke.py."""

from __future__ import annotations

import pygame

from retrodemos.demos.bruces_windows import (
    CANVAS_SIZE,
    GOT_IT_ROWS,
    STATUS_TEXT_ROWS,
    WINDOW_SIZE,
    WINDOW_TITLE_ROWS,
    BruceWindowsDemo,
)


def test_native_size_is_the_canvas_not_the_window():
    demo = BruceWindowsDemo()
    assert demo.NATIVE_SIZE == CANVAS_SIZE
    assert CANVAS_SIZE[0] > WINDOW_SIZE[0]
    assert CANVAS_SIZE[1] > WINDOW_SIZE[1]


def test_window_starts_centred():
    demo = BruceWindowsDemo()
    assert demo._window_pos == [
        (CANVAS_SIZE[0] - WINDOW_SIZE[0]) // 2,
        (CANVAS_SIZE[1] - WINDOW_SIZE[1]) // 2,
    ]


def test_dialog_starts_open():
    demo = BruceWindowsDemo()
    assert demo._dialog_open is True


def test_demo_runs_for_many_frames_without_raising():
    demo = BruceWindowsDemo()
    surface = pygame.Surface(demo.NATIVE_SIZE)
    for _ in range(100):
        demo.update(0.05)
        demo.draw(surface)


def test_dragging_the_title_bar_moves_the_window():
    demo = BruceWindowsDemo()
    start = tuple(demo._window_pos)
    title_bar = demo._title_bar_screen_rect()
    demo.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=title_bar.center, button=1))
    demo.handle_event(
        pygame.event.Event(
            pygame.MOUSEMOTION, pos=(title_bar.center[0] + 15, title_bar.center[1] + 5), rel=(15, 5), buttons=(1, 0, 0)
        )
    )
    assert demo._window_pos == [start[0] + 15, start[1] + 5]


def test_releasing_the_mouse_stops_the_drag():
    demo = BruceWindowsDemo()
    title_bar = demo._title_bar_screen_rect()
    demo.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=title_bar.center, button=1))
    demo.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=title_bar.center, button=1))
    pos_after_release = list(demo._window_pos)
    demo.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=(999, 999), rel=(50, 50), buttons=(0, 0, 0)))
    assert demo._window_pos == pos_after_release


def test_clicking_outside_the_title_bar_does_not_start_a_drag():
    demo = BruceWindowsDemo()
    start = list(demo._window_pos)
    demo.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(demo._window_pos[0] + 5, demo._window_pos[1] + 100), button=1))
    demo.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=(500, 500), rel=(50, 50), buttons=(1, 0, 0)))
    assert demo._window_pos == start


def test_dragging_clamps_to_the_canvas_bounds():
    demo = BruceWindowsDemo()
    title_bar = demo._title_bar_screen_rect()
    demo.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=title_bar.center, button=1))
    demo.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=(-500, -500), rel=(-2000, -2000), buttons=(1, 0, 0)))
    assert demo._window_pos == [0, 0]
    demo.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=(5000, 5000), rel=(6000, 6000), buttons=(1, 0, 0)))
    max_x = CANVAS_SIZE[0] - WINDOW_SIZE[0]
    max_y = CANVAS_SIZE[1] - WINDOW_SIZE[1]
    assert demo._window_pos == [max_x, max_y]


def test_clicking_got_it_closes_the_dialog():
    demo = BruceWindowsDemo()
    button = demo._button_screen_rect()
    demo.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=button.center, button=1))
    assert demo._dialog_open is False


def test_got_it_does_nothing_once_the_dialog_is_already_closed():
    demo = BruceWindowsDemo()
    button = demo._button_screen_rect()
    demo.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=button.center, button=1))
    assert demo._dialog_open is False
    # clicking the same spot again (now empty window body, dialog gone)
    # must not raise or reopen the dialog
    demo.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=button.center, button=1))
    assert demo._dialog_open is False


def test_reset_reopens_the_dialog_and_recentres_the_window():
    demo = BruceWindowsDemo()
    title_bar = demo._title_bar_screen_rect()
    demo.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=title_bar.center, button=1))
    demo.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=(0, 0), rel=(-40, -10), buttons=(1, 0, 0)))
    demo.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=(0, 0), button=1))
    button = demo._button_screen_rect()
    demo.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=button.center, button=1))
    demo.reset()
    assert demo._dialog_open is True
    assert demo._window_pos == [
        (CANVAS_SIZE[0] - WINDOW_SIZE[0]) // 2,
        (CANVAS_SIZE[1] - WINDOW_SIZE[1]) // 2,
    ]
    assert demo._dragging is False


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
