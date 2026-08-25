"""Tests for framework/pixel_font.py -- the hand-designed A-Z/0-9 window-
title font (no source to extract from, unlike every other font in this
project; see the module docstring)."""

from __future__ import annotations

from retrodemos.framework.pixel_font import GLYPH_GAP, GLYPH_H, GLYPH_W, WINDOW_FONT, text_cells


def test_every_glyph_fits_within_its_own_box():
    for ch, cells in WINDOW_FONT.items():
        for x, y in cells:
            assert 0 <= x < GLYPH_W, f"{ch!r} has a cell out of bounds: {(x, y)}"
            assert 0 <= y < GLYPH_H, f"{ch!r} has a cell out of bounds: {(x, y)}"


def test_every_letter_and_digit_is_covered():
    import string

    for ch in string.ascii_uppercase + string.digits:
        assert ch in WINDOW_FONT, f"missing glyph for {ch!r}"


def test_space_is_blank():
    assert WINDOW_FONT[" "] == set()


def test_every_letter_has_at_least_some_lit_cells():
    import string

    for ch in string.ascii_uppercase + string.digits:
        assert WINDOW_FONT[ch], f"{ch!r} renders as nothing"


def test_text_cells_lays_out_characters_left_to_right():
    cells, width = text_cells("AB")
    a_cells = {(x, y) for x, y in cells if x < GLYPH_W}
    b_cells = {(x, y) for x, y in cells if x >= GLYPH_W + GLYPH_GAP}
    assert a_cells == WINDOW_FONT["A"]
    assert {(x - (GLYPH_W + GLYPH_GAP), y) for x, y in b_cells} == WINDOW_FONT["B"]
    assert width == 2 * GLYPH_W + GLYPH_GAP


def test_text_cells_lowercases_input_by_uppercasing_it():
    lower, _ = text_cells("led")
    upper, _ = text_cells("LED")
    assert lower == upper


def test_text_cells_unknown_character_renders_blank_not_a_crash():
    cells, width = text_cells("A@B")
    assert width > 0
    # the middle glyph slot (unknown char) contributes nothing
    middle_cells = {(x, y) for x, y in cells if GLYPH_W + GLYPH_GAP <= x < 2 * (GLYPH_W + GLYPH_GAP)}
    assert middle_cells == set()


def test_text_cells_empty_string_has_positive_width():
    _, width = text_cells("")
    assert width >= 1
