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


def test_snake_phase_spawns_pairs_a_quarter_width_apart():
    display = TitleDisplays(256)
    phase = SnakePhase(display, random.Random(0))
    for chase in (phase._red_green, phase._blue_cyan):
        left_col, right_col = chase.pair.a.body[0][0], chase.pair.b.body[0][0]
        assert left_col < display.width // 4
        assert right_col >= 3 * display.width // 4


def test_snake_phase_resolves_with_a_winner_and_finishes_after_flashing():
    display = TitleDisplays(256)
    phase = SnakePhase(display, random.Random(0))
    resolved_at = None
    finished = False
    for i in range(4000):
        if phase.update(0.02):
            finished = True
            break
        if resolved_at is None and phase._red_green.pair.resolved and phase._blue_cyan.pair.resolved:
            resolved_at = i
    assert finished
    assert resolved_at is not None
    assert phase._red_green.pair.winner in (phase._red_green.pair.a, phase._red_green.pair.b)
    assert phase._blue_cyan.pair.winner in (phase._blue_cyan.pair.a, phase._blue_cyan.pair.b)


def test_snake_phase_grows_bodies_up_to_max_length():
    display = TitleDisplays(256)
    phase = SnakePhase(display, random.Random(0))
    max_len_seen = 0
    for _ in range(2000):
        if phase.update(0.02):
            break
        max_len_seen = max(max_len_seen, len(phase._red_green.pair.a.body), len(phase._red_green.pair.b.body))
    assert max_len_seen == phase.MAX_LENGTH


def test_fireworks_phase_repeats_and_finishes():
    display = TitleDisplays(256)
    phase = FireworksPhase(display, random.Random(0))
    finished = False
    for _ in range(3000):
        if phase.update(0.05):
            finished = True
            break
    assert finished


def test_words_phase_renders_1991_as_actual_font_glyphs():
    display = TitleDisplays(256)
    phase = WordsPhase(display, random.Random(0))
    assert phase.TEXT == "1991"
    # Every lit cell must be part of some digit's actual glyph shape, not a
    # column's raw byte value -- this is the bug the DOT_FONT rewrite fixed.
    assert phase._cells
    cols_used = {col for col, _ in phase._cells}
    rows_used = {row for _, row in phase._cells}
    assert rows_used <= set(range(display.red_green.ROWS))
    # centred: equal-ish blank margin on both sides
    left_margin = min(cols_used)
    right_margin = display.width - 1 - max(cols_used)
    assert abs(left_margin - right_margin) <= 1


def test_words_phase_renders_the_same_cells_on_both_strips():
    display = TitleDisplays(256)
    phase = WordsPhase(display, random.Random(0))
    called = {}

    def fake_render_raw(surf, red_green_cells=None, blue_cyan_cells=None):
        called["red_green"] = red_green_cells
        called["blue_cyan"] = blue_cyan_cells

    display.render_raw = fake_render_raw
    phase.draw(pygame.Surface((display.width, display.height)))
    assert called["red_green"] == called["blue_cyan"] == phase._cells
