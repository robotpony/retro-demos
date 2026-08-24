# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

Pre-implementation. There is no code and no `requirements.txt` yet. The repo holds reference images (`images/`), written mini-specs for all nine demos (`docs/`), and the README below. Do not assume a pygame project structure exists; you will likely be creating it.

## What this project is

Recreations of demo/UI programs Bruce originally wrote in the early 1990s for the Atari ST and early Windows machines. Each image in `images/` is a screenshot of one original program; most map to their own demo app, but a few closely related images share a single demo (see `demos.md` for the groupings). The demos are to be written in pygame, and all of them should share:

- The same command-line interface
- The same in-demo key command interface (a shared framework, not reimplemented per demo)

## Planned workflow (from README priorities, in order)

1. Analyze each image in `images/`, grouping related images into one demo where appropriate, and write a mini-spec per demo as `docs/<name>.md` (named after the demo, not the source image; see `demos.md` for the demo list and groupings). Done — all nine specs are written.
2. Design the shared interface: the common CLI and the common in-demo key commands used across all demos.
3. Build and iterate on each demo, timeboxed to 1 day per demo.
4. Polish pass on each demo, timeboxed to +1 day per demo.
5. Add an `index.html` that highlights the demos, similar to `~/projects/peep --preview`'s format.
6. Document and publish to GitHub.
7. Write a retrospective/nostalgia post about the project.

Check `demos.md` for per-demo status (Spec/Build columns) before starting work on a specific demo.
