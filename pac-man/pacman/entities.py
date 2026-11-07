from dataclasses import dataclass
from pacman.maze import MazeData, OFFSETS, OPPOSITE, WALL_N, WALL_E, WALL_S, WALL_W
from enum import Enum
from random import Random

STOP = 0
#  He creado esto para resolver empates. El orden que tenias tu no es el correcto, pero al iterar con esto en este orden los empates se resuelven solos
#  Imagina que tenemos WALL_N = 5 Y WALL_W = 5. Si no iteramos en el orden de N, W, S, E ganaria WALL_W  porque iba primero cuando no era asi
#  Wall_N: 5 < inf pasa a ser la best_distance y direction y luego, al procesar WALL_W: 5<5, no se actualiza nada al respeta el orden
TIEBREAK_ORDER = [WALL_N, WALL_W, WALL_S, WALL_E]


@dataclass
class Entity:
    """Class that represents something that moves through the maze."""

    x: int
    y: int
    speed: float
    direction: int = STOP
    progress: float = 0.0

    def choose_direction(self, maze: MazeData) -> int:  # que quiere hacer el personaje?
        """Return the direction to take from the current cell."""

        raise NotImplementedError

    def _pick(self, maze: MazeData) -> int:  # es posible que haga eso?
        """Returns a possible direction, or STOP."""

        direction = self.choose_direction(maze)
        if direction != STOP and maze.can_move(self.x, self.y, direction):
            return direction
        else:
            return STOP

    def update(self, dt: float, maze: MazeData) -> None:
        """Advance ``dt`` seconds."""

        remaining_cells = self.speed * dt
        if self.direction == STOP:
            self.direction = self._pick(maze)
        while self.direction != STOP:
            needed = (1 - self.progress)
            if remaining_cells < needed:
                self.progress += remaining_cells
                return
            else:
                remaining_cells -= needed
                dx, dy = OFFSETS[self.direction]
                self.x += dx
                self.y += dy
                self.progress = 0.0
                self.direction = self._pick(maze)

    def reverse(self) -> None:
        """Turn around between two cells."""

        if self.direction == STOP or self.progress == 0.0:
            return

        dx, dy = OFFSETS[self.direction]
        self.x += dx
        self.y += dy
        self.progress = 1.0 - self.progress
        self.direction = OPPOSITE[self.direction]

    def exact_position(self) -> tuple[float, float]:
        """Return the position as floats, for drawing."""

        if self.direction == STOP:
            return (float(self.x), float(self.y))
        else:
            dx, dy = OFFSETS[self.direction]
            return (self.x + dx * self.progress, self.y + dy * self.progress)


@dataclass
class Player(Entity):
    """Class that represents the player. Moves and turns when it can."""

    queued: int = STOP

    def queue_direction(self, direction: int) -> None:
        """Remember the direction the player wants to take."""

        if direction in OFFSETS:
            self.queued = direction
        else:
            raise ValueError(f"Invalid direction: {direction}")

    def choose_direction(self, maze: MazeData) -> int:
        """Choose the direction to take from the current cell.
        Use the queued direction if possible, else keep going, else STOP.
        """

        if self.queued != STOP and maze.can_move(self.x,
                                                 self.y,
                                                 self.queued):
            new_direction = self.queued
            self.queued = STOP
            return new_direction
        if self.direction != STOP:
            return self.direction
        else:
            return STOP

    def update(self, dt: float, maze: MazeData) -> None:
        """Advance ``dt`` seconds, turning around first if requested."""

        if (self.direction != STOP
                and self.queued == OPPOSITE[self.direction]
                and self.progress > 0):
            self.reverse()
            self.queued = STOP

        super().update(dt, maze)


class GhostStates(Enum):
    """Enum class that represents the
    status of ghosts."""

    SCARED = 1
    CHASING = 2
    EATEN = 3


class GhostPersonality(Enum):
    """Class that represents ghosts's personalities."""

    BLINKY = 1  # Persigue
    PINKY = 2  # Embosca 4 celdas por delante
    INKY = 3  # tiene tdah y ansiedad
    CLYDE = 4  # Cobarde


@dataclass(kw_only=True)
class Ghost(Entity):
    """Class that represents ghosts in the maze."""

    state: GhostStates
    corner: tuple[int, int]
    target: tuple[int, int]
    personality: GhostPersonality
    last_target_change: float = 0.0
    distraction_timer: float = 3.0  # Cada cuanto puede cambiar
    rng: Random

    def update_target(self,
                      player: Entity,
                      maze: MazeData,
                      current_time: float) -> None:
        if self.personality == GhostPersonality.BLINKY:
            self.target = (player.x, player.y)

        elif self.personality == GhostPersonality.PINKY:
            player_dir = player.direction
            if player_dir == STOP:
                self.target = (player.x, player.y)
                return
            target_x = player.x + 4 * OFFSETS[player_dir][0]
            target_y = player.y + 4 * OFFSETS[player_dir][1]

            bounds = (0 <= target_x < maze.width and
                      0 <= target_y < maze.height)
            if bounds and not maze.is_blocked(target_x, target_y):
                self.target = (target_x, target_y)
            else:
                self.target = (player.x, player.y)

        elif self.personality == GhostPersonality.CLYDE:
            distance = maze.distances_from(player.x, player.y)
            distance_player = distance.get((self.x, self.y), float('inf'))

            if distance_player > 8:
                self.target = (player.x, player.y)
            else:
                self.target = self.corner

        elif self.personality == GhostPersonality.INKY:
            if current_time - self.last_target_change > self.distraction_timer:
                if self.rng.random() < 0.5:
                    self.target = (player.x, player.y)
                else:
                    free_cells = []
                    for y in range(maze.height):
                        for x in range(maze.width):
                            if not maze.is_blocked(x, y):
                                free_cells.append((x, y))
                    self.target = self.rng.choice(free_cells)

                self.last_target_change = current_time

    def choose_direction(self, maze: MazeData) -> int:

        possible_directions: list[int] = []
        for direction in OFFSETS:
            if maze.can_move(self.x, self.y, direction):
                possible_directions.append(direction)

        # Filtramos la marcha atras si se esta moviendo y hay mas opciones
        if self.direction != STOP:
            if len(possible_directions) > 1 and OPPOSITE[self.direction] in possible_directions:
                possible_directions.remove(OPPOSITE[self.direction])

        if not possible_directions:
            return STOP

        if self.state == GhostStates.SCARED:
            return self.rng.choice(possible_directions)

        elif (self.state == GhostStates.CHASING or
              self.state == GhostStates.EATEN):
            if self.state == GhostStates.CHASING:
                distances = maze.distances_from(self.target[0], self.target[1])
            elif self.state == GhostStates.EATEN:
                distances = maze.distances_from(self.corner[0], self.corner[1])

            best_direction = STOP
            best_distance = float('inf')

            for direction in TIEBREAK_ORDER:
                if direction in possible_directions:
                    dx, dy = OFFSETS[direction]
                    nx, ny = self.x + dx, self.y + dy
                    if (nx, ny) in distances:
                        distance = distances[(nx, ny)]
                        if distance < best_distance:
                            best_distance = distance
                            best_direction = direction

            return best_direction
