"""Power-up pickups must glow faintly, not paint a solid disc.

The faint fill used to be drawn with an RGBA colour straight onto the
plain world surface, which has no alpha channel - pygame dropped the
alpha and the fill came out fully opaque, hiding the ring. The fill is
now drawn on a small SRCALPHA surface and blitted on.
"""

import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

import config
from powerups import PowerUp


def _blend(color, bg, alpha=60):
    # what a 60/255 alpha fill of color over bg looks like, per channel
    return tuple(
        (c * alpha + b * (255 - alpha) + 127) // 255
        for c, b in zip(color, bg)
    )


def _close(actual, expected, tol=1):
    # SDL rounds the blend; allow a unit either way
    return all(abs(a - e) <= tol for a, e in zip(actual, expected))


def _draw_powerup(kind):
    pygame.init()
    surf = pygame.Surface((config.WIDTH, config.HEIGHT))
    surf.fill(config.BG_COLOR)
    PowerUp(200, 200, kind=kind).draw(surf)
    return surf


def test_powerup_fill_is_faint_not_opaque():
    # fresh power-up: t=0 so pulse is 1.0 and r=14, life 9s so no blink.
    # sample inside the disc near the edge, clear of the centred label
    surf = _draw_powerup("spread")
    try:
        fill = surf.get_at((211, 200))[:3]
        assert _close(fill, _blend(config.NEON_YELLOW, config.BG_COLOR)), fill
        # the ring at the disc edge stays full strength
        ring = surf.get_at((213, 200))[:3]
        assert ring == config.NEON_YELLOW, ring
    finally:
        pygame.quit()


def test_powerup_fill_blend_is_not_colour_specific():
    # same faint fill for a different kind (cyan shield), not just yellow
    surf = _draw_powerup("shield")
    try:
        fill = surf.get_at((211, 200))[:3]
        assert _close(fill, _blend(config.NEON_CYAN, config.BG_COLOR)), fill
        ring = surf.get_at((213, 200))[:3]
        assert ring == config.NEON_CYAN, ring
    finally:
        pygame.quit()
