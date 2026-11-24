"""Every screen of the game: menu, highscores, instructions, game, end."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from pacman.game import Game, GameEvent, GameState, LevelLoadError, new_game
from pacman.highscores import MAX_NAME_LENGTH, ScoreEntry, validate_name
from pacman.maze import WALL_E, WALL_N, WALL_S, WALL_W
from pacman.ui.renderer import GameRenderer
from pacman.ui.theme import (BACKGROUND, CYAN, GHOST_COLORS, GREEN, GREY,
                             PELLET, RED, WHITE, WINDOW_HEIGHT, WINDOW_WIDTH,
                             YELLOW, draw_text)

if TYPE_CHECKING:
    from pacman.ui.app import App

# Flechas (por tecla) y WASD (por posicion fisica: funciona en AZERTY/QWERTY)
ARROW_KEYS = {pygame.K_UP: WALL_N, pygame.K_DOWN: WALL_S,
              pygame.K_LEFT: WALL_W, pygame.K_RIGHT: WALL_E}
WASD_SCANCODES = {pygame.KSCAN_W: WALL_N, pygame.KSCAN_S: WALL_S,
                  pygame.KSCAN_A: WALL_W, pygame.KSCAN_D: WALL_E}
END_DELAY = 2.0


def key_direction(event: pygame.event.Event) -> int | None:
    """Return the maze direction for a KEYDOWN event, or None."""

    if event.key in ARROW_KEYS:
        return ARROW_KEYS[event.key]
    scancode = getattr(event, "scancode", None)
    if scancode in WASD_SCANCODES:
        return WASD_SCANCODES[scancode]
    return None


def is_up(event: pygame.event.Event) -> bool:
    """Menu navigation: up."""

    return key_direction(event) == WALL_N


def is_down(event: pygame.event.Event) -> bool:
    """Menu navigation: down."""

    return key_direction(event) == WALL_S


def is_confirm(event: pygame.event.Event) -> bool:
    """Menu navigation: validate."""

    return event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)


def draw_overlay(screen: pygame.Surface, alpha: int = 170) -> None:
    """Darken the whole window (used behind pop-up menus)."""

    shade = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    shade.fill((0, 0, 0, alpha))
    screen.blit(shade, (0, 0))


def draw_menu(screen: pygame.Surface, app: App, options: list[str],
              selected: int, top: int, x: int) -> None:
    """Vertical list of options with the selected one highlighted."""

    for i, label in enumerate(options):
        y = top + i * 56
        if i == selected:
            icon = app.menu_sprites.pacman_frame(WALL_E, app.clock_time)
            draw_text(screen, app.fonts.big, label, YELLOW, (x, y))
            width = app.fonts.big.size(label)[0]
            screen.blit(icon, (x - width // 2 - 46, y - 16))
        else:
            draw_text(screen, app.fonts.big, label, WHITE, (x, y))


def draw_score_table(screen: pygame.Surface, app: App,
                     entries: list[ScoreEntry], top: int, x: int,
                     highlight: ScoreEntry | None = None) -> None:
    """Top-10 table centred on ``x``."""

    if not entries:
        draw_text(screen, app.fonts.medium, "No scores yet", GREY,
                  (x, top + 20))
        return
    for i, entry in enumerate(entries):
        y = top + i * 34
        color = GREEN if entry is highlight else WHITE
        draw_text(screen, app.fonts.medium, f"{i + 1:>2}.", GREY,
                  (x - 130, y), "right")
        draw_text(screen, app.fonts.medium, entry.name, color,
                  (x - 115, y), "left")
        draw_text(screen, app.fonts.medium, str(entry.score), color,
                  (x + 150, y), "right")


class Screen:
    """Base class for one screen of the application."""

    def __init__(self, app: App) -> None:
        """Remember the application to switch screens."""

        self.app = app

    def handle_event(self, event: pygame.event.Event) -> None:
        """React to one pygame event."""

    def update(self, dt: float) -> None:
        """Advance ``dt`` seconds."""

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the screen."""


