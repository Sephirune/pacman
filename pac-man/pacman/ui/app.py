"""The pygame application: window, main loop and screen switching.

pygame functions used here and their MLX equivalents:

* ``pygame.display.set_mode``   -> ``mlx_new_window``
* ``pygame.Surface`` + drawing  -> ``mlx_new_image`` + pixel writes
* ``Surface.blit`` / ``flip``   -> ``mlx_put_image_to_window``
* ``Font.render``               -> ``mlx_string_put``
* ``pygame.event.get``          -> ``mlx_key_hook`` / ``mlx_hook``
* ``Clock.tick`` loop           -> ``mlx_loop_hook``
* ``pygame.quit``               -> ``mlx_destroy_window``
"""

import os
import sys

import pygame

from pacman.config import GameConfig
from pacman.highscores import HighScores
from pacman.ui.screens import MenuScreen, Screen, start_game_screen
from pacman.ui.sprites import SpriteSet
from pacman.ui.theme import FPS, WINDOW_HEIGHT, WINDOW_WIDTH, Fonts

MAX_DT = 0.05   # evita saltos enormes si la ventana se congela un momento


def resolve_highscore_path(config: GameConfig, config_path: str) -> str:
    """Relative highscore paths are relative to the config file folder."""

    path = config.highscore_filename
    if os.path.isabs(path):
        return path
    base = os.path.dirname(os.path.abspath(config_path))
    return os.path.join(base, path)


class App:
    """Owns the window and the current screen."""

    def __init__(self, config: GameConfig, config_path: str) -> None:
        """Open the window and load the highscores."""

        self.config = config
        self.message = ""
        self.clock_time = 0.0
        self.running = False

        self.highscores = HighScores(
            resolve_highscore_path(config, config_path))
        warnings: list[str] = []
        self.highscores.load(warnings)
        self._report(warnings)

        # Solo ventana y texto: el juego no usa sonido (MLX tampoco).
        pygame.display.init()
        pygame.font.init()
        pygame.display.set_caption("Pac-Man")
        self.window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.fonts = Fonts()
        self.menu_sprites = SpriteSet(32)
        self.screen: Screen = MenuScreen(self)

    @staticmethod
    def _report(warnings: list[str]) -> None:
        """Print warnings on stderr."""

        for warning in warnings:
            print(f"Warning: {warning}", file=sys.stderr)

    # Acciones que piden las pantallas
    def switch(self, screen: Screen) -> None:
        """Show another screen from the next frame."""

        self.screen = screen

    def start_game(self) -> None:
        """Start a new game from level 1."""

        self.switch(start_game_screen(self))

    def save_highscores(self) -> None:
        """Write the table to disk, reporting problems."""

        warnings: list[str] = []
        if not self.highscores.save(warnings):
            self.message = "Could not save highscores (see terminal)."
        self._report(warnings)

    def quit(self) -> None:
        """Stop the main loop."""

        self.running = False

    def run(self) -> None:
        """Main loop: events -> update -> draw, FPS times per second."""

        self.running = True
        try:
            while self.running:
                dt = min(self.clock.tick(FPS) / 1000.0, MAX_DT)
                self.clock_time += dt
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    else:
                        self.screen.handle_event(event)
                self.screen.update(dt)
                self.screen.draw(self.window)
                pygame.display.flip()
        finally:
            pygame.quit()
