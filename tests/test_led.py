"""Tests for the LED demo and the shared seven-segment renderer it uses."""

from __future__ import annotations

import pygame

from retrodemos.demos.led import DEFAULT_TEXT, DIGIT_COUNT, LedDemo
from retrodemos.framework.led_grid import ALL_SEGMENT_PIXELS, SEGMENTS, SevenSegmentDisplay


def test_segments_dont_overlap():
    # A pixel claimed by two segments was exactly what caused the stray/extra
    # dot bugs Bruce caught during design; keep this from silently coming back.
    seen: dict[tuple[int, int], str] = {}
    for name, pixels in SEGMENTS.items():
        for p in pixels:
            assert p not in seen, f"pixel {p} claimed by both {seen.get(p)} and {name}"
            seen[p] = name


def test_display_renders_at_declared_size():
    display = SevenSegmentDisplay(DIGIT_COUNT)
    surface = pygame.Surface((display.width, display.height))
    display.render(surface, "01234567")  # should not raise


def test_display_pads_short_text_and_truncates_long_text():
    display = SevenSegmentDisplay(4)
    surface = pygame.Surface((display.width, display.height))
    display.render(surface, "1")  # shorter than digit_count
    display.render(surface, "123456")  # longer than digit_count


def test_unknown_character_renders_as_blank_digit_not_a_crash():
    display = SevenSegmentDisplay(4)
    surface = pygame.Surface((display.width, display.height))
    display.render(surface, "1?2 ")


def test_all_ten_digits_render_without_raising():
    display = SevenSegmentDisplay(10)
    surface = pygame.Surface((display.width, display.height))
    display.render(surface, "0123456789")


def test_led_demo_native_size_matches_its_display():
    demo = LedDemo()
    assert demo.NATIVE_SIZE == (demo.display.width, demo.display.height)


def test_led_demo_default_text_is_digits_only():
    # led_grid only maps digits, space, and "-"; anything else silently
    # renders blank, so the default shouldn't rely on unsupported characters.
    for ch in DEFAULT_TEXT:
        assert ch.isdigit()


def test_led_demo_scrolls_over_time():
    demo = LedDemo()
    surface = pygame.Surface(demo.NATIVE_SIZE)
    demo.draw(surface)
    before = pygame.image.tobytes(surface, "RGB")
    for _ in range(50):
        demo.update(0.1)  # well past SCROLL_INTERVAL, offset should advance
    demo.draw(surface)
    after = pygame.image.tobytes(surface, "RGB")
    assert before != after


def test_led_demo_text_override():
    demo = LedDemo(text="42")
    assert demo.message == "42"


def test_led_demo_reset_returns_to_start_of_scroll():
    demo = LedDemo()
    for _ in range(20):
        demo.update(0.1)
    demo.reset()
    assert demo._offset == 0
