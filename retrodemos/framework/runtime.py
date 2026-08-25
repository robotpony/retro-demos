"""The loop that drives a Demo: events in, update, draw, scale, present.

Split out from __main__.py so tests can call run() directly against a real
or trivial Demo, headlessly (SDL_VIDEODRIVER=dummy) and with max_frames set,
without going through the CLI.
"""

from __future__ import annotations

import pygame

from .canvas import Canvas
from .demo import Demo
from .keys import handle_shared_keys

_MOUSE_POS_EVENTS = (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP)


def _to_native_space(event: pygame.event.Event, scale: int) -> pygame.event.Event:
    """Mouse events carry real window-pixel coordinates, but a demo draws
    (and should think) entirely in its own native resolution -- it has no
    way to know the canvas scale runtime.run() was launched with. Rescale
    `pos` (and `rel`, for MOUSEMOTION) down to native space here, once, so
    every demo's handle_event() can treat event coordinates as native
    pixels without doing this conversion itself. First needed for Bruce's
    Windows (2026-08-24), the first interactive demo; Cinqtris's About
    button will want the same thing.

    Integer division matches Canvas's own nearest-neighbour scaling: each
    native pixel maps to exactly `scale` window pixels, so floor-dividing
    a window coordinate recovers the native pixel it falls within."""
    if scale == 1 or event.type not in _MOUSE_POS_EVENTS:
        return event
    data = dict(event.dict)
    data["pos"] = (event.pos[0] // scale, event.pos[1] // scale)
    if event.type == pygame.MOUSEMOTION:
        data["rel"] = (event.rel[0] // scale, event.rel[1] // scale)
    return pygame.event.Event(event.type, data)


# Rough allowance for OS chrome outside the usable desktop area (menu bar,
# dock, taskbar) that pygame.display.Info() doesn't account for -- keeps
# a fitted window from landing flush against the screen edge.
_SCREEN_MARGIN = (40, 80)


def _fit_scale(native_size: tuple[int, int], requested_scale: int) -> int:
    """Never hand back a scale that makes the window bigger than the
    screen -- the desktop shell's 1024x576 canvas at the CLI's default
    scale of 3 is 3072x1728, larger than most screens outright. Shrinks
    to the largest scale (down to 1) that still fits; never grows past
    what was requested, so small demos keep their usual 2-3x."""
    info = pygame.display.Info()
    screen_w, screen_h = info.current_w, info.current_h
    if screen_w <= 0 or screen_h <= 0:
        return requested_scale
    usable_w = max(1, screen_w - _SCREEN_MARGIN[0])
    usable_h = max(1, screen_h - _SCREEN_MARGIN[1])
    fit = min(usable_w // native_size[0], usable_h // native_size[1])
    return max(1, min(requested_scale, fit))


def run(
    demo: Demo,
    scale: int = 3,
    fps: int = 60,
    fullscreen: bool = False,
    max_frames: int | None = None,
) -> None:
    """Run demo until quit, or until max_frames frames have been drawn.

    max_frames is for tests; real runs leave it as None and rely on the quit
    keys or window close to end the loop. Caller is responsible for
    pygame.init()/pygame.quit().
    """
    if not fullscreen:
        fitted = _fit_scale(demo.NATIVE_SIZE, scale)
        if fitted != scale:
            print(f"retrodemos: scale {scale} would not fit the screen -- using {fitted} instead.")
        scale = fitted
    canvas = Canvas(demo.NATIVE_SIZE, scale=scale)
    # NOFRAME drops the OS title bar/border in windowed mode, so the window
    # reads as the retro program itself rather than a modern app window
    # around it; redundant (and skipped) under FULLSCREEN, which already has
    # no window chrome of its own.
    flags = pygame.FULLSCREEN if fullscreen else pygame.NOFRAME
    window = pygame.display.set_mode(canvas.window_size, flags)
    clock = pygame.time.Clock()

    paused = False
    frame = 0
    running = True
    while running:
        dt = clock.tick(fps) / 1000.0

        for event in pygame.event.get():
            signal = handle_shared_keys(event)
            if signal.quit:
                running = False
                continue
            if signal.toggle_pause:
                paused = not paused
                continue
            if signal.restart:
                demo.reset()
                continue
            if not signal.claimed:
                demo.handle_event(_to_native_space(event, scale))

        if not running:
            break

        if not paused:
            demo.update(dt)

        demo.draw(canvas.native_surface)
        canvas.present(window)
        pygame.display.flip()

        frame += 1
        if max_frames is not None and frame >= max_frames:
            running = False
