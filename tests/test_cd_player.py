"""Tests for the CD Player demo -- the digit font, the readout/track/pause
simulation, and the continuous update/draw loop. Its window frames route
through framework.window_chrome.bevel_rect (see cd_player.py's module
docstring), but its inner controls (readout, buttons) are still
custom-drawn, a different border style than that shared helper's."""

from __future__ import annotations

import pygame

from retrodemos.demos.cd_player import (
    CELL_H,
    CELL_W,
    EQ_START_POS,
    MAIN_START_POS,
    PAUSE_DURATION,
    PAUSE_EVERY,
    SEG_ON,
    TRACK_COUNT,
    TRACK_LENGTH,
    CDPlayerDemo,
    _draw_digit,
)


def _click(demo: CDPlayerDemo, pos: tuple[int, int]) -> None:
    demo.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1))
    demo.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=pos, button=1))


def _render_text(text: str) -> pygame.Surface:
    surf = pygame.Surface((CELL_W * len(text), CELL_H))
    surf.fill((0, 0, 0))
    for i, ch in enumerate(text):
        _draw_digit(surf, i * CELL_W, 0, ch, SEG_ON)
    return surf


def _lit_cols(surf: pygame.Surface, y: int) -> str:
    return "".join("#" if surf.get_at((x, y))[:3] == SEG_ON else "." for x in range(surf.get_width()))


def test_digit_font_renders_one_as_just_the_right_hand_bars():
    surf = _render_text("1")
    # top/bottom bars (rows 1, 20) and the middle bar (row 10) should be unlit
    assert "#" not in _lit_cols(surf, 1)
    assert "#" not in _lit_cols(surf, 10)
    assert "#" not in _lit_cols(surf, 20)
    # the right-hand vertical (segments b/c) should be lit somewhere in the body
    assert "#" in _lit_cols(surf, 5)


def test_digit_font_renders_zero_with_no_middle_bar():
    surf = _render_text("0")
    assert "#" not in _lit_cols(surf, 10)  # middle bar (g) unlit
    assert "#" in _lit_cols(surf, 1)  # top bar (a) lit
    assert "#" in _lit_cols(surf, 20)  # bottom bar (d) lit


def test_digit_font_uses_the_standard_closed_six_and_nine():
    # No source data exists for individual digit shapes (see cd_player.py's
    # module docstring), so this is the conventional closed-6/closed-9
    # form, not measured content -- 6 has a top bar, 9 has a bottom bar.
    six = _render_text("6")
    assert "#" in _lit_cols(six, 1)  # top bar (a) lit
    assert "#" in _lit_cols(six, 20)  # bottom bar (d) lit
    nine = _render_text("9")
    assert "#" in _lit_cols(nine, 1)  # top bar (a) lit
    assert "#" in _lit_cols(nine, 20)  # bottom bar (d) lit


def test_space_renders_nothing_lit():
    surf = _render_text(" ")
    for y in range(CELL_H):
        assert "#" not in _lit_cols(surf, y)


def test_demo_native_size_is_stable():
    demo = CDPlayerDemo()
    assert demo.NATIVE_SIZE == (480, 180)


def test_demo_runs_for_many_frames_without_raising():
    demo = CDPlayerDemo()
    surface = pygame.Surface(demo.NATIVE_SIZE)
    for _ in range(500):
        demo.update(0.05)
        demo.draw(surface)


def test_reset_returns_to_track_one_at_zero_elapsed():
    demo = CDPlayerDemo()
    for _ in range(200):
        demo.update(0.5)
    demo.reset()
    assert demo.main._track == 1
    assert demo.main._elapsed == 0.0
    assert not demo.main._paused


def test_track_advances_and_wraps_after_track_count():
    demo = CDPlayerDemo()
    # Fast-forward well past one full cycle of every track. Periodic pauses
    # eat into wall time without advancing track time (see update()), so
    # the budget has to cover that downtime too, not just TRACK_LENGTH *
    # TRACK_COUNT worth of dt.
    seen_tracks = {demo.main._track}
    total = 0.0
    budget = TRACK_LENGTH * TRACK_COUNT * 1.3
    while total < budget:
        demo.update(1.0)
        total += 1.0
        seen_tracks.add(demo.main._track)
    assert seen_tracks == set(range(1, TRACK_COUNT + 1))
    assert 1 <= demo.main._track <= TRACK_COUNT


