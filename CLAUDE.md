# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

Framework built (`retrodemos/framework/`). LED, LED II, and Title are all built (`retrodemos/demos/led.py`+`led_phases.py`, `led_ii.py`+`led_ii_phases.py`, `title.py`+`title_phases.py`), each a scripted sequence rather than a single behaviour — see any demo's phases for the pattern a multi-stage demo follows, and `framework/phase.py`/`graph_walk.py`/`ticker.py` for the machinery all three share. (Title started as a single continuous behaviour, then was rebuilt into the same 5-phase script as its siblings once that was confirmed as the right shape for it too — every demo built so far has ended up wanting a scripted sequence.) Title needed its own renderer (`led_grid.BitColumnDisplay`) rather than reusing LED II's `DotMatrixDisplay` — its source image's pixel model turned out different enough (no bezel, no gap between columns, content computed from a byte value rather than a font) that forcing the reuse would have meant bending the abstraction, not applying it; see PLAN.md's "LED grid module" section before assuming a new demo fits an existing renderer. Because Title has two colour strips rather than one display, its phases drive both together through `TitleDisplays` (in `title.py`), not a single display object the way LED/LED II's phases do. See `PLAN.md` for the architecture and build order; see `demos.md` for per-demo spec/build status.

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

Four demos (Dooley, LED, LED II, Title) share `framework/led_grid.py`, but it turned out to hold three distinct renderer classes rather than one generic grid abstraction configured three ways — each demo's source image had its own pixel model closely enough that forcing a shared shape would have fought the source rather than matched it (see PLAN.md's "LED grid module" section for the full per-demo table and that history): `SevenSegmentDisplay` (LED: `render_raw` for per-segment control, `segment_adjacency` for the graph LED's snake/explosion phases path through), `DotMatrixDisplay` (LED II: `render_raw` for per-dot control, `text_dots` for its smoothly-scrolling marquee, `dot_grid_adjacency` for its snake/ripple phases, `DOT_FONT` for its 5x7 digit font), and `BitColumnDisplay` (Title: `render_values` for its byte-value-per-column content, `render_raw` for its snake/fireworks phases to address individual `(col, bit)` cells directly, no bezel, no gap between columns — a genuinely different pixel model, not a `DotMatrixDisplay` extension despite that being the original plan). `dot_grid_adjacency` is pure `(col, row)` topology with no dot-specific assumptions, so Title's bit grid reuses it directly (`dot_grid_adjacency(width, BitColumnDisplay.ROWS)`) rather than needing a near-duplicate "bit grid" function. Dooley's colour side-column is still open; check its own source image before assuming it fits one of the three rather than needing its own. Window chrome is deliberately *not* shared: Bruce's Windows, CD Player, and Tank Status Window each draw their own borders/title bars independently (rationale in `PLAN.md`'s "Window chrome" section).

A demo can be a single behaviour, or (like LED, LED II, and Title) a scripted sequence of phases that runs on a loop: `framework/phase.py`'s `Phase` base class (`update(dt) -> bool` returns True when finished, `draw(surface)`) plus `PhaseSequence`, which owns the phase list and index and runs it — advancing and calling `reset()` on the next phase when the current one finishes, looping back to the first phase after the last. A scripted demo builds its phase list in `__init__`, wraps it in a `PhaseSequence`, and delegates its own `update`/`draw`/`reset` to it (see `LedDemo`/`LedIIDemo`/`TitleDemo`); `retrodemos/demos/led_phases.py`, `led_ii_phases.py`, and `title_phases.py` have each demo's own `Phase` subclasses, the actual choreography. `Phase.display` doesn't have to be a single display object — Title's phases get `TitleDisplays` (in `title.py`), a small composite that drives both of its colour strips together, since Title's script is one script over two displays, not two independent ones. Reuse `Phase`/`PhaseSequence` as-is for any other demo whose spec describes multiple stages rather than one continuous behaviour — the sequencing itself needs no per-demo code (in practice, every demo built so far has ended up wanting one). A phase that advances in discrete steps (not continuously) should use `framework/ticker.py`'s `Ticker` for its dt-accumulation rather than hand-rolling one: LED's phases originally did this by hand and inconsistently, which is a live desync risk on a slow frame (see `Ticker`'s docstring). A phase that crawls or bursts across a grid (a snake, a radiating ripple/explosion) should use `framework/graph_walk.py`'s `Snake`/`bfs_rings`/`Burst` over that display's own adjacency graph (`segment_adjacency` or `dot_grid_adjacency`) rather than hand-rolling the walk — LED, LED II, and Title's snake/burst phases all share this now.

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
