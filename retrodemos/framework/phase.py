"""A single stage of a scripted, looping sequence.

Most demos are a single continuous behaviour, but some (LED's power-up ->
numbers -> snake -> explosion -> words script is the first example) are
better described as an ordered list of stages that runs on a loop. Phase is
the shared unit for that second kind: update() returns True once the stage
is finished, and the demo driving the sequence advances to the next Phase
and calls its reset() right before running it -- including the very first
run, and every time the whole script loops back to the start.

`display` is whatever shared render target/context the phases in one
sequence draw onto (a SevenSegmentDisplay for LED, a dot-matrix grid for a
future demo, etc.); Phase itself doesn't care what it is, only that every
phase in a sequence agrees on it.

See retrodemos/demos/led_phases.py for a worked example, and led.py for how
a demo sequences a list of Phases.
"""

from __future__ import annotations

import random
from typing import Any

import pygame


class Phase:
    def __init__(self, display: Any, rng: random.Random) -> None:
        self.display = display
        self.rng = rng
        self.reset()

    def reset(self) -> None:
        pass

    def update(self, dt: float) -> bool:
        raise NotImplementedError

    def draw(self, surface: pygame.Surface) -> None:
        raise NotImplementedError
