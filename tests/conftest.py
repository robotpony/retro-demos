"""Headless pygame setup shared by every test.

SDL_VIDEODRIVER/SDL_AUDIODRIVER must be set to "dummy" before pygame touches
SDL, so this runs at import time, before the pygame import below.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402
import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _pygame_lifecycle():
    pygame.init()
    yield
    pygame.quit()
