"""Tank Status Window's script: a single-player COMBAT-style round that
plays itself, scripted/looping rather than simulated with real collision
or AI (docs/tank-status-window.md's own open question, resolved in favour
of the cheaper option, since the dot-matrix rendering hides the
difference either way). Three phases loop: tanks patrol, tanks trade a
few scripted shots, one last explosion resets the round.

Reuses `framework/graph_walk.py`'s `Burst` (via `led_grid.dot_grid_adjacency`
over the main grid's 83x84 cells) for every explosion -- both a bullet's
small impact and the round-ending blast are the same class at different
`max_ring`/`fade_duration` settings, not two separate effects. Tank/wall
placement, movement speed, and fire timing are all invented judgement
calls (no source data exists for a "game state" -- see
`tank_status_window_grid.py`'s module docstring: WIN1.png's grid is a
lit-everywhere test pattern, not a captured frame of actual play).
"""

from __future__ import annotations

import pygame

from retrodemos.demos.tank_status_window_grid import MAIN_COLS, MAIN_ROWS, TankDisplay, status_text_cells
from retrodemos.framework.graph_walk import Burst
from retrodemos.framework.led_grid import dot_grid_adjacency
from retrodemos.framework.phase import Phase
from retrodemos.framework.ticker import Ticker

# A small fixed maze -- three rectangular wall blocks, invented, symmetric
# about the grid's vertical centre line so neither tank's lane favours it.
WALLS: frozenset[tuple[int, int]] = frozenset(
    (col, row)
    for col0, row0, w, h in ((18, 30, 6, 4), (58, 30, 6, 4), (38, 46, 8, 4))
    for col in range(col0, col0 + w)
    for row in range(row0, row0 + h)
)

TANK_SHAPE: tuple[str, ...] = (
    "..#..",
    ".###.",
    "#####",
)
TANK_W, TANK_H = 5, 3

PLAYER_ROW = MAIN_ROWS - TANK_H - 2  # near the bottom
ENEMY_ROW = 2  # near the top
LANE_MIN_COL = 3
LANE_MAX_COL = MAIN_COLS - TANK_W - 3

_GRAPH = dot_grid_adjacency(MAIN_COLS, MAIN_ROWS)


def _tank_cells(col: int, row: int) -> set[tuple[int, int]]:
    return {
        (col + dx, row + dy)
        for dy, line in enumerate(TANK_SHAPE)
        for dx, ch in enumerate(line)
        if ch == "#"
    }


class _Tank:
    """A tank that patrols back and forth along its own fixed row, one
    column per movement tick, reversing direction at the lane bounds."""

    def __init__(self, row: int, start_col: int, direction: int) -> None:
        self.row = row
        self.col = start_col
        self.direction = direction

    def step(self) -> None:
        self.col += self.direction
        if self.col <= LANE_MIN_COL or self.col >= LANE_MAX_COL:
            self.direction *= -1
            self.col = max(LANE_MIN_COL, min(LANE_MAX_COL, self.col))

    def cells(self) -> set[tuple[int, int]]:
        return _tank_cells(self.col, self.row)


class _Bullet:
    """A straight vertical shot: one row per tick, from the firing tank's
    column at the moment it fired, until it hits a wall cell or crosses
    into the opposing tank's row band."""

    def __init__(self, col: int, row: int, dy: int, target_row: int) -> None:
        self.col = col
        self.row = row
        self.dy = dy
        self.target_row = target_row
        self.exploded_at: tuple[int, int] | None = None

    def step(self) -> None:
        next_row = self.row + self.dy
        hit_wall = (self.col, next_row) in WALLS
        reached_target = next_row <= self.target_row if self.dy < 0 else next_row >= self.target_row
        if hit_wall or reached_target:
            self.exploded_at = (self.col, next_row)
        else:
            self.row = next_row


# Playtesting (2026-08-26): "animation should be faster (15%)" -- every
# duration below is scaled by _SPEED, not hand-retuned individually, so
# the whole script speeds up uniformly rather than just a few phases.
# "15% faster" means the rate increases 15% (time / 1.15), not time cut
# by 15%.
_SPEED = 1 / 1.15

MOVE_INTERVAL = 0.09 * _SPEED
FIRE_INTERVAL = 1.1 * _SPEED
IMPACT_MAX_RING = 3
IMPACT_FADE = 0.5 * _SPEED
BLAST_MAX_RING = 14
BLAST_FADE = 1.3 * _SPEED

PATROL_DURATION = 3.5 * _SPEED
ENGAGE_SHOT_COUNT = 5
RESET_HOLD = 0.7 * _SPEED


