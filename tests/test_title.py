"""Tests for the Title demo and its script phases. led_grid.py's
BitColumnDisplay/dot_grid_adjacency are covered separately in
tests/test_led_grid_bit_column.py and tests/test_graph_walk.py; this file
covers title.py and title_phases.py, mirroring test_led_ii.py's structure."""

from __future__ import annotations

import random

import pygame

from retrodemos.demos.title import TitleDemo, TitleDisplays
from retrodemos.demos.title_phases import FireworksPhase, PowerUpPhase, ScrollPhase, SnakePhase, WordsPhase


def test_title_demo_native_size_matches_the_source_image():
    demo = TitleDemo()
    # images/TITLE.png's bit-pattern area is 256 wide; 15px per strip
    # (8 rows * 2px pitch - 1) with a 1px gap between the two strips.
    assert demo.NATIVE_SIZE == (256, 31)


def test_title_demo_runs_through_every_phase_without_raising():
    demo = TitleDemo()
    surface = pygame.Surface(demo.NATIVE_SIZE)
    seen_phase_indices = {demo._sequence.index}
    for _ in range(4000):
        demo.update(0.05)
        demo.draw(surface)
        seen_phase_indices.add(demo._sequence.index)
    assert seen_phase_indices == set(range(len(demo._sequence.phases)))


def test_title_demo_reset_returns_to_phase_zero():
    demo = TitleDemo()
    for _ in range(50):
        demo.update(0.05)
    demo.reset()
    assert demo._sequence.index == 0


def test_powerup_phase_progresses_through_its_stages():
    display = TitleDisplays(256)
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


def test_scroll_phase_starts_at_the_identity_ramp():
    display = TitleDisplays(256)
    phase = ScrollPhase(display, random.Random(0))
    assert phase._red_green_offset == 0
    assert phase._blue_cyan_offset == 0


def test_scroll_phase_finishes_after_its_duration():
    display = TitleDisplays(256)
    phase = ScrollPhase(display, random.Random(0))
    finished = False
    for _ in range(300):
        if phase.update(0.05):
            finished = True
            break
    assert finished


def test_snake_phase_grows_both_strips_to_max_length_then_holds():
    display = TitleDisplays(256)
    phase = SnakePhase(display, random.Random(0))
    max_len_seen = 0
    finished = False
    for _ in range(2000):
        if phase.update(0.05):
            finished = True
            break
        max_len_seen = max(max_len_seen, len(phase._red_green_snake.body))
    assert finished
    assert max_len_seen == phase.MAX_LENGTH
    assert len(phase._red_green_snake.body) == phase.MAX_LENGTH
    assert len(phase._blue_cyan_snake.body) == phase.MAX_LENGTH


def test_fireworks_phase_repeats_and_finishes():
    display = TitleDisplays(256)
    phase = FireworksPhase(display, random.Random(0))
    finished = False
    for _ in range(3000):
        if phase.update(0.05):
            finished = True
            break
    assert finished


def test_words_phase_encodes_1991_as_ascii_bytes_centred_on_blank():
    display = TitleDisplays(256)
    phase = WordsPhase(display, random.Random(0))
    assert phase.TEXT_BYTES == [ord("1"), ord("9"), ord("9"), ord("1")]
    non_zero = [i for i, v in enumerate(phase._values) if v != 0]
    assert [phase._values[i] for i in non_zero] == phase.TEXT_BYTES
    # centred: equal-ish blank margin on both sides
    left_margin = non_zero[0]
    right_margin = len(phase._values) - 1 - non_zero[-1]
    assert abs(left_margin - right_margin) <= 1
