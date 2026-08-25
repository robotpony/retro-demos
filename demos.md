# Demos

Tracking list for the pygame recreations described in `README.md`. One row per demo. Update the Build column as work progresses. Each Spec file lives at `docs/<name>.md`, where `<name>` is a kebab-case slug of the Demo column (e.g. `docs/tank-status-window.md`), not the source image name, since grouped demos cover more than one image. All eight specs are written (README priority 1 is done; Dooley's spec was written and later removed when the demo was cut, see Excluded below).

Two images informed the grouping decisions below, resolved with Bruce on 2026-08-24: `CARDS.png` + `BACKS.png` are one demo, `CT_ANI.png` + `CT_PRTS.png` are one demo, `WINDOW1.png` and `WIN1.png` are separate demos, and `warped-retro-the-next-thumb.png` is excluded as the blog post's own thumbnail rather than a screenshot of an original program.

The shared framework itself (`retrodemos/framework/`: canvas, keys, `Demo` base, runtime, CLI) is built and tested; no individual demo below has started yet. See `CLAUDE.md` for commands and `PLAN.md` for the architecture.

## Demos

| Demo | Source image(s) | Mode | Spec | Build |
|---|---|---|---|---|
| Bruce's 21 | `CARDS.png`, `BACKS.png` | Automated | [docs/bruces-21.md](docs/bruces-21.md) | Not started |
| Cinqtris | `CT_ANI.png`, `CT_PRTS.png` | Automated + one button (About popup) | [docs/cinqtris.md](docs/cinqtris.md) | Not started |
| CD Player | `CDPLAYER.png` | Automated, simulated audio | [docs/cd-player.md](docs/cd-player.md) | Built (`retrodemos/demos/cd_player.py`) |
| LED | `LED-thumb.png` | Automated | [docs/led.md](docs/led.md) | Built (`retrodemos/demos/led.py`) |
| LED II | `LED-II-thumb.png` | Automated | [docs/led-ii.md](docs/led-ii.md) | Built (`retrodemos/demos/led_ii.py`) |
| Title | `TITLE.png` | Automated | [docs/title.md](docs/title.md) | Built (`retrodemos/demos/title.py`) |
| Bruce's Windows | `WINDOW1.png` | Interactive (exception; reference UI chrome) | [docs/bruces-windows.md](docs/bruces-windows.md) | Not started |
| Tank Status Window | `WIN1.png` | Automated | [docs/tank-status-window.md](docs/tank-status-window.md) | Not started |

## Excluded

| Image | Reason |
|---|---|
| `warped-retro-the-next-thumb.png` | Blog post thumbnail ("Warped Visions" logo over a forest background), not a screenshot of an original 1990s program. |
| `DOOLEY1.png` | Dooley was built (2026-08-24: `BevelCellDisplay` renderer, LED strip + colour palette + RGB-spinner/grid area), then cut from the project on request -- not going to work well as a demo. Demo code, tests, spec, and renderer removed the same day. |

## Project-wide decisions

- All demos are automated attract-mode, except **Bruce's Windows**, which is functionally interactive. Its chrome is not shared with other demos; see `PLAN.md`.
- **Cinqtris** is the one automated demo with a single interactive control: its "MADMAX" cell is a button that opens an About popup.
- README priority 2 (shared CLI and keybindings) is designed in `PLAN.md`: a single launcher (`python -m retrodemos <name>`) owns argument parsing, and Esc/Q, Space, and R are handled once for every demo.
- The LED framework's scope (shared by LED, LED II, and Title) is settled in `PLAN.md`: it owns both the grid renderer and the common scroll/cycle content helpers.
- End state (logged 2026-08-24, not scheduled -- see `PLAN.md`'s "Future: the unified desktop"): every demo above eventually runs as its own window inside Bruce's Windows' desktop chrome, not as a standalone `python -m retrodemos <name>` launch. Deferred until every demo in this table is built.

## Open questions

Per-demo open questions now live in each spec file. `docs/tank-status-window.md` still has one open: its button icon set will be a custom monochrome pixel set, but the specific icons are deferred until that demo is built (build order 8 in `PLAN.md`).
