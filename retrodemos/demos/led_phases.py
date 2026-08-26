"""The LED demo's script: an ordered sequence of phases that runs on a loop.

Choreography specified by Bruce (2026-08-24): power-up (flicker like a loose
connection, then a synchronized ring sweep that speeds up), scrolling
numbers, a segment "snake" that grows then wanders, a firework-style
explosion repeated 5 times, then a held "1991" credit -- then the whole
thing loops. See docs/led.md and PLAN.md for the demo overview.

Every phase's specific timings (tick durations, ring/snake sizes, hold
lengths) are judgement calls filling in what wasn't pinned down in the
spec; they're all named constants at the top of each class so they're easy
to retune without touching the choreography logic.
"""

from __future__ import annotations

import random

import pygame

from retrodemos.framework.graph_walk import Burst, Snake
from retrodemos.framework.led_grid import DIGIT_SEGMENTS, RING_ORDER, scroll_window, segment_adjacency
from retrodemos.framework.phase import Phase
from retrodemos.framework.ticker import Ticker


class PowerUpPhase(Phase):
    """All segments (and dots) flash on/off at random, like a loose
    connection; then a synchronized ring sweep around each digit's 6 outer
    segments (a-b-c-d-e-f, excluding the middle g) that speeds up over 3
    laps; then a brief blank hold before the numbers phase starts."""

    FLICKER_TICKS = 18
    FLICKER_TICK_DURATION = 0.08
    FLICKER_PROBABILITY = 0.55

    SWEEP_LAPS = 3
    SWEEP_START_TICK_DURATION = 0.12
    SWEEP_END_TICK_DURATION = 0.03

    BLANK_HOLD = 0.4

    def reset(self) -> None:
        self._stage = "flicker"
        self._ticker = Ticker(self.FLICKER_TICK_DURATION)
        self._blank_elapsed = 0.0
        self._flicker_tick_count = 0
        self._flicker_segments: dict[int, set[str]] = {}
        self._flicker_dots: set[int] = set()
        self._sweep_step = 0
        self._sweep_total_steps = self.SWEEP_LAPS * len(RING_ORDER)

    def _randomize_flicker(self) -> None:
        n = self.display.digit_count
        self._flicker_segments = {
            i: {s for s in DIGIT_SEGMENTS["8"] if self.rng.random() < self.FLICKER_PROBABILITY}
            for i in range(n)
        }
        self._flicker_dots = {i for i in range(n) if self.rng.random() < self.FLICKER_PROBABILITY}

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
            # Sweep speeds up over its 3 laps, so the ticker's interval is
            # updated before each poll (see Ticker.advance's docstring).
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
            self.display.render_raw(surface, self._flicker_segments, self._flicker_dots)
        elif self._stage == "sweep":
            current_segment = RING_ORDER[self._sweep_step % len(RING_ORDER)]
            lit = {i: {current_segment} for i in range(self.display.digit_count)}
            self.display.render_raw(surface, lit)
        else:
            self.display.render_raw(surface)


class NumbersPhase(Phase):
    """Scrolls a message (default "0123456789") across the display, looping
    for a couple of passes before handing off to the next phase."""

    DEFAULT_TEXT = "0123456789"
    # Playtesting (2026-08-26): first "speed up number scroll, 50% faster"
    # (0.4/1.5), then "still scrolls too slowly" on a second pass -- this
    # is a further, bigger jump rather than another incremental percentage.
    SCROLL_INTERVAL = 0.4 / 3.5
    LAPS = 2

    def __init__(self, display, rng: random.Random, text: str | None = None) -> None:
        self.text = text or self.DEFAULT_TEXT
        super().__init__(display, rng)

    def reset(self) -> None:
        self._ticker = Ticker(self.SCROLL_INTERVAL)
        self._offset = 0
        self._steps = 0
        self._loop_text = self.text + " " * self.display.digit_count
        self._total_steps = self.LAPS * len(self._loop_text)

    def update(self, dt: float) -> bool:
        for _ in range(self._ticker.advance(dt)):
            self._offset = (self._offset + 1) % len(self._loop_text)
            self._steps += 1
        return self._steps >= self._total_steps

    def draw(self, surface: pygame.Surface) -> None:
        window = scroll_window(self._loop_text, self._offset, self.display.digit_count)
        self.display.render(surface, window)


