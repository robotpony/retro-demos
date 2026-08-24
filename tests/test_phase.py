"""Tests for the shared Phase base class (framework/phase.py).

LED's phases (tests/test_led.py) exercise Phase indirectly through real
choreography; these tests cover the base class contract on its own, since
it's meant to be reused by any future demo with a scripted, looping
sequence (Dooley, Bruce's 21, Tank Status Window -- see PLAN.md).
"""

from __future__ import annotations

import random

import pytest

from retrodemos.framework.phase import Phase


def test_init_stores_display_and_rng_and_calls_reset():
    calls = []

    class RecordingPhase(Phase):
        def reset(self):
            calls.append("reset")

    rng = random.Random(0)
    phase = RecordingPhase(display="some-display", rng=rng)
    assert phase.display == "some-display"
    assert phase.rng is rng
    assert calls == ["reset"]  # reset() runs once, during __init__


def test_default_reset_is_a_no_op():
    class MinimalPhase(Phase):
        pass

    MinimalPhase(display=None, rng=random.Random(0))  # should not raise


def test_update_and_draw_are_not_implemented_by_default():
    class MinimalPhase(Phase):
        pass

    phase = MinimalPhase(display=None, rng=random.Random(0))
    with pytest.raises(NotImplementedError):
        phase.update(0.1)
    with pytest.raises(NotImplementedError):
        phase.draw(surface=None)
