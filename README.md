# Neon Drift

A neon-style 2D arcade space shooter I built to get comfortable with real-time
game loops, sprite-ish entity management, and procedural audio in pygame.

You pilot a little ship against escalating waves of enemies. That's the whole
pitch. It's the kind of game I grew up dumping quarters into, minus the
quarters.

## How to run

```bash
pip install pygame
python main.py
```

Python 3.10+ and pygame 2.x. No other dependencies, no asset files — every
sprite is drawn in code and every sound is synthesized at startup.

## Controls

- **Move:** WASD or arrow keys
- **Fire:** automatic (always on)
- **Pause:** P or Esc
- **Menus:** up/down + Enter

Grab falling pickups: **S** = spread shot, **R** = rapid fire, **D** = shield
(absorbs 3 hits).

## Enemies

| Enemy   | Behavior |
|---------|----------|
| Drifter | Chases you. Fast, fragile, dumb. |
| Weaver  | Sine-wave strafing run, shoots straight down. |
| Gunner  | Slow tank, parks near the top and fires aimed shots. Has an HP bar. |

Waves get bigger and slightly meaner over time (+HP every 4 waves, +speed per
wave). Clearing a wave pays a bonus.

## How it's put together

```
main.py       entry point, game loop, event pump
game.py       state machine (menu/playing/paused/gameover), waves,
              collisions, HUD, high-score name entry
player.py     ship movement, firing patterns, shield/invulnerability
enemies.py    the three enemy behaviors + hit flashes + HP bars
powerups.py   falling pickups and their timers
particles.py  explosions, sparks, thruster trail
starfield.py  3-layer parallax background
audio.py      numpy-synthesized SFX (no audio files)
scores.py     SQLite top-10 high-score table (~/.neon-drift/scores.db)
config.py     every tuning constant in one place
```

A few implementation notes:

- Collision is circle-based; entity counts stay small so brute-force
  pairwise checks are plenty fast.
- Screen shake is done by rendering the world to an offscreen surface and
  blitting it with a random offset — two lines, big payoff.
- The mixer is wrapped so the game runs silent (but fine) on machines with
  no audio device.
- High scores persist in SQLite under `~/.neon-drift/`. Set `NEON_DRIFT_DB`
  to point it somewhere else (I use this for testing).

## What I'd add next

- A proper boss every 5 waves (I sketched the pattern system with this in mind)
- More power-ups: homing missiles, a bomb that clears the screen
- Better enemy variety — the weaver/gunner behaviors were the fun part to tune
- Gamepad support

MIT licensed. Built for fun and for the portfolio.
