"""Falling pickups: spread shot, rapid fire, shield."""

import math
import random

import pygame

import config


class PowerUp:
    KINDS = list(config.POWERUPS.keys())

    def __init__(self, x, y, kind=None):
        self.kind = kind or random.choice(self.KINDS)
        spec = config.POWERUPS[self.kind]
        self.color = spec["color"]
        self.label = spec["label"]
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(random.uniform(-20, 20),
                                       config.POWERUP_FALL_SPEED)
        self.life = config.POWERUP_LIFETIME
        self.radius = 14
        self.t = 0.0
        self.dead = False

    @staticmethod
    def maybe_drop(x, y):
        if random.random() < config.POWERUP_DROP_CHANCE:
            return PowerUp(x, y)
        return None

    def update(self, dt):
        self.t += dt
        self.life -= dt
        self.pos += self.vel * dt
        if self.life <= 0 or self.pos.y > config.HEIGHT + 20:
            self.dead = True

    def draw(self, surf):
        x, y = int(self.pos.x), int(self.pos.y)
        # blink faster as it expires
        if self.life < 2.0 and int(self.t * 10) % 2 == 0:
            return
        pulse = 1.0 + 0.12 * math.sin(self.t * 6)
        r = int(self.radius * pulse)
        pygame.draw.circle(surf, self.color, (x, y), r, 2)
        pygame.draw.circle(surf, (*self.color, 60), (x, y), r)  # faint fill
        font = pygame.font.Font(None, 24)
        txt = font.render(self.label, True, config.WHITE)
        surf.blit(txt, txt.get_rect(center=(x, y)))
