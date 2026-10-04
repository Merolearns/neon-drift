"""Parallax starfield background.

Three layers of stars drifting downward at different speeds to sell the
illusion that the ship is flying forward. Cheap and effective.
"""

import math
import random

import pygame

import config


class Starfield:
    def __init__(self, width, height, layers=3, density=70):
        self.width = width
        self.height = height
        self.stars = []
        for layer in range(layers):
            # farther layers: slower, smaller, dimmer
            speed = 30 + layer * 55
            size = 1 + (2 - layer) // 2  # 2, 1, 1  (close enough)
            if layer == 0:
                size = 2
            brightness = 90 + layer * 55
            for _ in range(density):
                self.stars.append({
                    "x": random.uniform(0, width),
                    "y": random.uniform(0, height),
                    "speed": speed * random.uniform(0.8, 1.2),
                    "size": size,
                    "bright": min(255, int(brightness * random.uniform(0.7, 1.0))),
                    "tw": random.uniform(0, 6.28),  # twinkle phase
                })

    def update(self, dt):
        for s in self.stars:
            s["y"] += s["speed"] * dt
            s["tw"] += dt * 3
            if s["y"] > self.height:
                s["y"] -= self.height
                s["x"] = random.uniform(0, self.width)

    def draw(self, surf):
        for s in self.stars:
            # subtle twinkle so the field doesn't look static
            b = s["bright"] * (0.78 + 0.22 * math.sin(s["tw"]))
            b = max(40, min(255, int(b)))
            color = (b, b, min(255, b + 20))  # faint blue tint
            if s["size"] <= 1:
                surf.set_at((int(s["x"]), int(s["y"])), color)
            else:
                pygame.draw.circle(surf, color, (int(s["x"]), int(s["y"])), s["size"])
