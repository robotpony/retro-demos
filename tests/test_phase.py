"""Tests for the shared Phase base class and PhaseSequence sequencer
(framework/phase.py).

LED's phases (tests/test_led.py) exercise both indirectly through real
choreography; these tests cover the base class and sequencer contracts on
their own, since they're meant to be reused by any future demo with a
scripted, looping sequence (Dooley, Bruce's 21, Tank Status Window -- see
PLAN.md).
"""

from __future__ import annotations

import random

import pytest

from retrodemos.framework.phase import Phase, PhaseSequence


class CountingPhase(Phase):
    """Test double: finishes after `ticks_to_finish` update() calls, and
    records how many times reset()/draw() ran so sequencing behaviour can
    be asserted on without real choreography."""

    def __init__(self, ticks_to_finish: int) -> None:
        self.ticks_to_finish = ticks_to_finish
        self.reset_count = 0
        self.draw_count = 0
        self._ticks = 0
        super().__init__(display=None, rng=random.Random(0))

    def reset(self) -> None:
        self.reset_count += 1
        self._ticks = 0

    def update(self, dt: float) -> bool:
        self._ticks += 1
        return self._ticks >= self.ticks_to_finish

    def draw(self, surface) -> None:
        self.draw_count += 1


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


def test_sequence_rejects_an_empty_phase_list():
    with pytest.raises(ValueError):
        PhaseSequence([])


def test_sequence_starts_on_the_first_phase():
    a, b = CountingPhase(2), CountingPhase(2)
    sequence = PhaseSequence([a, b])
    assert sequence.index == 0
    assert sequence.current is a


def test_update_does_not_advance_while_the_current_phase_is_unfinished():
    a, b = CountingPhase(3), CountingPhase(3)
    sequence = PhaseSequence([a, b])
    sequence.update(0.1)
    assert sequence.index == 0
    assert sequence.current is a


def test_update_advances_and_resets_the_next_phase_when_current_finishes():
    a, b = CountingPhase(1), CountingPhase(5)
    sequence = PhaseSequence([a, b])
    resets_before = b.reset_count
    sequence.update(0.1)  # a finishes on its first tick
    assert sequence.index == 1
    assert sequence.current is b
    assert b.reset_count == resets_before + 1  # b resets right as it starts


def test_sequence_loops_back_to_the_first_phase_after_the_last_finishes():
    a, b = CountingPhase(1), CountingPhase(1)
    sequence = PhaseSequence([a, b])
    sequence.update(0.1)  # a -> b
    sequence.update(0.1)  # b finishes -> loops back to a
    assert sequence.index == 0
    assert sequence.current is a


def test_draw_delegates_only_to_the_current_phase():
    a, b = CountingPhase(1), CountingPhase(1)
    sequence = PhaseSequence([a, b])
    sequence.draw(surface=None)
    assert a.draw_count == 1
    assert b.draw_count == 0
    sequence.update(0.1)  # advance to b
    sequence.draw(surface=None)
    assert a.draw_count == 1
    assert b.draw_count == 1


def test_reset_returns_to_the_first_phase_and_resets_it():
    a, b = CountingPhase(1), CountingPhase(1)
    sequence = PhaseSequence([a, b])
    sequence.update(0.1)  # advance to b
    resets_before = a.reset_count
    sequence.reset()
    assert sequence.index == 0
    assert a.reset_count == resets_before + 1
