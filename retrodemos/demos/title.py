"""Title: an LED bit-pattern demo. Runs the same scripted-sequence
structure LED and LED II do (power-up, main content, snake, fireworks,
credit hold -- see title_phases.py), rebuilt on request (2026-08-24) from
its original single-behaviour form, once Title had the same shape of script
as its siblings rather than just a continuous scroll.

Each of the two colour strips (red/green, blue/cyan) is a
led_grid.BitColumnDisplay: a column is one byte value's own 8 bits, not a
lit/unlit dot. Every phase drives both strips together through
TitleDisplays below, addressing individual (col, bit) cells directly via
BitColumnDisplay.render_raw -- "indexing them as if they were real bits" --
for the phases that don't have a byte value to render (power-up flicker,
snake, fireworks), and only the main content phase uses render_values, the
higher-level byte-per-column API those cells were built from in the first
place. See led_grid.py's BitColumnDisplay docstring and docs/title.md for
the demo overview.
"""

from __future__ import annotations

import random

import pygame

from retrodemos.demos.title_phases import FireworksPhase, PowerUpPhase, ScrollPhase, SnakePhase, WordsPhase
from retrodemos.framework.demo import Demo
from retrodemos.framework.led_grid import BIT_COLUMN_COLORS, BitColumnDisplay
from retrodemos.framework.phase import PhaseSequence

WIDTH = 256  # matches images/TITLE.png's width -- one column per byte value
STRIP_GAP = 1  # matches the 1px black gap between the two strips in the source


class TitleDisplays:
    """The pair of BitColumnDisplay strips Title's phases draw onto
    together, stacked with STRIP_GAP between them. Every Title Phase gets
    one of these as its `display` (in place of the single display
    LED/LED II's phases get), since Title's script drives both strips as
    one composed unit rather than having a phase per strip."""

    def __init__(self, width: int, gap: int = STRIP_GAP) -> None:
        self.red_green = BitColumnDisplay(width, colors=BIT_COLUMN_COLORS["red-green"])
        self.blue_cyan = BitColumnDisplay(width, colors=BIT_COLUMN_COLORS["blue-cyan"])
        self.width = width
        self.gap = gap
        self.height = self.red_green.height + gap + self.blue_cyan.height
        self._top_surface = pygame.Surface((width, self.red_green.height))
        self._bottom_surface = pygame.Surface((width, self.blue_cyan.height))

    def render_values(self, surface: pygame.Surface, red_green_values: list[int], blue_cyan_values: list[int]) -> None:
        self.red_green.render_values(self._top_surface, red_green_values)
        self.blue_cyan.render_values(self._bottom_surface, blue_cyan_values)
        self._composite(surface)

    def render_raw(self, surface: pygame.Surface, red_green_cells=None, blue_cyan_cells=None) -> None:
        self.red_green.render_raw(self._top_surface, red_green_cells)
        self.blue_cyan.render_raw(self._bottom_surface, blue_cyan_cells)
        self._composite(surface)

    def _composite(self, surface: pygame.Surface) -> None:
        surface.fill((0, 0, 0))
        surface.blit(self._top_surface, (0, 0))
        surface.blit(self._bottom_surface, (0, self.red_green.height + self.gap))


_probe = TitleDisplays(WIDTH)
NATIVE_SIZE = (_probe.width, _probe.height)


class TitleDemo(Demo):
    NATIVE_SIZE = NATIVE_SIZE

    def __init__(self, **_ignored) -> None:
        self.display = TitleDisplays(WIDTH)
        self._rng = random.Random()
        self._sequence = PhaseSequence([
            PowerUpPhase(self.display, self._rng),
            ScrollPhase(self.display, self._rng),
            SnakePhase(self.display, self._rng),
            FireworksPhase(self.display, self._rng),
            WordsPhase(self.display, self._rng),
        ])

    def reset(self) -> None:
        self._sequence.reset()

    def update(self, dt: float) -> None:
        self._sequence.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        self._sequence.draw(surface)


DEMO_CLASS = TitleDemo
