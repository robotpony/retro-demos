"""Captures a representative PNG of every demo plus the desktop shell,
into screenshots/, for README.md. Not part of the test suite or the
shipped package -- re-run manually (SDL_VIDEODRIVER=dummy) whenever a
demo's visuals change enough to be worth re-capturing:

    SDL_VIDEODRIVER=dummy .venv/bin/python scripts/capture_screenshots.py

Each demo gets a fixed warm-up (simulated dt, not wall time, so this is
deterministic) chosen to land the capture mid-action -- a lit digit, a
marquee mid-scroll, cards mid-deal, tanks mid-patrol -- rather than on a
blank first frame or an early power-up flicker. Retune DEMO_WARMUPS if a
demo's own choreography timing changes enough to drift the capture back
to a boring frame.
"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

import pygame  # noqa: E402

pygame.init()

from retrodemos.__main__ import available_demos, load_demo  # noqa: E402

OUT_DIR = os.path.join(_REPO_ROOT, "screenshots")
SCALE = 2  # every demo's native canvas is small; upscale for README legibility

# (warm-up seconds of simulated time, dt per step) per demo -- see the
# module docstring for why these particular values were picked.
DEMO_WARMUPS = {
    "led": (2.0, 0.05),
    "led_ii": (8.0, 0.05),  # lands mid-marquee ("0123456789"), not the power-up sweep
    "title": (6.0, 0.05),  # lands mid-scroll, not the power-up sweep
    "cd_player": (5.0, 0.1),
    "bruces_windows": (0.0, 0.05),  # static content -- no warm-up needed
    "cinqtris": (2.0, 0.05),
    "bruces_21": (10.0, 0.05),  # lands mid-deal (AutoDealPhase), not the deck cycle
    "tank_status_window": (5.5, 0.05),  # lands in EngagePhase, tanks mid-exchange
}

# CD Player's own NATIVE_SIZE is a big standalone backdrop for its one
# small draggable window (docked near the top-left at MAIN_START_POS,
# 288x32) -- crop to just that window plus a small margin so the
# thumbnail isn't mostly empty backdrop, unlike every other demo here.
DEMO_CROPS = {
    "cd_player": (20, 8, 328, 60),
}


def capture(demo, warmup_seconds: float, dt: float, out_path: str, crop: tuple[int, int, int, int] | None = None) -> None:
    steps = max(1, int(warmup_seconds / dt))
    for _ in range(steps):
        demo.update(dt)
    surface = pygame.Surface(demo.NATIVE_SIZE)
    demo.draw(surface)
    if crop is not None:
        cropped = pygame.Surface((crop[2], crop[3]))
        cropped.blit(surface, (0, 0), crop)
        surface = cropped
    if SCALE != 1:
        w, h = surface.get_size()
        surface = pygame.transform.scale(surface, (w * SCALE, h * SCALE))
    pygame.image.save(surface, out_path)
    print(f"saved {out_path} ({surface.get_size()})")


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)

    # Desktop shell in its default state (icons visible, nothing open).
    desktop = load_demo("desktop")
    capture(desktop, 0.0, 0.05, os.path.join(OUT_DIR, "desktop.png"))

    for name in available_demos():
        if name == "desktop":
            continue
        warmup, dt = DEMO_WARMUPS.get(name, (1.0, 0.05))
        demo = load_demo(name)
        capture(demo, warmup, dt, os.path.join(OUT_DIR, f"{name}.png"), crop=DEMO_CROPS.get(name))


if __name__ == "__main__":
    main()
