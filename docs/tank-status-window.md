# Tank Status Window

**Source:** `WIN1.png`
**Mode:** Automated attract-mode

## What it shows

A window titled "Tank Status Window" containing a large red/black dot-matrix grid, a smaller secondary dot-matrix strip beneath it, and a row of blank grey buttons along the bottom. In the source image the grid is a uniform solid block (no game state visible) and the buttons carry no icon art at all.

## Behaviour

An automated, single-player COMBAT (Atari 2600 style) game plays itself within the grid. Tanks, walls, and bullets are recreated and animated, but rendered in the same red/black dot-matrix style as `WIN1.png` rather than as full-colour sprites.

## Interaction

None beyond the shared quit/pause controls. The bottom-row buttons are placeholder monochrome icons that visually support the demo; they are decorative, not required to be functional.

## Assets

No existing sprite sheet; the dot-matrix rendering is custom-drawn.

## Open questions

- **Simulation fidelity.** Whether "plays itself" needs real game logic (collision, scoring, AI movement) or a scripted/looping animation that just reads as gameplay isn't decided. Treat as scripted/looping unless told otherwise, since it's cheaper and the dot-matrix rendering hides the difference.
- The exact bottom-button icon set isn't defined; none are visible in the source image. Treat as a small fixed row of generic monochrome icons unless told otherwise.
- "Monochrome emoji" placeholders likely means a small bitmap/glyph sprite set rather than literal Unicode emoji characters (pygame has no built-in colour emoji rendering); confirm before building the shared button framework so it isn't built twice.
