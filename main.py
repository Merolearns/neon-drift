"""Neon Drift — entry point."""

import pygame

import config
from game import Game


def main():
    pygame.init()
    pygame.display.set_caption(config.TITLE)
    screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
    clock = pygame.time.Clock()
    game = Game(screen)

    running = True
    while running:
        dt = min(clock.tick(config.FPS) / 1000.0, 0.05)  # clamp huge pauses
        for event in pygame.event.get():
            if game.handle_event(event) == "quit":
                running = False
        keys = pygame.key.get_pressed()
        game.update(dt, keys)
        game.draw()

    pygame.quit()


if __name__ == "__main__":
    main()
