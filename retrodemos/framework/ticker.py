"""Fixed-interval tick accumulator, for any Phase (or other update loop)
that needs to advance in discrete steps rather than continuously.

Handles a variable dt uniformly: advance() accumulates dt and returns how
many whole ticks have elapsed since the last call, carrying the remainder
forward so a slow frame catches up instead of losing time. Before this
existed, LED's phases (led_phases.py) each hand-rolled this, and did so
inconsistently: some used a `while` loop and caught up correctly, others
used a plain `if` and silently dropped ticks on a slow frame -- harmless at
a steady 60fps, but a real (if untested) desync risk the moment a frame
spikes.
"""

from __future__ import annotations


class Ticker:
    def __init__(self, interval: float) -> None:
        self.interval = interval
        self._elapsed = 0.0

    def reset(self) -> None:
        self._elapsed = 0.0

    def advance(self, dt: float) -> int:
        """Accumulate dt and return how many whole ticks fired this call.

        `interval` may be changed between calls -- it's read fresh on every
        iteration of the catch-up loop -- to support a smoothly varying
        tick rate, e.g. PowerUpPhase's accelerating sweep.
        """
        self._elapsed += dt
        ticks = 0
        while self._elapsed >= self.interval:
            self._elapsed -= self.interval
            ticks += 1
        return ticks
