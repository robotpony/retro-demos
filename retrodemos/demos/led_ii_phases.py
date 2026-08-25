"""LED II's script: an ordered sequence of phases that runs on a loop,
mirroring LED's own five-beat structure (led_phases.py) but reworked for a
dot-matrix grid instead of seven-segment digits: power-up (random dot
flicker, then a column sweep that speeds up), a smoothly-scrolling marquee,
a snake-chase minigame across the dot grid, a rippling burst that radiates
outward and repeats, then a held "1991" credit -- then the whole thing loops.

Unlike LED's choreography, none of this comes from a specific spec of
Bruce's for LED II; it's a deliberate structural echo of LED's script,
confirmed with Bruce before building (2026-08-24) rather than assumed. See
docs/led-ii.md and PLAN.md for the demo overview.

SnakePhase was rebuilt 2026-08-24, porting the snake-chase minigame Title's
own SnakePhase introduced the same day: two ChaseSnakes (graph_walk.py) hunt
each other across the grid via a shared graph_walk.ChasePair, rather than a
single Snake wandering at random. See SnakePhase's own docstring for the
full rationale.

Every phase's specific timings (tick durations, snake/ripple sizes, hold
lengths) are judgement calls, tuned for this display's much larger grid
(83x9 dots vs LED's 11 digit cells) rather than reused verbatim from LED's
own constants; they're all named constants at the top of each class so
they're easy to retune without touching the choreography logic -- same
convention as led_phases.py.
"""

from __future__ import annotations

import random

import pygame

from retrodemos.framework.graph_walk import Burst, ChasePair
from retrodemos.framework.led_grid import DotMatrixDisplay, dot_grid_adjacency
from retrodemos.framework.phase import Phase
from retrodemos.framework.ticker import Ticker


