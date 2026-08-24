"""Title's script: an ordered sequence of phases that runs on a loop,
mirroring LED and LED II's five-beat structure (power-up, main content,
snake, fireworks, credit hold) -- confirmed with Bruce (2026-08-24), same
as LED II's script was, since Title had no such spec of its own either.

Every phase drives both of Title's colour strips together (see
title.py's TitleDisplays) rather than one display each, since Title's
script is one script over two strips, not two independent scripts. Where a
phase needs to light individual cells rather than render a byte value
(power-up flicker, snake, fireworks), it addresses (col, bit) cells
directly through BitColumnDisplay.render_raw and framework/graph_walk.py's
Snake/Burst over led_grid.dot_grid_adjacency(width, ROWS) -- the same
primitives LED II's phases use, over a bit grid instead of a dot grid (see
led_grid.py's BitColumnDisplay docstring for why that graph function is
reused rather than duplicated). Only ScrollPhase (the main content) uses
render_values, the byte-value-driven API those cells were built from.

Every phase's specific timings and sizes are judgement calls tuned for this
display's shape (256 columns x 8 rows per strip -- much wider and shallower
than LED II's 83x9 grid), not reused verbatim from LED II's constants;
they're all named class constants, same convention as led_phases.py and
led_ii_phases.py.
"""

from __future__ import annotations

import pygame

from retrodemos.framework.graph_walk import Burst, Snake
from retrodemos.framework.led_grid import dot_grid_adjacency
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


class SnakePhase(Phase):
    """A snake crawls each strip's bit grid independently (same graph
    topology, two separate Snake instances so the two strips don't mirror
    each other): grows to 45 cells, then keeps moving at that length. Sized
    up from LED II's 35 given this grid is wider still (256 vs 83
    columns), though much shallower (8 rows vs 9)."""

    STEP_INTERVAL = 0.012
    MAX_LENGTH = 45
    STEPS = 260

    def reset(self) -> None:
        graph = dot_grid_adjacency(self.display.width, self.display.red_green.ROWS)
        self._red_green_snake = Snake(graph, self.rng.choice(list(graph.keys())), self.MAX_LENGTH, self.rng)
        self._blue_cyan_snake = Snake(graph, self.rng.choice(list(graph.keys())), self.MAX_LENGTH, self.rng)
        self._ticker = Ticker(self.STEP_INTERVAL)
        self._steps_taken = 0

    def update(self, dt: float) -> bool:
        for _ in range(self._ticker.advance(dt)):
            self._red_green_snake.advance()
            self._blue_cyan_snake.advance()
            self._steps_taken += 1
        return self._steps_taken >= self.STEPS

    def draw(self, surface: pygame.Surface) -> None:
        self.display.render_raw(surface, set(self._red_green_snake.body), set(self._blue_cyan_snake.body))


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
    power-up. LED and LED II hold "1991" via their own font; Title has no
    font (a BitColumnDisplay column is a byte value, not a glyph cell), so
    it encodes the same "1991" credit as its own literal ASCII byte values
    (0x31, 0x39, 0x39, 0x31) in four centred columns, every other column
    at value 0 (blank) -- the same composition WordsPhase's siblings use
    (a short credit centred on an otherwise blank field), expressed in
    Title's own vocabulary of bytes rather than borrowing a font it
    doesn't have."""

    TEXT_BYTES = [ord(c) for c in "1991"]
    HOLD_DURATION = 2.5

    def reset(self) -> None:
        self._elapsed = 0.0
        width = self.display.width
        values = [0] * width
        start = (width - len(self.TEXT_BYTES)) // 2
        for i, byte in enumerate(self.TEXT_BYTES):
            values[start + i] = byte
        self._values = values

    def update(self, dt: float) -> bool:
        self._elapsed += dt
        return self._elapsed >= self.HOLD_DURATION

    def draw(self, surface: pygame.Surface) -> None:
        self.display.render_values(surface, self._values, self._values)
