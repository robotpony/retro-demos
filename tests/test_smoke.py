"""Headless smoke tests for the shared framework, plus one launch case per
demo (PLAN.md's "Testing" section: launch it, run a few frames, assert
nothing raises -- no _CountingDemo needed for those, just the real Demo).
Demo-specific rendering/geometry tests live in their own tests/test_<demo>.py.
"""

from __future__ import annotations

import pygame

from retrodemos.framework.canvas import Canvas
from retrodemos.framework.demo import Demo
from retrodemos.framework.keys import handle_shared_keys
from retrodemos.framework.runtime import _fit_scale, run


class _CountingDemo(Demo):
    """Minimal Demo used only by these tests: counts calls instead of drawing anything real."""

    NATIVE_SIZE = (64, 48)

    def __init__(self) -> None:
        self.updates = 0
        self.draws = 0
        self.events_seen: list[pygame.event.Event] = []
        self.reset_count = 0

    def handle_event(self, event: pygame.event.Event) -> None:
        self.events_seen.append(event)

    def update(self, dt: float) -> None:
        self.updates += 1

    def draw(self, surface: pygame.Surface) -> None:
        self.draws += 1
        assert surface.get_size() == self.NATIVE_SIZE

    def reset(self) -> None:
        self.reset_count += 1


def test_runtime_runs_for_max_frames_then_stops():
    demo = _CountingDemo()
    run(demo, scale=2, fps=1000, max_frames=5)
    assert demo.updates == 5
    assert demo.draws == 5


def test_runtime_quits_on_quit_key_without_drawing_that_frame():
    demo = _CountingDemo()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    run(demo, scale=2, fps=1000, max_frames=1000)
    assert demo.draws == 0
    assert demo.updates == 0


def test_pause_key_stops_updates_but_not_draws():
    demo = _CountingDemo()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
    run(demo, scale=2, fps=1000, max_frames=5)
    assert demo.updates == 0  # paused takes effect before the first update
    assert demo.draws == 5  # drawing still happens while paused


def test_demo_can_request_quit_via_want_quit():
    # A demo can end the run itself, not just Esc/Q -- the desktop
    # shell's own menu-bar Quit item, so far the only user of this.
    # want_quit is checked right after events, before that frame's own
    # update/draw, same as the quit key -- set before run() even starts,
    # so the loop ends without a single iteration's work happening.
    demo = _CountingDemo()
    demo.want_quit = True
    run(demo, scale=2, fps=1000, max_frames=1000)
    assert demo.draws == 0
    assert demo.updates == 0


def test_want_quit_set_mid_run_stops_the_loop_before_max_frames():
    class _QuitsAfterThreeUpdates(_CountingDemo):
        def update(self, dt: float) -> None:
            super().update(dt)
            if self.updates == 3:
                self.want_quit = True

    demo = _QuitsAfterThreeUpdates()
    run(demo, scale=2, fps=1000, max_frames=1000)
    assert demo.updates == 3
    assert demo.draws == 3  # the frame that set want_quit still finishes drawing


def test_restart_key_calls_reset():
    demo = _CountingDemo()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r))
    run(demo, scale=2, fps=1000, max_frames=3)
    assert demo.reset_count == 1


def _keydowns_seen(demo: _CountingDemo) -> list[int]:
    return [e.key for e in demo.events_seen if e.type == pygame.KEYDOWN]


def test_shared_keys_dont_reach_demo_handle_event():
    # SDL posts its own housekeeping events (AudioDeviceAdded, ActiveEvent,
    # WindowEnter, ...) even under the dummy driver; those legitimately reach
    # handle_event too, so this only checks the posted key itself is absent.
    demo = _CountingDemo()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
    run(demo, scale=2, fps=1000, max_frames=2)
    assert pygame.K_SPACE not in _keydowns_seen(demo)


def test_demo_specific_event_reaches_handle_event():
    demo = _CountingDemo()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a))
    run(demo, scale=2, fps=1000, max_frames=2)
    assert pygame.K_a in _keydowns_seen(demo)


def test_canvas_scales_to_window_size():
    canvas = Canvas((64, 48), scale=3)
    assert canvas.window_size == (192, 144)
    window = pygame.Surface(canvas.window_size)
    canvas.present(window)  # should not raise


def test_fit_scale_shrinks_a_canvas_too_big_for_the_screen():
    # The dummy driver reports a 1024x768 "screen" -- the desktop shell's
    # 1024x576 canvas at the CLI's default scale of 3 would be 3072x1728,
    # nowhere close to fitting, so this should fall all the way back to 1x.
    assert _fit_scale((1024, 576), 3) == 1


