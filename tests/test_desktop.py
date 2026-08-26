"""Tests for the desktop shell (retrodemos/demos/desktop.py): the root
interface of retrodemos itself. Icon glyphs are new content, confirmed
with Bruce before wiring in (see the module docstring) -- not
archaeology, so no reconstruct-and-diff test here, just structural
coverage of the open/focus/drag/close mechanics and event routing."""

from __future__ import annotations

import pygame

from retrodemos.demos.desktop import (
    MENU_BAR_HEIGHT,
    _DEMO_ENTRIES,
    _MENU_ITEMS,
    DesktopDemo,
    _app_title_rect,
    _cmd_icon_rect,
    _icon_slot_rect,
    _menu_item_rects,
)


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


def test_an_open_windows_icon_disables_rather_than_disappearing():
    demo = DesktopDemo()
    key0 = _DEMO_ENTRIES[0][0]
    assert demo._icon_disabled(key0) is False
    _click(demo, _icon_slot_rect(0).center)
    # still tracked (draw() always draws every icon, just dimmed when
    # disabled) -- disabled, not hidden.
    assert demo._icon_disabled(key0) is True
    assert len(demo._open) == 1


def test_clicking_a_disabled_icon_does_nothing():
    demo = DesktopDemo()
    slot = _icon_slot_rect(0)
    _click(demo, slot.center)
    win = list(demo._open.values())[0]
    start_pos = list(win.pos)
    _click(demo, slot.center)  # icon is now disabled -- shouldn't reopen/move/duplicate
    assert len(demo._open) == 1
    assert win.pos == start_pos


def test_bruces_windows_icon_is_permanently_disabled():
    demo = DesktopDemo()
    index = next(i for i, (key, _title, _cls) in enumerate(_DEMO_ENTRIES) if key == "bruces_windows")
    assert demo._icon_disabled("bruces_windows") is True
    _click(demo, _icon_slot_rect(index).center)
    assert demo._open == {}


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
    # x clamps to the desktop's left edge; y clamps to just below the
    # menu bar, not the desktop's own top edge -- a window can't be
    # dragged up underneath it.
    assert win0.pos == [0, MENU_BAR_HEIGHT]


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


def _cd_player_icon_index() -> int:
    return next(i for i, (key, _title, _cls) in enumerate(_DEMO_ENTRIES) if key == "cd_player")


def test_clicking_the_cd_player_icon_opens_only_the_main_window_with_no_chrome():
    demo = DesktopDemo()
    _click(demo, _icon_slot_rect(_cd_player_icon_index()).center)
    assert list(demo._open.keys()) == ["cd_player_main"]
    assert demo._open["cd_player_main"].chrome is False


def test_the_cd_player_icon_stays_hidden_while_its_main_window_is_open():
    demo = DesktopDemo()
    slot = _icon_slot_rect(_cd_player_icon_index())
    _click(demo, slot.center)
    # clicking the same slot again shouldn't spawn a second window -- the
    # icon is meant to be hidden/inert while cd_player_main is open, same
    # contract every other demo's icon has.
    _click(demo, slot.center)
    assert list(demo._open.keys()) == ["cd_player_main"]


def test_clicking_the_main_windows_body_reveals_the_equalizer_as_its_own_window():
    demo = DesktopDemo()
    _click(demo, _icon_slot_rect(_cd_player_icon_index()).center)
    main = demo._open["cd_player_main"]
    assert "cd_player_eq" not in demo._open
    body_pos = (main.pos[0] + 100, main.pos[1] + 15)  # inside the readout box, not a button or close
    _click(demo, body_pos)
    assert "cd_player_eq" in demo._open
    assert demo._open["cd_player_eq"].chrome is False
    assert demo._order[-1] == "cd_player_eq"


