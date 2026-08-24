# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

Framework built (`retrodemos/framework/`). LED is the first demo built (`retrodemos/demos/led.py` + `led_phases.py`), a scripted sequence rather than a single behaviour — see its phases for the pattern a multi-stage demo follows. See `PLAN.md` for the architecture and build order; see `demos.md` for per-demo spec/build status.

## What this project is

Recreations of demo/UI programs Bruce originally wrote in the early 1990s for the Atari ST and early Windows machines. Each image in `images/` is a screenshot of one original program; most map to their own demo app, but a few closely related images share a single demo (see `demos.md` for the groupings). The demos are written in pygame-ce, and all of them share one CLI, one set of in-demo keybindings, and a common `Demo` interface, all defined in `retrodemos/framework/` (design rationale in `PLAN.md`).

## Commands

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# List / run a demo
.venv/bin/python -m retrodemos --list
.venv/bin/python -m retrodemos <name> [--scale N] [--fps N] [--fullscreen]

# Tests (headless; SDL_VIDEODRIVER must be dummy, conftest.py sets it too)
SDL_VIDEODRIVER=dummy .venv/bin/python -m pytest tests/
SDL_VIDEODRIVER=dummy .venv/bin/python -m pytest tests/test_smoke.py::test_name  # single test
```

## Architecture

`retrodemos/__main__.py` is the single entry point for every demo (`python -m retrodemos <name>`). It owns argument parsing and discovers demos by scanning `retrodemos/demos/` for modules exposing a module-level `DEMO_CLASS` (a `Demo` subclass) — a new demo needs no launcher changes, just a module in that package.

`retrodemos/framework/runtime.py`'s `run()` drives every demo identically: it owns the window, the fixed-integer-scale canvas (`canvas.py`), and the shared keybindings (`keys.py`: Esc/Q quit, Space pause, R restart, consumed before a demo ever sees them). A demo only implements `handle_event` / `update` / `draw` / `reset` (`framework/demo.py`) — no demo touches `pygame.display` or the event loop directly. This split is also what makes `tests/test_smoke.py` possible headlessly: tests drive `run()` against a trivial in-test `Demo` with `max_frames` set, no real display needed.

Four demos (Dooley, LED, LED II, Title) share `framework/led_grid.py` for their cell-grid rendering and scroll/cycle animation helpers. It currently only implements the seven-segment renderer LED needs (`SevenSegmentDisplay`, `render_raw` for per-segment control, `segment_adjacency` for the graph LED's snake/explosion phases path through); LED II, Title, and Dooley need a dot-matrix grid style this module doesn't have yet — extend it when building those, don't fork a parallel renderer. Window chrome is deliberately *not* shared: Bruce's Windows, CD Player, and Tank Status Window each draw their own borders/title bars independently (rationale in `PLAN.md`'s "Window chrome" section).

A demo can be a single behaviour, or (like LED) a scripted sequence of phases that runs on a loop: a small `Phase` base class (`update(dt) -> bool` returns True when finished, `draw(surface)`) with the demo itself just holding a phase list and index, advancing and calling `reset()` on the next phase when the current one finishes. See `retrodemos/demos/led_phases.py` for the pattern; reuse it for any other demo whose spec describes multiple stages rather than one continuous behaviour.

Extracting a demo's exact pixel font/grid from its source image is its own worked-out method — see `docs/pixel-archaeology.md` before starting that part of a new demo. The short version: don't hand-derive geometry by eye; find a repeated "clean" tile in the source, reconstruct the whole image from your rendering code, and diff it byte-for-byte against the source before trusting it.

## Planned workflow (from README priorities, in order)

1. Mini-spec per demo in `docs/<name>.md`. Done.
2. Shared interface design. Done — see `PLAN.md`.
3. Build and iterate on each demo, timeboxed to 1 day per demo, in the order in `PLAN.md`'s "Build order" table. In progress — LED done, LED II next.
4. Polish pass on each demo, timeboxed to +1 day per demo.
5. Add an `index.html` that highlights the demos, similar to `~/projects/peep --preview`'s format.
6. Document and publish to GitHub.
7. Write a retrospective/nostalgia post about the project.

Check `demos.md` for per-demo status (Spec/Build columns) before starting work on a specific demo.
