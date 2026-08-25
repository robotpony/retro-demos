"""Tests for the CD Player demo. No shared framework renderer is involved
(see cd_player.py's module docstring for why its chrome is custom-drawn,
not extracted) -- this file covers cd_player.py directly: the digit font,
the readout/track/pause simulation, and the continuous update/draw loop."""

from __future__ import annotations

import pygame

from retrodemos.demos.cd_player import (
    CELL_H,
    CELL_W,
    PAUSE_DURATION,
    PAUSE_EVERY,
    SEG_OFF,
    SEG_ON,
    TRACK_COUNT,
    TRACK_LENGTH,
    CDPlayerDemo,
    _draw_digit,
)


def _render_text(text: str) -> pygame.Surface:
    surf = pygame.Surface((CELL_W * len(text), CELL_H))
    surf.fill((0, 0, 0))
    for i, ch in enumerate(text):
        _draw_digit(surf, i * CELL_W, 0, ch, SEG_ON, SEG_OFF)
    return surf


def _lit_cols(surf: pygame.Surface, y: int) -> str:
    return "".join("#" if surf.get_at((x, y))[:3] == SEG_ON else "." for x in range(surf.get_width()))


def test_digit_font_renders_one_as_just_the_right_hand_bars():
    surf = _render_text("1")
    # top/bottom bars (rows 0, 19) and the middle bar (row 9) should be unlit
    assert "#" not in _lit_cols(surf, 0)
    assert "#" not in _lit_cols(surf, 9)
    assert "#" not in _lit_cols(surf, 19)
    # the right-hand vertical (segments b/c) should be lit somewhere in the body
    assert "#" in _lit_cols(surf, 5)


def test_digit_font_renders_zero_with_no_middle_bar():
    surf = _render_text("0")
    assert "#" not in _lit_cols(surf, 9)  # middle bar (g) unlit
    assert "#" in _lit_cols(surf, 0)  # top bar (a) lit
    assert "#" in _lit_cols(surf, 19)  # bottom bar (d) lit


def test_digit_font_six_and_nine_keep_the_sources_own_quirks():
    # Measured from CDPLAYER.png directly: this font's "6" has no top bar,
    # and "9" has no bottom bar -- not "corrected" to a textbook 7-segment
    # shape. See cd_player.py's DIGIT_SEGMENTS.
    six = _render_text("6")
    assert "#" not in _lit_cols(six, 0)  # top bar (a) unlit
    assert "#" in _lit_cols(six, 19)  # bottom bar (d) lit
    nine = _render_text("9")
    assert "#" in _lit_cols(nine, 0)  # top bar (a) lit
    assert "#" not in _lit_cols(nine, 19)  # bottom bar (d) unlit


def test_space_renders_nothing_lit():
    surf = _render_text(" ")
    for y in range(CELL_H):
        assert "#" not in _lit_cols(surf, y)


def test_demo_native_size_is_stable():
    demo = CDPlayerDemo()
    assert demo.NATIVE_SIZE == (340, 90)


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
    assert demo._track == 1
    assert demo._elapsed == 0.0
    assert not demo._paused


def test_track_advances_and_wraps_after_track_count():
    demo = CDPlayerDemo()
    # Fast-forward well past one full cycle of every track. Periodic pauses
    # eat into wall time without advancing track time (see update()), so
    # the budget has to cover that downtime too, not just TRACK_LENGTH *
    # TRACK_COUNT worth of dt.
    seen_tracks = {demo._track}
    total = 0.0
    budget = TRACK_LENGTH * TRACK_COUNT * 1.3
    while total < budget:
        demo.update(1.0)
        total += 1.0
        seen_tracks.add(demo._track)
    assert seen_tracks == set(range(1, TRACK_COUNT + 1))
    assert 1 <= demo._track <= TRACK_COUNT


def test_playback_pauses_periodically_then_resumes():
    demo = CDPlayerDemo()
    saw_paused = False
    saw_resumed_after_pause = False
    for _ in range(int((PAUSE_EVERY + PAUSE_DURATION + 5) / 0.1)):
        demo.update(0.1)
        if demo._paused:
            saw_paused = True
        elif saw_paused:
            saw_resumed_after_pause = True
    assert saw_paused
    assert saw_resumed_after_pause


def test_meter_levels_go_quiet_while_paused():
    demo = CDPlayerDemo()
    demo._paused = True
    demo._pause_elapsed = 0.0
    demo.update(0.5)
    assert all(level == 0.0 for level in demo._levels)


def test_active_button_reflects_play_pause_state():
    demo = CDPlayerDemo()
    demo._paused = False
    assert demo._active_button() == "play"
    demo._paused = True
    assert demo._active_button() == "pause"
