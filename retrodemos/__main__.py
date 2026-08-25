"""Single CLI entry point for every demo: `python -m retrodemos <name>`.

Owns argument parsing once so no demo duplicates it. A demo is any module in
retrodemos/demos/ that exposes a module-level DEMO_CLASS (a Demo subclass).

`python -m retrodemos` with no name opens the desktop shell (`demos/desktop.py`,
`DESKTOP_DEMO_NAME` below) instead of printing `--list`'s text dump -- the
settled spec for `PLAN.md`'s "Future: the unified desktop" (2026-08-25):
the desktop is the root interface of `retrodemos` itself now, not just
another demo, though it's still launchable by name
(`python -m retrodemos desktop`) like any other for dev/testing. `--list`
stays available as an explicit flag for the old text listing.
"""

from __future__ import annotations

import argparse
import importlib
import pkgutil
import sys

import pygame

from retrodemos import demos as demos_package
from retrodemos.framework.demo import Demo
from retrodemos.framework.runtime import run

DESKTOP_DEMO_NAME = "desktop"


def available_demos() -> list[str]:
    """Every module in retrodemos/demos/ that actually exposes a
    module-level DEMO_CLASS -- a helper module a demo depends on (e.g.
    led_phases.py, led_ii_phases.py) lives in the same package but isn't
    itself runnable, so it's excluded rather than listed as if it were."""
    names = []
    for _, name, _ in pkgutil.iter_modules(demos_package.__path__):
        module = importlib.import_module(f"retrodemos.demos.{name}")
        if hasattr(module, "DEMO_CLASS"):
            names.append(name)
    return sorted(names)


def load_demo(name: str, *, text: str | None = None) -> Demo:
    module = importlib.import_module(f"retrodemos.demos.{name}")
    return module.DEMO_CLASS(text=text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="retrodemos",
        description="Retro pygame demos. Run one by name, or use --list to see what's available.",
    )
    parser.add_argument("name", nargs="?", help="Demo to run (see --list).")
    parser.add_argument("--list", action="store_true", help="List available demos and exit.")
    parser.add_argument("--scale", type=int, default=3, help="Integer scale factor (default: 3).")
    parser.add_argument("--fps", type=int, default=60, help="Frame rate cap (default: 60).")
    parser.add_argument("--fullscreen", action="store_true", help="Run fullscreen.")
    parser.add_argument(
        "--text", default=None, help="Override a demo's default text/message, for demos that use it."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    demos = available_demos()

    if args.list:
        if demos:
            print("Available demos:")
            for name in demos:
                print(f"  {name}")
        else:
            print("No demos yet. See PLAN.md's build order.")
        return 0

    name = args.name or DESKTOP_DEMO_NAME
    if name not in demos:
        print(f"Unknown demo: {name!r}. Use --list to see available demos.", file=sys.stderr)
        return 1

    pygame.init()
    try:
        demo = load_demo(name, text=args.text)
        run(demo, scale=args.scale, fps=args.fps, fullscreen=args.fullscreen)
    finally:
        pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
