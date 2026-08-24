# Demos

Tracking list for the pygame recreations described in `README.md`. One row per demo. Update the Spec and Build columns as work progresses; each Spec file lives at `docs/<name>.md` once written (per README priority 1, none exist yet).

Two images informed the grouping decisions below, resolved with Bruce on 2026-08-24: `CARDS.png` + `BACKS.png` are one demo, `CT_ANI.png` + `CT_PRTS.png` are one demo, `WINDOW1.png` and `WIN1.png` are separate demos, and `warped-retro-the-next-thumb.png` is excluded as the blog post's own thumbnail rather than a screenshot of an original program.

## Demos

| Demo | Source image(s) | What it shows | Spec | Build |
|---|---|---|---|---|
| Bruce's 21 | `CARDS.png`, `BACKS.png` | Full A-K playing card deck (4 suits) plus two card-back designs labelled "Bruce's 21". Likely a blackjack-family card game. | Not written | Not started |
| Cinqtris | `CT_ANI.png`, `CT_PRTS.png` | Tetris-style game titled "CINQTRIS". `CT_ANI` is the title/score screen (vertical red/green level bars, "MAX" readout); `CT_PRTS` is the asset sheet (gem/tile colour palette, bitmap font, button-state sprites). | Not written | Not started |
| CD Player | `CDPLAYER.png` | CD player interface: numeric LED track/time readout, transport buttons (play/pause/stop/skip), and a bank of vertical sliders (likely an equalizer). | Not written | Not started |
| Dooley | `DOOLEY1.png` | LED-style display with colour pixels down the left edge. Shares the LED demo framework (see LED, LED II, and Title below); its own colour-pixel column is what distinguishes it. | Not written | Not started |
| LED | `LED-thumb.png` | Seven-segment digit display, single row (like a digital clock or counter readout). Built on the shared LED demo framework; animates text/digits in the style specific to this display type. | Not written | Not started |
| LED II | `LED-II-thumb.png` | Dot-matrix LED display, rows of red dots (likely a scrolling text/marquee display). Built on the shared LED demo framework; animates in the style specific to this display type. | Not written | Not started |
| Title | `TITLE.png` | LED bit-pattern demo. Per Bruce: the two pattern sets at the bottom are read column by column, left to right, each column a set of bits representing a vertical line with values 0-255. Built on the shared LED demo framework; animates in the style specific to this display type. | Not written | Not started |
| Bruce's Windows | `WINDOW1.png` | Windows 3.1-style chrome: title bar, a "Welcome to Bruce's Windows" dialog with a "Got it" button, and a status bar. Candidate reference for the shared in-demo UI framework mentioned in the README, but tracked as its own demo per Bruce's answer. | Not written | Not started |
| Tank Status Window | `WIN1.png` | A window titled "Tank Status Window" containing a large red/black dot-matrix grid and a row of icon buttons along the bottom. Shows an automated, single-player COMBAT (Atari 2600 style) game running in the grid; the bottom row uses placeholder monochrome emoji as stand-ins for the demo's control buttons. | Not written | Not started |

## Excluded

| Image | Reason |
|---|---|
| `warped-retro-the-next-thumb.png` | Blog post thumbnail ("Warped Visions" logo over a forest background), not a screenshot of an original 1990s program. |

## Open questions

- **Tank simulation fidelity.** For Tank Status Window, confirm whether the automated COMBAT-style demo needs real game logic (collision, scoring, AI movement) or a scripted/looping animation that just reads as gameplay.
- **Emoji button rendering.** Pygame has no built-in colour emoji rendering. "Monochrome emoji" placeholder buttons likely means a small bitmap/glyph sprite set rather than literal Unicode emoji characters; confirm before building the shared button framework so it isn't built twice.
- **LED framework scope.** Dooley, LED, LED II, and Title share a demo framework but each animates differently. Confirm what the shared module actually owns (e.g. LED-cell rendering, colour/on-off state) versus what's per-demo (the animation/content driving those cells), so `docs/` specs for the four don't duplicate the framework description.
