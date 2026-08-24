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


def test_snake_phase_grows_to_max_length_then_holds():
    display = DotMatrixDisplay(cols=COLS)
    phase = SnakePhase(display, random.Random(0))
    max_len_seen = 0
    finished = False
    for _ in range(1000):
        if phase.update(0.05):
            finished = True
            break
        max_len_seen = max(max_len_seen, len(phase._snake.body))
    assert finished
    assert max_len_seen == phase.MAX_LENGTH
    assert len(phase._snake.body) == phase.MAX_LENGTH


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
