# Demos

Tracking list for the pygame recreations described in `README.md`. One row per demo. Update the Build column as work progresses. Each Spec file lives at `docs/<name>.md`, where `<name>` is a kebab-case slug of the Demo column (e.g. `docs/tank-status-window.md`), not the source image name, since grouped demos cover more than one image. All eight specs are written (README priority 1 is done; Dooley's spec was written and later removed when the demo was cut, see Excluded below).

Two images informed the grouping decisions below, resolved with Bruce on 2026-08-24: `CARDS.png` + `BACKS.png` are one demo, `CT_ANI.png` + `CT_PRTS.png` are one demo, `WINDOW1.png` and `WIN1.png` are separate demos, and `warped-retro-the-next-thumb.png` is excluded as the blog post's own thumbnail rather than a screenshot of an original program.

The shared framework itself (`retrodemos/framework/`: canvas, keys, `Demo` base, runtime, CLI) is built and tested; no individual demo below has started yet. See `CLAUDE.md` for commands and `PLAN.md` for the architecture.

## Demos

| Demo | Source image(s) | Mode | Spec | Build |
|---|---|---|---|---|
| Bruce's 21 | `CARDS.png`, `BACKS.png` | Automated | [docs/bruces-21.md](docs/bruces-21.md) | Built (`retrodemos/demos/bruces_21.py`) |
| Cinqtris | `CT_ANI.png` | Automated + click-to-slide MADMAX | [docs/cinqtris.md](docs/cinqtris.md) | Built (`retrodemos/demos/cinqtris.py`) |
| CD Player | `CDPLAYER.png` | Interactive (drag/focus two windows), simulated audio | [docs/cd-player.md](docs/cd-player.md) | Built (`retrodemos/demos/cd_player.py`) |
| LED | `LED-thumb.png` | Automated | [docs/led.md](docs/led.md) | Built (`retrodemos/demos/led.py`) |
| LED II | `LED-II-thumb.png` | Automated | [docs/led-ii.md](docs/led-ii.md) | Built (`retrodemos/demos/led_ii.py`) |
| Title | `TITLE.png` | Automated | [docs/title.md](docs/title.md) | Built (`retrodemos/demos/title.py`) |
| Bruce's Windows | `WINDOW1.png` | Interactive (exception; reference UI chrome) | [docs/bruces-windows.md](docs/bruces-windows.md) | Built (`retrodemos/demos/bruces_windows.py`) |
| Tank Status Window | `WIN1.png` | Automated | [docs/tank-status-window.md](docs/tank-status-window.md) | Built (`retrodemos/demos/tank_status_window.py`) |

## Excluded

| Image | Reason |
|---|---|
| `warped-retro-the-next-thumb.png` | Blog post thumbnail ("Warped Visions" logo over a forest background), not a screenshot of an original 1990s program. |
| `DOOLEY1.png` | Dooley was built (2026-08-24: `BevelCellDisplay` renderer, LED strip + colour palette + RGB-spinner/grid area), then cut from the project on request -- not going to work well as a demo. Demo code, tests, spec, and renderer removed the same day. |

## Project-wide decisions

- All demos are automated attract-mode, except **Bruce's Windows** and **CD Player**, which are functionally interactive (CD Player's own main and equalizer windows can each be dragged and clicked to front, added 2026-08-25 once playtesting showed they're genuinely separate windows in the source, not one panel). Neither's chrome is shared with other demos; see `PLAN.md`.
- **Cinqtris** is an automated demo (wordmark + cascading equalizer, stacked vertically and centred) with a single interactive control: clicking anywhere slides a "MADMAX" logo across the screen and off the far edge. Its original spec described a "MADMAX" button opening an About popup instead; that was descoped in favour of the slide during design review (2026-08-25), see `docs/cinqtris.md`'s Open questions.
- README priority 2 (shared CLI and keybindings) is designed in `PLAN.md`: a single launcher (`python -m retrodemos <name>`) owns argument parsing, and Esc/Q, Space, and R are handled once for every demo.
- The LED framework's scope (shared by LED, LED II, and Title) is settled in `PLAN.md`: it owns both the grid renderer and the common scroll/cycle content helpers.
- Desktop shell (`retrodemos/demos/desktop.py`, spec logged 2026-08-24, built 2026-08-25 -- see `PLAN.md`'s "Future: the unified desktop"): `python -m retrodemos` with no name now opens a 1024x576 desktop with one icon per built demo; click to open it as its own draggable/closable window (`framework/window_chrome.py`), the same as a real desktop would host several little utility programs at once. `python -m retrodemos <name>` still runs any one demo standalone. All eight planned demos now have icons (LED, LED II, Title, CD Player, Bruce's Windows' own exhibit, Cinqtris, Bruce's 21, and Tank Status Window). A macOS-style top menu bar (added 2026-08-25) sits above every window: white, exactly a line of `pixel_font` text tall, bold (no shadow -- an earlier drop-shadow version was replaced once seen live), a ⌘ icon with a functional dropdown (About / Close All Windows / Quit) at the left, and the focused window's name after it, or "HELP" (click it for a condensed README panel) when nothing is focused. CD Player's icon is special-cased to open two independent top-level windows (main + equalizer, the equalizer hidden until revealed) rather than the generic one-window-per-icon path every other demo uses -- see `desktop.py`'s own module docstring. An open demo's icon dims instead of disappearing (2026-08-25: disappearing read as "weird"); Bruce's Windows' own icon is disabled outright for now, a demo of windowing chrome feeling redundant on a desktop that's itself a real windowing system.
- **Bruce's 21** (2026-08-25) is the first demo to load its source PNGs (`CARDS.png`, `BACKS.png`) at runtime rather than hand-encoding pixel data -- confirmed with Bruce: 52 detailed card faces plus 2 backs is too much art to transcribe by hand accurately. See `retrodemos/demos/bruces_21.py`'s module docstring for the full account, including the `CARDS.png` 14th column of non-card splash art that's out of scope for now.
- **Tank Status Window** (2026-08-25) is the eighth and last of the originally planned demos. `WIN1.png`'s own grid turned out to be a lit-everywhere test pattern, not a captured game frame, so the "COMBAT plays itself" behaviour is entirely invented, scripted/looping content (patrol -> engage -> reset) built on `Phase`/`PhaseSequence`, `graph_walk.Burst` for every explosion, and `pixel_font`'s alphabet for the secondary strip's status text -- see `retrodemos/demos/tank_status_window_phases.py`'s module docstring.

## Open questions

Per-demo open questions now live in each spec file. All 8 planned demos are built; `docs/tank-status-window.md` still notes one open item (a possible custom icon set for its decorative button row, not required for the demo to work).
