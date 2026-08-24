"""Fixed integer-scale pixel canvas.

Demos draw at their native pixel resolution; Canvas blits that up to the real
window at a fixed integer scale (nearest-neighbour, via pygame.transform.scale)
so the pixel-art look stays crisp instead of going soft or blurry.
"""

from __future__ import annotations

import pygame


class Canvas:
    def __init__(self, native_size: tuple[int, int], scale: int = 3) -> None:
        if scale < 1:
            raise ValueError(f"scale must be >= 1, got {scale}")
        self.native_size = native_size
        self.scale = scale
        self.native_surface = pygame.Surface(native_size)
        self.window_size = (native_size[0] * scale, native_size[1] * scale)

    def present(self, window: pygame.Surface) -> None:
        """Scale the native surface up and blit it onto the window surface."""
        if self.scale == 1:
            window.blit(self.native_surface, (0, 0))
            return
        scaled = pygame.transform.scale(self.native_surface, self.window_size)
        window.blit(scaled, (0, 0))
