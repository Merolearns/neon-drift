"""Game orchestration: state machine, waves, collisions, HUD, menus.

States: menu -> playing <-> paused -> gameover -> (scores | menu)
"""

import random

import pygame

import config
from audio import SoundBank
from enemies import make_enemy
from particles import ParticleSystem
from player import Player
from powerups import PowerUp
from scores import ScoreDB
from starfield import Starfield


class Bullet:
    def __init__(self, x, y, vx, vy, friendly=True):
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(vx, vy)
        self.friendly = friendly
        self.radius = config.BULLET_RADIUS if friendly else config.ENEMY_BULLET_RADIUS
        self.dead = False
        self.color = config.NEON_CYAN if friendly else config.NEON_RED

    def update(self, dt):
        self.pos += self.vel * dt
        if (self.pos.x < -20 or self.pos.x > config.WIDTH + 20 or
                self.pos.y < -20 or self.pos.y > config.HEIGHT + 20):
            self.dead = True

    def draw(self, surf):
        x, y = int(self.pos.x), int(self.pos.y)
        # short tracer line along velocity
        d = self.vel.normalize() if self.vel.length_squared() else pygame.math.Vector2(0, -1)
        tail = (x - int(d.x * 12), y - int(d.y * 12))
        pygame.draw.line(surf, self.color, tail, (x, y), 3)
        pygame.draw.circle(surf, config.WHITE, (x, y), 2)


def _dist(a, b):
    return (a - b).length()


