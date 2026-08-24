# LED II

**Source:** `LED-II-thumb.png`
**Mode:** Automated attract-mode

## What it shows

Dot-matrix LED display: rows of red dots, marquee-style.

## Behaviour

Runs a scripted sequence on a loop, mirroring LED's own five-beat structure -- confirmed with Bruce (2026-08-24), since (unlike LED) there was no existing spec pinning down LED II's script: power-up (random dot flicker, then a column sweep that speeds up), a smoothly-scrolling marquee (default `0123456789`, `--text` overridable), a "snake" that crawls the dot grid (grows to ~35 dots -- retuned longer on request, 2026-08-24, since 20 read as small against the 83x9 grid), a rippling firework burst that radiates outward with per-dot brightness that fades individually plus a scatter of spark dots (also retuned bigger/richer on the same request: wider radius, more sparks, varying brightness instead of a flat lit/unlit ring), then a held "1991" credit (reused from LED's own credit, not a confirmed fact about LED II specifically -- flag for Bruce to change if wrong). See `retrodemos/demos/led_ii_phases.py` for each phase's choreography.

## Interaction

None beyond the shared quit/pause controls.

## Assets

Shares the LED rendering framework with `led.md`, `title.md`, and `dooley.md`. Its dot-matrix renderer (`framework/led_grid.py`'s `DotMatrixDisplay`) and 5x7 digit font are new as of this demo; `text.md` and `dooley.md` should extend rather than fork them.

## Future polish (out of scope for now)

- A dot-matrix alphabet (currently digits, space, and "-" only -- see `led_grid.DOT_FONT`), if a demo ever needs to scroll real words instead of numbers.
- Confirm the "1991" credit and the marquee's default text with Bruce; both are LED's own values reused by assumption, not verified for LED II.
- LED intensity is now done for LED II's own fireworks (`led_grid.lerp_color`, `DotMatrixDisplay.render_raw`'s intensity-dict support, `graph_walk.Burst`'s per-node fade) -- but LED's own `ExplosionPhase`/power-up flicker don't use it yet, and neither does LED II's power-up flicker or column sweep. Worth revisiting whether those should too, for consistency.
- The timing-momentum and synthesized-beep polish items tracked in `PLAN.md`'s "Future framework polish" still apply here, once built.
