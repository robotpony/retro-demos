"""Tests for Tank Status Window: the chrome/dot-grid renderer
(tank_status_window_grid.py) and the three-phase scripted round
(tank_status_window_phases.py)."""

from __future__ import annotations

import random

import pygame

from retrodemos.demos.tank_status_window import TankStatusWindowDemo
from retrodemos.demos.tank_status_window_grid import (
    BUTTON_COUNT,
    BUTTON_ROW_H,
    BUTTON_ROW_W,
    BUTTON_ROW_X0,
    BUTTON_ROW_Y0,
    MAIN_COLS,
    MAIN_ROWS,
    SEC_COLS,
    SEC_ROWS,
    TITLE_DIVIDER_BOTTOM_Y,
    WINDOW_H,
    WINDOW_W,
    TankDisplay,
    status_text_cells,
)
from retrodemos.demos.tank_status_window_phases import (
    LANE_MAX_COL,
    LANE_MIN_COL,
    MAX_SHOTS,
    PATROL_DURATION,
    WALLS,
    WINS_NEEDED,
    EngagePhase,
    PatrolPhase,
    ResetPhase,
    _Tank,
)


# Deliberately not reproduced -- a one-row (y=327) scanline artifact in
# the source where both side borders blip from red to black, then revert
# the next row. Doesn't recur, isn't mirrored top/bottom the way the real
# title-bar divider notches are, and lands on no structural boundary --
# see tank_status_window_grid.py's module docstring for the full call.
_KNOWN_SOURCE_ARTIFACT_PIXELS = {(1, 327), (2, 327), (268, 327), (269, 327)}

# Deliberate departure from the source (2026-08-26 playtesting, on the
# built demo rather than the raw reconstruct-and-diff): WIN1.png's right
# edge really is 3px of black (270-272) versus 1px on the other three
# sides, but that read as a stray extra line rather than a border, so
# RED_X1 was widened to make all four sides an even 1px hairline instead.
# Every row of the frame's own red band (not the horizontal divider under
# the title bar, which stays black clear across) differs at these two
# columns as a result.
_SYMMETRIC_BORDER_DEPARTURE_PIXELS = {
    (x, y) for x in (270, 271) for y in range(1, WINDOW_H - 1) if y != TITLE_DIVIDER_BOTTOM_Y
}


def test_chrome_reconstructs_the_source_image_almost_exactly():
    # WIN1.png's own grid is a lit-everywhere test pattern (see the
    # module docstring), so setting every cell lit here reconstructs the
    # *whole* source image, chrome included -- not just the grids. The
    # button row's own interior is excluded: it now carries invented
    # decorative icons (2026-08-26 playtesting) that don't exist in the
    # source's own blank buttons, so it's not comparable pixel-for-pixel.
    display = TankDisplay()
    display.main_cells = {(c, r) for r in range(MAIN_ROWS) for c in range(MAIN_COLS)}
    display.secondary_cells = {(c, r) for r in range(SEC_ROWS) for c in range(SEC_COLS)}
    mine = pygame.Surface((WINDOW_W, WINDOW_H))
    display.draw(mine)
    src = pygame.image.load("images/WIN1.png")
    assert mine.get_size() == src.get_size()
    button_row = pygame.Rect(BUTTON_ROW_X0, BUTTON_ROW_Y0, BUTTON_ROW_W, BUTTON_ROW_H)
    mismatches = {
        (x, y)
        for y in range(WINDOW_H)
        for x in range(WINDOW_W)
        if not button_row.collidepoint(x, y) and mine.get_at((x, y))[:3] != src.get_at((x, y))[:3]
    }
    assert mismatches == _KNOWN_SOURCE_ARTIFACT_PIXELS | _SYMMETRIC_BORDER_DEPARTURE_PIXELS


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


def test_engage_phase_resolves_a_best_of_n_match_and_finishes():
    # 2026-08-26 playtesting: "it should keep score like snake in previous
    # demos" -- a fixed shot count became a best-of-WINS_NEEDED match.
    display = TankDisplay()
    phase = EngagePhase(display, random.Random(0))
    finished = False
    for _ in range(4000):
        finished = phase.update(0.02)
        if finished:
            break
    assert finished
    assert max(phase._score) >= WINS_NEEDED or phase._shots_fired >= MAX_SHOTS
    assert not phase._bullets
    assert not phase._bursts


def test_engage_phase_score_cells_land_on_each_tanks_own_side():
    display = TankDisplay()
    phase = EngagePhase(display, random.Random(0))
    phase._score = [2, 1]
    cells = phase._score_cells()
    assert cells == {(0, 0), (0, 1), (SEC_COLS - 1, 0)}


def test_engage_phase_moves_faster_and_more_randomly_than_patrol():
    from retrodemos.demos.tank_status_window_phases import ENGAGE_MOVE_INTERVAL, MOVE_INTERVAL

    assert ENGAGE_MOVE_INTERVAL < MOVE_INTERVAL


def test_reset_phase_launches_a_rocket_before_the_burst_ignites():
    display = TankDisplay()
    phase = ResetPhase(display, random.Random(0))
    assert phase._burst is None
    assert phase._rocket.target == phase._target
    for _ in range(50):
        phase.update(0.02)
        if phase._burst is not None:
            break
    assert phase._burst is not None


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


def test_status_text_crossfades_instead_of_snapping():
    # 2026-08-26 playtesting: the status line "should animate between
    # each state" -- mid-transition, secondary_cells should be a
    # blended-intensity dict, not a flat set showing the new text outright.
    display = TankDisplay()
    phase = PatrolPhase(display, random.Random(0))
    phase._start_status_transition("ENGAGE")
    phase._update_status(0.001)
    assert isinstance(display.secondary_cells, dict)
    assert any(0.0 < v < 1.0 for v in display.secondary_cells.values())


def test_enemy_tank_sprite_is_vertically_flipped_from_the_players():
    from retrodemos.demos.tank_status_window_phases import ENEMY_TANK_SHAPE, TANK_SHAPE

    assert ENEMY_TANK_SHAPE == tuple(reversed(TANK_SHAPE))
    assert ENEMY_TANK_SHAPE != TANK_SHAPE


def test_demo_native_size_matches_grid_module():
    demo = TankStatusWindowDemo()
    assert demo.NATIVE_SIZE == (WINDOW_W, WINDOW_H)


def test_button_row_animator_presses_a_random_button_then_releases_it():
    # 2026-08-26 playtesting: the bottom row "should be pressable, but
    # ultimately do nothing other than animate" -- ambient, not clickable.
    demo = TankStatusWindowDemo()
    assert demo._display.pressed_button is None
    saw_pressed = False
    for _ in range(200):
        demo.update(0.05)
        if demo._display.pressed_button is not None:
            assert 0 <= demo._display.pressed_button < BUTTON_COUNT
            saw_pressed = True
    assert saw_pressed


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
