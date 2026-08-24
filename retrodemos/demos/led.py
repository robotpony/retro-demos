"""LED: a single-row seven-segment digit display. See docs/led.md.

Only digits, space, and "-" render (see led_grid.DIGIT_SEGMENTS); there's no
seven-segment alphabet yet, so --text is limited to those characters until
one gets built.
"""

from __future__ import annotations

import pygame

from retrodemos.framework.demo import Demo
from retrodemos.framework.led_grid import SevenSegmentDisplay

DIGIT_COUNT = 8
DEFAULT_TEXT = "0123456789"
SCROLL_INTERVAL = 0.4  # seconds per character step

_probe = SevenSegmentDisplay(DIGIT_COUNT)
NATIVE_SIZE = (_probe.width, _probe.height)


class LedDemo(Demo):
    NATIVE_SIZE = NATIVE_SIZE

    def __init__(self, *, text: str | None = None, **_ignored) -> None:
        self.display = SevenSegmentDisplay(DIGIT_COUNT)
        self.message = text if text else DEFAULT_TEXT
        self.reset()

    def reset(self) -> None:
        self._elapsed = 0.0
        self._offset = 0

    def update(self, dt: float) -> None:
        self._elapsed += dt
        loop = self._loop_text()
        while self._elapsed >= SCROLL_INTERVAL:
            self._elapsed -= SCROLL_INTERVAL
            self._offset = (self._offset + 1) % len(loop)

    def _loop_text(self) -> str:
        # A full window of blanks between repeats so the scroll reads as one
        # message passing by, not the end and the restart mashed together.
        return self.message + " " * DIGIT_COUNT

    def draw(self, surface: pygame.Surface) -> None:
        loop = self._loop_text()
        window = (loop[self._offset:] + loop)[:DIGIT_COUNT]
        self.display.render(surface, window)


DEMO_CLASS = LedDemo
