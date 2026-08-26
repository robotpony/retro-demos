"""Title's script: an ordered sequence of phases that runs on a loop,
mirroring LED and LED II's five-beat structure (power-up, main content,
snake, fireworks, credit hold) -- confirmed with Bruce (2026-08-24), same
as LED II's script was, since Title had no such spec of its own either.

Every phase drives both of Title's colour strips together (see
title.py's TitleDisplays) rather than one display each, since Title's
script is one script over two strips, not two independent scripts. Where a
phase needs to light individual cells rather than render a byte value
(power-up flicker, snake, fireworks, words), it addresses (col, bit) cells
directly through BitColumnDisplay.render_raw and framework/graph_walk.py's
ChaseSnake/Burst over led_grid.dot_grid_adjacency(width, ROWS) -- the same
graph function LED II's phases use, over a bit grid instead of a dot grid
(see led_grid.py's BitColumnDisplay docstring for why it's reused rather
than duplicated). Only ScrollPhase (the main content) uses render_values,
the byte-value-driven API those cells were built from; WordsPhase looks
like it should too (it renders fixed text) but doesn't -- see its own
docstring for why a byte-value-per-column API can't spell anything.

SnakePhase (2026-08-24) isn't a wandering Snake like LED/LED II's -- it's a
chase minigame built on graph_walk.ChaseSnake, added because a plain Snake's
unbiased random walk barely covers ground on this wide grid. Rebuilt again
2026-08-26 (playtesting) into a best-of-3 match per strip via
graph_walk.ChaseMatch, with a lower CHASE_CHANCE for more randomized paths;
FireworksPhase gained a graph_walk.Rocket launch trail before each pair of
bursts ignites, and ScrollPhase's own scroll intervals were sped up. See
each phase's own docstring for the full rationale; the short version is
every phase's own docstring should be treated as more current than this
file-level summary where the two disagree.

Every phase's specific timings and sizes are judgement calls tuned for this
display's shape (256 columns x 8 rows per strip -- much wider and shallower
than LED II's 83x9 grid), not reused verbatim from LED II's constants;
they're all named class constants, same convention as led_phases.py and
led_ii_phases.py.
"""

from __future__ import annotations

import random

import pygame

from retrodemos.framework.graph_walk import Burst, ChaseMatch, ChasePair, Rocket
from retrodemos.framework.led_grid import DOT_FONT, GLYPH_GAP, GLYPH_H, GLYPH_W, dot_grid_adjacency
from retrodemos.framework.phase import Phase
from retrodemos.framework.ticker import Ticker


class PowerUpPhase(Phase):
    """Random bits flash on/off across both strips, like a loose
    connection; then a column sweep travels left to right across the full
    width (both strips together), speeding up; then a brief blank hold
    before the scroll starts."""

    FLICKER_TICKS = 18
    FLICKER_TICK_DURATION = 0.08
    FLICKER_PROBABILITY = 0.35

    SWEEP_START_TICK_DURATION = 0.012
    SWEEP_END_TICK_DURATION = 0.003

    BLANK_HOLD = 0.4

    def reset(self) -> None:
        self._stage = "flicker"
        self._ticker = Ticker(self.FLICKER_TICK_DURATION)
        self._blank_elapsed = 0.0
        self._flicker_tick_count = 0
        self._flicker_red_green: set[tuple[int, int]] = set()
        self._flicker_blue_cyan: set[tuple[int, int]] = set()
        self._sweep_step = 0
        self._sweep_total_steps = self.display.width

    def _randomize_flicker(self) -> None:
        width = self.display.width
        rows = range(self.display.red_green.ROWS)
        self._flicker_red_green = {
            (x, r) for x in range(width) for r in rows if self.rng.random() < self.FLICKER_PROBABILITY
        }
        self._flicker_blue_cyan = {
            (x, r) for x in range(width) for r in rows if self.rng.random() < self.FLICKER_PROBABILITY
        }

    def _sweep_tick_duration(self) -> float:
        progress = self._sweep_step / self._sweep_total_steps
        return self.SWEEP_START_TICK_DURATION + (
            self.SWEEP_END_TICK_DURATION - self.SWEEP_START_TICK_DURATION
        ) * progress

    def update(self, dt: float) -> bool:
        if self._stage == "flicker":
            for _ in range(self._ticker.advance(dt)):
                self._randomize_flicker()
                self._flicker_tick_count += 1
                if self._flicker_tick_count >= self.FLICKER_TICKS:
                    self._stage = "sweep"
                    self._ticker.interval = self._sweep_tick_duration()
                    self._ticker.reset()
                    break
            return False
        if self._stage == "sweep":
            self._ticker.interval = self._sweep_tick_duration()
            for _ in range(self._ticker.advance(dt)):
                self._sweep_step += 1
                if self._sweep_step >= self._sweep_total_steps:
                    self._stage = "blank"
                    break
                self._ticker.interval = self._sweep_tick_duration()
            return False
        self._blank_elapsed += dt
        return self._blank_elapsed >= self.BLANK_HOLD  # stage == "blank"

    def draw(self, surface: pygame.Surface) -> None:
        if self._stage == "flicker":
            self.display.render_raw(surface, self._flicker_red_green, self._flicker_blue_cyan)
        elif self._stage == "sweep":
            rows = range(self.display.red_green.ROWS)
            current_col = self._sweep_step % self.display.width
            lit = {(current_col, r) for r in rows}
            self.display.render_raw(surface, lit, lit)
        else:
            self.display.render_raw(surface)


