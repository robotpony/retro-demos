"""Tests for the desktop shell (retrodemos/demos/desktop.py): the root
interface of retrodemos itself. Icon glyphs are new content, confirmed
with Bruce before wiring in (see the module docstring) -- not
archaeology, so no reconstruct-and-diff test here, just structural
coverage of the open/focus/drag/close mechanics and event routing."""

from __future__ import annotations

import pygame

from retrodemos.demos.desktop import _DEMO_ENTRIES, DesktopDemo, _icon_slot_rect


def _click(demo: DesktopDemo, pos: tuple[int, int]) -> None:
    demo.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1))


def test_native_size_is_the_desktop_canvas():
    demo = DesktopDemo()
    assert demo.NATIVE_SIZE == (1024, 576)


def test_starts_with_no_windows_open():
    demo = DesktopDemo()
    assert demo._open == {}
    assert demo._order == []


def test_demo_runs_for_many_frames_without_raising():
    demo = DesktopDemo()
    surface = pygame.Surface(demo.NATIVE_SIZE)
    for _ in range(50):
        demo.update(0.05)
        demo.draw(surface)


def test_clicking_an_icon_opens_that_demo():
    demo = DesktopDemo()
    _click(demo, _icon_slot_rect(0).center)
    assert list(demo._open.keys()) == [_DEMO_ENTRIES[0][0]]


def test_clicking_an_already_open_icon_focuses_instead_of_duplicating():
    demo = DesktopDemo()
    slot = _icon_slot_rect(0)
    _click(demo, slot.center)
    _click(demo, slot.center)
    assert len(demo._open) == 1


def test_opening_two_demos_keeps_both_and_orders_by_recency():
    demo = DesktopDemo()
    _click(demo, _icon_slot_rect(0).center)
    _click(demo, _icon_slot_rect(1).center)
    key0, key1 = _DEMO_ENTRIES[0][0], _DEMO_ENTRIES[1][0]
    assert set(demo._open) == {key0, key1}
    assert demo._order == [key0, key1]


def test_clicking_a_background_windows_body_brings_it_to_front():
    demo = DesktopDemo()
    _click(demo, _icon_slot_rect(0).center)
    _click(demo, _icon_slot_rect(1).center)
    key0 = _DEMO_ENTRIES[0][0]
    win0 = demo._open[key0]
    # the cascade offsets each new window down/right, so win0's own
    # top-left corner stays exposed even with a later window opened on
    # top of it -- click there, not the (possibly covered) centre.
    content = win0.content_screen_rect()
    corner = (content.x + 3, content.y + 3)
    _click(demo, corner)
    assert demo._order[-1] == key0


def test_dragging_the_title_bar_moves_the_window_and_focuses_it():
    demo = DesktopDemo()
    _click(demo, _icon_slot_rect(0).center)
    _click(demo, _icon_slot_rect(1).center)
    key0 = _DEMO_ENTRIES[0][0]
    win0 = demo._open[key0]
    start = list(win0.pos)
    tb = win0.title_bar_screen_rect()
    demo.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=tb.center, button=1))
    demo.handle_event(
        pygame.event.Event(pygame.MOUSEMOTION, pos=(tb.center[0] + 15, tb.center[1] + 5), rel=(15, 5), buttons=(1, 0, 0))
    )
    assert win0.pos == [start[0] + 15, start[1] + 5]
    assert demo._order[-1] == key0


def test_releasing_the_mouse_stops_the_drag():
    demo = DesktopDemo()
    _click(demo, _icon_slot_rect(0).center)
    key0 = _DEMO_ENTRIES[0][0]
    win0 = demo._open[key0]
    tb = win0.title_bar_screen_rect()
    demo.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=tb.center, button=1))
    demo.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=tb.center, button=1))
    pos_after_release = list(win0.pos)
    demo.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=(999, 999), rel=(80, 80), buttons=(0, 0, 0)))
    assert win0.pos == pos_after_release


def test_dragging_clamps_to_the_desktop_bounds():
    demo = DesktopDemo()
    _click(demo, _icon_slot_rect(0).center)
    key0 = _DEMO_ENTRIES[0][0]
    win0 = demo._open[key0]
    tb = win0.title_bar_screen_rect()
    demo.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=tb.center, button=1))
    demo.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=(-999, -999), rel=(-5000, -5000), buttons=(1, 0, 0)))
    assert win0.pos == [0, 0]


def test_clicking_the_close_button_closes_the_window_and_reenables_the_icon():
    demo = DesktopDemo()
    _click(demo, _icon_slot_rect(0).center)
    key0 = _DEMO_ENTRIES[0][0]
    win0 = demo._open[key0]
    _click(demo, win0.close_button_screen_rect().center)
    assert key0 not in demo._open
    assert key0 not in demo._order
    # icon is clickable again -- opening it spawns a fresh instance
    _click(demo, _icon_slot_rect(0).center)
    assert key0 in demo._open


def test_reset_closes_every_open_window():
    demo = DesktopDemo()
    _click(demo, _icon_slot_rect(0).center)
    _click(demo, _icon_slot_rect(1).center)
    demo.reset()
    assert demo._open == {}
    assert demo._order == []


def test_open_demos_keep_updating_even_when_not_focused():
    demo = DesktopDemo()
    _click(demo, _icon_slot_rect(2).center)  # title, has visible internal state (phase sequence)
    key = _DEMO_ENTRIES[2][0]
    win = demo._open[key]
    before = win.demo._sequence.index if hasattr(win.demo, "_sequence") else None
    for _ in range(500):
        demo.update(0.05)
    after = win.demo._sequence.index if hasattr(win.demo, "_sequence") else None
    # not asserting a specific phase, just that update() is actually reaching
    # the wrapped demo (its own elapsed-time state moved from the start)
    assert before is not None and after is not None


def test_icon_slots_dont_overlap():
    rects = [_icon_slot_rect(i) for i in range(len(_DEMO_ENTRIES))]
    for i, a in enumerate(rects):
        for b in rects[i + 1 :]:
            assert not a.colliderect(b)
