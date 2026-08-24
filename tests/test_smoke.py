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
from retrodemos.framework.runtime import run


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


def test_handle_shared_keys_maps_quit_pause_restart():
    quit_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_q)
    pause_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)
    restart_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r)
    other_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a)

    assert handle_shared_keys(quit_event).quit
    assert handle_shared_keys(pause_event).toggle_pause
    assert handle_shared_keys(restart_event).restart
    assert not handle_shared_keys(other_event).claimed


def test_cli_lists_demos_when_none_given(capsys):
    from retrodemos.__main__ import main

    exit_code = main(["--list"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "No demos yet" in captured.out or "Available demos" in captured.out


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