class _TankSceneBase(Phase):
    """Shared bookkeeping every phase in this script needs: the two
    tanks' positions carry over between phases (PatrolPhase reset()
    re-seeds them fresh each loop), walls are always drawn, and the
    render step is identical everywhere -- only what advances differs."""

    display: TankDisplay

    def _seed_tanks(self) -> None:
        self.player = _Tank(PLAYER_ROW, LANE_MIN_COL, 1)
        self.enemy = _Tank(ENEMY_ROW, LANE_MAX_COL, -1)

    def _base_cells(self) -> set[tuple[int, int]]:
        return set(WALLS) | self.player.cells() | self.enemy.cells()

    def draw(self, surface: pygame.Surface) -> None:
        self.display.draw(surface)


class PatrolPhase(_TankSceneBase):
    """Both tanks patrol their lanes; no shots fired. Secondary strip
    reads "PATROL"."""

    def reset(self) -> None:
        self._seed_tanks()
        self._move_ticker = Ticker(MOVE_INTERVAL)
        self._elapsed = 0.0
        self.display.secondary_cells = status_text_cells("PATROL")
        self._render()

    def _render(self) -> None:
        self.display.main_cells = self._base_cells()

    def update(self, dt: float) -> bool:
        self._elapsed += dt
        for _ in range(self._move_ticker.advance(dt)):
            self.player.step()
            self.enemy.step()
        self._render()
        return self._elapsed >= PATROL_DURATION


class EngagePhase(_TankSceneBase):
    """Tanks keep patrolling while trading ENGAGE_SHOT_COUNT scripted
    shots, alternating player/enemy; each impact is a small Burst.
    Secondary strip reads "ENGAGE"."""

    def reset(self) -> None:
        self._seed_tanks()
        self._move_ticker = Ticker(MOVE_INTERVAL)
        self._fire_ticker = Ticker(FIRE_INTERVAL)
        self._shots_fired = 0
        self._next_firer = 0  # 0 = player, 1 = enemy
        self._bullets: list[_Bullet] = []
        self._bursts: list[Burst] = []
        self.display.secondary_cells = status_text_cells("ENGAGE")
        self._render()

    def _fire_next(self) -> None:
        if self._shots_fired >= ENGAGE_SHOT_COUNT:
            return
        if self._next_firer == 0:
            bullet = _Bullet(self.player.col + TANK_W // 2, self.player.row, -1, self.enemy.row)
        else:
            bullet = _Bullet(self.enemy.col + TANK_W // 2, self.enemy.row + TANK_H, 1, self.player.row)
        self._bullets.append(bullet)
        self._shots_fired += 1
        self._next_firer = 1 - self._next_firer

    def _render(self) -> None:
        cells: dict[tuple[int, int], float] = {cell: 1.0 for cell in self._base_cells()}
        for bullet in self._bullets:
            cells[(bullet.col, bullet.row)] = 1.0
        for burst in self._bursts:
            for cell, level in burst.intensities().items():
                cells[cell] = max(cells.get(cell, 0.0), level)
        self.display.main_cells = cells

    def update(self, dt: float) -> bool:
        for _ in range(self._move_ticker.advance(dt)):
            self.player.step()
            self.enemy.step()
        for _ in range(self._fire_ticker.advance(dt)):
            self._fire_next()
        for bullet in list(self._bullets):
            bullet.step()
            if bullet.exploded_at is not None:
                burst = Burst(_GRAPH, bullet.exploded_at, IMPACT_MAX_RING, IMPACT_FADE, spark_count=0, rng=self.rng)
                burst.expand_next_ring()
                self._bursts.append(burst)
                self._bullets.remove(bullet)
        for burst in self._bursts:
            burst.age(dt)
            if burst.is_expanding:
                burst.expand_next_ring()
            else:
                burst.add_sparks()  # spark_count=0 -- this only flips burned_out on, no extra embers
        self._bursts = [b for b in self._bursts if not b.burned_out]
        self._render()
        return self._shots_fired >= ENGAGE_SHOT_COUNT and not self._bullets and not self._bursts


class ResetPhase(_TankSceneBase):
    """One last, bigger Burst at the grid's centre -- reads as the round
    ending -- then a brief blank hold before looping back to PatrolPhase.
    Secondary strip reads "RESET"."""

    def reset(self) -> None:
        self._seed_tanks()
        center = (MAIN_COLS // 2, MAIN_ROWS // 2)
        self._burst = Burst(_GRAPH, center, BLAST_MAX_RING, BLAST_FADE, spark_count=0, rng=self.rng)
        self._burst.expand_next_ring()
        self._hold = 0.0
        self.display.secondary_cells = status_text_cells("RESET")
        self._render()

    def _render(self) -> None:
        self.display.main_cells = dict(self._burst.intensities())

    def update(self, dt: float) -> bool:
        self._burst.age(dt)
        if self._burst.is_expanding:
            self._burst.expand_next_ring()
        else:
            self._burst.add_sparks()  # spark_count=0 -- flips burned_out on, no extra embers
        self._render()
        if not self._burst.burned_out:
            return False
        self._hold += dt
        return self._hold >= RESET_HOLD
