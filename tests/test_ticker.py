"""Tests for the fixed-interval tick accumulator."""

from __future__ import annotations

from retrodemos.framework.ticker import Ticker


def test_advance_fires_once_per_interval():
    ticker = Ticker(0.1)
    assert ticker.advance(0.05) == 0
    assert ticker.advance(0.05) == 1  # 0.10 total
    assert ticker.advance(0.05) == 0
    assert ticker.advance(0.05) == 1  # 0.20 total


def test_advance_catches_up_a_slow_frame():
    # A single big dt should fire every tick it covers, not just one --
    # this is exactly the behaviour LED's phases lost when they used a
    # plain `if` instead of a `while` loop (see led_phases.py history).
    ticker = Ticker(0.1)
    assert ticker.advance(0.45) == 4


def test_advance_carries_remainder_forward():
    ticker = Ticker(0.1)
    ticker.advance(0.09)
    assert ticker.advance(0.02) == 1  # 0.09 + 0.02 = 0.11 -> one tick, 0.01 left


def test_reset_clears_accumulated_time():
    ticker = Ticker(0.1)
    ticker.advance(0.09)
    ticker.reset()
    assert ticker.advance(0.09) == 0


def test_interval_can_change_between_calls():
    ticker = Ticker(0.1)
    ticker.advance(0.05)  # 0.05 elapsed, below the 0.1 interval: 0 ticks
    ticker.interval = 0.02
    # 0.05 + 0.02 = 0.07, now checked against the new, smaller interval
    assert ticker.advance(0.02) == 3
