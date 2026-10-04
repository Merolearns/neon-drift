"""The player ship: movement, firing, power-up timers, damage handling."""

import math
import random

import pygame

import config


class Player:
    def __init__(self, x, y):
        self.pos = pygame.math.Vector2(x, y)
        self.radius = config.PLAYER_RADIUS
        self.lives = config.PLAYER_LIVES
        self.fire_timer = 0.0
        self.invuln = 0.0          # mercy invulnerability after taking a hit
        self.shield_charges = 0
        self.power_timers = {}     # kind -> seconds remaining
        self.thruster_phase = 0.0
        self.alive = True

    def reset(self, x, y):
        self.__init__(x, y)

    # --- power-ups ---
    def add_powerup(self, kind):
        dur = config.POWERUPS[kind]["duration"]
        self.power_timers[kind] = dur
        if kind == "shield":
            self.shield_charges = config.SHIELD_CHARGES

    def has(self, kind):
        return self.power_timers.get(kind, 0.0) > 0.0

    # --- per-frame ---
    def update(self, dt, keys):
        # movement
        dx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - \
             (keys[pygame.K_a] or keys[pygame.K_LEFT])
        dy = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - \
             (keys[pygame.K_w] or keys[pygame.K_UP])
        if dx and dy:  # normalize diagonals so they aren't faster
            dx *= 0.7071
            dy *= 0.7071
        self.pos.x += dx * config.PLAYER_SPEED * dt
        self.pos.y += dy * config.PLAYER_SPEED * dt
        # keep on screen
        self.pos.x = max(self.radius, min(config.WIDTH - self.radius, self.pos.x))
        self.pos.y = max(self.radius, min(config.HEIGHT - self.radius, self.pos.y))

        if self.invuln > 0:
            self.invuln -= dt
        self.thruster_phase += dt * 20

        # tick down power-up timers
        expired = [k for k, t in self.power_timers.items() if t - dt <= 0]
        for k in expired:
            del self.power_timers[k]
            if k == "shield":
                self.shield_charges = 0
        for k in self.power_timers:
            self.power_timers[k] -= dt

        # firing
        self.fire_timer -= dt
        shots = []
        cd = config.RAPID_FIRE_CD if self.has("rapid") else config.PLAYER_FIRE_CD
        if self.fire_timer <= 0:
            self.fire_timer = cd
            shots = self._make_shots()
        return shots

    def _make_shots(self):
        x, y = self.pos.x, self.pos.y - 18
        v = config.BULLET_SPEED
        if self.has("spread"):
            return [(x, y, -140, -v), (x, y, 0, -v), (x, y, 140, -v)]
        return [(x, y, 0, -v)]

    def hit(self):
        """Called when something collides with the ship.

        Returns 'shield' if the shield ate it, 'hit' if a life was lost
        but the ship survives, 'dead' if that was the last life,
        or None if currently invulnerable (no effect).
        """
        if self.invuln > 0 or not self.alive:
            return None
        if self.shield_charges > 0:
            self.shield_charges -= 1
            self.invuln = 1.0
            if self.shield_charges == 0:
                self.power_timers.pop("shield", None)
            return "shield"
        self.lives -= 1
        self.invuln = config.INVULN_TIME
        if self.lives <= 0:
            self.alive = False
            return "dead"
        return "hit"

    # --- drawing ---
    def draw(self, surf):
        if not self.alive:
            return
        # blink while invulnerable
        if self.invuln > 0 and int(self.invuln * 12) % 2 == 0:
            return
        x, y = self.pos.x, self.pos.y
        # glow halo
        glow = pygame.Surface((70, 70), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*config.NEON_CYAN, 40), (35, 35), 32)
        surf.blit(glow, (x - 35, y - 35))
        # thruster flame (flickers)
        flick = 10 + 6 * math.sin(self.thruster_phase) + random.uniform(-2, 2)
        flame = [(x - 6, y + 12), (x + 6, y + 12), (x, y + 12 + flick)]
        pygame.draw.polygon(surf, config.NEON_ORANGE, flame)
        # hull
        hull = [(x, y - 18), (x - 14, y + 12), (x, y + 5), (x + 14, y + 12)]
        pygame.draw.polygon(surf, config.NEON_CYAN, hull)
        pygame.draw.polygon(surf, config.WHITE, hull, 2)
        # cockpit
        pygame.draw.circle(surf, config.WHITE, (int(x), int(y - 2)), 4)
        # shield ring
        if self.shield_charges > 0:
            pygame.draw.circle(surf, config.NEON_CYAN,
                               (int(x), int(y)), self.radius + 8, 2)
