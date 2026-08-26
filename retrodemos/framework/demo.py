"""The interface every demo implements.

The runtime (see runtime.py) drives a Demo generically: it owns the window,
scaling, and the shared quit/pause/restart keybindings, and calls into a Demo
only for what's specific to it. That split is also what makes headless
testing possible; tests can drive a Demo's update/draw loop directly, with no
real display.
"""

from __future__ import annotations

import pygame


class Demo:
    """Base class for a single demo.

    Subclasses set NATIVE_SIZE and override update/draw (and handle_event,
    reset, if they need them). Everything here has a working default so a
    minimal demo needs only NATIVE_SIZE and draw.

    __init__ must accept a keyword-only `text: str | None = None` (the
    launcher's --text always passes it, even to demos that ignore it), plus
    **kwargs for forward compatibility with future shared options.
    """

    #: Native pixel resolution, before the runtime scales it up for display.
    NATIVE_SIZE: tuple[int, int] = (320, 240)

    #: Optional convention, not enforced here (runtime.run() reads it via
    #: getattr with a False default): set True to ask the runtime to end
    #: the run, the same way Esc/Q does. Poll-based, not a callback -- set
    #: it in handle_event/update and the next frame's check picks it up.
    #: So far only the desktop shell's own menu-bar Quit item uses this.
    want_quit: bool = False

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle one event not already claimed by the shared keybindings.

        Quit (Esc/Q), pause (Space), and restart (R) are handled by the
        runtime and never reach here. Override for demo-specific interaction,
        e.g. Bruce's Windows' draggable title bar or Cinqtris's About button.
        """

    def update(self, dt: float) -> None:
        """Advance demo state by dt seconds. Not called while paused."""

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the current frame onto surface, which is NATIVE_SIZE in size."""

    def reset(self) -> None:
        """Reset demo state. Default no-op; override if there's state to reset."""
