"""Tests for the LED II demo and its script phases. led_grid.py's
DotMatrixDisplay/scroll_window/dot_grid_adjacency are covered separately in
tests/test_led_grid_dot_matrix.py; this file covers led_ii.py and
led_ii_phases.py, mirroring test_led.py's structure."""

from __future__ import annotations

import random

import pygame

from retrodemos.demos.led_ii import COLS, LedIIDemo
from retrodemos.demos.led_ii_phases import MarqueePhase, PowerUpPhase, RipplePhase, SnakePhase, WordsPhase
from retrodemos.framework.led_grid import DotMatrixDisplay


def test_led_ii_demo_native_size_matches_its_display():
    demo = LedIIDemo()
    assert demo.NATIVE_SIZE == (demo.display.width, demo.display.height)


def test_led_ii_demo_runs_through_every_phase_without_raising():
    demo = LedIIDemo()
    surface = pygame.Surface(demo.NATIVE_SIZE)
    seen_phase_indices = {demo._sequence.index}
    # enough ticks to cycle through all 5 phases at least once
    for _ in range(6000):
        demo.update(0.05)
        demo.draw(surface)
        seen_phase_indices.add(demo._sequence.index)
    assert seen_phase_indices == set(range(len(demo._sequence.phases)))


def test_led_ii_demo_reset_returns_to_phase_zero():
    demo = LedIIDemo()
    for _ in range(50):
        demo.update(0.05)
    demo.reset()
    assert demo._sequence.index == 0


def test_marquee_phase_text_override():
    display = DotMatrixDisplay(cols=COLS)
    phase = MarqueePhase(display, random.Random(0), text="42")
    assert phase.text == "42"


def test_marquee_phase_finishes_after_its_laps():
    display = DotMatrixDisplay(cols=COLS)
    phase = MarqueePhase(display, random.Random(0))
    finished = False
    for _ in range(5000):
        if phase.update(0.05):
            finished = True
            break
    assert finished


def test_powerup_phase_progresses_through_its_stages():
    display = DotMatrixDisplay(cols=COLS)
    phase = PowerUpPhase(display, random.Random(0))
    assert phase._stage == "flicker"
    stages_seen = {"flicker"}
    finished = False
    for _ in range(500):
        if phase.update(0.05):
            finished = True
            break
        stages_seen.add(phase._stage)
    assert finished
    assert stages_seen == {"flicker", "sweep", "blank"}


def test_snake_phase_spawns_a_quarter_width_apart():
    display = DotMatrixDisplay(cols=COLS)
    phase = SnakePhase(display, random.Random(0))
    pair = phase._match.round
    left_col, right_col = pair.a.body[0][0], pair.b.body[0][0]
    assert left_col < display.cols // 4
    assert right_col >= 3 * display.cols // 4


def test_snake_phase_resolves_with_a_winner_and_finishes_after_flashing():
    display = DotMatrixDisplay(cols=COLS)
    phase = SnakePhase(display, random.Random(0))
    resolved_at = None
    finished = False
    for i in range(20000):
        if phase.update(0.05):
            finished = True
            break
        if resolved_at is None and phase._match.round.resolved:
            resolved_at = i
    assert finished
    assert resolved_at is not None


def test_snake_phase_grows_bodies_up_to_max_length():
    display = DotMatrixDisplay(cols=COLS)
    phase = SnakePhase(display, random.Random(0))
    max_len_seen = 0
    for _ in range(20000):
        if phase.update(0.05):
            break
        pair = phase._match.round
        max_len_seen = max(max_len_seen, len(pair.a.body), len(pair.b.body))
    assert max_len_seen == phase.MAX_LENGTH


def test_snake_phase_is_a_best_of_n_match_scored_on_each_snakes_own_side():
    # 2026-08-26 playtesting: "restart until one snake scores 3 (score
    # tracked as dots on each snake's own starting side)".
    display = DotMatrixDisplay(cols=COLS)
    phase = SnakePhase(display, random.Random(0))
    rounds_seen = 1
    last_round = phase._match.round
    finished = False
    for _ in range(20000):
        if phase.update(0.05):
            finished = True
            break
        if phase._match.round is not last_round:
            rounds_seen += 1
            last_round = phase._match.round
    assert finished
    assert phase._match.finished
    assert phase._match.score[phase._match.match_winner] == phase.WINS_NEEDED
    assert rounds_seen >= phase.WINS_NEEDED
    # score dots land on the left column for side 0, right column for side 1
    score_cells = phase._score_cells()
    left_col, right_col = 0, display.cols - 1
    assert all(col in (left_col, right_col) for col, _row in score_cells)


def test_ripple_phase_launches_a_rocket_before_the_burst_ignites():
    display = DotMatrixDisplay(cols=COLS)
    phase = RipplePhase(display, random.Random(0))
    assert phase._burst is None  # starts mid-launch, not already exploding
    launch_col = phase._rocket.target[0]
    assert phase._rocket.start == (launch_col, display.ROWS - 1)
    for _ in range(50):
        phase.update(0.05)
        if phase._burst is not None:
            break
    assert phase._burst is not None


def test_ripple_phase_repeats_and_finishes():
    display = DotMatrixDisplay(cols=COLS)
    phase = RipplePhase(display, random.Random(0))
    finished = False
    for _ in range(2000):
        if phase.update(0.05):
            finished = True
            break
    assert finished


def test_words_phase_shows_centered_text():
    display = DotMatrixDisplay(cols=COLS)
    phase = WordsPhase(display, random.Random(0))
    assert phase.TEXT in phase._text
    assert len(phase._text) == display.char_count
