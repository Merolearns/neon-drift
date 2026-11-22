"""A survivable hit must not play the death explosion.

A ram with lives to spare used to fire the same big explosion sound and
particle burst as dying, so the player could not tell a lost life from
game over. The big explosion is now reserved for the fatal hit.
"""

import os
import sys
import tempfile

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["NEON_DRIFT_DB"] = os.path.join(tempfile.mkdtemp(), "scores.db")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

import config
from enemies import make_enemy
from game import Game


class FakeKeys:
    def __getitem__(self, _):
        return False


def _fresh_game():
    pygame.init()
    screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
    game = Game(screen)
    game.start_game()
    return game


def _ram_player(game):
    # a drifter sitting on the player collides within a few frames
    lives_before = game.player.lives
    game.enemies.append(
        make_enemy("drifter", game.player.pos.x, game.player.pos.y, 1))
    keys = FakeKeys()
    for _ in range(120):
        game.update(1 / 60, keys)
        if game.player.lives < lives_before or game.state == "gameover":
            break


def test_nonfatal_hit_uses_small_feedback():
    game = _fresh_game()
    game.player.lives = 3
    game.player.invuln = 0
    calls = []

    def recorder(name, *args, **kwargs):
        calls.append((name, args, kwargs))

    game.sounds.explosion = lambda big=False: recorder("explosion", big=big)
    game.sounds.player_hit = lambda: recorder("player_hit")
    _ram_player(game)
    assert game.player.lives == 2
    assert game.state == "playing"
    assert ("player_hit", (), {}) in calls
    assert not any(c[0] == "explosion" for c in calls), calls
    pygame.quit()


def test_fatal_hit_uses_big_explosion():
    game = _fresh_game()
    game.player.lives = 1
    game.player.invuln = 0
    calls = []

    def recorder(name, *args, **kwargs):
        calls.append((name, args, kwargs))

    game.sounds.explosion = lambda big=False: recorder("explosion", big=big)
    game.sounds.player_hit = lambda: recorder("player_hit")
    _ram_player(game)
    assert game.state == "gameover"
    assert ("explosion", (), {"big": True}) in calls
    pygame.quit()
