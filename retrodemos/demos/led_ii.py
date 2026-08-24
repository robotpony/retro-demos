"""LED II: a dot-matrix marquee display that runs a scripted sequence on a
loop -- power-up, a scrolling marquee, a dot-grid snake, a rippling burst,
then a held "1991" -- see led_ii_phases.py for each stage's choreography
and docs/led-ii.md for the demo overview.

Only digits, space, and "-" render in the marquee phase (see
led_grid.DOT_FONT); there's no dot-matrix alphabet yet, so --text is
limited to those characters until one gets built (same limitation LED's
own seven-segment font has).
"""

from __future__ import annotations

import random

import pygame

from retrodemos.demos.led_ii_phases import MarqueePhase, PowerUpPhase, RipplePhase, SnakePhase, WordsPhase
from retrodemos.framework.demo import Demo
from retrodemos.framework.led_grid import DotMatrixDisplay
from retrodemos.framework.phase import PhaseSequence

COLS = 83  # matches images/LED-II-thumb.png, which shows 83 dot columns

_probe = DotMatrixDisplay(cols=COLS)
NATIVE_SIZE = (_probe.width, _probe.height)


class LedIIDemo(Demo):
    NATIVE_SIZE = NATIVE_SIZE

    def __init__(self, *, text: str | None = None, **_ignored) -> None:
        self.display = DotMatrixDisplay(cols=COLS)
        self._rng = random.Random()
        self._sequence = PhaseSequence([
            PowerUpPhase(self.display, self._rng),
            MarqueePhase(self.display, self._rng, text=text),
            SnakePhase(self.display, self._rng),
            RipplePhase(self.display, self._rng),
            WordsPhase(self.display, self._rng),
        ])

    def reset(self) -> None:
        self._sequence.reset()

    def update(self, dt: float) -> None:
        self._sequence.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        self._sequence.draw(surface)


DEMO_CLASS = LedIIDemo
