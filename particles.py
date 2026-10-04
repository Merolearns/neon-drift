"""Tiny particle system for explosions, sparks, thruster trails, etc.

Particles are just dicts in a list — no need for a class per particle.
Dead ones get culled every frame.
"""

import math
import random

import pygame


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def spawn(self, x, y, color, count=12, speed=220.0, life=0.6,
              size=3, spread=math.pi * 2, angle=0.0, drag=2.0, gravity=0.0):
        for _ in range(count):
            a = angle + random.uniform(-spread / 2, spread / 2)
            sp = speed * random.uniform(0.3, 1.0)
            self.particles.append({
                "x": x, "y": y,
                "vx": math.cos(a) * sp, "vy": math.sin(a) * sp,
                "life": life * random.uniform(0.6, 1.0),
                "max_life": life,
                "color": color,
                "size": size * random.uniform(0.6, 1.2),
                "drag": drag,
                "gravity": gravity,
            })

    def explosion(self, x, y, color, big=False):
        n = 40 if big else 22
        self.spawn(x, y, color, count=n, speed=320 if big else 220,
                   life=0.8 if big else 0.55, size=4)
        # white-hot core flash
        self.spawn(x, y, (255, 255, 255), count=n // 3, speed=120,
                   life=0.3, size=3)

    def trail(self, x, y, color):
        self.spawn(x, y, color, count=1, speed=40, life=0.35, size=3,
                   spread=0.6, angle=math.pi / 2, drag=1.0)

    def sparks(self, x, y, color, count=8):
        self.spawn(x, y, color, count=count, speed=380, life=0.35, size=2)

    def update(self, dt):
        alive = []
        for p in self.particles:
            p["life"] -= dt
            if p["life"] <= 0:
                continue
            # drag
            d = max(0.0, 1.0 - p["drag"] * dt)
            p["vx"] *= d
            p["vy"] *= d
            p["vy"] += p["gravity"] * dt
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            alive.append(p)
        self.particles = alive

    def draw(self, surf):
        for p in self.particles:
            t = p["life"] / p["max_life"]  # 1 -> 0
            r, g, b = p["color"]
            # fade to black as it dies — reads as a glow cooling off
            color = (int(r * t), int(g * t), int(b * t))
            rad = max(1, int(p["size"] * t))
            pygame.draw.circle(surf, color, (int(p["x"]), int(p["y"])), rad)

    def clear(self):
        self.particles.clear()
