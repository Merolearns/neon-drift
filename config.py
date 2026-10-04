"""All tuning knobs for Neon Drift live here.

I got tired of magic numbers scattered across files, so everything
gameplay-related is a constant in this module. Tweak away.
"""

import os

# --- window ---
WIDTH, HEIGHT = 960, 720
FPS = 60
TITLE = "Neon Drift"

# --- palette (dark bg + neon accents) ---
BG_COLOR = (8, 10, 24)
NEON_CYAN = (0, 229, 255)
NEON_MAGENTA = (255, 45, 149)
NEON_YELLOW = (255, 235, 59)
NEON_GREEN = (57, 255, 20)
NEON_RED = (255, 77, 77)
NEON_ORANGE = (255, 140, 0)
NEON_PURPLE = (178, 102, 255)
WHITE = (235, 245, 255)
DIM = (110, 130, 170)
DARK_PANEL = (14, 18, 38)

# --- player ---
PLAYER_SPEED = 380.0          # px/s
PLAYER_RADIUS = 14
PLAYER_FIRE_CD = 0.16        # seconds between shots
PLAYER_LIVES = 3
INVULN_TIME = 2.0            # mercy invulnerability after a hit
RAPID_FIRE_CD = 0.07

# --- bullets ---
BULLET_SPEED = 640.0
BULLET_RADIUS = 4
ENEMY_BULLET_SPEED = 260.0
ENEMY_BULLET_RADIUS = 5

# --- enemies ---
# kind: hp, speed, radius, score, color, fire cooldown (0 = never fires)
ENEMIES = {
    "drifter": {"hp": 2, "speed": 135.0, "radius": 14, "score": 50,
                "color": NEON_MAGENTA, "fire_cd": 0.0},
    "weaver":  {"hp": 3, "speed": 175.0, "radius": 15, "score": 100,
                "color": NEON_ORANGE, "fire_cd": 2.4},
    "gunner":  {"hp": 9, "speed": 70.0,  "radius": 23, "score": 250,
                "color": NEON_RED, "fire_cd": 1.7},
}
# small per-wave scaling so late waves stay spicy
WAVE_HP_BONUS_EVERY = 4      # +1 hp every N waves
WAVE_SPEED_SCALE = 0.03      # +3% speed per wave

# --- powerups ---
POWERUP_DROP_CHANCE = 0.12
POWERUP_FALL_SPEED = 70.0
POWERUP_LIFETIME = 9.0
POWERUPS = {
    "spread": {"duration": 12.0, "color": NEON_YELLOW, "label": "S"},
    "rapid":  {"duration": 10.0, "color": NEON_GREEN,  "label": "R"},
    "shield": {"duration": 15.0, "color": NEON_CYAN,   "label": "D"},
}
SHIELD_CHARGES = 3

# --- waves ---
WAVE_BASE_COUNT = 4
WAVE_COUNT_STEP = 2
WAVE_CLEAR_BONUS = 100       # x wave number
SPAWN_STAGGER = 0.35         # seconds between spawns within a wave

# --- feel ---
SHAKE_MAX = 14.0
SHAKE_DECAY = 40.0           # px/s^2-ish, tuned by feel

# --- high scores ---
SCORE_TABLE_SIZE = 10
MAX_NAME_LEN = 10


def db_path():
    """Where the high-score sqlite db lives.

    Env override exists mostly so tests don't touch the real file.
    """
    override = os.environ.get("NEON_DRIFT_DB")
    if override:
        return override
    home = os.path.expanduser("~")
    d = os.path.join(home, ".neon-drift")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "scores.db")
