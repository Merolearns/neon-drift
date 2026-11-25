"""SoundBank must degrade to silent when numpy is missing.

A user who followed the README's old `pip install pygame` line had no
numpy, so the game crashed on startup building its sounds — even
though the module promises the game still runs when sound is
unavailable.
"""

import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
import pytest

import config
from audio import SoundBank
from game import Game


@pytest.fixture
def working_mixer(monkeypatch):
    # a machine WITH an audio device: mixer init succeeds, so _build()
    # actually runs and would hit the missing numpy import
    monkeypatch.setattr(pygame.mixer, "pre_init", lambda *a, **k: None)
    monkeypatch.setattr(pygame.mixer, "init", lambda *a, **k: None)


def test_soundbank_runs_silent_without_numpy(monkeypatch, working_mixer):
    # block numpy the way a missing install does: `import numpy`
    # raises ImportError on every call inside _sine/_noise/_to_sound
    monkeypatch.setitem(sys.modules, "numpy", None)
    bank = SoundBank()
    assert bank.enabled is False
    assert bank.sounds == {}
    bank.play("shoot")  # no-op, must not raise
    bank.explosion(big=True)


def test_soundbank_builds_when_numpy_present():
    # real mixer init on the dummy driver (verified: init succeeds,
    # all 9 sounds build, play works)
    bank = SoundBank()
    assert bank.enabled is True
    assert "shoot" in bank.sounds
    bank.play("shoot")


def test_game_starts_without_numpy(monkeypatch, working_mixer):
    # end to end: the crash was at startup, when Game builds its bank
    monkeypatch.setitem(sys.modules, "numpy", None)
    pygame.init()
    screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
    game = Game(screen)
    assert game.sounds.enabled is False
    game.sounds.shoot()  # no-op, must not raise
    pygame.quit()
