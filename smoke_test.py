"""Headless smoke test for Neon Drift.

Runs the game with dummy video/audio drivers, simulates a few hundred
frames of real gameplay, forces collisions, pause, game-over, name entry,
and high-score persistence. Any exception = failure.
"""

import os
import sys
import tempfile

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
# throwaway high-score db so the real one is untouched
os.environ["NEON_DRIFT_DB"] = os.path.join(tempfile.mkdtemp(), "scores.db")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame

import config
from enemies import make_enemy
from game import Game
from scores import ScoreDB


class FakeKeys:
    def __getitem__(self, _):
        return False


def keydown(key, uni=""):
    return pygame.event.Event(pygame.KEYDOWN, {"key": key, "unicode": uni})


def main():
    pygame.init()
    screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
    game = Game(screen)
    keys = FakeKeys()

    # menu -> start game via keyboard
    assert game.state == "menu"
    assert game.handle_event(keydown(pygame.K_RETURN)) is None
    assert game.state == "playing", game.state

    # simulate ~10 seconds of gameplay: spawning, firing, collisions
    for _ in range(600):
        game.update(1 / 60, keys)
        game.draw()
    assert game.wave >= 1
    assert game.score >= 0
    print(f"gameplay ok: wave={game.wave} score={game.score} "
          f"enemies={len(game.enemies)} bullets={len(game.bullets)}")

    # force an enemy onto the player -> ram collision path
    game.enemies.append(make_enemy("drifter", game.player.pos.x, game.player.pos.y, 1))
    lives_before = game.player.lives
    for _ in range(120):
        game.update(1 / 60, keys)
    assert game.player.lives < lives_before or game.state == "gameover", \
        "ram collision did not damage the player"
    print("ram collision ok")

    # pause / resume
    game.handle_event(keydown(pygame.K_p))
    assert game.state == "paused", game.state
    game.handle_event(keydown(pygame.K_p))
    assert game.state == "playing", game.state
    print("pause ok")

    # force game over
    game.player.lives = 1
    game.player.invuln = 0
    game.enemies.append(make_enemy("drifter", game.player.pos.x, game.player.pos.y, 1))
    for _ in range(120):
        game.update(1 / 60, keys)
        if game.state == "gameover":
            break
    assert game.state == "gameover", game.state
    print("game over ok")

    # name entry -> save -> scores screen
    if game.entering_name:
        for ch in "SMOKE":
            game.handle_event(keydown(ord(ch.lower()), ch))
        game.handle_event(keydown(pygame.K_RETURN))
    assert game.state == "scores", game.state
    rows = game.scores.top()
    assert any(r[0] == "SMOKE" for r in rows), rows
    print("high-score save ok:", rows[0])

    # scores persist across instances
    db2 = ScoreDB()
    assert any(r[0] == "SMOKE" for r in db2.top())
    print("high-score persistence ok")

    # the table stays bounded: only the top 10 survive, lowest pruned
    prune_db = ScoreDB(path=os.path.join(tempfile.mkdtemp(), "prune.db"))
    for i in range(12):
        prune_db.add_score(f"P{i}", i * 10, 1)
    import sqlite3
    with sqlite3.connect(prune_db.path) as con:
        n = con.execute("SELECT COUNT(*) FROM scores").fetchone()[0]
    assert n == config.SCORE_TABLE_SIZE, n
    assert [r[1] for r in prune_db.top()] == \
        [110, 100, 90, 80, 70, 60, 50, 40, 30, 20]
    print("high-score prune ok")

    # back to menu
    game.handle_event(keydown(pygame.K_RETURN))
    assert game.state == "menu", game.state

    # weavers spawned near an edge must stay on-screen while sine-drifting
    edge_weaver = make_enemy("weaver", 40, 100, 1)
    for _ in range(600):
        edge_weaver.update(1 / 60, game.player.pos)
        assert edge_weaver.radius <= edge_weaver.pos.x <= config.WIDTH - edge_weaver.radius, \
            edge_weaver.pos.x
    print("weaver on-screen clamp ok")

    # a weaver that slips past the player must not stall the wave
    game.start_game()
    game.spawn_queue.clear()
    game.enemies.append(make_enemy("weaver", 100, config.HEIGHT - 5, 1))
    for _ in range(300):
        game.update(1 / 60, keys)
        if game.wave == 2:
            break
    assert game.wave == 2, f"wave stalled with {len(game.enemies)} enemies left"
    print("weaver exit ok")

    # power-up application path
    game.start_game()
    game.player.add_powerup("spread")
    game.player.add_powerup("rapid")
    game.player.add_powerup("shield")
    assert game.player.has("spread") and game.player.shield_charges == 3
    shots = game.player.update(0.016, keys)
    assert len(shots) == 3, shots  # spread = 3-way
    print("power-ups ok")

    pygame.quit()
    print("SMOKE OK — no exceptions")


def test_smoke():
    main()


if __name__ == "__main__":
    main()
