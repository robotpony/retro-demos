# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

Pre-implementation. There is no code, no `requirements.txt`, and no git history yet. The repo currently holds only reference images (`images/`), an empty `docs/` folder, and the README below. Do not assume a pygame project structure exists; you will likely be creating it.

## What this project is

Recreations of demo/UI programs Bruce originally wrote in the early 1990s for the Atari ST and early Windows machines. Each image in `images/` is a screenshot of one original program and is meant to become one demo app that reproduces its design. The demos are to be written in pygame, and all of them should share:

- The same command-line interface
- The same in-demo key command interface (a shared framework, not reimplemented per demo)

## Planned workflow (from README priorities, in order)

1. Analyze each image in `images/` and write a mini-spec for it as `docs/<IMAGE_NAME>.md` (one spec per image, named after the image file).
2. Design the shared interface: the common CLI and the common in-demo key commands used across all demos.
3. Build and iterate on each demo, timeboxed to 1 day per demo.
4. Polish pass on each demo, timeboxed to +1 day per demo.
5. Document and publish to GitHub.
6. Write a retrospective/nostalgia post about the project.

When asked to work on a specific demo, check whether its `docs/<name>.md` spec exists first; if not, that's step 1 and should happen before implementation.

## Notes

- `.gitignores` (plural) is not a filename git recognizes as an ignore file; `.DS_Store` currently shows as untracked in `git status` because of this. If cleaning up repo hygiene, this likely needs to be renamed to `.gitignore`.
