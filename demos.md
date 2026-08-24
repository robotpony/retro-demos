# Demos

Tracking list for the pygame recreations described in `README.md`. One row per demo. Update the Build column as work progresses. Each Spec file lives at `docs/<name>.md`, where `<name>` is a kebab-case slug of the Demo column (e.g. `docs/tank-status-window.md`), not the source image name, since grouped demos cover more than one image. All nine specs are written (README priority 1 is done).

Two images informed the grouping decisions below, resolved with Bruce on 2026-08-24: `CARDS.png` + `BACKS.png` are one demo, `CT_ANI.png` + `CT_PRTS.png` are one demo, `WINDOW1.png` and `WIN1.png` are separate demos, and `warped-retro-the-next-thumb.png` is excluded as the blog post's own thumbnail rather than a screenshot of an original program.

## Demos

| Demo | Source image(s) | Mode | Spec | Build |
|---|---|---|---|---|
| Bruce's 21 | `CARDS.png`, `BACKS.png` | Automated | [docs/bruces-21.md](docs/bruces-21.md) | Not started |
| Cinqtris | `CT_ANI.png`, `CT_PRTS.png` | Automated + one button (About popup) | [docs/cinqtris.md](docs/cinqtris.md) | Not started |
| CD Player | `CDPLAYER.png` | Automated, simulated audio | [docs/cd-player.md](docs/cd-player.md) | Not started |
| Dooley | `DOOLEY1.png` | Automated | [docs/dooley.md](docs/dooley.md) | Not started |
| LED | `LED-thumb.png` | Automated | [docs/led.md](docs/led.md) | Not started |
| LED II | `LED-II-thumb.png` | Automated | [docs/led-ii.md](docs/led-ii.md) | Not started |
| Title | `TITLE.png` | Automated | [docs/title.md](docs/title.md) | Not started |
| Bruce's Windows | `WINDOW1.png` | Interactive (exception; reference UI chrome) | [docs/bruces-windows.md](docs/bruces-windows.md) | Not started |
| Tank Status Window | `WIN1.png` | Automated | [docs/tank-status-window.md](docs/tank-status-window.md) | Not started |

## Excluded

| Image | Reason |
|---|---|
| `warped-retro-the-next-thumb.png` | Blog post thumbnail ("Warped Visions" logo over a forest background), not a screenshot of an original 1990s program. |

## Project-wide decisions

- All demos are automated attract-mode, except **Bruce's Windows**, which is functionally interactive and may double as the reference for the shared UI framework (README priority 2, not yet designed).
- **Cinqtris** is the one automated demo with a single interactive control: its "MADMAX" cell is a button that opens an About popup.

## Open questions

Per-demo open questions now live in each spec file. Remaining cross-demo questions:

- **LED framework scope.** Dooley, LED, LED II, and Title share a demo framework but each animates differently (colour-pixel column, digits, dot-matrix scroll, bit-pattern columns). What the shared module owns (e.g. LED-cell rendering, colour/on-off state) versus what's per-demo (the content driving those cells) isn't decided yet.
- **Shared CLI/keybinding framework.** README priority 2. Most specs above reference "shared quit/pause controls" without those controls being defined yet (Cinqtris and Bruce's Windows are the exceptions, per their own Interaction sections).