def _horizontal_bias(current: tuple[int, str], candidate: tuple[int, str]) -> float:
    """Weight a candidate step higher when it crosses into a different
    digit cell than the snake's current head -- playtesting (2026-08-26:
    "moving horizontally more") wanted the crawl to drift across the
    display rather than loop within one digit's own 7 segments."""
    return 4.0 if candidate[0] != current[0] else 1.0


class SnakePhase(Phase):
    """A snake crawls the segment-adjacency graph: starts as 1 lit segment,
    grows by one each step until it's MAX_LENGTH long, then keeps moving
    at that length, reshaping as it goes. Weighted toward crossing digits
    (see `_horizontal_bias`) rather than a uniform random walk."""

    STEP_INTERVAL = 0.12
    MAX_LENGTH = 9  # playtesting (2026-08-26): "grow longer by at least a few segments" -- was 5
    STEPS = 100  # scaled up with MAX_LENGTH so the wander phase still gets a real stretch after growing

    def reset(self) -> None:
        graph = segment_adjacency(self.display.digit_count)
        start = self.rng.choice(list(graph.keys()))
        self._snake = Snake(graph, start, self.MAX_LENGTH, self.rng, weight_fn=_horizontal_bias)
        self._ticker = Ticker(self.STEP_INTERVAL)
        self._steps_taken = 0

    def update(self, dt: float) -> bool:
        for _ in range(self._ticker.advance(dt)):
            self._snake.advance()
            self._steps_taken += 1
        return self._steps_taken >= self.STEPS

    def draw(self, surface: pygame.Surface) -> None:
        lit: dict[int, set[str]] = {}
        for digit_i, seg in self._snake.body:
            lit.setdefault(digit_i, set()).add(seg)
        self.display.render_raw(surface, lit)


class ExplosionPhase(Phase):
    """A firework: picks a random digit, then radiates outward from its
    centre via `graph_walk.Burst` (ring-by-ring ignition, then a scatter
    of extra sparks, each node fading independently), and repeats from a
    new random digit REPEATS times before moving on.

    Rebuilt 2026-08-26 on `Burst` -- it used to hand-roll the same ring
    expansion (`bfs_rings`) with one flat, all-or-nothing fade instead of
    real per-node brightness falloff (playtesting: "brightness falling
    off"), the adoption `graph_walk.py`'s own docstring already flagged
    as a likely future move once LED II's RipplePhase proved the class
    out. MAX_RING also grew from 3 to 6 ("explode further")."""

    REPEATS = 5
    RING_INTERVAL = 0.09
    MAX_RING = 6
    FADE_DURATION = 0.5
    SPARK_COUNT = 6

    def reset(self) -> None:
        self._graph = segment_adjacency(self.display.digit_count)
        self._repeat_index = 0
        self._start_new_burst()

    def _start_new_burst(self) -> None:
        digit_i = self.rng.randrange(self.display.digit_count)
        self._burst = Burst(
            self._graph, (digit_i, "g"), self.MAX_RING, self.FADE_DURATION, self.SPARK_COUNT, self.rng
        )
        self._burst.expand_next_ring()  # light the centre immediately, not on the first tick
        self._ticker = Ticker(self.RING_INTERVAL)

    def update(self, dt: float) -> bool:
        self._burst.age(dt)
        if self._burst.is_expanding:
            for _ in range(self._ticker.advance(dt)):
                self._burst.expand_next_ring()
        else:
            self._burst.add_sparks()
        if not self._burst.burned_out:
            return False
        self._repeat_index += 1
        if self._repeat_index >= self.REPEATS:
            return True
        self._start_new_burst()
        return False

    def draw(self, surface: pygame.Surface) -> None:
        self.display.render_raw(surface, self._burst.intensities())


class WordsPhase(Phase):
    """Holds a short message, centred, before the script loops back to power-up."""

    TEXT = "1991"
    HOLD_DURATION = 2.5

    def reset(self) -> None:
        self._elapsed = 0.0
        n = self.display.digit_count
        pad_left = (n - len(self.TEXT)) // 2
        self._text = self.TEXT.rjust(pad_left + len(self.TEXT)).ljust(n)

    def update(self, dt: float) -> bool:
        self._elapsed += dt
        return self._elapsed >= self.HOLD_DURATION

    def draw(self, surface: pygame.Surface) -> None:
        self.display.render(surface, self._text)
