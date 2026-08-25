# LED

**Source:** `LED-thumb.png`
**Mode:** Automated attract-mode

## What it shows

Single-row, seven-segment digit display, like a digital clock or counter.

## Behaviour

Runs a scripted sequence on a loop, per Bruce's spec (2026-08-24): power-up (flicker like a loose connection, then a synchronized ring sweep that speeds up), scrolling numbers (default `0123456789`, `--text` overridable), a segment "snake" that grows to length 5 then wanders, a firework-style explosion repeated 5 times, then a held "1991" credit. See `retrodemos/demos/led_phases.py` for each phase's choreography.

## Interaction

None beyond the shared quit/pause controls.

## Assets

Shares the LED rendering framework with `led-ii.md` and `title.md`.

## Future polish (out of scope for now)

- More frames/rings in the explosion burst (currently capped at a radius of 3 for locality).
- Repeat the power-up flicker a few times with varied timings, instead of one flicker run.
- Vary LED intensity, not just on/off. The power-up flicker (and the segment renderer generally) currently only has two states, `LIT` and `UNLIT` (`led_grid.py`); a flicker that dims and brightens rather than snapping between two fixed colours would read as closer to a loose connection. This needs a brightness/intensity concept in `led_grid.py` itself, not just LED's phases, since LED II and Title's dot-matrix grids would want the same control (tracked in `PLAN.md`'s "Future framework polish").
- Give phase timing momentum: speed up, hold, then ease back down, rather than the current shape (fixed intervals, or `PowerUpPhase`'s sweep which only speeds up with no ease-out). Wants a shared easing helper alongside `Ticker` (tracked in `PLAN.md`).
- Rudimentary sound: simple synthesized beeps (sine tones, short envelopes) timed to the flicker, sweep, snake, and explosion. No audio exists anywhere in the framework yet, and `PLAN.md`'s "out of scope" list currently rules out *real* audio playback for CD Player specifically (simulating a CD deck) -- a small synthesized-beep capability is a different, narrower thing, but is a new project decision either way and worth confirming with Bruce before building (tracked in `PLAN.md`).
