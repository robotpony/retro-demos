"""Tests for the LED demo, its script phases, and the shared seven-segment
renderer they're built on."""

from __future__ import annotations

import random

import pygame

from retrodemos.demos.led import DIGIT_COUNT, LedDemo
from retrodemos.demos.led_phases import (
    ExplosionPhase,
    NumbersPhase,
    PowerUpPhase,
    SnakePhase,
    WordsPhase,
)
from retrodemos.framework.led_grid import RING_ORDER, SEGMENTS, SevenSegmentDisplay, segment_adjacency


def test_segments_dont_overlap():
    # A pixel claimed by two segments was exactly what caused the stray/extra
    # dot bugs Bruce caught during design; keep this from silently coming back.
    seen: dict[tuple[int, int], str] = {}
    for name, pixels in SEGMENTS.items():
        for p in pixels:
            assert p not in seen, f"pixel {p} claimed by both {seen.get(p)} and {name}"
            seen[p] = name


def test_ring_order_is_the_six_outer_segments_only():
    assert set(RING_ORDER) == set(SEGMENTS) - {"g"}
    assert len(RING_ORDER) == 6


def test_display_renders_at_declared_size():
    display = SevenSegmentDisplay(DIGIT_COUNT)
    surface = pygame.Surface((display.width, display.height))
    display.render(surface, "01234567")  # should not raise


def test_display_pads_short_text_and_truncates_long_text():
    display = SevenSegmentDisplay(4)
    surface = pygame.Surface((display.width, display.height))
    display.render(surface, "1")  # shorter than digit_count
    display.render(surface, "123456")  # longer than digit_count


def test_unknown_character_renders_as_blank_digit_not_a_crash():
    display = SevenSegmentDisplay(4)
    surface = pygame.Surface((display.width, display.height))
    display.render(surface, "1?2 ")


def test_all_ten_digits_render_without_raising():
    display = SevenSegmentDisplay(10)
    surface = pygame.Surface((display.width, display.height))
    display.render(surface, "0123456789")


def test_render_raw_lights_only_the_requested_segments():
    display = SevenSegmentDisplay(2)
    surface = pygame.Surface((display.width, display.height))
    display.render_raw(surface, {0: {"a"}}, lit_dots={1})
    # digit 0's segment "a" was requested -- should be lit
    ax, ay = next(iter(SEGMENTS["a"]))
    origin0 = display.border + display.margin
    assert surface.get_at((origin0 + ax, display.border + ay))[:3] == (255, 0, 0)
    # digit 1's segment "a" was not requested -- should stay dim
    origin1 = origin0 + 17  # CELL_W
    assert surface.get_at((origin1 + ax, display.border + ay))[:3] == (64, 0, 0)


def test_segment_adjacency_is_symmetric_and_connects_across_digits():
    graph = segment_adjacency(3)
    for node, neighbours in graph.items():
        for n in neighbours:
            assert node in graph[n], f"{node} -> {n} not symmetric"
    # digit 0's "b" (right side) should connect to digit 1's "f" (left side)
    assert (1, "f") in graph[(0, "b")]


def test_led_demo_native_size_matches_its_display():
    demo = LedDemo()
    assert demo.NATIVE_SIZE == (demo.display.width, demo.display.height)


def test_led_demo_runs_through_every_phase_without_raising():
    demo = LedDemo()
    surface = pygame.Surface(demo.NATIVE_SIZE)
    seen_phase_indices = {demo._sequence.index}
    # enough ticks to cycle through all 5 phases at least once
    for _ in range(4000):
        demo.update(0.05)
        demo.draw(surface)
        seen_phase_indices.add(demo._sequence.index)
    assert seen_phase_indices == set(range(len(demo._sequence.phases)))


def test_led_demo_reset_returns_to_phase_zero():
    demo = LedDemo()
    for _ in range(50):
        demo.update(0.05)
    demo.reset()
    assert demo._sequence.index == 0


def test_numbers_phase_text_override():
    display = SevenSegmentDisplay(DIGIT_COUNT)
    phase = NumbersPhase(display, random.Random(0), text="42")
    assert phase.text == "42"


def test_numbers_phase_finishes_after_its_laps():
    display = SevenSegmentDisplay(DIGIT_COUNT)
    phase = NumbersPhase(display, random.Random(0))
    finished = False
    for _ in range(2000):
        if phase.update(0.05):
            finished = True
            break
    assert finished


def test_powerup_phase_progresses_through_its_stages():
    display = SevenSegmentDisplay(DIGIT_COUNT)
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
    display = SevenSegmentDisplay(DIGIT_COUNT)
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


def test_explosion_phase_repeats_and_finishes():
    display = SevenSegmentDisplay(DIGIT_COUNT)
    phase = ExplosionPhase(display, random.Random(0))
    finished = False
    for _ in range(2000):
        if phase.update(0.05):
            finished = True
            break
    assert finished


def test_words_phase_shows_centered_text():
    display = SevenSegmentDisplay(DIGIT_COUNT)
    phase = WordsPhase(display, random.Random(0))
    assert phase.TEXT in phase._text
    assert len(phase._text) == DIGIT_COUNT
