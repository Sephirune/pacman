"""Pre-rendered images for every moving thing in the game.

All shapes are drawn once into off-screen images when a level starts
(the MLX equivalent is ``mlx_new_image`` + writing pixels into it). During
the game the images are only copied to the window, like
``mlx_put_image_to_window``.
"""

import math

import pygame

from pacman.entities import STOP
from pacman.maze import OFFSETS, WALL_E, WALL_N, WALL_S, WALL_W
from pacman.ui.theme import (BLACK, GHOST_COLORS, PELLET, RED, SCARED_BLUE,
                             WHITE, YELLOW, Color)

TRANSPARENT = (0, 0, 0, 0)
MOUTH_ANGLES = [4, 28, 48]           # grados, apertura de la boca por frame
DIRECTION_ANGLE = {WALL_E: 0, WALL_N: 90, WALL_W: 180, WALL_S: 270,
                   STOP: 0}


def _new_image(size: int) -> pygame.Surface:
    """Return a fully transparent square image."""

    image = pygame.Surface((size, size), pygame.SRCALPHA)
    image.fill(TRANSPARENT)
    return image


def make_pacman(size: int, direction: int, mouth: int) -> pygame.Surface:
    """Draw Pac-Man facing ``direction`` with a mouth of ``mouth`` degrees."""

    image = _new_image(size)
    c = size / 2
    r = size * 0.45
    pygame.draw.circle(image, YELLOW, (c, c), r)
    if mouth > 0:
        facing = math.radians(DIRECTION_ANGLE.get(direction, 0))
        half = math.radians(mouth)
        points = [(c, c)]
        steps = 8
        for i in range(steps + 1):
            a = facing - half + 2 * half * i / steps
            points.append((c + math.cos(a) * (r + 2),
                           c - math.sin(a) * (r + 2)))
        pygame.draw.polygon(image, TRANSPARENT, points)
    return image


def _ghost_body(image: pygame.Surface, color: Color) -> None:
    """Draw the dome + wavy skirt shape of a ghost."""

    s = image.get_width()
    left, right = s * 0.08, s * 0.92
    top_c = s * 0.45
    r = (right - left) / 2
    pygame.draw.circle(image, color, (s / 2, top_c), r)
    pygame.draw.rect(image, color,
                     pygame.Rect(round(left), round(top_c),
                                 round(right - left), round(s * 0.42)))
    # Falda ondulada: tres picos hacia abajo
    bottom = s * 0.92
    width = (right - left) / 3
    for i in range(3):
        x0 = left + i * width
        pygame.draw.polygon(image, color, [
            (x0, bottom - s * 0.06), (x0 + width / 2, bottom),
            (x0 + width, bottom - s * 0.06)])
        pygame.draw.polygon(image, color, [
            (x0, top_c), (x0 + width, top_c),
            (x0 + width, bottom - s * 0.06), (x0, bottom - s * 0.06)])


def _ghost_eyes(image: pygame.Surface, direction: int) -> None:
    """Draw the two eyes looking towards ``direction``."""

    s = image.get_width()
    dx, dy = OFFSETS.get(direction, (0, 0))
    for ex in (s * 0.33, s * 0.67):
        ey = s * 0.42
        eye = pygame.Rect(0, 0, round(s * 0.24), round(s * 0.30))
        eye.center = (round(ex + dx * s * 0.04), round(ey + dy * s * 0.04))
        pygame.draw.ellipse(image, WHITE, eye)
        pygame.draw.circle(image, (30, 30, 200),
                           (ex + dx * s * 0.08, ey + dy * s * 0.08),
                           max(1.0, s * 0.07))


def make_ghost(size: int, color: Color, direction: int) -> pygame.Surface:
    """Normal ghost of ``color`` looking towards ``direction``."""

    image = _new_image(size)
    _ghost_body(image, color)
    _ghost_eyes(image, direction)
    return image


def make_scared_ghost(size: int, flash: bool) -> pygame.Surface:
    """Edible ghost; ``flash`` gives the white version used at the end."""

    image = _new_image(size)
    body, face = (WHITE, RED) if flash else (SCARED_BLUE, PELLET)
    _ghost_body(image, body)
    for ex in (0.36, 0.64):
        pygame.draw.circle(image, face, (size * ex, size * 0.42),
                           max(1.0, size * 0.06))
    points = []
    for i in range(7):
        x = size * (0.22 + 0.56 * i / 6)
        y = size * (0.66 if i % 2 == 0 else 0.60)
        points.append((x, y))
    pygame.draw.lines(image, face, False, points, max(1, size // 16))
    return image


def make_eyes(size: int, direction: int) -> pygame.Surface:
    """Only the eyes: a ghost that was eaten and goes back home."""

    image = _new_image(size)
    _ghost_eyes(image, direction)
    return image


def make_dot(size: int, radius: float, color: Color) -> pygame.Surface:
    """A round dot centred in a ``size`` square image."""

    image = _new_image(size)
    pygame.draw.circle(image, color, (size / 2, size / 2), max(1.0, radius))
    return image


class SpriteSet:
    """Every image needed to draw a level at a given tile size."""

    def __init__(self, tile: int) -> None:
        """Pre-render all images for tiles of ``tile`` pixels."""

        self.tile = tile
        directions = [WALL_N, WALL_E, WALL_S, WALL_W, STOP]
        self.pacman: dict[tuple[int, int], pygame.Surface] = {}
        for d in directions:
            for frame, mouth in enumerate(MOUTH_ANGLES):
                self.pacman[(d, frame)] = make_pacman(tile, d, mouth)
        self.ghosts: dict[tuple[int, int], pygame.Surface] = {}
        self.eyes: dict[int, pygame.Surface] = {}
        for d in directions:
            self.eyes[d] = make_eyes(tile, d)
            for i, color in enumerate(GHOST_COLORS):
                self.ghosts[(i, d)] = make_ghost(tile, color, d)
        self.scared = make_scared_ghost(tile, False)
        self.scared_flash = make_scared_ghost(tile, True)
        self.pacgum = make_dot(tile, tile * 0.11, PELLET)
        self.super_pacgum = make_dot(tile, tile * 0.30, PELLET)
        self.blank = make_dot(tile, 0, BLACK)

    def pacman_frame(self, direction: int, t: float) -> pygame.Surface:
        """Pac-Man image for ``direction`` at animation time ``t``."""

        if direction == STOP:
            return self.pacman[(STOP, 1)]
        cycle = [0, 1, 2, 1]
        frame = cycle[int(t * 14) % len(cycle)]
        return self.pacman[(direction, frame)]