class Game:
    def __init__(self, screen):
        self.screen = screen
        self.world = pygame.Surface((config.WIDTH, config.HEIGHT))
        self.font_big = pygame.font.Font(None, 72)
        self.font_med = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)
        self.starfield = Starfield(config.WIDTH, config.HEIGHT)
        self.particles = ParticleSystem()
        self.sounds = SoundBank()
        self.scores = ScoreDB()
        self.state = "menu"
        self.menu_idx = 0
        self.menu_items = ["Start Game", "High Scores", "Quit"]
        self.shake = 0.0
        self.name_entry = ""
        self.entering_name = False
        self.reset_run()

    # --- run lifecycle ---
    def reset_run(self):
        self.player = Player(config.WIDTH / 2, config.HEIGHT - 90)
        self.enemies = []
        self.bullets = []
        self.powerups = []
        self.score = 0
        self.wave = 0
        self.banner_text = ""
        self.banner_t = 0.0
        self.spawn_queue = []   # (time_left, kind)
        self.wave_pause = 0.0
        self.particles.clear()
        self.shake = 0.0

    def start_game(self):
        self.reset_run()
        self.state = "playing"
        self._next_wave()
        self.sounds.wave()

    def to_menu(self):
        self.state = "menu"
        self.menu_idx = 0

    def _next_wave(self):
        self.wave += 1
        count = config.WAVE_BASE_COUNT + config.WAVE_COUNT_STEP * (self.wave - 1)
        kinds = []
        for i in range(count):
            r = random.random()
            if self.wave >= 3 and r < 0.18:
                kinds.append("gunner")
            elif self.wave >= 2 and r < 0.45:
                kinds.append("weaver")
            else:
                kinds.append("drifter")
        random.shuffle(kinds)
        self.spawn_queue = [[i * config.SPAWN_STAGGER, k] for i, k in enumerate(kinds)]
        self.banner_text = f"WAVE {self.wave}"
        self.banner_t = 2.0
        self.sounds.wave()

    # --- events ---
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return "quit"
        if event.type != pygame.KEYDOWN:
            return None
        k = event.key
        if self.state == "menu":
            if k in (pygame.K_UP, pygame.K_w):
                self.menu_idx = (self.menu_idx - 1) % len(self.menu_items)
                self.sounds.ui()
            elif k in (pygame.K_DOWN, pygame.K_s):
                self.menu_idx = (self.menu_idx + 1) % len(self.menu_items)
                self.sounds.ui()
            elif k in (pygame.K_RETURN, pygame.K_SPACE):
                choice = self.menu_items[self.menu_idx]
                self.sounds.ui()
                if choice == "Start Game":
                    self.start_game()
                elif choice == "High Scores":
                    self.state = "scores"
                else:
                    return "quit"
        elif self.state == "scores":
            if k in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE):
                self.to_menu()
        elif self.state == "playing":
            if k in (pygame.K_p, pygame.K_ESCAPE):
                self.state = "paused"
                self.sounds.ui()
        elif self.state == "paused":
            if k in (pygame.K_p, pygame.K_ESCAPE, pygame.K_RETURN):
                self.state = "playing"
                self.sounds.ui()
            elif k == pygame.K_q:
                self.to_menu()
        elif self.state == "gameover":
            if self.entering_name:
                if k == pygame.K_RETURN and self.name_entry.strip():
                    self._save_score()
                elif k == pygame.K_BACKSPACE:
                    self.name_entry = self.name_entry[:-1]
                elif k == pygame.K_ESCAPE:
                    self._save_score()  # save with default name
                elif event.unicode and len(self.name_entry) < config.MAX_NAME_LEN:
                    ch = event.unicode.upper()
                    if ch.isalnum():
                        self.name_entry += ch
            elif k in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                self.to_menu()
        return None

    def _save_score(self):
        name = self.name_entry.strip() or "ACE"
        self.scores.add_score(name, self.score, self.wave)
        self.entering_name = False
        self.state = "scores"

    # --- update ---
    def update(self, dt, keys):
        self.starfield.update(dt)
        self.particles.update(dt)
        if self.banner_t > 0:
            self.banner_t -= dt
        self.shake = max(0.0, self.shake - config.SHAKE_DECAY * dt)

        if self.state == "playing":
            self._update_playing(dt, keys)

    def _update_playing(self, dt, keys):
        # player
        new_shots = self.player.update(dt, keys)
        for sx, sy, svx, svy in new_shots:
            self.bullets.append(Bullet(sx, sy, svx, svy, friendly=True))
        if new_shots:
            self.sounds.shoot()
        # thruster particles
        if random.random() < 0.6:
            self.particles.trail(self.player.pos.x, self.player.pos.y + 14,
                                 config.NEON_CYAN)

        # staggered spawning
        for item in self.spawn_queue:
            item[0] -= dt
        ready = [item for item in self.spawn_queue if item[0] <= 0]
        self.spawn_queue = [item for item in self.spawn_queue if item[0] > 0]
        for _, kind in ready:
            x = random.uniform(40, config.WIDTH - 40)
            self.enemies.append(make_enemy(kind, x, -40, self.wave))

        # enemies
        for e in self.enemies:
            e.update(dt, self.player.pos)
            shot = e.try_fire(dt, self.player.pos)
            if shot:
                x, y, vx, vy = shot
                self.bullets.append(Bullet(x, y, vx, vy, friendly=False))
                self.sounds.enemy_shoot()

        for b in self.bullets:
            b.update(dt)
        for p in self.powerups:
            p.update(dt)

        self._collisions()

        # cull
        self.enemies = [e for e in self.enemies if not e.dead]
        self.bullets = [b for b in self.bullets if not b.dead]
        self.powerups = [p for p in self.powerups if not p.dead]

        # wave cleared?
        if not self.enemies and not self.spawn_queue:
            self.wave_pause += dt
            if self.wave_pause > 2.0:
                self.wave_pause = 0.0
                self.score += config.WAVE_CLEAR_BONUS * self.wave
                self._next_wave()

    def _collisions(self):
        p = self.player
        # player bullets vs enemies
        for b in self.bullets:
            if not b.friendly or b.dead:
                continue
            for e in self.enemies:
                if e.dead:
                    continue
                if _dist(b.pos, e.pos) < b.radius + e.radius:
                    b.dead = True
                    self.particles.sparks(b.pos.x, b.pos.y, config.NEON_YELLOW, 5)
                    if e.take_damage():
                        self.score += e.score
                        self.particles.explosion(e.pos.x, e.pos.y, e.color)
                        self.sounds.explosion()
                        drop = PowerUp.maybe_drop(e.pos.x, e.pos.y)
                        if drop:
                            self.powerups.append(drop)
                    break
        # enemies vs player (ramming)
        for e in self.enemies:
            if e.dead:
                continue
            if _dist(e.pos, p.pos) < e.radius + p.radius * 0.8:
                e.dead = True
                self.particles.explosion(e.pos.x, e.pos.y, e.color)
                self._damage_player("ram")
        # enemy bullets vs player
        for b in self.bullets:
            if b.friendly or b.dead:
                continue
            if _dist(b.pos, p.pos) < b.radius + p.radius * 0.8:
                b.dead = True
                self._damage_player("shot")
                break
        # powerups vs player
        for pu in self.powerups:
            if pu.dead:
                continue
            if _dist(pu.pos, p.pos) < pu.radius + p.radius:
                pu.dead = True
                p.add_powerup(pu.kind)
                self.sounds.powerup()
                self.particles.sparks(pu.pos.x, pu.pos.y, pu.color, 12)

    def _damage_player(self, cause):
        result = self.player.hit()
        if result is None:
            return
        self.shake = config.SHAKE_MAX
        if result == "shield":
            self.sounds.player_hit()
            self.particles.sparks(self.player.pos.x, self.player.pos.y,
                                 config.NEON_CYAN, 14)
        else:
            self.sounds.explosion(big=True)
            self.particles.explosion(self.player.pos.x, self.player.pos.y,
                                     config.NEON_CYAN, big=True)
            if result == "dead":
                self.sounds.gameover()
                self.state = "gameover"
                if self.scores.qualifies(self.score):
                    self.entering_name = True
                    self.name_entry = ""
                # clear the field so the game-over screen is readable
                self.enemies.clear()
                self.bullets.clear()

    # --- drawing ---
    def draw(self):
        self.screen.fill(config.BG_COLOR)
        if self.state in ("playing", "paused", "gameover"):
            self._draw_world()
        elif self.state == "menu":
            self._draw_menu()
        elif self.state == "scores":
            self._draw_scores()
        if self.state == "paused":
            self._draw_paused()
        elif self.state == "gameover":
            self._draw_gameover()
        pygame.display.flip()

    def _draw_world(self):
        w = self.world
        w.fill(config.BG_COLOR)
        self.starfield.draw(w)
        for pu in self.powerups:
            pu.draw(w)
        for e in self.enemies:
            e.draw(w)
        for b in self.bullets:
            b.draw(w)
        self.player.draw(w)
        self.particles.draw(w)
        # screen shake
        ox = random.uniform(-self.shake, self.shake) if self.shake > 0 else 0
        oy = random.uniform(-self.shake, self.shake) if self.shake > 0 else 0
        self.screen.blit(w, (ox, oy))
        self._draw_hud()
        if self.banner_t > 0 and self.state == "playing":
            alpha = min(255, int(255 * self.banner_t))
            txt = self.font_big.render(self.banner_text, True, config.NEON_CYAN)
            txt.set_alpha(alpha)
            self.screen.blit(txt, txt.get_rect(
                center=(config.WIDTH / 2, config.HEIGHT / 2 - 60)))

    def _draw_hud(self):
        s = self.screen
        # score / wave top-left
        score_txt = self.font_med.render(f"{self.score:,}", True, config.WHITE)
        s.blit(score_txt, (16, 10))
        wave_txt = self.font_small.render(f"WAVE {self.wave}", True, config.DIM)
        s.blit(wave_txt, (16, 48))
        # lives top-right as little ships
        for i in range(self.player.lives):
            x = config.WIDTH - 24 - i * 30
            pts = [(x, 18), (x - 9, 34), (x + 9, 34)]
            pygame.draw.polygon(s, config.NEON_CYAN, pts)
        # active power-up timers bottom-left
        y = config.HEIGHT - 24
        for kind, t in self.player.power_timers.items():
            spec = config.POWERUPS[kind]
            total = spec["duration"]
            label = self.font_small.render(kind.upper(), True, spec["color"])
            s.blit(label, (16, y - 40))
            pygame.draw.rect(s, (50, 50, 70), (100, y - 34, 120, 10))
            pygame.draw.rect(s, spec["color"], (100, y - 34, 120 * t / total, 10))
            y -= 30

    def _draw_menu(self):
        s = self.screen
        self.starfield.draw(s)
        title = self.font_big.render("NEON DRIFT", True, config.NEON_CYAN)
        s.blit(title, title.get_rect(center=(config.WIDTH / 2, 180)))
        sub = self.font_small.render("a tiny arcade shooter", True, config.DIM)
        s.blit(sub, sub.get_rect(center=(config.WIDTH / 2, 225)))
        for i, item in enumerate(self.menu_items):
            color = config.NEON_YELLOW if i == self.menu_idx else config.WHITE
            prefix = "> " if i == self.menu_idx else "  "
            txt = self.font_med.render(prefix + item, True, color)
            s.blit(txt, txt.get_rect(center=(config.WIDTH / 2, 340 + i * 55)))
        best = self.scores.best()
        if best:
            bt = self.font_small.render(f"best: {best:,}", True, config.DIM)
            s.blit(bt, bt.get_rect(center=(config.WIDTH / 2, 560)))
        help_txt = self.font_small.render(
            "move: WASD / arrows      pause: P      auto-fire is always on",
            True, config.DIM)
        s.blit(help_txt, help_txt.get_rect(center=(config.WIDTH / 2, 640)))

    def _draw_scores(self):
        s = self.screen
        s.fill(config.BG_COLOR)
        self.starfield.draw(s)
        title = self.font_med.render("HIGH SCORES", True, config.NEON_YELLOW)
        s.blit(title, title.get_rect(center=(config.WIDTH / 2, 90)))
        rows = self.scores.top()
        if not rows:
            txt = self.font_small.render("no scores yet — go fly!", True, config.DIM)
            s.blit(txt, txt.get_rect(center=(config.WIDTH / 2, 200)))
        for i, (name, score, wave) in enumerate(rows):
            color = config.NEON_YELLOW if i == 0 else config.WHITE
            line = f"{i + 1:2d}. {name:<10} {score:>8,}   wave {wave}"
            txt = self.font_med.render(line, True, color)
            s.blit(txt, txt.get_rect(center=(config.WIDTH / 2, 170 + i * 42)))
        hint = self.font_small.render("ENTER: back", True, config.DIM)
        s.blit(hint, hint.get_rect(center=(config.WIDTH / 2, config.HEIGHT - 60)))

    def _draw_paused(self):
        overlay = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        txt = self.font_big.render("PAUSED", True, config.WHITE)
        self.screen.blit(txt, txt.get_rect(center=(config.WIDTH / 2, 300)))
        hint = self.font_small.render("P: resume      Q: quit to menu", True, config.DIM)
        self.screen.blit(hint, hint.get_rect(center=(config.WIDTH / 2, 380)))

    def _draw_gameover(self):
        overlay = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))
        txt = self.font_big.render("GAME OVER", True, config.NEON_RED)
        self.screen.blit(txt, txt.get_rect(center=(config.WIDTH / 2, 220)))
        st = self.font_med.render(f"score: {self.score:,}   wave: {self.wave}",
                                  True, config.WHITE)
        self.screen.blit(st, st.get_rect(center=(config.WIDTH / 2, 300)))
        if self.entering_name:
            p = self.font_med.render("NEW HIGH SCORE! enter your name:",
                                     True, config.NEON_YELLOW)
            self.screen.blit(p, p.get_rect(center=(config.WIDTH / 2, 380)))
            cursor = "_" if int(pygame.time.get_ticks() / 400) % 2 == 0 else " "
            nt = self.font_big.render(self.name_entry + cursor, True, config.WHITE)
            self.screen.blit(nt, nt.get_rect(center=(config.WIDTH / 2, 450)))
        else:
            hint = self.font_small.render("ENTER: continue", True, config.DIM)
            self.screen.blit(hint, hint.get_rect(center=(config.WIDTH / 2, 420)))
