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
unbiased random walk barely covers ground on this wide grid. See its own
docstring for the full rationale; the short version is every phase's own
docstring should be treated as more current than this file-level summary
where the two disagree.

Every phase's specific timings and sizes are judgement calls tuned for this
display's shape (256 columns x 8 rows per strip -- much wider and shallower
than LED II's 83x9 grid), not reused verbatim from LED II's constants;
they're all named class constants, same convention as led_phases.py and
led_ii_phases.py.
"""

from __future__ import annotations

import random

import pygame

from retrodemos.framework.graph_walk import Burst, ChaseSnake
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
    RED_GREEN_SCROLL_INTERVAL = 0.03
    BLUE_CYAN_SCROLL_INTERVAL = 0.045
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


class _ChasePair:
    """One strip's snake-chase minigame: two ChaseSnakes spawned a good
    distance apart (opposite quarters of the width, so there's real ground
    to cross) that hunt each other's head every step, until one's head lands
    on the other's body -- that one wins, flashes a few times, and the pair
    is done. `SnakePhase` runs one of these per strip so red_green and
    blue_cyan resolve independently, same as the plain wandering snake this
    replaced.

    Movement and flashing are both paced by their own `Ticker` rather than
    stepping once per `update()` call, same reason every other discrete-step
    Phase in this file uses one: dt varies per frame and a Ticker catches up
    correctly on a slow one instead of silently dropping steps."""

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
        self.rng = rng
        self.max_steps = max_steps
        left_start = (rng.randrange(0, width // 4), rng.randrange(rows))
        right_start = (rng.randrange(3 * width // 4, width), rng.randrange(rows))
        self.a = ChaseSnake(graph, left_start, max_length, rng, distance, chase_chance)
        self.b = ChaseSnake(graph, right_start, max_length, rng, distance, chase_chance)
        self.winner: ChaseSnake | None = None
        self.steps_taken = 0
        self.flash_on = True
        self._step_ticker = Ticker(step_interval)
        self._flash_ticker = Ticker(flash_interval)
        self._flash_toggles = 0
        self._flash_target = flash_cycles * 2  # on + off per cycle

    @property
    def resolved(self) -> bool:
        return self.winner is not None

    @property
    def finished(self) -> bool:
        return self.resolved and self._flash_toggles >= self._flash_target

    def _step(self) -> None:
        self.steps_taken += 1
        self.a.advance(self.b.body[0])
        self.b.advance(self.a.body[0])
        a_caught = self.a.body[0] in self.b.body
        b_caught = self.b.body[0] in self.a.body
        if a_caught and b_caught:
            self.winner = self.rng.choice([self.a, self.b])  # head-on collision: pick either
        elif a_caught:
            self.winner = self.a
        elif b_caught:
            self.winner = self.b
        elif self.steps_taken >= self.max_steps:
            # Safety net -- two snakes actively closing distance on this grid
            # should always catch well before max_steps, but don't let a
            # pathological case hang the phase forever.
            self.winner = self.rng.choice([self.a, self.b])

    def update(self, dt: float) -> None:
        if not self.resolved:
            for _ in range(self._step_ticker.advance(dt)):
                self._step()
                if self.resolved:
                    break
            return
        for _ in range(self._flash_ticker.advance(dt)):
            self.flash_on = not self.flash_on
            self._flash_toggles += 1
            if self._flash_toggles >= self._flash_target:
                break

    def lit_cells(self) -> set[tuple[int, int]]:
        if not self.resolved:
            return set(self.a.body) | set(self.b.body)
        return set(self.winner.body) if self.flash_on else set()


class SnakePhase(Phase):
    """A chase minigame on each strip: two snakes spawn a quarter-width
    apart and hunt each other's head across the bit grid (red_green's pair
    independent of blue_cyan's, same "the two strips don't mirror each
    other" rule the original wandering snake used) until one catches the
    other, flashes WIN_FLASH_CYCLES times, and hands off to fireworks --
    which now reads as this chase's own finish, not just the next scripted
    beat.

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
    available. Spawning the pair a guaranteed quarter-width apart (rather
    than trusting two fully random starts to land far apart) is what makes
    "far more horizontal movement" true by construction, not just likely.

    This pattern (ChaseSnake, quarter-width spawns, weighted distance,
    catch-and-flash finish) isn't ported to LED/LED II's own SnakePhases
    yet -- worth doing next time either is touched; see PLAN.md's "Future
    framework polish"."""

    STEP_INTERVAL = 0.025
    MAX_LENGTH = 30
    MAX_STEPS = 1200
    CHASE_CHANCE = 0.65
    X_WEIGHT = 4.0
    Y_WEIGHT = 1.0
    WIN_FLASH_INTERVAL = 0.12
    WIN_FLASH_CYCLES = 5

    def reset(self) -> None:
        width = self.display.width
        rows = self.display.red_green.ROWS
        graph = dot_grid_adjacency(width, rows)

        def distance(a: tuple[int, int], b: tuple[int, int]) -> float:
            return _chase_distance(a, b, self.X_WEIGHT, self.Y_WEIGHT)

        def make_pair() -> _ChasePair:
            return _ChasePair(
                graph, width, rows, self.rng, distance, self.MAX_LENGTH, self.CHASE_CHANCE,
                self.MAX_STEPS, self.STEP_INTERVAL, self.WIN_FLASH_INTERVAL, self.WIN_FLASH_CYCLES,
            )

        self._red_green = make_pair()
        self._blue_cyan = make_pair()

    def update(self, dt: float) -> bool:
        self._red_green.update(dt)
        self._blue_cyan.update(dt)
        return self._red_green.finished and self._blue_cyan.finished

    def draw(self, surface: pygame.Surface) -> None:
        self.display.render_raw(surface, self._red_green.lit_cells(), self._blue_cyan.lit_cells())


class FireworksPhase(Phase):
    """Fireworks on both strips together: each burst picks an independent
    random (col, bit) start per strip and radiates outward via
    framework/graph_walk.py's Burst, same per-cell randomized fading
    brightness and spark scatter as LED II's RipplePhase. Repeats
    REPEATS times before moving on. Radius and spark count sized up
    further than LED II's given how much wider this grid is."""

    REPEATS = 5
    RING_INTERVAL = 0.01
    MAX_RING = 30
    SPARK_COUNT = 30
    FADE_DURATION = 0.5

    def reset(self) -> None:
        self._graph = dot_grid_adjacency(self.display.width, self.display.red_green.ROWS)
        self._repeat_index = 0
        self._start_new_burst()

    def _random_start(self) -> tuple[int, int]:
        return (self.rng.randrange(self.display.width), self.rng.randrange(self.display.red_green.ROWS))

    def _start_new_burst(self) -> None:
        self._red_green_burst = Burst(
            self._graph, self._random_start(), self.MAX_RING, self.FADE_DURATION, self.SPARK_COUNT, self.rng
        )
        self._blue_cyan_burst = Burst(
            self._graph, self._random_start(), self.MAX_RING, self.FADE_DURATION, self.SPARK_COUNT, self.rng
        )
        self._ticker = Ticker(self.RING_INTERVAL)

    def update(self, dt: float) -> bool:
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
        self.display.render_raw(surface, self._red_green_burst.intensities(), self._blue_cyan_burst.intensities())


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
