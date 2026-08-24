"""Tests for the dot-matrix renderer and scroll_window helper
(framework/led_grid.py), built for LED II.

test_led.py covers the seven-segment side of led_grid.py; this file covers
the dot-matrix side and the scroll helper both renderers can use.
"""

from __future__ import annotations

import pygame

from retrodemos.framework.led_grid import DOT_FONT, DotMatrixDisplay, lerp_color, scroll_window


def test_display_size_matches_the_source_image():
    # images/LED-II-thumb.png is 256x32 -- see docs/pixel-archaeology.md's
    # findings for LED II. This is the reconstruct-and-diff bar stated as a
    # size check; the full byte-for-byte diff was done interactively, not
    # as an automated test (there's no source image shipped for a live
    # pixel-diff test to read).
    display = DotMatrixDisplay(cols=83)
    assert (display.width, display.height) == (256, 32)


def test_render_raw_lights_only_the_requested_cells():
    display = DotMatrixDisplay(cols=4)
    surface = pygame.Surface((display.width, display.height))
    display.render_raw(surface, {(0, 0)})
    origin_x = display.h_border + display.margin
    origin_y = display.v_border + display.margin
    assert surface.get_at((origin_x, origin_y))[:3] == (191, 0, 0)  # DOT_LIT
    # the next dot over (col 1) should stay unlit
    assert surface.get_at((origin_x + display.PITCH, origin_y))[:3] == (48, 0, 0)  # DOT_UNLIT


def test_render_pads_short_text_and_truncates_long_text():
    display = DotMatrixDisplay(cols=83)
    surface = pygame.Surface((display.width, display.height))
    display.render(surface, "1")  # shorter than char_count
    display.render(surface, "0" * 50)  # longer than char_count


def test_unknown_character_renders_as_blank_cell_not_a_crash():
    display = DotMatrixDisplay(cols=20)
    surface = pygame.Surface((display.width, display.height))
    display.render(surface, "1?2 -")


def test_dot_font_glyphs_stay_within_their_5x7_cell():
    for ch, pixels in DOT_FONT.items():
        for x, y in pixels:
            assert 0 <= x < 5, f"{ch!r} has an out-of-bounds column {x}"
            assert 0 <= y < 7, f"{ch!r} has an out-of-bounds row {y}"


def test_dot_font_covers_digits_space_and_hyphen():
    assert set(DOT_FONT) == set("0123456789- ")


def test_scroll_window_wraps_around_the_end():
    assert scroll_window("ABCDE", offset=3, width=4) == "DEAB"


def test_scroll_window_at_zero_offset_is_the_start():
    assert scroll_window("ABCDE", offset=0, width=3) == "ABC"


def test_scroll_window_handles_empty_text():
    assert scroll_window("", offset=0, width=3) == "   "


def test_lerp_color_at_the_endpoints():
    assert lerp_color((48, 0, 0), (191, 0, 0), 0.0) == (48, 0, 0)
    assert lerp_color((48, 0, 0), (191, 0, 0), 1.0) == (191, 0, 0)


def test_lerp_color_midpoint():
    assert lerp_color((0, 0, 0), (100, 200, 40), 0.5) == (50, 100, 20)


def test_lerp_color_clamps_out_of_range_t():
    assert lerp_color((48, 0, 0), (191, 0, 0), -1.0) == (48, 0, 0)
    assert lerp_color((48, 0, 0), (191, 0, 0), 2.0) == (191, 0, 0)


def test_render_raw_accepts_a_plain_set_as_fully_lit():
    # backward-compat path: a set of cells, all at full DOT_LIT brightness.
    display = DotMatrixDisplay(cols=4)
    surface = pygame.Surface((display.width, display.height))
    display.render_raw(surface, {(0, 0)})
    origin_x = display.h_border + display.margin
    origin_y = display.v_border + display.margin
    assert surface.get_at((origin_x, origin_y))[:3] == (191, 0, 0)


def test_render_raw_accepts_a_dict_for_partial_brightness():
    display = DotMatrixDisplay(cols=4)
    surface = pygame.Surface((display.width, display.height))
    display.render_raw(surface, {(0, 0): 0.5})
    origin_x = display.h_border + display.margin
    origin_y = display.v_border + display.margin
    assert surface.get_at((origin_x, origin_y))[:3] == lerp_color((48, 0, 0), (191, 0, 0), 0.5)


def test_render_raw_with_none_is_fully_unlit():
    display = DotMatrixDisplay(cols=2)
    surface = pygame.Surface((display.width, display.height))
    display.render_raw(surface, None)
    origin_x = display.h_border + display.margin
    origin_y = display.v_border + display.margin
    assert surface.get_at((origin_x, origin_y))[:3] == (48, 0, 0)
