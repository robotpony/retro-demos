"""Tank Status Window's script: a single-player COMBAT-style round that
plays itself, scripted/looping rather than simulated with real collision
or AI (docs/tank-status-window.md's own open question, resolved in favour
of the cheaper option, since the dot-matrix rendering hides the
difference either way). Three phases loop: tanks patrol, tanks trade
scripted shots until one side wins a best-of-WINS_NEEDED match, one last
explosion resets the round.

Reuses `framework/graph_walk.py`'s `Burst` (via `led_grid.dot_grid_adjacency`
over the main grid's 83x84 cells) for every explosion -- both a bullet's
small impact and the round-ending blast are the same class at different
`max_ring`/`fade_duration` settings, not two separate effects.
`graph_walk.Rocket` also drives the round-ending blast's own launch trail
(2026-08-26 playtesting), the same "climb, then ignite" shape LED II's and
Title's fireworks phases use. Tank/wall placement, movement speed, and
fire timing are all invented judgement calls (no source data exists for a
"game state" -- see `tank_status_window_grid.py`'s module docstring:
WIN1.png's grid is a lit-everywhere test pattern, not a captured frame of
actual play).

2026-08-26 playtesting reworked EngagePhase from a fixed shot count into a
best-of-WINS_NEEDED match (score tracked per side, same idea as LED II's
and Title's snake-chase matches, though tanks trading shots aren't a
`graph_walk.ChasePair` round so this doesn't reuse `ChaseMatch` itself)
with faster, more randomized tank movement during the exchange; the
secondary strip's status text now crossfades between states
(`_TankSceneBase._start_status_transition`/`_update_status`) instead of
snapping; the enemy tank's sprite is now vertically flipped so its barrel
points down, toward the player it's actually firing at; and every phase
runs longer.
"""

from __future__ import annotations

import random

import pygame

from retrodemos.demos.tank_status_window_grid import MAIN_COLS, MAIN_ROWS, SEC_COLS, TankDisplay, status_text_cells
from retrodemos.framework.graph_walk import Burst, Rocket
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

# A blockier silhouette than the original 5x3 wedge (2026-08-26
# playtesting: "redesign the tank sprites to look like actual Combat
# (Atari 2600, 1978) tanks") -- a centred barrel over a wide hull with two
# track "gaps" at the base, reading as a tank body plus treads at this
# grid's resolution. Invented, like the original shape -- no source data
# exists for tank sprites (WIN1.png's grid is a lit-everywhere test
# pattern). The enemy's own copy is vertically flipped (barrel pointing
# down) so it visually faces the player it fires at, rather than sharing
# the player's up-pointing orientation -- the same playtesting round
# called that mismatch out directly ("flip the top tank to face
# downward").
TANK_SHAPE: tuple[str, ...] = (
    "...#...",
    ".#####.",
    "#######",
    "#.###.#",
)
ENEMY_TANK_SHAPE: tuple[str, ...] = tuple(reversed(TANK_SHAPE))
TANK_W, TANK_H = len(TANK_SHAPE[0]), len(TANK_SHAPE)

PLAYER_ROW = MAIN_ROWS - TANK_H - 2  # near the bottom
ENEMY_ROW = 2  # near the top
LANE_MIN_COL = 3
LANE_MAX_COL = MAIN_COLS - TANK_W - 3

_GRAPH = dot_grid_adjacency(MAIN_COLS, MAIN_ROWS)


def _tank_cells(col: int, row: int, shape: tuple[str, ...]) -> set[tuple[int, int]]:
    return {
        (col + dx, row + dy)
        for dy, line in enumerate(shape)
        for dx, ch in enumerate(line)
        if ch == "#"
    }


class _Tank:
    """A tank that patrols back and forth along its own fixed row, one
    column per movement tick, reversing direction at the lane bounds.

    `step()` takes an optional `rng`/`reverse_chance` (2026-08-26
    playtesting: EngagePhase's tanks should "move faster and more
    randomly") -- when given, there's a `reverse_chance` probability of
    reversing early, on top of the deterministic bounce at the lane ends,
    so a chase reads as more erratic. PatrolPhase/ResetPhase call `step()`
    with no arguments and get the original deterministic patrol back."""

    def __init__(self, row: int, start_col: int, direction: int, shape: tuple[str, ...] = TANK_SHAPE) -> None:
        self.row = row
        self.col = start_col
        self.direction = direction
        self.shape = shape

    def step(self, rng: random.Random | None = None, reverse_chance: float = 0.0) -> None:
        if rng is not None and rng.random() < reverse_chance:
            self.direction *= -1
        self.col += self.direction
        if self.col <= LANE_MIN_COL or self.col >= LANE_MAX_COL:
            self.direction *= -1
            self.col = max(LANE_MIN_COL, min(LANE_MAX_COL, self.col))

    def cells(self) -> set[tuple[int, int]]:
        return _tank_cells(self.col, self.row, self.shape)


