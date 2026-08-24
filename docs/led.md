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

Shares the LED rendering framework with `led-ii.md`, `title.md`, and `dooley.md`.

## Future polish (out of scope for now)

- More frames/rings in the explosion burst (currently capped at a radius of 3 for locality).
- Repeat the power-up flicker a few times with varied timings, instead of one flicker run.
