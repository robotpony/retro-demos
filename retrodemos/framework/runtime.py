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
    canvas = Canvas(demo.NATIVE_SIZE, scale=scale)
    flags = pygame.FULLSCREEN if fullscreen else 0
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
                demo.handle_event(event)

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
