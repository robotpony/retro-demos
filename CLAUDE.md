# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

Framework scaffolded (`retrodemos/framework/`), no demos built yet. See `PLAN.md` for the architecture and build order; see `demos.md` for per-demo spec/build status.

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

Four demos (Dooley, LED, LED II, Title) will share `framework/led_grid.py` (not yet built — lands with the LED demo, build order 1 in `PLAN.md`) for their cell-grid rendering and scroll/cycle animation helpers. Window chrome is deliberately *not* shared: Bruce's Windows, CD Player, and Tank Status Window each draw their own borders/title bars independently (rationale in `PLAN.md`'s "Window chrome" section).

## Planned workflow (from README priorities, in order)

1. Mini-spec per demo in `docs/<name>.md`. Done.
2. Shared interface design. Done — see `PLAN.md`. Framework scaffold (canvas, keys, `Demo` base, runtime, CLI) built and tested; `led_grid.py` deferred to the LED demo's build slot.
3. Build and iterate on each demo, timeboxed to 1 day per demo, in the order in `PLAN.md`'s "Build order" table.
4. Polish pass on each demo, timeboxed to +1 day per demo.
5. Add an `index.html` that highlights the demos, similar to `~/projects/peep --preview`'s format.
6. Document and publish to GitHub.
7. Write a retrospective/nostalgia post about the project.

Check `demos.md` for per-demo status (Spec/Build columns) before starting work on a specific demo.