def test_playback_pauses_periodically_then_resumes():
    demo = CDPlayerDemo()
    saw_paused = False
    saw_resumed_after_pause = False
    for _ in range(int((PAUSE_EVERY + PAUSE_DURATION + 5) / 0.1)):
        demo.update(0.1)
        if demo.main._paused:
            saw_paused = True
        elif saw_paused:
            saw_resumed_after_pause = True
    assert saw_paused
    assert saw_resumed_after_pause


def test_meter_levels_go_quiet_while_paused():
    demo = CDPlayerDemo()
    demo.main._paused = True
    demo.main._pause_elapsed = 0.0
    demo.update(0.5)
    assert all(level == 0.0 for level in demo.main._levels)


def test_active_button_reflects_play_pause_state():
    demo = CDPlayerDemo()
    demo.main._paused = False
    assert demo.main._active_button() == "play"
    demo.main._paused = True
    assert demo.main._active_button() == "pause"


def test_windows_start_docked_with_the_equalizer_hidden():
    demo = CDPlayerDemo()
    assert demo._win_pos["main"] == list(MAIN_START_POS)
    assert demo._win_pos["eq"] == list(EQ_START_POS)
    # The equalizer is a genuinely separate window, hidden until revealed
    # by clicking the main window's body (2026-08-25 playtesting).
    assert demo._order == ["main"]


def _main_body_pos(demo: CDPlayerDemo) -> tuple[int, int]:
    """A point inside the main window that isn't its close button or any
    transport button -- deep in the readout box, well clear of both."""
    wx, wy = demo._win_pos["main"]
    return (wx + 100, wy + 15)


def test_clicking_the_main_windows_body_reveals_the_equalizer():
    demo = CDPlayerDemo()
    assert "eq" not in demo._order
    _click(demo, _main_body_pos(demo))
    assert demo._order == ["main", "eq"]


def test_clicking_the_main_windows_body_starts_a_drag_too():
    demo = CDPlayerDemo()
    start = demo._win_pos["main"][:]
    grab = _main_body_pos(demo)
    demo.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=grab, button=1))
    demo.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=(grab[0] + 20, grab[1] + 10), rel=(20, 10), buttons=(1, 0, 0)))
    assert demo._win_pos["main"] == [start[0] + 20, start[1] + 10]
    demo.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=(grab[0] + 20, grab[1] + 10), button=1))
    # motion after release shouldn't keep dragging
    demo.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=(grab[0] + 99, grab[1] + 99), rel=(79, 89), buttons=(0, 0, 0)))
    assert demo._win_pos["main"] == [start[0] + 20, start[1] + 10]


def test_clicking_a_transport_button_presses_it_without_dragging_or_revealing():
    demo = CDPlayerDemo()
    wx, wy = demo._win_pos["main"]
    stop_rect = demo.main.button_rects["stop"]
    pos = (wx + stop_rect.centerx, wy + stop_rect.centery)
    demo.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1))
    assert demo.main._pressed == "stop"
    assert demo._dragging is None
    assert "eq" not in demo._order
    demo.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=pos, button=1))
    assert demo.main._pressed is None


def test_clicking_the_main_windows_close_button_closes_it():
    demo = CDPlayerDemo()
    wx, wy = demo._win_pos["main"]
    close = demo.main.close_rect
    _click(demo, (wx + close.centerx, wy + close.centery))
    assert demo._order == []


def test_clicking_the_equalizers_close_button_closes_only_the_equalizer():
    demo = CDPlayerDemo()
    _click(demo, _main_body_pos(demo))  # reveal it first
    assert demo._order == ["main", "eq"]
    wx, wy = demo._win_pos["eq"]
    close = demo.eq.close_rect
    _click(demo, (wx + close.centerx, wy + close.centery))
    assert demo._order == ["main"]


def test_clicking_empty_background_does_not_change_focus_or_start_a_drag():
    demo = CDPlayerDemo()
    order_before = demo._order[:]
    _click(demo, (demo.NATIVE_SIZE[0] - 5, demo.NATIVE_SIZE[1] - 5))
    assert demo._order == order_before
    assert demo._dragging is None
