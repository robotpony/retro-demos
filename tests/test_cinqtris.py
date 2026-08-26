"""Tests for the Cinqtris demo: the wordmark colour cycle, the equalizer
cascade, and the click-triggered MADMAX slide. No shared framework
renderer is involved (see cinqtris.py's module docstring) -- everything
here covers cinqtris.py directly."""

from __future__ import annotations

import pygame

from retrodemos.demos.cinqtris import (
    CONTENT_W,
    EQ_FRAMES,
    EQ_W,
    MM_TOTAL_W,
    WIDTH,
    WORD_BAND_COLORS,
    CinqtrisDemo,
)


def _click(demo: CinqtrisDemo, pos: tuple[int, int] = (10, 10)) -> None:
    demo.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1))


def test_wordmark_and_equalizer_share_the_same_native_width():
    # The two are meant to line up exactly -- both 128 native px, per
    # CT_ANI.png itself (see module docstring).
    assert CONTENT_W == EQ_W


def test_demo_native_size_is_stable():
    demo = CinqtrisDemo()
    assert demo.NATIVE_SIZE == (WIDTH, demo.NATIVE_SIZE[1])


def test_demo_runs_for_many_frames_without_raising():
    demo = CinqtrisDemo()
    surface = pygame.Surface(demo.NATIVE_SIZE)
    for i in range(500):
        if i == 100:
            _click(demo)  # exercise the slide mid-run too
        demo.update(0.05)
        demo.draw(surface)


def test_reset_starts_with_madmax_hidden_off_screen():
    demo = CinqtrisDemo()
    assert demo._mm_sliding is False
    assert demo._mm_x == -MM_TOTAL_W


def test_clicking_triggers_the_slide():
    demo = CinqtrisDemo()
    _click(demo)
    assert demo._mm_sliding is True


def test_clicking_again_mid_slide_does_not_restart_it():
    demo = CinqtrisDemo()
    _click(demo)
    demo.update(1.0)
    x_after_one_second = demo._mm_x
    _click(demo)  # should be a no-op -- already sliding
    assert demo._mm_x == x_after_one_second


def test_slide_completes_and_hides_again():
    demo = CinqtrisDemo()
    _click(demo)
    for _ in range(1000):
        demo.update(0.05)
        if not demo._mm_sliding:
            break
    assert demo._mm_sliding is False


def test_wordmark_frame_cycles_through_all_3_colour_frames():
    demo = CinqtrisDemo()
    seen = {demo._word_frame}
    for _ in range(200):
        demo.update(0.05)
        seen.add(demo._word_frame)
    assert seen == set(range(len(WORD_BAND_COLORS)))


def test_equalizer_phase_cycles_through_all_14_frames():
    demo = CinqtrisDemo()
    seen = {demo._eq_phase}
    for _ in range(200):
        demo.update(0.05)
        seen.add(demo._eq_phase)
    assert seen == set(range(len(EQ_FRAMES)))
