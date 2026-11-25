"""Draws a running Game: maze, pacgums, entities and the HUD."""

import pygame

from pacman.entities import GhostStates
from pacman.game import Game, GameState
from pacman.level import Level
from pacman.maze import (BLOCKED, OFFSETS, WALL_E, WALL_N, WALL_S, WALL_W,
                         MazeData)
from pacman.ui.sprites import SpriteSet
from pacman.ui.theme import (BACKGROUND, GREEN, GREY, RED, WALL, WALL_FILL,
                             WHITE, WINDOW_HEIGHT, WINDOW_WIDTH, YELLOW,
                             Fonts, draw_text)

HUD_HEIGHT = 56
FOOTER_HEIGHT = 40
MARGIN = 12
MAX_TILE = 40
MIN_TILE = 8
FLASH_TIME = 2.0   # el fantasma asustado parpadea los ultimos 2 segundos


def tile_size_for(maze: MazeData) -> int:
    """Biggest tile size so the whole maze fits in the play area."""

    area_w = WINDOW_WIDTH - 2 * MARGIN
    area_h = WINDOW_HEIGHT - HUD_HEIGHT - FOOTER_HEIGHT - 2 * MARGIN
    tile = min(area_w // maze.width, area_h // maze.height, MAX_TILE)
    return max(tile, MIN_TILE)


def render_maze(maze: MazeData, tile: int) -> pygame.Surface:
    """Draw the walls of ``maze`` once into an image."""

    image = pygame.Surface((maze.width * tile, maze.height * tile))
    image.fill(BACKGROUND)
    thick = max(2, tile // 7)
    for y in range(maze.height):
        for x in range(maze.width):
            cell = maze.grid[y][x]
            left, top = x * tile, y * tile
            right, bottom = left + tile - 1, top + tile - 1
            if cell == BLOCKED:
                pygame.draw.rect(image, WALL_FILL,
                                 pygame.Rect(left, top, tile, tile))
            edges = [
                (WALL_N, (left, top), (right, top)),
                (WALL_S, (left, bottom), (right, bottom)),
                (WALL_W, (left, top), (left, bottom)),
                (WALL_E, (right, top), (right, bottom)),
            ]
            for bit, start, end in edges:
                # Entre dos celdas del "42" no se dibuja pared: bloque macizo
                dx, dy = OFFSETS[bit]
                inside_42 = (cell == BLOCKED and
                             maze.is_blocked(x + dx, y + dy) and
                             0 <= x + dx < maze.width and
                             0 <= y + dy < maze.height)
                if cell & bit and not inside_42:
                    pygame.draw.line(image, WALL, start, end, thick)
                    pygame.draw.circle(image, WALL, start, thick / 2)
                    pygame.draw.circle(image, WALL, end, thick / 2)
    return image


class FloatingText:
    """Small text that floats up and disappears (e.g. "+200")."""

    def __init__(self, text: str, pos: tuple[float, float]) -> None:
        """Create the text at pixel position ``pos``."""

        self.text = text
        self.x, self.y = pos
        self.ttl = 1.0

    def update(self, dt: float) -> None:
        """Move up and fade."""

        self.ttl -= dt
        self.y -= 20 * dt


class GameRenderer:
    """Keeps the per-level images and draws a Game on the window."""

    def __init__(self, fonts: Fonts) -> None:
        """Create an empty renderer; images are built on first draw."""

        self.fonts = fonts
        self._level: Level | None = None
        self.tile = MAX_TILE
        self.origin = (0, 0)
        self.maze_image = pygame.Surface((1, 1))
        self.sprites = SpriteSet(self.tile)
        self.hud_sprites = SpriteSet(24)
        self.floating: list[FloatingText] = []
        self.anim_time = 0.0

    def _prepare(self, level: Level) -> None:
        """Rebuild images when a new level starts."""

        if self._level is level:
            return
        self._level = level
        tile = tile_size_for(level.maze)
        if tile != self.tile:
            self.tile = tile
            self.sprites = SpriteSet(tile)
        self.maze_image = render_maze(level.maze, tile)
        play_h = WINDOW_HEIGHT - HUD_HEIGHT - FOOTER_HEIGHT
        ox = (WINDOW_WIDTH - self.maze_image.get_width()) // 2
        oy = HUD_HEIGHT + (play_h - self.maze_image.get_height()) // 2
        self.origin = (ox, oy)
        self.floating.clear()

    def to_screen(self, fx: float, fy: float) -> tuple[int, int]:
        """Top-left pixel of the (float) cell position ``(fx, fy)``."""

        return (round(self.origin[0] + fx * self.tile),
                round(self.origin[1] + fy * self.tile))

    def add_floating(self, text: str, cell: tuple[float, float]) -> None:
        """Show ``text`` above the given cell for one second."""

        px, py = self.to_screen(*cell)
        self.floating.append(FloatingText(text, (px + self.tile / 2, py)))

    def update(self, dt: float) -> None:
        """Advance animations."""

        self.anim_time += dt
        for f in self.floating:
            f.update(dt)
        self.floating = [f for f in self.floating if f.ttl > 0]

    # ------------------------------------------------------------------
    def draw(self, screen: pygame.Surface, game: Game) -> None:
        """Draw the whole game view."""

        self._prepare(game.level)
        screen.fill(BACKGROUND)
        screen.blit(self.maze_image, self.origin)
        self._draw_pacgums(screen, game)
        self._draw_ghosts(screen, game)
        px, py = game.player.exact_position()
        moving = (game.ready_timer <= 0
                  and game.state == GameState.PLAYING)
        frame = self.sprites.pacman_frame(
            game.player.direction, self.anim_time if moving else 0.1)
        screen.blit(frame, self.to_screen(px, py))
        for f in self.floating:
            draw_text(screen, self.fonts.small, f.text, WHITE,
                      (round(f.x), round(f.y)))
        if game.ready_timer > 0 and game.state == GameState.PLAYING:
            sx, sy = self.to_screen(*game.level.player_start)
            draw_text(screen, self.fonts.medium, "READY!", YELLOW,
                      (sx + self.tile // 2, sy - self.tile // 2))
        self._draw_hud(screen, game)

    def _draw_pacgums(self, screen: pygame.Surface, game: Game) -> None:
        """Small and big dots."""

        for cell in game.level.pacgums:
            screen.blit(self.sprites.pacgum, self.to_screen(*cell))
        if int(self.anim_time * 4) % 2 == 0:
            for cell in game.level.super_pacgums:
                screen.blit(self.sprites.super_pacgum, self.to_screen(*cell))

    def _draw_ghosts(self, screen: pygame.Surface, game: Game) -> None:
        """Ghost images depending on their state."""

        flash = (game.scared_timer < FLASH_TIME
                 and int(self.anim_time * 6) % 2 == 0)
        for i, ghost in enumerate(game.ghosts):
            if ghost.state == GhostStates.SCARED:
                image = (self.sprites.scared_flash if flash
                         else self.sprites.scared)
            elif ghost.state == GhostStates.EATEN:
                image = self.sprites.eyes[ghost.direction]
            else:
                image = self.sprites.ghosts[(i % 4, ghost.direction)]
            screen.blit(image, self.to_screen(*ghost.exact_position()))

    def _draw_hud(self, screen: pygame.Surface, game: Game) -> None:
        """Score, level, time, lives and active cheats."""

        mid = HUD_HEIGHT // 2
        draw_text(screen, self.fonts.medium, f"SCORE {game.score}", WHITE,
                  (24, mid), "left")
        draw_text(screen, self.fonts.medium,
                  f"LEVEL {game.level_number}/{game.level_count}", YELLOW,
                  (WINDOW_WIDTH // 2, mid))
        left = int(game.time_left + 0.999)
        time_color = RED if left <= 10 else WHITE
        draw_text(screen, self.fonts.medium,
                  f"TIME {left // 60}:{left % 60:02d}", time_color,
                  (WINDOW_WIDTH - 24, mid), "right")

        foot = WINDOW_HEIGHT - FOOTER_HEIGHT // 2
        icon = self.hud_sprites.pacman[(WALL_W, 1)]
        shown = min(game.lives, 8)
        for i in range(shown):
            screen.blit(icon, (20 + i * 30, foot - 12))
        if game.lives > shown:
            draw_text(screen, self.fonts.small, f"x{game.lives}", WHITE,
                      (24 + shown * 30, foot), "left")

        cheats = []
        if game.cheat_invincible:
            cheats.append("INVINCIBLE")
        if game.cheat_freeze:
            cheats.append("FREEZE")
        if game.cheat_speed != 1.0:
            cheats.append("SPEED")
        if cheats:
            draw_text(screen, self.fonts.small,
                      "CHEATS: " + " ".join(cheats), GREEN,
                      (WINDOW_WIDTH - 20, foot), "right")
        else:
            draw_text(screen, self.fonts.small, "P / ESC: pause", GREY,
                      (WINDOW_WIDTH - 20, foot), "right")