def test_fit_scale_never_exceeds_the_requested_scale():
    # A small demo's canvas easily fits the dummy 1024x768 screen even at
    # a large scale -- fit_scale should hand back exactly what was asked
    # for, not grow past it.
    assert _fit_scale((64, 48), 3) == 3


def test_mouse_events_are_rescaled_to_native_space_before_reaching_the_demo():
    demo = _CountingDemo()
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(30, 15), button=1))
    pygame.event.post(pygame.event.Event(pygame.MOUSEMOTION, pos=(32, 19), rel=(2, 4), buttons=(1, 0, 0)))
    run(demo, scale=2, fps=1000, max_frames=2)
    down = next(e for e in demo.events_seen if e.type == pygame.MOUSEBUTTONDOWN)
    motion = next(e for e in demo.events_seen if e.type == pygame.MOUSEMOTION)
    assert down.pos == (15, 7)  # (30, 15) // 2
    assert motion.pos == (16, 9)  # (32, 19) // 2
    assert motion.rel == (1, 2)  # (2, 4) // 2


def test_mouse_events_pass_through_unscaled_when_scale_is_one():
    demo = _CountingDemo()
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(30, 15), button=1))
    run(demo, scale=1, fps=1000, max_frames=2)
    down = next(e for e in demo.events_seen if e.type == pygame.MOUSEBUTTONDOWN)
    assert down.pos == (30, 15)


def test_handle_shared_keys_maps_quit_pause_restart():
    quit_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_q)
    pause_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)
    restart_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r)
    other_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a)

    assert handle_shared_keys(quit_event).quit
    assert handle_shared_keys(pause_event).toggle_pause
    assert handle_shared_keys(restart_event).restart
    assert not handle_shared_keys(other_event).claimed


def test_cli_lists_demos_with_explicit_list_flag(capsys):
    from retrodemos.__main__ import main

    exit_code = main(["--list"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "No demos yet" in captured.out or "Available demos" in captured.out


def test_cli_no_name_defaults_to_the_desktop_shell():
    # main([]) would actually launch and block on run()'s event loop (no
    # max_frames to bound it), so this checks the dispatch logic itself --
    # the desktop is what "no name given" resolves to and loads as --
    # rather than calling main() for real.
    from retrodemos.__main__ import DESKTOP_DEMO_NAME, available_demos, build_parser, load_demo

    args = build_parser().parse_args([])
    assert args.name is None
    assert DESKTOP_DEMO_NAME in available_demos()
    demo = load_demo(DESKTOP_DEMO_NAME)
    assert demo.NATIVE_SIZE == (1024, 576)


def test_cli_list_excludes_helper_modules_without_a_demo_class():
    # led_phases.py and led_ii_phases.py live in retrodemos/demos/ (each
    # demo's own choreography module) but expose no DEMO_CLASS, so they
    # aren't runnable demos and shouldn't be listed as if they were.
    from retrodemos.__main__ import available_demos

    demos = available_demos()
    assert "led" in demos
    assert "led_ii" in demos
    assert "led_phases" not in demos
    assert "led_ii_phases" not in demos


def test_cli_rejects_unknown_demo_name(capsys):
    from retrodemos.__main__ import main

    exit_code = main(["not-a-real-demo"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Unknown demo" in captured.err


def test_led_demo_runs_headlessly():
    from retrodemos.demos.led import LedDemo

    demo = LedDemo()
    run(demo, scale=2, fps=1000, max_frames=5)


def test_led_ii_demo_runs_headlessly():
    from retrodemos.demos.led_ii import LedIIDemo

    demo = LedIIDemo()
    run(demo, scale=2, fps=1000, max_frames=5)


def test_title_demo_runs_headlessly():
    from retrodemos.demos.title import TitleDemo

    demo = TitleDemo()
    run(demo, scale=2, fps=1000, max_frames=5)


def test_bruces_21_demo_runs_headlessly():
    from retrodemos.demos.bruces_21 import Bruces21Demo

    demo = Bruces21Demo()
    run(demo, scale=2, fps=1000, max_frames=5)


def test_tank_status_window_demo_runs_headlessly():
    from retrodemos.demos.tank_status_window import TankStatusWindowDemo

    demo = TankStatusWindowDemo()
    run(demo, scale=2, fps=1000, max_frames=5)