class _Bullet:
    """A straight vertical shot: one row per tick, from the firing tank's
    column at the moment it fired, until it hits a wall cell or crosses
    into the opposing tank's row band. `shooter` (0 = player, 1 = enemy)
    is who scores the point if this shot actually lands on the other
    tank rather than just a wall (see EngagePhase's own `_resolve_shot`)."""

    def __init__(self, col: int, row: int, dy: int, target_row: int, shooter: int) -> None:
        self.col = col
        self.row = row
        self.dy = dy
        self.target_row = target_row
        self.shooter = shooter
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

# Lengthened and given a rocket lead-in, same request as LED II's/Title's
# own fireworks (2026-08-26 playtesting): was MAX_RING=14, FADE=1.3.
BLAST_MAX_RING = 22
BLAST_FADE = 2.0 * _SPEED
ROCKET_DURATION = 0.4 * _SPEED

# Every phase runs longer (2026-08-26 playtesting: "scenes need to get
# longer"). PATROL_DURATION/RESET_HOLD were 3.5/0.7; EngagePhase no longer
# has a fixed duration of its own (see WINS_NEEDED below) but ENGAGE_SPEED
# below makes its own exchange more frantic to compensate for however
# long a best-of-3 match happens to run.
PATROL_DURATION = 5.5 * _SPEED
RESET_HOLD = 1.2 * _SPEED

# EngagePhase is now a best-of-WINS_NEEDED match (2026-08-26 playtesting:
# "it should keep score like snake in previous demos") rather than a
# fixed ENGAGE_SHOT_COUNT -- MAX_SHOTS is only a safety net (a real match
# should always resolve well before it, same role ChasePair's own
# max_steps plays) so a run of pure misses can't hang the phase forever.
WINS_NEEDED = 3
MAX_SHOTS = 40
ENGAGE_MOVE_INTERVAL = MOVE_INTERVAL / 1.6  # faster movement during the exchange
ENGAGE_REVERSE_CHANCE = 0.12  # more randomized paths, same request

STATUS_TRANSITION_DURATION = 0.3 * _SPEED


class _TankSceneBase(Phase):
    """Shared bookkeeping every phase in this script needs: each phase
    reseeds both tanks' positions fresh in its own reset(), walls are
    always drawn, and the render step is identical everywhere -- only
    what advances differs.

    `_start_status_transition`/`_update_status` (2026-08-26 playtesting:
    the status text "should animate between each state" instead of
    snapping) crossfade the secondary strip from whatever it currently
    shows to a new piece of text over STATUS_TRANSITION_DURATION -- every
    phase's reset() starts one instead of setting `secondary_cells`
    directly, and every phase's update() advances it each frame."""

    display: TankDisplay

    def _seed_tanks(self) -> None:
        self.player = _Tank(PLAYER_ROW, LANE_MIN_COL, 1, TANK_SHAPE)
        self.enemy = _Tank(ENEMY_ROW, LANE_MAX_COL, -1, ENEMY_TANK_SHAPE)

    def _base_cells(self) -> set[tuple[int, int]]:
        return set(WALLS) | self.player.cells() | self.enemy.cells()

    def _start_status_transition(self, text: str) -> None:
        current = self.display.secondary_cells
        self._status_from = set(current) if not isinstance(current, dict) else {c for c, v in current.items() if v > 0}
        self._status_to = status_text_cells(text)
        self._status_elapsed = 0.0

    def _update_status(self, dt: float, extra_cells: set[tuple[int, int]] | None = None) -> None:
        self._status_elapsed += dt
        t = min(1.0, self._status_elapsed / STATUS_TRANSITION_DURATION)
        intensity: dict[tuple[int, int], float] = {}
        for cell in self._status_from:
            intensity[cell] = max(intensity.get(cell, 0.0), 1.0 - t)
        for cell in self._status_to:
            intensity[cell] = max(intensity.get(cell, 0.0), t)
        for cell in extra_cells or ():
            intensity[cell] = 1.0
        self.display.secondary_cells = intensity

    def draw(self, surface: pygame.Surface) -> None:
        self.display.draw(surface)


class PatrolPhase(_TankSceneBase):
    """Both tanks patrol their lanes; no shots fired. Secondary strip
    crossfades to "PATROL"."""

    def reset(self) -> None:
        self._seed_tanks()
        self._move_ticker = Ticker(MOVE_INTERVAL)
        self._elapsed = 0.0
        self._start_status_transition("PATROL")
        self._render()

    def _render(self) -> None:
        self.display.main_cells = self._base_cells()

    def update(self, dt: float) -> bool:
        self._elapsed += dt
        for _ in range(self._move_ticker.advance(dt)):
            self.player.step()
            self.enemy.step()
        self._update_status(dt)
        self._render()
        return self._elapsed >= PATROL_DURATION