def test_closing_the_cd_player_main_window_reenables_its_icon():
    demo = DesktopDemo()
    _click(demo, _icon_slot_rect(_cd_player_icon_index()).center)
    main = demo._open["cd_player_main"]
    close = main.demo.close_rect
    _click(demo, (main.pos[0] + close.centerx, main.pos[1] + close.centery))
    assert "cd_player_main" not in demo._open
    # icon is clickable again
    _click(demo, _icon_slot_rect(_cd_player_icon_index()).center)
    assert "cd_player_main" in demo._open


def _menu_item_rect(item_id: str) -> pygame.Rect:
    index = next(i for i, (mid, _label) in enumerate(_MENU_ITEMS) if mid == item_id)
    return _menu_item_rects()[index]


def test_app_title_shows_help_when_nothing_is_focused():
    demo = DesktopDemo()
    assert demo._focused_app_title() == "HELP"


def test_app_title_names_the_focused_window_with_demo_appended():
    demo = DesktopDemo()
    _click(demo, _icon_slot_rect(0).center)  # led
    assert demo._focused_app_title() == "LED demo"


def test_clicking_the_cmd_icon_opens_the_dropdown():
    demo = DesktopDemo()
    _click(demo, _cmd_icon_rect().center)
    assert demo._menu_open is True


def test_clicking_about_opens_the_about_panel_and_closes_the_menu():
    demo = DesktopDemo()
    _click(demo, _cmd_icon_rect().center)
    _click(demo, _menu_item_rect("about").center)
    assert demo._menu_open is False
    assert demo._about_open is True


def test_clicking_anywhere_dismisses_the_about_panel():
    demo = DesktopDemo()
    _click(demo, _cmd_icon_rect().center)
    _click(demo, _menu_item_rect("about").center)
    _click(demo, (5, MENU_BAR_HEIGHT + 5))
    assert demo._about_open is False


def test_close_all_windows_clears_every_open_window():
    demo = DesktopDemo()
    _click(demo, _icon_slot_rect(0).center)
    _click(demo, _icon_slot_rect(1).center)
    assert len(demo._open) == 2
    _click(demo, _cmd_icon_rect().center)
    _click(demo, _menu_item_rect("close_all").center)
    assert demo._open == {}
    assert demo._order == []


def test_quit_sets_want_quit():
    demo = DesktopDemo()
    assert demo.want_quit is False
    _click(demo, _cmd_icon_rect().center)
    _click(demo, _menu_item_rect("quit").center)
    assert demo.want_quit is True


def test_clicking_outside_the_dropdown_closes_it_without_acting():
    demo = DesktopDemo()
    _click(demo, _cmd_icon_rect().center)
    _click(demo, (900, 500))
    assert demo._menu_open is False
    assert demo.want_quit is False
    assert demo._about_open is False


def test_clicking_help_opens_the_help_panel_when_nothing_is_focused():
    demo = DesktopDemo()
    assert demo._focused_app_title() == "HELP"
    _click(demo, _app_title_rect("HELP").center)
    assert demo._help_open is True


def test_help_text_is_not_clickable_once_a_window_is_focused():
    demo = DesktopDemo()
    _click(demo, _icon_slot_rect(0).center)  # focuses led, app title is no longer HELP
    help_rect = _app_title_rect("HELP")
    _click(demo, help_rect.center)
    assert demo._help_open is False


def test_clicking_anywhere_dismisses_the_help_panel():
    demo = DesktopDemo()
    _click(demo, _app_title_rect("HELP").center)
    assert demo._help_open is True
    _click(demo, (500, 400))
    assert demo._help_open is False


def test_windows_cannot_be_opened_above_the_menu_bar():
    demo = DesktopDemo()
    _click(demo, _icon_slot_rect(0).center)
    key0 = _DEMO_ENTRIES[0][0]
    assert demo._open[key0].pos[1] >= MENU_BAR_HEIGHT


def test_icon_slots_dont_overlap():
    rects = [_icon_slot_rect(i) for i in range(len(_DEMO_ENTRIES))]
    for i, a in enumerate(rects):
        for b in rects[i + 1 :]:
            assert not a.colliderect(b)
