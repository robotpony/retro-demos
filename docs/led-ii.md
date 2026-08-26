# LED II

**Source:** `LED-II-thumb.png`
**Mode:** Automated attract-mode

## What it shows

Dot-matrix LED display: rows of red dots, marquee-style.

## Behaviour

Runs a scripted sequence on a loop, mirroring LED's own five-beat structure -- confirmed with Bruce (2026-08-24), since (unlike LED) there was no existing spec pinning down LED II's script: power-up (random dot flicker, then a column sweep that speeds up), a smoothly-scrolling marquee (default `0123456789`, `--text` overridable), a snake-chase minigame across the dot grid, a rippling firework burst, then a held "1991" credit (reused from LED's own credit, not a confirmed fact about LED II specifically -- flag for Bruce to change if wrong). See `retrodemos/demos/led_ii_phases.py` for each phase's choreography.

Playtesting (2026-08-26) reworked three of these phases:

- **SnakePhase** is now a best-of-3 match (`graph_walk.ChaseMatch`) instead of a single round: two `graph_walk.ChaseSnake`s spawn a quarter-width apart and hunt each other via a shared `graph_walk.ChasePair` (ported from Title's own snake-chase minigame, 2026-08-24) until one catches the other and flashes, scoring a point; a fresh round spawns immediately unless a side has already won 3. Score is shown as dots stacked on each snake's own starting side (column 0 for the left spawn, the rightmost column for the right) so it reads as that side's tally. `CHASE_CHANCE` was also lowered (0.65 -> 0.45) so a round reads as more of a scramble and less of a beeline.
- **MarqueePhase** now accelerates its scroll interval over the phase's run (0.05s -> 0.012s) instead of holding one fixed speed.
- **RipplePhase**'s firework burst now gets a launch trail first: a `graph_walk.Rocket` climbs straight up from the bottom row to the burst's own target column/row, and only once it arrives does the burst itself (radiating outward with per-dot brightness that fades individually plus a scatter of spark dots -- also retuned bigger/richer on request, 2026-08-24: wider radius, more sparks, varying brightness instead of a flat lit/unlit ring) begin expanding.

## Interaction

None beyond the shared quit/pause controls.

## Assets

Shares the LED rendering framework with `led.md` and `title.md`. Its dot-matrix renderer (`framework/led_grid.py`'s `DotMatrixDisplay`) and 5x7 digit font are new as of this demo; `title.md` should extend rather than fork them.

## Future polish (out of scope for now)

- A dot-matrix alphabet (currently digits, space, and "-" only -- see `led_grid.DOT_FONT`), if a demo ever needs to scroll real words instead of numbers.
- Confirm the "1991" credit and the marquee's default text with Bruce; both are LED's own values reused by assumption, not verified for LED II.
- LED intensity is now done for LED II's own fireworks (`led_grid.lerp_color`, `DotMatrixDisplay.render_raw`'s intensity-dict support, `graph_walk.Burst`'s per-node fade) -- but LED's own `ExplosionPhase`/power-up flicker don't use it yet, and neither does LED II's power-up flicker or column sweep. Worth revisiting whether those should too, for consistency.
- The timing-momentum and synthesized-beep polish items tracked in `PLAN.md`'s "Future framework polish" still apply here, once built.
