"""All sound effects are synthesized at runtime with numpy.

No audio files needed — everything is generated from sine waves and
filtered noise. If the mixer can't init (headless server, no audio
device), every method just no-ops so the game still runs.
"""

import math

import pygame

SAMPLE_RATE = 22050


def _sine(freq, dur, vol=0.5, slide_to=None):
    """Sine tone, optionally sliding from freq to slide_to, with quick fade."""
    import numpy as np
    n = int(SAMPLE_RATE * dur)
    t = np.arange(n) / SAMPLE_RATE
    if slide_to is not None:
        # linear frequency sweep
        freqs = np.linspace(freq, slide_to, n)
        phase = 2 * math.pi * np.cumsum(freqs) / SAMPLE_RATE
    else:
        phase = 2 * math.pi * freq * t
    wave = np.sin(phase)
    # exponential decay + tiny fade-in to avoid clicks
    env = np.exp(-3.0 * t / dur)
    fade = min(64, n // 10)
    env[:fade] *= np.linspace(0, 1, fade)
    return (wave * env * vol).astype(np.float32)


def _noise(dur, vol=0.5, lowpass=0.3):
    """White noise burst with decay; lowpass fakes an explosion-ish thump."""
    import numpy as np
    n = int(SAMPLE_RATE * dur)
    rng = np.random.default_rng()
    wave = rng.standard_normal(n).astype(np.float32)
    # crude lowpass: moving average
    k = max(1, int(1 / lowpass))
    kernel = np.ones(k) / k
    wave = np.convolve(wave, kernel, mode="same")
    t = np.arange(n) / SAMPLE_RATE
    env = np.exp(-4.0 * t / dur)
    return (wave * env * vol).astype(np.float32)


def _to_sound(samples):
    import numpy as np
    pcm = np.int16(np.clip(samples, -1.0, 1.0) * 32767)
    # mono -> stereo by duplication (mixer inits stereo below)
    stereo = np.stack([pcm, pcm], axis=1)
    return pygame.sndarray.make_sound(stereo)


class SoundBank:
    def __init__(self):
        self.enabled = False
        self.sounds = {}
        try:
            pygame.mixer.pre_init(SAMPLE_RATE, -16, 2, 512)
            pygame.mixer.init()
            self.enabled = True
        except pygame.error:
            # no audio device — game runs silent
            return
        self._build()

    def _build(self):
        import numpy as np
        self.sounds["shoot"] = _to_sound(_sine(880, 0.09, vol=0.25, slide_to=420))
        self.sounds["enemy_shoot"] = _to_sound(_sine(300, 0.12, vol=0.2, slide_to=180))
        boom = _noise(0.45, vol=0.5) + _sine(90, 0.45, vol=0.5, slide_to=35)
        self.sounds["explosion"] = _to_sound(boom)
        small = _noise(0.25, vol=0.35) + _sine(140, 0.25, vol=0.35, slide_to=60)
        self.sounds["explosion_small"] = _to_sound(small)
        # powerup: three rising blips stitched together
        arp = np.concatenate([
            _sine(520, 0.09, vol=0.3),
            _sine(660, 0.09, vol=0.3),
            _sine(880, 0.14, vol=0.3),
        ])
        self.sounds["powerup"] = _to_sound(arp)
        self.sounds["player_hit"] = _to_sound(_sine(160, 0.25, vol=0.5, slide_to=60))
        self.sounds["wave"] = _to_sound(np.concatenate([
            _sine(440, 0.12, vol=0.3), _sine(587, 0.18, vol=0.3)]))
        self.sounds["gameover"] = _to_sound(_sine(400, 0.9, vol=0.4, slide_to=70))
        self.sounds["ui"] = _to_sound(_sine(700, 0.05, vol=0.2))
        for s in self.sounds.values():
            s.set_volume(0.7)

    def play(self, name):
        if not self.enabled:
            return
        snd = self.sounds.get(name)
        if snd is not None:
            snd.play()

    # convenience wrappers so call sites read nicely
    def shoot(self): self.play("shoot")
    def enemy_shoot(self): self.play("enemy_shoot")
    def explosion(self, big=False):
        self.play("explosion" if big else "explosion_small")
    def powerup(self): self.play("powerup")
    def player_hit(self): self.play("player_hit")
    def wave(self): self.play("wave")
    def gameover(self): self.play("gameover")
    def ui(self): self.play("ui")