class ScrollPhase(Phase):
    """The main content: both strips scroll their value-per-column mapping
    over time (in opposite directions, at different speeds, so the two
    strips read as distinct), starting from offset 0 -- the exact identity
    ramp images/TITLE.png itself shows -- each time the phase (re)starts.
    Runs for DURATION seconds before handing off, since (unlike the
    original single-behaviour Title) this is now one stage of a loop, not
    the whole demo."""

    DURATION = 6.0
    # Sped up 2026-08-26 playtesting ("speed up Title's own scroll"):
    # was 0.03 / 0.045.
    RED_GREEN_SCROLL_INTERVAL = 0.02
    BLUE_CYAN_SCROLL_INTERVAL = 0.03
    BLUE_CYAN_DIRECTION = -1

    def reset(self) -> None:
        self._elapsed = 0.0
        self._red_green_offset = 0
        self._blue_cyan_offset = 0
        self._red_green_ticker = Ticker(self.RED_GREEN_SCROLL_INTERVAL)
        self._blue_cyan_ticker = Ticker(self.BLUE_CYAN_SCROLL_INTERVAL)

    def update(self, dt: float) -> bool:
        self._elapsed += dt
        width = self.display.width
        for _ in range(self._red_green_ticker.advance(dt)):
            self._red_green_offset = (self._red_green_offset + 1) % width
        for _ in range(self._blue_cyan_ticker.advance(dt)):
            self._blue_cyan_offset = (self._blue_cyan_offset + self.BLUE_CYAN_DIRECTION) % width
        return self._elapsed >= self.DURATION

    def draw(self, surface: pygame.Surface) -> None:
        width = self.display.width
        red_green_values = [(x + self._red_green_offset) % width for x in range(width)]
        blue_cyan_values = [(x + self._blue_cyan_offset) % width for x in range(width)]
        self.display.render_values(surface, red_green_values, blue_cyan_values)


def _chase_distance(a: tuple[int, int], b: tuple[int, int], x_weight: float, y_weight: float) -> float:
    """Weighted Manhattan distance for Title's chase: moving a step closer
    on whichever axis has the bigger weight lowers this more, so
    ChaseSnake's argmin favours that axis whenever it still has ground to
    close, and only takes the other axis's step once it doesn't."""
    return abs(a[0] - b[0]) * x_weight + abs(a[1] - b[1]) * y_weight


