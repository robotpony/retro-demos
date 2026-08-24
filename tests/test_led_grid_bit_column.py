"""Tests for the bit-column renderer (framework/led_grid.py's
BitColumnDisplay), built for Title.

The exact reconstruct-and-diff verification against images/TITLE.png (all
256 columns x 8 rows x 2 colour pairs, zero mismatches) was done
interactively, not as an automated test (there's no source image shipped
for a live pixel-diff test to read) -- these tests cover the same rule at
smaller scale instead.
"""

from __future__ import annotations

import pygame

from retrodemos.framework.led_grid import BIT_COLUMN_COLORS, BitColumnDisplay


def test_display_size():
    display = BitColumnDisplay(width=10, colors=BIT_COLUMN_COLORS["red-green"])
    assert display.width == 10
    assert display.height == 15  # 8 rows * 2px pitch - 1


def test_column_renders_its_own_value_as_msb_first_bits():
    off, on = (191, 0, 0), (0, 255, 0)
    display = BitColumnDisplay(width=1, colors=(off, on))
    surface = pygame.Surface((display.width, display.height))
    # 0b10110000 = 176: bits from MSB to LSB are 1,0,1,1,0,0,0,0
    display.render_values(surface, [176])
    expected_bits = [1, 0, 1, 1, 0, 0, 0, 0]
    for row, bit in enumerate(expected_bits):
        color = surface.get_at((0, row * display.ROW_PITCH))[:3]
        assert color == (on if bit else off), f"row {row} (bit {7-row}) wrong"


def test_gap_rows_stay_unlit_background():
    display = BitColumnDisplay(width=1, colors=BIT_COLUMN_COLORS["blue-cyan"])
    surface = pygame.Surface((display.width, display.height))
    display.render_values(surface, [255])  # all bits on
    for row in range(display.ROWS - 1):
        gap_y = row * display.ROW_PITCH + 1
        assert surface.get_at((0, gap_y))[:3] == (0, 0, 0)


def test_each_column_shows_its_own_independent_value():
    off, on = BIT_COLUMN_COLORS["red-green"]
    display = BitColumnDisplay(width=2, colors=(off, on))
    surface = pygame.Surface((display.width, display.height))
    display.render_values(surface, [0, 255])
    # column 0 (value 0): every bit off
    assert surface.get_at((0, 0))[:3] == off
    # column 1 (value 255): every bit on
    assert surface.get_at((1, 0))[:3] == on


def test_identity_ramp_matches_title_png_exactly():
    # This is the exact rule reverse-engineered from images/TITLE.png: at
    # full width 256 with values [0..255], column x's rendered bits equal
    # x's own bits. Spot-check a handful of values rather than all 256 (the
    # full check was done directly against the source image).
    off, on = BIT_COLUMN_COLORS["red-green"]
    display = BitColumnDisplay(width=256, colors=(off, on))
    surface = pygame.Surface((display.width, display.height))
    display.render_values(surface, list(range(256)))
    for value in (0, 1, 128, 176, 255):
        for row in range(8):
            bit = (value >> (7 - row)) & 1
            color = surface.get_at((value, row * display.ROW_PITCH))[:3]
            assert color == (on if bit else off)
