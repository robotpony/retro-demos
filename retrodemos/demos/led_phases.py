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
from collections import deque

import pygame

from retrodemos.framework.led_grid import DIGIT_SEGMENTS, RING_ORDER, SevenSegmentDisplay, segment_adjacency


class Phase:
    """One stage of the script. update() returns True once finished; the
    sequencer (LedDemo) calls reset() right before a phase's first run and
    every time it's about to run again, since the whole script loops."""

    def __init__(self, display: SevenSegmentDisplay, rng: random.Random) -> None:
        self.display = display
        self.rng = rng
        self.reset()

    def reset(self) -> None:
        pass

    def update(self, dt: float) -> bool:
        raise NotImplementedError

    def draw(self, surface: pygame.Surface) -> None:
        raise NotImplementedError


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
        self._timer = 0.0
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

    def update(self, dt: float) -> bool:
        self._timer += dt
        if self._stage == "flicker":
            if self._timer >= self.FLICKER_TICK_DURATION:
                self._timer = 0.0
                self._randomize_flicker()
                self._flicker_tick_count += 1
                if self._flicker_tick_count >= self.FLICKER_TICKS:
                    self._stage = "sweep"
            return False
        if self._stage == "sweep":
            progress = self._sweep_step / self._sweep_total_steps
            tick_duration = self.SWEEP_START_TICK_DURATION + (
                self.SWEEP_END_TICK_DURATION - self.SWEEP_START_TICK_DURATION
            ) * progress
            if self._timer >= tick_duration:
                self._timer = 0.0
                self._sweep_step += 1
                if self._sweep_step >= self._sweep_total_steps:
                    self._stage = "blank"
            return False
        return self._timer >= self.BLANK_HOLD  # stage == "blank"

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
    SCROLL_INTERVAL = 0.4
    LAPS = 2

    def __init__(self, display: SevenSegmentDisplay, rng: random.Random, text: str | None = None) -> None:
        self.text = text or self.DEFAULT_TEXT
        super().__init__(display, rng)

    def reset(self) -> None:
        self._elapsed = 0.0
        self._offset = 0
        self._steps = 0
        self._loop_text = self.text + " " * self.display.digit_count
        self._total_steps = self.LAPS * len(self._loop_text)

    def update(self, dt: float) -> bool:
        self._elapsed += dt
        while self._elapsed >= self.SCROLL_INTERVAL:
            self._elapsed -= self.SCROLL_INTERVAL
            self._offset = (self._offset + 1) % len(self._loop_text)
            self._steps += 1
        return self._steps >= self._total_steps

    def draw(self, surface: pygame.Surface) -> None:
        loop = self._loop_text
        window = (loop[self._offset :] + loop)[: self.display.digit_count]
        self.display.render(surface, window)


class SnakePhase(Phase):
    """A snake crawls the segment-adjacency graph: starts as 1 lit segment,
    grows by one each step until it's 5 long, then keeps moving at that
    length, reshaping as it goes."""

    STEP_INTERVAL = 0.12
    MAX_LENGTH = 5
    STEPS = 60

    def reset(self) -> None:
        self._graph = segment_adjacency(self.display.digit_count)
        start = self.rng.choice(list(self._graph.keys()))
        self._body: list[tuple[int, str]] = [start]
        self._elapsed = 0.0
        self._steps_taken = 0

    def update(self, dt: float) -> bool:
        self._elapsed += dt
        while self._elapsed >= self.STEP_INTERVAL:
            self._elapsed -= self.STEP_INTERVAL
            self._advance()
            self._steps_taken += 1
        return self._steps_taken >= self.STEPS

    def _advance(self) -> None:
        head = self._body[0]
        neighbours = list(self._graph[head])
        previous = self._body[1] if len(self._body) > 1 else None
        candidates = [n for n in neighbours if n != previous] or neighbours
        self._body.insert(0, self.rng.choice(candidates))
        if len(self._body) > self.MAX_LENGTH:
            self._body.pop()

    def draw(self, surface: pygame.Surface) -> None:
        lit: dict[int, set[str]] = {}
        for digit_i, seg in self._body:
            lit.setdefault(digit_i, set()).add(seg)
        self.display.render_raw(surface, lit)


class ExplosionPhase(Phase):
    """A firework: picks a random digit, then lights up segments radiating
    outward from its centre (ring by ring, through the adjacency graph,
    capped at MAX_RING so a burst stays local), fades to black, and repeats
    from a new random digit REPEATS times before moving on."""

    REPEATS = 5
    RING_INTERVAL = 0.09
    MAX_RING = 3
    FADE_HOLD = 0.15

    def reset(self) -> None:
        self._graph = segment_adjacency(self.display.digit_count)
        self._repeat_index = 0
        self._start_new_burst()

    def _start_new_burst(self) -> None:
        digit_i = self.rng.randrange(self.display.digit_count)
        self._rings = self._bfs_rings((digit_i, "g"))
        self._current_ring = 0
        self._elapsed = 0.0
        self._stage = "expand"

    def _bfs_rings(self, start: tuple[int, str]) -> list[list[tuple[int, str]]]:
        visited = {start: 0}
        queue = deque([start])
        rings: list[list[tuple[int, str]]] = [[start]]
        while queue:
            node = queue.popleft()
            dist = visited[node]
            if dist >= self.MAX_RING:
                continue
            for neighbour in self._graph.get(node, ()):
                if neighbour not in visited:
                    visited[neighbour] = dist + 1
                    queue.append(neighbour)
                    while len(rings) <= dist + 1:
                        rings.append([])
                    rings[dist + 1].append(neighbour)
        return rings

    def update(self, dt: float) -> bool:
        self._elapsed += dt
        if self._stage == "expand":
            if self._elapsed >= self.RING_INTERVAL:
                self._elapsed = 0.0
                self._current_ring += 1
                if self._current_ring >= len(self._rings):
                    self._stage = "fade"
            return False
        # stage == "fade"
        if self._elapsed >= self.FADE_HOLD:
            self._repeat_index += 1
            if self._repeat_index >= self.REPEATS:
                return True
            self._start_new_burst()
        return False

    def draw(self, surface: pygame.Surface) -> None:
        lit: dict[int, set[str]] = {}
        if self._stage == "expand":
            for ring in self._rings[: self._current_ring + 1]:
                for digit_i, seg in ring:
                    lit.setdefault(digit_i, set()).add(seg)
        self.display.render_raw(surface, lit)


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