class EngagePhase(_TankSceneBase):
    """Tanks keep patrolling (faster and more randomly than PatrolPhase's
    own steady sweep -- ENGAGE_MOVE_INTERVAL/ENGAGE_REVERSE_CHANCE) while
    trading shots, alternating player/enemy, until one side wins
    WINS_NEEDED hits -- a best-of-N match like LED II's/Title's own
    snake-chase games (2026-08-26 playtesting: "it should keep score like
    snake in previous demos"). A shot that reaches the opposing tank's row
    band without hitting a wall first counts as a hit only if it actually
    lands on that tank's own columns (`_resolve_shot`); every impact,
    hit or miss, still gets a small Burst. Score is shown as dots on each
    tank's own side of the secondary strip (column 0 for the player,
    the rightmost column for the enemy), alongside the crossfading
    "ENGAGE" text -- same convention as the snake games' own score dots."""

    def reset(self) -> None:
        self._seed_tanks()
        self._move_ticker = Ticker(ENGAGE_MOVE_INTERVAL)
        self._fire_ticker = Ticker(FIRE_INTERVAL)
        self._shots_fired = 0
        self._next_firer = 0  # 0 = player, 1 = enemy
        self._score = [0, 0]
        self._bullets: list[_Bullet] = []
        self._bursts: list[Burst] = []
        self._start_status_transition("ENGAGE")
        self._render()

    @property
    def _match_over(self) -> bool:
        return max(self._score) >= WINS_NEEDED or self._shots_fired >= MAX_SHOTS

    def _fire_next(self) -> None:
        if self._match_over:
            return
        if self._next_firer == 0:
            bullet = _Bullet(self.player.col + TANK_W // 2, self.player.row, -1, self.enemy.row, shooter=0)
        else:
            bullet = _Bullet(self.enemy.col + TANK_W // 2, self.enemy.row + TANK_H, 1, self.player.row, shooter=1)
        self._bullets.append(bullet)
        self._shots_fired += 1
        self._next_firer = 1 - self._next_firer

    def _resolve_shot(self, bullet: _Bullet) -> bool:
        if bullet.exploded_at in WALLS:
            return False
        target = self.enemy if bullet.shooter == 0 else self.player
        col, _row = bullet.exploded_at
        return target.col <= col < target.col + TANK_W

    def _score_cells(self) -> set[tuple[int, int]]:
        left_col, right_col = 0, SEC_COLS - 1
        cells = {(left_col, row) for row in range(self._score[0])}
        cells |= {(right_col, row) for row in range(self._score[1])}
        return cells

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
            self.player.step(self.rng, ENGAGE_REVERSE_CHANCE)
            self.enemy.step(self.rng, ENGAGE_REVERSE_CHANCE)
        for _ in range(self._fire_ticker.advance(dt)):
            self._fire_next()
        for bullet in list(self._bullets):
            bullet.step()
            if bullet.exploded_at is not None:
                if self._resolve_shot(bullet):
                    self._score[bullet.shooter] += 1
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
        self._update_status(dt, self._score_cells())
        self._render()
        return self._match_over and not self._bullets and not self._bursts


class ResetPhase(_TankSceneBase):
    """A rocket climbs from the bottom row to the grid's centre, then one
    last, bigger Burst ignites there -- reads as the round ending -- then
    a brief blank hold before looping back to PatrolPhase. Secondary strip
    crossfades to "RESET".

    The rocket lead-in was added 2026-08-26 (playtesting: fireworks "need
    to have the rocket portion ... flies to the centre point, then the
    explosion happens"), the same `graph_walk.Rocket` launch-then-ignite
    shape LED II's and Title's own fireworks phases use."""

    def reset(self) -> None:
        self._seed_tanks()
        self._target = (MAIN_COLS // 2, MAIN_ROWS // 2)
        self._rocket = Rocket((self._target[0], MAIN_ROWS - 1), self._target, ROCKET_DURATION)
        self._burst: Burst | None = None
        self._hold = 0.0
        self._start_status_transition("RESET")
        self._render()

    def _render(self) -> None:
        if self._burst is None:
            self.display.main_cells = {self._rocket.position(): 1.0}
        else:
            self.display.main_cells = dict(self._burst.intensities())

    def update(self, dt: float) -> bool:
        self._update_status(dt)
        if self._burst is None:
            self._rocket.age(dt)
            if not self._rocket.done:
                self._render()
                return False
            self._burst = Burst(_GRAPH, self._target, BLAST_MAX_RING, BLAST_FADE, spark_count=0, rng=self.rng)
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
