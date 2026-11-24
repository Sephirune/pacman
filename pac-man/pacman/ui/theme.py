"""Colors, fonts and small text helpers shared by every screen.

Every drawing helper here only renders text to an image and copies it to
the window, which is what ``mlx_string_put`` does with the MLX library.
"""

import pygame

Color = tuple[int, int, int]

WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768
FPS = 60

BLACK: Color = (0, 0, 0)
BACKGROUND: Color = (5, 5, 16)
WALL: Color = (33, 33, 222)
WALL_FILL: Color = (12, 12, 70)
WHITE: Color = (240, 240, 240)
GREY: Color = (130, 130, 150)
YELLOW: Color = (255, 221, 0)
RED: Color = (255, 40, 40)
PINK: Color = (255, 160, 220)
CYAN: Color = (0, 230, 255)
ORANGE: Color = (255, 170, 60)
SCARED_BLUE: Color = (40, 40, 255)
PELLET: Color = (255, 190, 170)
GREEN: Color = (90, 230, 90)

GHOST_COLORS: list[Color] = [RED, PINK, CYAN, ORANGE]


class Fonts:
    """Lazily created fonts (pygame.font must be initialised first)."""

    def __init__(self) -> None:
        """Create the three font sizes used by the game."""

        self.title = pygame.font.Font(None, 96)
        self.big = pygame.font.Font(None, 56)
        self.medium = pygame.font.Font(None, 36)
        self.small = pygame.font.Font(None, 26)


def draw_text(surface: pygame.Surface, font: pygame.font.Font, text: str,
              color: Color, pos: tuple[int, int],
              align: str = "center") -> pygame.Rect:
    """Draw ``text`` on ``surface``.

    ``align`` is ``"center"``, ``"left"`` or ``"right"`` and tells which
    point of the text ``pos`` refers to (vertical position is the centre).
    """

    image = font.render(text, True, color)
    rect = image.get_rect()
    if align == "left":
        rect.midleft = pos
    elif align == "right":
        rect.midright = pos
    else:
        rect.center = pos
    surface.blit(image, rect)
    return rect