class PowerUpPhase(Phase):
    """Random dots flash on/off, like a loose connection; then a column
    sweep travels left to right across the full grid, speeding up over a
    couple of passes; then a brief blank hold before the marquee starts."""

    FLICKER_TICKS = 18
    FLICKER_TICK_DURATION = 0.08
    FLICKER_PROBABILITY = 0.35

    SWEEP_PASSES = 2
    SWEEP_START_TICK_DURATION = 0.035
    SWEEP_END_TICK_DURATION = 0.008

    BLANK_HOLD = 0.4

    def reset(self) -> None:
        self._stage = "flicker"
        self._ticker = Ticker(self.FLICKER_TICK_DURATION)
        self._blank_elapsed = 0.0
        self._flicker_tick_count = 0
        self._flicker_dots: set[tuple[int, int]] = set()
        self._sweep_step = 0
        self._sweep_total_steps = self.SWEEP_PASSES * self.display.cols

    def _randomize_flicker(self) -> None:
        self._flicker_dots = {
            (col, row)
            for row in range(self.display.ROWS)
            for col in range(self.display.cols)
            if self.rng.random() < self.FLICKER_PROBABILITY
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
            self.display.render_raw(surface, self._flicker_dots)
        elif self._stage == "sweep":
            current_col = self._sweep_step % self.display.cols
            lit = {(current_col, row) for row in range(self.display.ROWS)}
            self.display.render_raw(surface, lit)
        else:
            self.display.render_raw(surface)


class MarqueePhase(Phase):
    """Smoothly scrolls a message across the dot matrix one dot-column at a
    time -- unlike LED's NumbersPhase, which jumps a whole character cell
    per step (fine for seven-segment digits, but a dot-matrix marquee reads
    as continuous motion). Loops for a couple of passes before handing off
    to the next phase."""

    DEFAULT_TEXT = "0123456789"
    GAP = "   "  # blank characters between repeats
    SCROLL_INTERVAL = 0.04
    LAPS = 2

    def __init__(self, display: DotMatrixDisplay, rng: random.Random, text: str | None = None) -> None:
        self.text = text or self.DEFAULT_TEXT
        super().__init__(display, rng)

    def reset(self) -> None:
        dots, self._text_width = self.display.text_dots(self.text + self.GAP)
        self._dots_by_col: dict[int, set[int]] = {}
        for x, y in dots:
            self._dots_by_col.setdefault(x, set()).add(y)
        self._offset = 0
        self._steps = 0
        self._total_steps = self.LAPS * self._text_width
        self._ticker = Ticker(self.SCROLL_INTERVAL)

    def update(self, dt: float) -> bool:
        for _ in range(self._ticker.advance(dt)):
            self._offset = (self._offset + 1) % self._text_width
            self._steps += 1
        return self._steps >= self._total_steps

    def draw(self, surface: pygame.Surface) -> None:
        window: set[tuple[int, int]] = set()
        for local_col in range(self.display.cols):
            virtual_col = (local_col + self._offset) % self._text_width
            for row in self._dots_by_col.get(virtual_col, ()):
                window.add((local_col, row))
        self.display.render_raw(surface, window)


def _chase_distance(a: tuple[int, int], b: tuple[int, int], x_weight: float, y_weight: float) -> float:
    """Weighted Manhattan distance for LED II's chase: moving a step closer
    on whichever axis has the bigger weight lowers this more, so
    ChaseSnake's argmin favours that axis whenever it still has ground to
    close. Same idea as Title's own `_chase_distance`, weighted milder
    (2:1, not 4:1) since this grid's 83:9 width:height ratio is wide but
    nowhere near Title's 32:1."""
    return abs(a[0] - b[0]) * x_weight + abs(a[1] - b[1]) * y_weight


class SnakePhase(Phase):
    """A chase minigame: two snakes spawn a quarter-width apart and hunt
    each other's head across the dot grid until one catches the other,
    flashes WIN_FLASH_CYCLES times, and hands off to the ripple burst --
    which now reads as this chase's own finish, not just the next scripted
    beat.

    Rebuilt 2026-08-24, porting Title's snake-chase minigame pattern (a
    plain wandering `Snake` picks its next cell uniformly at random, so its
    net drift over a few hundred steps is a random walk's sqrt(steps) --
    reading as wobbling in place rather than a hunt). The catch/win/flash
    bookkeeping now lives in `graph_walk.ChasePair`, shared with Title's own
    SnakePhase (`title_phases.py`) -- this class only supplies what's
    specific to this grid: `_chase_distance`'s milder axis weighting (this
    grid is wide but far more square than Title's 256x8 strip) and the
    quarter-width spawn rule sized to 83 columns instead of 256. See
    PLAN.md's "Future framework polish" for the porting history."""

    STEP_INTERVAL = 0.025
    MAX_LENGTH = 28
    MAX_STEPS = 900
    CHASE_CHANCE = 0.65
    X_WEIGHT = 2.0
    Y_WEIGHT = 1.0
    WIN_FLASH_INTERVAL = 0.12
    WIN_FLASH_CYCLES = 5

    def reset(self) -> None:
        cols, rows = self.display.cols, self.display.ROWS
        graph = dot_grid_adjacency(cols, rows)

        def distance(a: tuple[int, int], b: tuple[int, int]) -> float:
            return _chase_distance(a, b, self.X_WEIGHT, self.Y_WEIGHT)

        left_start = (self.rng.randrange(0, cols // 4), self.rng.randrange(rows))
        right_start = (self.rng.randrange(3 * cols // 4, cols), self.rng.randrange(rows))
        self._pair = ChasePair(
            graph, left_start, right_start, self.MAX_LENGTH, self.rng, distance, self.CHASE_CHANCE,
            self.MAX_STEPS, self.WIN_FLASH_CYCLES,
        )
        self._step_ticker = Ticker(self.STEP_INTERVAL)
        self._flash_ticker = Ticker(self.WIN_FLASH_INTERVAL)

    def update(self, dt: float) -> bool:
        if not self._pair.resolved:
            for _ in range(self._step_ticker.advance(dt)):
                self._pair.step()
                if self._pair.resolved:
                    break
            return False
        for _ in range(self._flash_ticker.advance(dt)):
            self._pair.flash_tick()
            if self._pair.finished:
                break
        return self._pair.finished

    def draw(self, surface: pygame.Surface) -> None:
        self.display.render_raw(surface, self._pair.lit_cells())


class RipplePhase(Phase):
    """Fireworks: picks a random dot, then bursts outward from it using
    framework/graph_walk.py's Burst -- rings of dots ignite outward (capped
    at MAX_RING, generous given how much room this grid has) at a
    randomized peak brightness that fades individually, plus a scatter of
    SPARK_COUNT extra dots beyond the clean ring shape, so it reads as a
    firework's particles rather than a uniform expanding disc. Repeats from
    a new random dot REPEATS times before moving on. The dot-grid
    counterpart of LED's segment firework explosion, though LED's own
    ExplosionPhase doesn't use Burst (or vary brightness) yet.

    Tuned up on request (2026-08-24): more particles, a bigger radius given
    how much more room this grid has than LED's, and varying brightness
    instead of a flat lit/unlit ring."""

    REPEATS = 6
    RING_INTERVAL = 0.015
    MAX_RING = 24
    SPARK_COUNT = 24
    FADE_DURATION = 0.5

    def reset(self) -> None:
        self._graph = dot_grid_adjacency(self.display.cols, self.display.ROWS)
        self._repeat_index = 0
        self._start_new_burst()

    def _start_new_burst(self) -> None:
        start = (self.rng.randrange(self.display.cols), self.rng.randrange(self.display.ROWS))
        self._burst = Burst(self._graph, start, self.MAX_RING, self.FADE_DURATION, self.SPARK_COUNT, self.rng)
        self._ticker = Ticker(self.RING_INTERVAL)

    def update(self, dt: float) -> bool:
        self._burst.age(dt)
        if self._burst.is_expanding:
            for _ in range(self._ticker.advance(dt)):
                self._burst.expand_next_ring()
                if not self._burst.is_expanding:
                    break
            return False
        self._burst.add_sparks()
        if self._burst.burned_out:
            self._repeat_index += 1
            if self._repeat_index >= self.REPEATS:
                return True
            self._start_new_burst()
        return False

    def draw(self, surface: pygame.Surface) -> None:
        self.display.render_raw(surface, self._burst.intensities())


class WordsPhase(Phase):
    """Holds a short message, centred, before the script loops back to
    power-up. Digits only (see led_grid.DOT_FONT's limitation), so this
    reuses LED's own "1991" credit rather than a different string -- an
    assumption flagged for Bruce to confirm or change, not a known fact
    about LED II specifically."""

    TEXT = "1991"
    HOLD_DURATION = 2.5

    def reset(self) -> None:
        self._elapsed = 0.0
        n = self.display.char_count
        pad_left = (n - len(self.TEXT)) // 2
        self._text = self.TEXT.rjust(pad_left + len(self.TEXT)).ljust(n)

    def update(self, dt: float) -> bool:
        self._elapsed += dt
        return self._elapsed >= self.HOLD_DURATION

    def draw(self, surface: pygame.Surface) -> None:
        self.display.render(surface, self._text)