class _TitleChase:
    """One strip's snake-chase minigame: spawns a graph_walk.ChasePair a
    guaranteed quarter-width apart (so there's real ground to cross) and
    paces its step/flash ticks with its own Tickers, same reason every
    other discrete-step Phase in this file uses one -- dt varies per frame
    and a Ticker catches up correctly on a slow one instead of silently
    dropping steps. `SnakePhase` runs one of these per strip so red_green
    and blue_cyan resolve independently, same as the plain wandering snake
    this replaced.

    The catch/win/flash bookkeeping itself lives in `graph_walk.ChasePair`,
    shared with LED II's own SnakePhase (`led_ii_phases.py`) -- this class
    only owns what's specific to Title: the quarter-width spawn rule and
    the Ticker-paced stepping."""

    def __init__(
        self,
        graph: dict[tuple[int, int], set[tuple[int, int]]],
        width: int,
        rows: int,
        rng: random.Random,
        distance,
        max_length: int,
        chase_chance: float,
        max_steps: int,
        step_interval: float,
        flash_interval: float,
        flash_cycles: int,
    ) -> None:
        left_start = (rng.randrange(0, width // 4), rng.randrange(rows))
        right_start = (rng.randrange(3 * width // 4, width), rng.randrange(rows))
        self.pair = ChasePair(
            graph, left_start, right_start, max_length, rng, distance, chase_chance, max_steps, flash_cycles
        )
        self._step_ticker = Ticker(step_interval)
        self._flash_ticker = Ticker(flash_interval)

    @property
    def finished(self) -> bool:
        return self.pair.finished

    @property
    def winner_index(self) -> int | None:
        return self.pair.winner_index

    def update(self, dt: float) -> None:
        if not self.pair.resolved:
            for _ in range(self._step_ticker.advance(dt)):
                self.pair.step()
                if self.pair.resolved:
                    break
            return
        for _ in range(self._flash_ticker.advance(dt)):
            self.pair.flash_tick()
            if self.pair.finished:
                break

    def lit_cells(self) -> set[tuple[int, int]]:
        return self.pair.lit_cells()


class SnakePhase(Phase):
    """A chase minigame on each strip: two snakes spawn a quarter-width
    apart and hunt each other's head across the bit grid (red_green's
    match independent of blue_cyan's, same "the two strips don't mirror
    each other" rule the original wandering snake used) until one catches
    the other and flashes -- now a best-of-WINS_NEEDED match per strip
    (`graph_walk.ChaseMatch`, 2026-08-26 playtesting: "apply the same
    best-of-3 treatment as LED II"), with a fresh round spawning
    immediately after each score unless that strip's match is already won.
    Only hands off to fireworks once *both* strips have finished their own
    match. Score is shown as dots stacked on each snake's own starting
    side of its strip (column 0 for the left spawn, the rightmost column
    for the right), same convention as LED II's own SnakePhase.

    Rebuilt 2026-08-24 from a single unbiased Snake per strip (request: the
    scene should run longer and cover far more horizontal ground). A plain
    Snake picks its next cell uniformly at random among its neighbours, so
    on a 256-wide x 8-row grid its net drift over a few hundred steps is a
    random walk's sqrt(steps) -- a few columns at most, reading as wobbling
    in place rather than travel. `graph_walk.ChaseSnake` fixes both
    problems: biasing steps toward a target (each snake's target is the
    other's head, recomputed every step) makes the walk read as directed
    motion, and `_chase_distance`'s X_WEIGHT/Y_WEIGHT bias keeps that motion
    mostly horizontal on this wide-but-shallow grid -- a vertical step it
    doesn't strictly need scores worse than a horizontal one that's still
    available. Spawning each round a guaranteed quarter-width apart (rather
    than trusting two fully random starts to land far apart) is what makes
    "far more horizontal movement" true by construction, not just likely.
    CHASE_CHANCE was also lowered 2026-08-26 (0.65 -> 0.45, same
    playtesting: "snakes should take more randomized paths").

    The catch/win/flash bookkeeping (`graph_walk.ChasePair`) and the
    best-of-N match bookkeeping (`graph_walk.ChaseMatch`) are both shared
    with LED II's own SnakePhase (`led_ii_phases.py`); this class's own
    `_TitleChase` wrapper covers what's Title-specific: two independent
    matches (one per strip) and the quarter-width spawn rule tuned for
    this grid's 32:1 width:height ratio. LED's segment-graph SnakePhase
    hasn't been ported to a chase minigame yet -- worth doing next time
    it's touched; see PLAN.md's "Future framework polish"."""

    STEP_INTERVAL = 0.025
    MAX_LENGTH = 30
    MAX_STEPS = 1200
    CHASE_CHANCE = 0.45
    X_WEIGHT = 4.0
    Y_WEIGHT = 1.0
    WIN_FLASH_INTERVAL = 0.12
    WIN_FLASH_CYCLES = 5
    WINS_NEEDED = 3

    def reset(self) -> None:
        width = self.display.width
        rows = self.display.red_green.ROWS
        graph = dot_grid_adjacency(width, rows)

        def distance(a: tuple[int, int], b: tuple[int, int]) -> float:
            return _chase_distance(a, b, self.X_WEIGHT, self.Y_WEIGHT)

        def make_round() -> _TitleChase:
            return _TitleChase(
                graph, width, rows, self.rng, distance, self.MAX_LENGTH, self.CHASE_CHANCE,
                self.MAX_STEPS, self.STEP_INTERVAL, self.WIN_FLASH_INTERVAL, self.WIN_FLASH_CYCLES,
            )

        self._red_green_match = ChaseMatch(make_round, self.WINS_NEEDED)
        self._blue_cyan_match = ChaseMatch(make_round, self.WINS_NEEDED)

    def _score_cells(self, match: ChaseMatch, rows: int) -> set[tuple[int, int]]:
        left_col, right_col = 0, self.display.width - 1
        cells = {(left_col, row) for row in range(match.score[0])}
        cells |= {(right_col, row) for row in range(match.score[1])}
        return cells

    def _advance(self, match: ChaseMatch, dt: float) -> None:
        match.round.update(dt)
        match.update()

    def update(self, dt: float) -> bool:
        self._advance(self._red_green_match, dt)
        self._advance(self._blue_cyan_match, dt)
        return self._red_green_match.finished and self._blue_cyan_match.finished

    def draw(self, surface: pygame.Surface) -> None:
        rows = self.display.red_green.ROWS
        red_green_cells = self._red_green_match.round.lit_cells() | self._score_cells(self._red_green_match, rows)
        blue_cyan_cells = self._blue_cyan_match.round.lit_cells() | self._score_cells(self._blue_cyan_match, rows)
        self.display.render_raw(surface, red_green_cells, blue_cyan_cells)


class FireworksPhase(Phase):
    """Fireworks on both strips together: each burst picks an independent
    random (col, bit) target per strip and radiates outward via
    framework/graph_walk.py's Burst, same per-cell randomized fading
    brightness and spark scatter as LED II's RipplePhase. Repeats
    REPEATS times before moving on. Radius and spark count sized up
    further than LED II's given how much wider this grid is.

    A rocket lead-in was added 2026-08-26 (same request as LED II's own
    RipplePhase): before each pair of bursts ignites, a
    `graph_walk.Rocket` per strip climbs straight up from the bottom row
    to that burst's own target column/row, and only once both rockets
    arrive does either burst begin expanding."""

    REPEATS = 5
    RING_INTERVAL = 0.01
    MAX_RING = 30
    SPARK_COUNT = 30
    FADE_DURATION = 0.5
    ROCKET_DURATION = 0.3

    def reset(self) -> None:
        self._graph = dot_grid_adjacency(self.display.width, self.display.red_green.ROWS)
        self._repeat_index = 0
        self._start_new_burst()

    def _random_target(self) -> tuple[int, int]:
        return (self.rng.randrange(self.display.width), self.rng.randrange(self.display.red_green.ROWS))

    def _start_new_burst(self) -> None:
        rows = self.display.red_green.ROWS
        red_green_target = self._random_target()
        blue_cyan_target = self._random_target()
        self._red_green_rocket = Rocket((red_green_target[0], rows - 1), red_green_target, self.ROCKET_DURATION)
        self._blue_cyan_rocket = Rocket((blue_cyan_target[0], rows - 1), blue_cyan_target, self.ROCKET_DURATION)
        self._red_green_target = red_green_target
        self._blue_cyan_target = blue_cyan_target
        self._red_green_burst: Burst | None = None
        self._blue_cyan_burst: Burst | None = None
        self._ticker = Ticker(self.RING_INTERVAL)

    def _ignite_if_ready(self) -> None:
        if self._red_green_burst is None and self._red_green_rocket.done:
            self._red_green_burst = Burst(
                self._graph, self._red_green_target, self.MAX_RING, self.FADE_DURATION, self.SPARK_COUNT, self.rng
            )
        if self._blue_cyan_burst is None and self._blue_cyan_rocket.done:
            self._blue_cyan_burst = Burst(
                self._graph, self._blue_cyan_target, self.MAX_RING, self.FADE_DURATION, self.SPARK_COUNT, self.rng
            )

    def update(self, dt: float) -> bool:
        if self._red_green_burst is None:
            self._red_green_rocket.age(dt)
        if self._blue_cyan_burst is None:
            self._blue_cyan_rocket.age(dt)
        self._ignite_if_ready()
        if self._red_green_burst is None or self._blue_cyan_burst is None:
            return False
        self._red_green_burst.age(dt)
        self._blue_cyan_burst.age(dt)
        if self._red_green_burst.is_expanding or self._blue_cyan_burst.is_expanding:
            for _ in range(self._ticker.advance(dt)):
                if self._red_green_burst.is_expanding:
                    self._red_green_burst.expand_next_ring()
                if self._blue_cyan_burst.is_expanding:
                    self._blue_cyan_burst.expand_next_ring()
                if not (self._red_green_burst.is_expanding or self._blue_cyan_burst.is_expanding):
                    break
            return False
        self._red_green_burst.add_sparks()
        self._blue_cyan_burst.add_sparks()
        if self._red_green_burst.burned_out and self._blue_cyan_burst.burned_out:
            self._repeat_index += 1
            if self._repeat_index >= self.REPEATS:
                return True
            self._start_new_burst()
        return False

    def draw(self, surface: pygame.Surface) -> None:
        red_green = (
            self._red_green_burst.intensities()
            if self._red_green_burst is not None
            else {self._red_green_rocket.position(): 1.0}
        )
        blue_cyan = (
            self._blue_cyan_burst.intensities()
            if self._blue_cyan_burst is not None
            else {self._blue_cyan_rocket.position(): 1.0}
        )
        self.display.render_raw(surface, red_green, blue_cyan)


class WordsPhase(Phase):
    """Holds a short credit, centred, before the script loops back to
    power-up. LED and LED II hold "1991" via their own font machinery
    (SevenSegmentDisplay/DotMatrixDisplay); Title's BitColumnDisplay has no
    font of its own (a column is a byte value rendered as its own 8 bits,
    not a glyph cell), so this phase borrows `led_grid.DOT_FONT` -- the same
    5x7 digit font DotMatrixDisplay's marquee uses -- and lights the
    matching (col, row) cells directly via render_raw, the same "addressing
    individual cells for choreography that isn't a value-per-column mapping"
    role render_raw already plays for SnakePhase/FireworksPhase above.

    Fixed 2026-08-24: the previous version tried to spell "1991" by writing
    its literal ASCII byte values (0x31, 0x39, 0x39, 0x31) into
    render_values, one byte per column. But a BitColumnDisplay column just
    renders a byte's own 8 bits as pixels top-to-bottom -- 0x31 is
    0b00110001, not a glyph -- so that never read as text, just four columns
    of bit noise. Reusing DOT_FONT instead means every pixel that's lit is
    lit because it's part of the digit's actual shape."""

    TEXT = "1991"
    HOLD_DURATION = 2.5

    def reset(self) -> None:
        self._elapsed = 0.0
        rows = self.display.red_green.ROWS
        row_offset = (rows - GLYPH_H) // 2
        text_width = len(self.TEXT) * (GLYPH_W + GLYPH_GAP) - GLYPH_GAP
        col_start = (self.display.width - text_width) // 2
        cells: set[tuple[int, int]] = set()
        for i, ch in enumerate(self.TEXT):
            glyph = DOT_FONT.get(ch, DOT_FONT[" "])
            char_col = col_start + i * (GLYPH_W + GLYPH_GAP)
            for gx, gy in glyph:
                cells.add((char_col + gx, row_offset + gy))
        self._cells = cells

    def update(self, dt: float) -> bool:
        self._elapsed += dt
        return self._elapsed >= self.HOLD_DURATION

    def draw(self, surface: pygame.Surface) -> None:
        self.display.render_raw(surface, self._cells, self._cells)
