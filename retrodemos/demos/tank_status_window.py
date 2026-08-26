"""Tank Status Window: an automated attract loop that recreates
`images/WIN1.png` -- a red/black-framed window with an 83x84 red/black
dot-matrix grid, a smaller 83x9 status strip, and a row of 11 blank grey
buttons -- and plays a looping, scripted single-player COMBAT-style round
inside the big grid. See `docs/tank-status-window.md` for the demo
overview, `tank_status_window_grid.py` for the chrome/dot-grid renderer
and every measured constant, and `tank_status_window_phases.py` for the
three-phase script (patrol, engage, reset) that drives it.

`WIN1.png`'s own grid shows every dot lit -- a test pattern, not a
captured game frame -- so nothing about which dots are lit, or what a
"game" here even looks like, came from the source; see
`tank_status_window_phases.py`'s module docstring for what's invented and
why it's scripted/looping rather than a real simulation (the spec's own
open question, resolved in favour of the cheaper option).

Uses `Phase`/`PhaseSequence` like LED/LED II/Title/Bruce's 21: the spec
describes an automated game "playing itself" as a loop, which reads
naturally as a small script (patrol -> engage -> reset) rather than one
continuous behaviour.
"""

from __future__ import annotations

import random

import pygame

from retrodemos.demos.tank_status_window_grid import NATIVE_SIZE, TankDisplay
from retrodemos.demos.tank_status_window_phases import EngagePhase, PatrolPhase, ResetPhase
from retrodemos.framework.demo import Demo
from retrodemos.framework.phase import PhaseSequence


class TankStatusWindowDemo(Demo):
    NATIVE_SIZE = NATIVE_SIZE

    def __init__(self, *, text: str | None = None, **_ignored) -> None:
        self._display = TankDisplay()
        self._rng = random.Random()
        self._sequence = PhaseSequence([
            PatrolPhase(self._display, self._rng),
            EngagePhase(self._display, self._rng),
            ResetPhase(self._display, self._rng),
        ])

    def reset(self) -> None:
        self._sequence.reset()

    def update(self, dt: float) -> None:
        self._sequence.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        self._sequence.draw(surface)


DEMO_CLASS = TankStatusWindowDemo
