"""A single stage of a scripted, looping sequence, and the sequencer that
runs a list of them.

Most demos are a single continuous behaviour, but some (LED's power-up ->
numbers -> snake -> explosion -> words script is the first example) are
better described as an ordered list of stages that runs on a loop. Phase is
the shared unit for that second kind: update() returns True once the stage
is finished, and PhaseSequence advances to the next Phase and calls its
reset() right before running it -- including the very first run, and every
time the whole script loops back to the start.

`display` is whatever shared render target/context the phases in one
sequence draw onto (a SevenSegmentDisplay for LED, a dot-matrix grid for a
future demo, etc.); Phase itself doesn't care what it is, only that every
phase in a sequence agrees on it.

See retrodemos/demos/led_phases.py for a worked example, and led.py for how
a demo builds its phase list and hands it to a PhaseSequence.
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


class PhaseSequence:
    """Runs a fixed list of Phases in order, looping back to the first once
    the last one finishes.

    A scripted-sequence demo builds its phase list once (typically in its
    own __init__) and wraps it in a PhaseSequence, then delegates its own
    update/draw/reset to it -- rather than hand-tracking a phase index the
    way LedDemo originally did. See led.py.
    """

    def __init__(self, phases: list[Phase]) -> None:
        if not phases:
            raise ValueError("PhaseSequence needs at least one phase")
        self.phases = phases
        self.reset()

    @property
    def current(self) -> Phase:
        return self.phases[self.index]

    def reset(self) -> None:
        self.index = 0
        self.phases[0].reset()

    def update(self, dt: float) -> None:
        if self.current.update(dt):
            self.index = (self.index + 1) % len(self.phases)
            self.phases[self.index].reset()

    def draw(self, surface: pygame.Surface) -> None:
        self.current.draw(surface)
