"""Tests for Tank Status Window: the chrome/dot-grid renderer
(tank_status_window_grid.py) and the three-phase scripted round
(tank_status_window_phases.py)."""

from __future__ import annotations

import random

import pygame

from retrodemos.demos.tank_status_window import TankStatusWindowDemo
from retrodemos.demos.tank_status_window_grid import (
    BUTTON_COUNT,
    MAIN_COLS,
    MAIN_ROWS,
    SEC_COLS,
    SEC_ROWS,
    WINDOW_H,
    WINDOW_W,
    TankDisplay,
    status_text_cells,
)
from retrodemos.demos.tank_status_window_phases import (
    ENGAGE_SHOT_COUNT,
    LANE_MAX_COL,
    LANE_MIN_COL,
    PATROL_DURATION,
    WALLS,
    EngagePhase,
    PatrolPhase,
    ResetPhase,
    _Tank,
)


def test_grid_dimensions_match_measured_source():
    # 83x84 main grid, 83x9 secondary strip, 11 buttons -- all measured
    # directly from images/WIN1.png (see tank_status_window_grid.py).
    assert (MAIN_COLS, MAIN_ROWS) == (83, 84)
    assert (SEC_COLS, SEC_ROWS) == (83, 9)
    assert BUTTON_COUNT == 11


def test_window_native_size_matches_source_image():
    assert (WINDOW_W, WINDOW_H) == (273, 350)


def test_walls_stay_within_the_main_grid():
    for col, row in WALLS:
        assert 0 <= col < MAIN_COLS
        assert 0 <= row < MAIN_ROWS


def test_display_draws_with_a_set_and_a_dict_of_cells():
    display = TankDisplay()
    surface = pygame.Surface((WINDOW_W, WINDOW_H))
    display.main_cells = {(1, 1), (2, 2)}
    display.secondary_cells = {(0, 0)}
    display.draw(surface)  # should not raise
    display.main_cells = {(1, 1): 0.5, (2, 2): 1.0}
    display.draw(surface)  # should not raise


def test_status_text_cells_stays_within_the_secondary_strip():
    for word in ("PATROL", "ENGAGE", "RESET"):
        cells = status_text_cells(word)
        assert cells, f"{word!r} produced no lit cells"
        for col, row in cells:
            assert 0 <= col < SEC_COLS
            assert 0 <= row < SEC_ROWS


def test_tank_stays_within_its_lane_bounds():
    tank = _Tank(row=0, start_col=LANE_MIN_COL, direction=1)
    seen_cols = set()
    for _ in range(500):
        tank.step()
        seen_cols.add(tank.col)
    assert min(seen_cols) >= LANE_MIN_COL
    assert max(seen_cols) <= LANE_MAX_COL


def test_patrol_phase_finishes_after_its_duration():
    display = TankDisplay()
    phase = PatrolPhase(display, random.Random(0))
    finished = False
    elapsed = 0.0
    while elapsed < PATROL_DURATION + 1.0:
        finished = phase.update(0.05)
        elapsed += 0.05
        if finished:
            break
    assert finished


def test_engage_phase_fires_all_its_shots_and_finishes():
    display = TankDisplay()
    phase = EngagePhase(display, random.Random(0))
    finished = False
    for _ in range(2000):
        finished = phase.update(0.02)
        if finished:
            break
    assert finished
    assert phase._shots_fired == ENGAGE_SHOT_COUNT
    assert not phase._bullets
    assert not phase._bursts


def test_reset_phase_burst_burns_out_and_phase_finishes():
    display = TankDisplay()
    phase = ResetPhase(display, random.Random(0))
    finished = False
    for _ in range(2000):
        finished = phase.update(0.02)
        if finished:
            break
    assert finished
    assert phase._burst.burned_out


def test_demo_native_size_matches_grid_module():
    demo = TankStatusWindowDemo()
    assert demo.NATIVE_SIZE == (WINDOW_W, WINDOW_H)


def test_demo_loops_through_all_three_phases_across_many_frames():
    demo = TankStatusWindowDemo()
    surface = pygame.Surface(demo.NATIVE_SIZE)
    seen_phases = set()
    for _ in range(4000):
        demo.update(0.02)
        demo.draw(surface)
        seen_phases.add(type(demo._sequence.current).__name__)
    assert seen_phases == {"PatrolPhase", "EngagePhase", "ResetPhase"}


def test_demo_reset_restarts_the_sequence():
    demo = TankStatusWindowDemo()
    surface = pygame.Surface(demo.NATIVE_SIZE)
    for _ in range(200):
        demo.update(0.02)
        demo.draw(surface)
    demo.reset()
    assert demo._sequence.index == 0
    assert isinstance(demo._sequence.current, PatrolPhase)
