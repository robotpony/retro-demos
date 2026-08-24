"""LED: a single-row seven-segment digit display that runs a scripted
sequence on a loop -- power-up, scrolling numbers, a segment snake, a
firework explosion, then a held "1991" -- see led_phases.py for each
stage's choreography and docs/led.md for the demo overview.

Only digits, space, and "-" render in the numbers phase (see
led_grid.DIGIT_SEGMENTS); there's no seven-segment alphabet yet, so --text
is limited to those characters until one gets built.
"""

from __future__ import annotations

import random

import pygame

from retrodemos.demos.led_phases import ExplosionPhase, NumbersPhase, PowerUpPhase, SnakePhase, WordsPhase
from retrodemos.framework.demo import Demo
from retrodemos.framework.led_grid import SevenSegmentDisplay
from retrodemos.framework.phase import PhaseSequence

DIGIT_COUNT = 11  # matches images/LED-thumb.png, which shows 11 digit cells

_probe = SevenSegmentDisplay(DIGIT_COUNT)
NATIVE_SIZE = (_probe.width, _probe.height)


class LedDemo(Demo):
    NATIVE_SIZE = NATIVE_SIZE

    def __init__(self, *, text: str | None = None, **_ignored) -> None:
        self.display = SevenSegmentDisplay(DIGIT_COUNT)
        self._rng = random.Random()
        self._sequence = PhaseSequence([
            PowerUpPhase(self.display, self._rng),
            NumbersPhase(self.display, self._rng, text=text),
            SnakePhase(self.display, self._rng),
            ExplosionPhase(self.display, self._rng),
            WordsPhase(self.display, self._rng),
        ])

    def reset(self) -> None:
        self._sequence.reset()

    def update(self, dt: float) -> None:
        self._sequence.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        self._sequence.draw(surface)


DEMO_CLASS = LedDemo
