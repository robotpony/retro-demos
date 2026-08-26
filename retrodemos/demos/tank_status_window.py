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

Opens chromeless on the desktop shell (`desktop.py`'s `_CHROMELESS`,
2026-08-26): this demo's own `draw()` already produces WIN1.png's
complete red/black window frame, so wrapping it in the desktop's generic
window chrome nested one frame inside another -- caught in playtesting,
the same "window inside a window" bug CD Player's own two windows hit
first. `WIN1.png` has no close control of its own (only the minimize and
dropdown boxes), so the minimize box doubles as this demo's close
control when opened from the desktop -- `close_rect` and `closed` follow
the same convention `cd_player.py`'s own chromeless windows use. Confirmed
2026-08-26 playtesting: this was already working, not a new fix.

The same playtesting round added `_ButtonRowAnimator`: an ambient,
non-functional press animation for the bottom button row (which also
gained its own invented icons -- see `tank_status_window_grid.py`'s
`_BUTTON_ICONS`), owned by the demo itself rather than any one phase so
it keeps animating across phase transitions.
"""

from __future__ import annotations

import random

import pygame

from retrodemos.demos.tank_status_window_grid import BUTTON_COUNT, MIN_BOX_RECT, NATIVE_SIZE, TankDisplay
from retrodemos.demos.tank_status_window_phases import EngagePhase, PatrolPhase, ResetPhase
from retrodemos.framework.demo import Demo
from retrodemos.framework.phase import PhaseSequence


class _ButtonRowAnimator:
    """Ambient, non-functional press animation for the bottom button row
    (2026-08-26 playtesting: the buttons "should be pressable, but
    ultimately do nothing other than animate"): picks a random button,
    holds it "pressed" for PRESS_DURATION, waits a random gap, then picks
    another. Owned by the demo itself rather than any one phase so it
    keeps animating uninterrupted across phase transitions -- unlike the
    tanks/status text, which each phase reseeds on its own reset()."""

    PRESS_DURATION = 0.15
    GAP_RANGE = (0.4, 1.6)

    def __init__(self, rng: random.Random) -> None:
        self.rng = rng
        self.pressed_index: int | None = None
        self._elapsed = 0.0
        self._target = self.rng.uniform(*self.GAP_RANGE)

    def update(self, dt: float) -> None:
        self._elapsed += dt
        if self._elapsed < self._target:
            return
        self._elapsed = 0.0
        if self.pressed_index is None:
            self.pressed_index = self.rng.randrange(BUTTON_COUNT)
            self._target = self.PRESS_DURATION
        else:
            self.pressed_index = None
            self._target = self.rng.uniform(*self.GAP_RANGE)


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
        self._buttons = _ButtonRowAnimator(self._rng)
        self.close_rect = pygame.Rect(*MIN_BOX_RECT)
        self.closed = False

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.close_rect.collidepoint(event.pos):
            self.closed = True

    def reset(self) -> None:
        self._sequence.reset()

    def update(self, dt: float) -> None:
        self._sequence.update(dt)
        self._buttons.update(dt)
        self._display.pressed_button = self._buttons.pressed_index

    def draw(self, surface: pygame.Surface) -> None:
        self._sequence.draw(surface)


DEMO_CLASS = TankStatusWindowDemo
