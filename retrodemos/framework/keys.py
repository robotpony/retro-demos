"""Shared keybindings, handled once by the runtime for every demo.

| Key      | Action        |
|----------|---------------|
| Esc / Q  | Quit          |
| Space    | Pause/resume  |
| R        | Restart       |

See PLAN.md's "Shared keybindings" section. Demo-specific interaction (e.g.
Bruce's Windows' drag, Cinqtris's About button) is handled separately, in
each demo's own handle_event.
"""

from __future__ import annotations

from dataclasses import dataclass

import pygame

QUIT_KEYS = {pygame.K_ESCAPE, pygame.K_q}
PAUSE_KEY = pygame.K_SPACE
RESTART_KEY = pygame.K_r


@dataclass
class RuntimeSignal:
    quit: bool = False
    toggle_pause: bool = False
    restart: bool = False

    @property
    def claimed(self) -> bool:
        """Whether this event was one of the shared keys (and so shouldn't
        also be passed to the demo's own handle_event)."""
        return self.quit or self.toggle_pause or self.restart


def handle_shared_keys(event: pygame.event.Event) -> RuntimeSignal:
    """Check a single event against the shared keybindings.

    Returns a RuntimeSignal with everything False for events that aren't the
    window close button or one of the shared keys.
    """
    signal = RuntimeSignal()
    if event.type == pygame.QUIT:
        signal.quit = True
    elif event.type == pygame.KEYDOWN:
        if event.key in QUIT_KEYS:
            signal.quit = True
        elif event.key == PAUSE_KEY:
            signal.toggle_pause = True
        elif event.key == RESTART_KEY:
            signal.restart = True
    return signal
