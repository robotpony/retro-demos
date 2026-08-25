"""Tests for the Dooley demo. led_grid.py's BevelCellDisplay is covered
separately in tests/test_led_grid_bevel_cell.py; this file covers
dooley.py's content generation and the demo's continuous update/draw loop
(no Phase/PhaseSequence -- see dooley.py's module docstring for why)."""

from __future__ import annotations

import pygame

from retrodemos.demos.dooley import (
    DEFAULT_TEXT,
    PALETTE_HUES,
    STRIP_COLS,
    STRIP_GAP,
    STRIP_ROWS,
    DooleyDemo,
    _palette_row_cells,
    _text_dots,
)


def test_dooley_demo_native_size_matches_the_source_image():
    demo = DooleyDemo()
    # images/DOOLEY1.png is 256x128.
    assert demo.NATIVE_SIZE == (256, 128)


def test_dooley_demo_runs_for_many_frames_without_raising():
    demo = DooleyDemo()
    surface = pygame.Surface(demo.NATIVE_SIZE)
    for _ in range(500):
        demo.update(0.05)
        demo.draw(surface)


def test_dooley_demo_reset_returns_to_the_start_of_the_scroll():
    demo = DooleyDemo()
    for _ in range(50):
        demo.update(0.05)
    assert demo._scroll_offset != 0
    demo.reset()
    assert demo._scroll_offset == 0
    assert demo._palette_offset == 0
    assert demo._active_spinner == 0


def test_dooley_demo_accepts_a_text_override():
    demo = DooleyDemo(text="42")
    assert demo._text == "42"


def test_default_text_is_the_digit_sequence():
    assert DEFAULT_TEXT == "0123456789"


def test_text_dots_spells_the_digits_readably():
    by_col, width = _text_dots("07" + STRIP_GAP)
    grid = ["".join("#" if row in by_col.get(c, set()) else "." for c in range(width)) for row in range(5)]
    # "0" is a closed loop, "7" is a top bar + a falling diagonal/stroke --
    # distinguishable by their first two rows: "0" opens both sides, "7"'s
    # left side closes up after the top bar.
    assert grid[0].startswith("###.###")  # both glyphs open with a full top bar
    assert grid[1][0] == "#" and grid[1][1] == "."  # "0" row1 col0 lit (side), col1 blank
    zero_start = 0
    seven_start = 4  # DIGIT_GLYPH_W(3) + DIGIT_GLYPH_GAP(1)
    assert any(row[zero_start] == "#" for row in grid)  # "0" has a lit left edge somewhere
    assert grid[0][seven_start : seven_start + 3] == "###"  # "7"'s top bar


def test_text_dots_stays_within_six_rows():
    by_col, _ = _text_dots(DEFAULT_TEXT)
    lit_rows = {row for rows in by_col.values() for row in rows}
    assert lit_rows <= set(range(STRIP_ROWS))


def test_strip_scroll_wraps_around_its_total_width():
    demo = DooleyDemo()
    total_width = demo._text_width
    for _ in range(total_width * 3):
        demo.update(1.0)  # far more than one scroll tick per update
    assert 0 <= demo._scroll_offset < total_width


def test_palette_row_cells_black_hue_has_no_bright_solid():
    cells = _palette_row_cells((0, 0, 0), None, reversed_=False)
    solid_dark, dither, solid_bright = cells
    assert solid_dark.primary == (0, 0, 0)
    assert solid_bright.primary is None  # no bright variant of black
    assert dither.primary == (0, 0, 0)  # dithers against background instead


def test_palette_row_cells_reversed_swaps_dark_and_bright_ends():
    dark, bright = (191, 0, 0), (255, 0, 0)
    forward = _palette_row_cells(dark, bright, reversed_=False)
    reversed_cells = _palette_row_cells(dark, bright, reversed_=True)
    assert forward[0].primary == dark and forward[2].primary == bright
    assert reversed_cells[0].primary == bright and reversed_cells[2].primary == dark


def test_palette_cycles_through_all_seven_hues():
    demo = DooleyDemo()
    seen = set()
    for _ in range(len(PALETTE_HUES) * 20):
        demo.update(0.05)
        seen.add(demo._palette_offset)
    assert seen == set(range(len(PALETTE_HUES)))
