"""Enemy ships. Three behaviors:

- Drifter: dumb chaser, beelines for the player.
- Weaver: sine-wave strafing run across the screen, spits shots downward.
- Gunner: slow tank, parks at the top and fires aimed shots.
"""

import math
import random

import pygame

import config


class Enemy:
    def __init__(self, kind, x, y, wave):
        spec = config.ENEMIES[kind]
        self.kind = kind
        self.pos = pygame.math.Vector2(x, y)
        self.radius = spec["radius"]
        self.color = spec["color"]
        self.score = spec["score"]
        # waves get meaner: a little more hp and speed over time
        self.hp = spec["hp"] + wave // config.WAVE_HP_BONUS_EVERY
        self.max_hp = self.hp
        self.speed = spec["speed"] * (1 + wave * config.WAVE_SPEED_SCALE)
        self.fire_cd = spec["fire_cd"]
        self.fire_timer = random.uniform(0.5, self.fire_cd) if self.fire_cd else 0
        self.t = 0.0          # age, used for sine motion etc.
        self.flash = 0.0      # white hit-flash timer
        self.dead = False

    def take_damage(self, n=1):
        self.hp -= n
        self.flash = 0.08
        if self.hp <= 0:
            self.dead = True
        return self.dead

    def try_fire(self, dt, player_pos):
        """Returns an (x, y, vx, vy) enemy-bullet tuple, or None."""
        if not self.fire_cd:
            return None
        self.fire_timer -= dt
        if self.fire_timer > 0:
            return None
        self.fire_timer = self.fire_cd * random.uniform(0.85, 1.2)
        return self._aimed_shot(player_pos)

    def _aimed_shot(self, player_pos):
        d = player_pos - self.pos
        if d.length_squared() < 1:
            d = pygame.math.Vector2(0, 1)
        d = d.normalize() * config.ENEMY_BULLET_SPEED
        return (self.pos.x, self.pos.y, d.x, d.y)

    def update(self, dt, player_pos):
        self.t += dt
        if self.flash > 0:
            self.flash -= dt

    def draw(self, surf):
        color = config.WHITE if self.flash > 0 else self.color
        x, y = int(self.pos.x), int(self.pos.y)
        r = self.radius
        # glow
        glow = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*self.color, 35), (r * 2, r * 2), r * 2)
        surf.blit(glow, (x - r * 2, y - r * 2))
        self._draw_shape(surf, x, y, r, color)
        # hp pips for tough enemies
        if self.max_hp >= 5:
            w = r * 2
            frac = self.hp / self.max_hp
            pygame.draw.rect(surf, (60, 60, 80), (x - r, y - r - 10, w, 4))
            pygame.draw.rect(surf, config.NEON_RED,
                             (x - r, y - r - 10, w * frac, 4))

    def _draw_shape(self, surf, x, y, r, color):
        raise NotImplementedError


class Drifter(Enemy):
    """Chases the player with a slight wobble."""

    def __init__(self, x, y, wave):
        super().__init__("drifter", x, y, wave)

    def update(self, dt, player_pos):
        super().update(dt, player_pos)
        d = player_pos - self.pos
        if d.length_squared() > 1:
            d = d.normalize()
        wobble = pygame.math.Vector2(-d.y, d.x) * math.sin(self.t * 5) * 0.35
        self.pos += (d + wobble) * self.speed * dt

    def _draw_shape(self, surf, x, y, r, color):
        pts = [(x, y - r), (x + r, y), (x, y + r), (x - r, y)]
        pygame.draw.polygon(surf, color, pts)
        pygame.draw.polygon(surf, config.WHITE, pts, 2)


class Weaver(Enemy):
    """Sweeps down in a sine wave, firing straight down periodically."""

    def __init__(self, x, y, wave):
        super().__init__("weaver", x, y, wave)
        self.base_x = x
        self.vy = self.speed * 0.55

    def update(self, dt, player_pos):
        super().update(dt, player_pos)
        self.pos.y += self.vy * dt
        self.pos.x = self.base_x + math.sin(self.t * 3.2) * 130

    def try_fire(self, dt, player_pos):
        if not self.fire_cd:
            return None
        self.fire_timer -= dt
        if self.fire_timer > 0:
            return None
        self.fire_timer = self.fire_cd * random.uniform(0.85, 1.2)
        v = config.ENEMY_BULLET_SPEED
        return (self.pos.x, self.pos.y + self.radius, 0, v)

    def _draw_shape(self, surf, x, y, r, color):
        pts = [(x, y + r), (x - r, y - r // 2), (x, y - r), (x + r, y - r // 2)]
        pygame.draw.polygon(surf, color, pts)
        pygame.draw.polygon(surf, config.WHITE, pts, 2)


class Gunner(Enemy):
    """Descends to the upper third, then strafes and fires aimed shots."""

    def __init__(self, x, y, wave):
        super().__init__("gunner", x, y, wave)
        self.target_y = random.uniform(90, 200)
        self.strafe_dir = random.choice([-1, 1])

    def update(self, dt, player_pos):
        super().update(dt, player_pos)
        if self.pos.y < self.target_y:
            self.pos.y += self.speed * dt
        else:
            self.pos.x += self.strafe_dir * self.speed * 0.8 * dt
            if self.pos.x < 60 or self.pos.x > config.WIDTH - 60:
                self.strafe_dir *= -1
                self.pos.x = max(60, min(config.WIDTH - 60, self.pos.x))

    def _draw_shape(self, surf, x, y, r, color):
        pts = []
        for i in range(6):
            a = math.pi / 6 + i * math.pi / 3
            pts.append((x + r * math.cos(a), y + r * math.sin(a)))
        pygame.draw.polygon(surf, color, pts)
        pygame.draw.polygon(surf, config.WHITE, pts, 2)
        pygame.draw.circle(surf, config.WHITE, (x, y), r // 3)


ENEMY_CLASSES = {"drifter": Drifter, "weaver": Weaver, "gunner": Gunner}


def make_enemy(kind, x, y, wave):
    return ENEMY_CLASSES[kind](x, y, wave)