# ----------------------------------------------------------------------
class MenuScreen(Screen):
    """Main menu with the top-10 table on the side."""

    OPTIONS = ["Start Game", "View Highscores", "Instructions", "Exit"]

    def __init__(self, app: App, highlight: ScoreEntry | None = None) -> None:
        """Start with the first option selected. ``highlight`` is the
        score just saved, shown in green in the top-10 table."""

        super().__init__(app)
        self.selected = 0
        self.highlight = highlight

    def handle_event(self, event: pygame.event.Event) -> None:
        """Arrows / WASD to move, Enter to validate, Esc to quit."""

        if event.type != pygame.KEYDOWN:
            return
        if is_up(event):
            self.selected = (self.selected - 1) % len(self.OPTIONS)
        elif is_down(event):
            self.selected = (self.selected + 1) % len(self.OPTIONS)
        elif event.key == pygame.K_ESCAPE:
            self.app.quit()
        elif is_confirm(event):
            choice = self.OPTIONS[self.selected]
            if choice == "Start Game":
                self.app.start_game()
            elif choice == "View Highscores":
                self.app.switch(HighscoresScreen(self.app))
            elif choice == "Instructions":
                self.app.switch(InstructionsScreen(self.app))
            else:
                self.app.quit()

    def draw(self, screen: pygame.Surface) -> None:
        """Title, options, highscores and a little animation."""

        screen.fill(BACKGROUND)
        draw_text(screen, self.app.fonts.title, "PAC-MAN", YELLOW,
                  (WINDOW_WIDTH // 2, 90))
        draw_text(screen, self.app.fonts.small, "Ghosts! More ghosts!",
                  GREY, (WINDOW_WIDTH // 2, 145))
        draw_menu(screen, self.app, self.OPTIONS, self.selected, 270, 300)

        draw_text(screen, self.app.fonts.medium, "TOP 10", CYAN, (740, 215))
        draw_score_table(screen, self.app, self.app.highscores.top(),
                         255, 740, self.highlight)

        self._draw_parade(screen)
        if self.app.message:
            draw_text(screen, self.app.fonts.small, self.app.message, RED,
                      (WINDOW_WIDTH // 2, WINDOW_HEIGHT - 30))

    def _draw_parade(self, screen: pygame.Surface) -> None:
        """Pac-Man chased by the four ghosts at the bottom of the menu."""

        sprites = self.app.menu_sprites
        y = 640
        span = WINDOW_WIDTH + 300
        x = int(self.app.clock_time * 160) % span - 150
        for i in range(0, WINDOW_WIDTH, 40):
            if i > x + 30:
                screen.blit(sprites.pacgum, (i, y))
        screen.blit(sprites.pacman_frame(WALL_E, self.app.clock_time),
                    (x, y))
        for i in range(4):
            screen.blit(sprites.ghosts[(i, WALL_E)], (x - 60 - i * 40, y))


# ----------------------------------------------------------------------
class HighscoresScreen(Screen):
    """Full top-10 table."""

    def __init__(self, app: App, highlight: ScoreEntry | None = None) -> None:
        """``highlight`` is the entry just added (shown in green)."""

        super().__init__(app)
        self.highlight = highlight

    def handle_event(self, event: pygame.event.Event) -> None:
        """Any validating key goes back to the menu."""

        if event.type == pygame.KEYDOWN and (
                is_confirm(event) or event.key == pygame.K_ESCAPE):
            self.app.switch(MenuScreen(self.app))

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the table."""

        screen.fill(BACKGROUND)
        draw_text(screen, self.app.fonts.big, "HIGHSCORES", YELLOW,
                  (WINDOW_WIDTH // 2, 80))
        draw_score_table(screen, self.app, self.app.highscores.top(), 170,
                         WINDOW_WIDTH // 2, self.highlight)
        draw_text(screen, self.app.fonts.small,
                  "Press ENTER or ESC to go back", GREY,
                  (WINDOW_WIDTH // 2, WINDOW_HEIGHT - 50))


# ----------------------------------------------------------------------
INSTRUCTIONS = [
    ("CONTROLS", CYAN),
    ("Arrow keys or WASD : move", WHITE),
    ("P or ESC : pause / resume", WHITE),
    ("", WHITE),
    ("RULES", CYAN),
    ("Eat every small dot to clear the level.", WHITE),
    ("Big dots in the corners make ghosts edible for a while.", WHITE),
    ("Touching a ghost costs a life; edible ghosts give points.", WHITE),
    ("When the timer runs out you lose a life and it restarts.", WHITE),
    ("Clear every level to win. Score and lives carry over.", WHITE),
    ("", WHITE),
    ("CHEATS (for evaluation)", GREEN),
    ("1 : invincible    2 : freeze ghosts    3 : skip level", WHITE),
    ("4 : extra life    5 : double speed", WHITE),
]


class InstructionsScreen(Screen):
    """Controls and rules."""

    def handle_event(self, event: pygame.event.Event) -> None:
        """Any validating key goes back to the menu."""

        if event.type == pygame.KEYDOWN and (
                is_confirm(event) or event.key == pygame.K_ESCAPE):
            self.app.switch(MenuScreen(self.app))

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the text and the ghost roster."""

        screen.fill(BACKGROUND)
        draw_text(screen, self.app.fonts.big, "INSTRUCTIONS", YELLOW,
                  (WINDOW_WIDTH // 2, 60))
        y = 130
        for line, color in INSTRUCTIONS:
            draw_text(screen, self.app.fonts.medium, line, color,
                      (WINDOW_WIDTH // 2, y))
            y += 34
        names = ["Blinky: chases", "Pinky: ambushes",
                 "Inky: unpredictable", "Clyde: shy"]
        for i, name in enumerate(names):
            x = 80 + i * 230
            screen.blit(self.app.menu_sprites.ghosts[(i, WALL_E)],
                        (x, 630))
            draw_text(screen, self.app.fonts.small, name, GHOST_COLORS[i],
                      (x + 40, 646), "left")
        draw_text(screen, self.app.fonts.small,
                  "Press ENTER or ESC to go back", GREY,
                  (WINDOW_WIDTH // 2, WINDOW_HEIGHT - 40))


# ----------------------------------------------------------------------
class GameScreen(Screen):
    """The game itself, with the pause menu on top when paused."""

    PAUSE_OPTIONS = ["Resume", "Main Menu"]

    def __init__(self, app: App, game: Game) -> None:
        """Wrap a freshly created Game."""

        super().__init__(app)
        self.game = game
        self.renderer = GameRenderer(app.fonts)
        self.pause_selected = 0
        self.end_timer = END_DELAY

    def handle_event(self, event: pygame.event.Event) -> None:
        """Movement, pause and cheat keys."""

        if event.type == pygame.WINDOWFOCUSLOST:
            self.game.pause()
            return
        if event.type != pygame.KEYDOWN or self.game.is_over:
            return
        if self.game.state == GameState.PAUSED:
            self._pause_event(event)
            return
        direction = key_direction(event)
        if direction is not None:
            self.game.player.queue_direction(direction)
        elif event.key in (pygame.K_p, pygame.K_ESCAPE):
            self.pause_selected = 0
            self.game.pause()
        elif event.key in (pygame.K_1, pygame.K_KP1):
            self.game.cheat_invincible = not self.game.cheat_invincible
        elif event.key in (pygame.K_2, pygame.K_KP2):
            self.game.cheat_freeze = not self.game.cheat_freeze
        elif event.key in (pygame.K_3, pygame.K_KP3):
            self.game.cheat_skip = True
        elif event.key in (pygame.K_4, pygame.K_KP4):
            self.game.cheat_add_life()
        elif event.key in (pygame.K_5, pygame.K_KP5):
            self.game.toggle_cheat_speed()

    def _pause_event(self, event: pygame.event.Event) -> None:
        """Navigation inside the pause menu."""

        if event.key in (pygame.K_p, pygame.K_ESCAPE):
            self.game.resume()
        elif is_up(event) or is_down(event):
            self.pause_selected = 1 - self.pause_selected
        elif is_confirm(event):
            if self.pause_selected == 0:
                self.game.resume()
            else:
                self.app.switch(MenuScreen(self.app))

    def update(self, dt: float) -> None:
        """Advance the game, then react to what happened."""

        self.game.update(dt)
        for event in self.game.pop_events():
            pos = (float(self.game.player.x), float(self.game.player.y))
            if event == GameEvent.GHOST_EATEN:
                self.renderer.add_floating(
                    f"+{self.game.config.points_per_ghost}", pos)
            elif event == GameEvent.TIME_UP:
                self.renderer.add_floating("TIME UP!", pos)
        if self.game.state != GameState.PAUSED:
            self.renderer.update(dt)

        if self.game.state == GameState.ERROR:
            self.app.message = f"Error: {self.game.error_message}"
            self.app.switch(MenuScreen(self.app))
        elif self.game.is_over:
            self.end_timer -= dt
            if self.end_timer <= 0:
                self.app.switch(EndScreen(self.app, self.game))

    def draw(self, screen: pygame.Surface) -> None:
        """Game view + pause / end overlays."""

        self.renderer.draw(screen, self.game)
        cx, cy = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2
        if self.game.state == GameState.PAUSED:
            draw_overlay(screen)
            draw_text(screen, self.app.fonts.title, "PAUSED", YELLOW,
                      (cx, cy - 120))
            draw_menu(screen, self.app, self.PAUSE_OPTIONS,
                      self.pause_selected, cy, cx)
        elif self.game.state == GameState.GAME_OVER:
            draw_overlay(screen, 110)
            draw_text(screen, self.app.fonts.title, "GAME OVER", RED,
                      (cx, cy))
        elif self.game.state == GameState.VICTORY:
            draw_overlay(screen, 110)
            draw_text(screen, self.app.fonts.title, "YOU WIN!", YELLOW,
                      (cx, cy))


# ----------------------------------------------------------------------
class EndScreen(Screen):
    """Game over / victory: final score and name input."""

    def __init__(self, app: App, game: Game) -> None:
        """Keep the result of the finished game."""

        super().__init__(app)
        self.victory = game.state == GameState.VICTORY
        self.score = game.score
        self.level_reached = game.level_number
        self.level_count = game.level_count
        self.name = ""
        self.error = ""

    def handle_event(self, event: pygame.event.Event) -> None:
        """Type a name; Enter saves, Esc skips."""

        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self.app.switch(MenuScreen(self.app))
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self._save()
        elif event.key == pygame.K_BACKSPACE:
            self.name = self.name[:-1]
            self.error = ""
        else:
            char = event.unicode
            if (len(char) == 1 and len(self.name) < MAX_NAME_LENGTH
                    and (char == " " or (char.isascii()
                                         and char.isalnum()))):
                self.name += char
                self.error = ""

    def _save(self) -> None:
        """Validate the name, add the score and save the file."""

        try:
            name = validate_name(self.name)
        except ValueError as e:
            self.error = str(e)
            return
        entered = self.app.highscores.add(name, self.score)
        self.app.save_highscores()
        highlight = None
        if entered:
            for entry in self.app.highscores.top():
                if entry.name == name and entry.score == self.score:
                    highlight = entry
        self.app.message = "" if entered else \
            f"{name}: {self.score} points did not reach the top 10."
        self.app.switch(MenuScreen(self.app, highlight))

    def draw(self, screen: pygame.Surface) -> None:
        """Result, score and input box."""

        screen.fill(BACKGROUND)
        cx = WINDOW_WIDTH // 2
        if self.victory:
            draw_text(screen, self.app.fonts.title, "CONGRATULATIONS!",
                      YELLOW, (cx, 130))
            draw_text(screen, self.app.fonts.medium,
                      f"You cleared all {self.level_count} levels!",
                      WHITE, (cx, 200))
        else:
            draw_text(screen, self.app.fonts.title, "GAME OVER", RED,
                      (cx, 130))
            draw_text(screen, self.app.fonts.medium,
                      f"You reached level {self.level_reached}"
                      f" of {self.level_count}", WHITE, (cx, 200))
        draw_text(screen, self.app.fonts.big, f"FINAL SCORE: {self.score}",
                  PELLET, (cx, 290))

        draw_text(screen, self.app.fonts.medium, "Enter your name:", WHITE,
                  (cx, 390))
        box = pygame.Rect(0, 0, 360, 60)
        box.center = (cx, 450)
        pygame.draw.rect(screen, CYAN, box, 3, border_radius=6)
        cursor = "_" if int(self.app.clock_time * 2) % 2 == 0 else " "
        draw_text(screen, self.app.fonts.big, self.name + cursor, YELLOW,
                  box.center)
        draw_text(screen, self.app.fonts.small,
                  f"Max {MAX_NAME_LENGTH} characters: letters, digits "
                  "and spaces", GREY, (cx, 505))
        if self.error:
            draw_text(screen, self.app.fonts.small, self.error, RED,
                      (cx, 540))
        draw_text(screen, self.app.fonts.small,
                  "ENTER: save score    ESC: skip", GREY,
                  (cx, WINDOW_HEIGHT - 60))


def start_game_screen(app: App) -> Screen:
    """Create a new game, or stay on the menu with an error message."""

    try:
        game = new_game(app.config)
    except LevelLoadError as e:
        app.message = f"Error: {e}"
        return MenuScreen(app)
    app.message = ""
    return GameScreen(app, game)
