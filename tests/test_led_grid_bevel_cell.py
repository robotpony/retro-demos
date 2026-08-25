"""Tests for the bevelled-cell renderer (framework/led_grid.py's
BevelCellDisplay), built for Dooley.

The exact reconstruct-and-diff verification against images/DOOLEY1.png was
done interactively (2026-08-24), not as an automated test (same convention
as test_led_grid_bit_column.py/test_led_grid_dot_matrix.py -- there's no
source image shipped for a live pixel-diff test to read): a 33x6 grid, all
cells lit the same yellow (191,191,0), reconstructed the LED strip region
(x=4..136, y=4..28) with zero mismatches across all 3168 pixels; two 3x7
grids (one raised, one sunken, 1px gap between them) built from the
dark/dither/bright-per-hue formula in dooley_phases.py reconstructed the
full palette region (x=0..11, y=32..88) with zero mismatches across all 684
pixels.
"""

from __future__ import annotations

import pygame

from retrodemos.framework.led_grid import BEZEL_CORNER, BEZEL_DARK, BEZEL_LIGHT, BevelCellDisplay, CellFill


def test_display_size():
    display = BevelCellDisplay(cols=33, rows=6)
    assert (display.width, display.height) == (132, 24)  # 4px pitch, no gap


def test_solid_fill_lights_the_2x2_centre_with_a_raised_bevel():
    display = BevelCellDisplay(cols=1, rows=1)
    surface = pygame.Surface((display.width, display.height))
    yellow = (191, 191, 0)
    display.render_raw(surface, {(0, 0): CellFill(yellow)})
    # top/left bevel edge
    assert surface.get_at((0, 0))[:3] == BEZEL_DARK
    assert surface.get_at((1, 0))[:3] == BEZEL_DARK
    assert surface.get_at((2, 0))[:3] == BEZEL_DARK
    assert surface.get_at((3, 0))[:3] == BEZEL_CORNER
    assert surface.get_at((0, 1))[:3] == BEZEL_DARK
    # 2x2 centre, solid
    for dx in (1, 2):
        for dy in (1, 2):
            assert surface.get_at((dx, dy))[:3] == yellow
    # bottom/right bevel edge
    assert surface.get_at((3, 1))[:3] == BEZEL_LIGHT
    assert surface.get_at((0, 3))[:3] == BEZEL_CORNER
    assert surface.get_at((1, 3))[:3] == BEZEL_LIGHT
    assert surface.get_at((3, 3))[:3] == BEZEL_LIGHT


def test_dither_fill_checkerboards_primary_and_secondary_on_the_diagonals():
    display = BevelCellDisplay(cols=1, rows=1)
    surface = pygame.Surface((display.width, display.height))
    dark, bright = (191, 0, 0), (255, 0, 0)
    display.render_raw(surface, {(0, 0): CellFill(dark, bright)})
    assert surface.get_at((1, 1))[:3] == dark  # top-left: main diagonal
    assert surface.get_at((2, 2))[:3] == dark  # bottom-right: main diagonal
    assert surface.get_at((2, 1))[:3] == bright  # top-right: anti-diagonal
    assert surface.get_at((1, 2))[:3] == bright  # bottom-left: anti-diagonal


def test_blank_fill_still_draws_the_bevel_with_background_centre():
    display = BevelCellDisplay(cols=1, rows=1)
    surface = pygame.Surface((display.width, display.height))
    display.render_raw(surface, {(0, 0): CellFill()})
    assert surface.get_at((0, 0))[:3] == BEZEL_DARK  # bevel still drawn
    for dx in (1, 2):
        for dy in (1, 2):
            assert surface.get_at((dx, dy))[:3] == BEZEL_CORNER


def test_missing_cell_renders_as_an_empty_raised_bevel():
    display = BevelCellDisplay(cols=2, rows=1)
    surface = pygame.Surface((display.width, display.height))
    display.render_raw(surface, {})  # no cells specified at all
    assert surface.get_at((0, 0))[:3] == BEZEL_DARK
    assert surface.get_at((1, 1))[:3] == BEZEL_CORNER


def test_sunken_fill_swaps_the_bevel_edges():
    display = BevelCellDisplay(cols=1, rows=1)
    surface = pygame.Surface((display.width, display.height))
    display.render_raw(surface, {(0, 0): CellFill(sunken=True)})
    assert surface.get_at((0, 0))[:3] == BEZEL_LIGHT  # top/left now light
    assert surface.get_at((3, 1))[:3] == BEZEL_DARK  # bottom/right now dark


def test_cells_share_edges_with_no_gap_between_them():
    display = BevelCellDisplay(cols=2, rows=1)
    surface = pygame.Surface((display.width, display.height))
    yellow = (191, 191, 0)
    display.render_raw(surface, {(0, 0): CellFill(yellow), (1, 0): CellFill(yellow)})
    # second cell starts immediately at x=4, no gap column
    assert surface.get_at((4, 0))[:3] == BEZEL_DARK
    assert surface.get_at((5, 1))[:3] == yellow
