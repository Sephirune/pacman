from dataclasses import dataclass
from pacman.maze import MazeData, OFFSETS, OPPOSITE
from enum import Enum
from random import Random

STOP = 0
WALL_N, WALL_E, WALL_S, WALL_W = 1, 2, 4, 8
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


@dataclass
class GhostStates(Enum):
    """Enum class that represents the
    status of ghosts."""
    SCARED = 1
    CHASING = 2
    EATEN = 3


@dataclass(kw_only=True)
class Ghost(Entity):
    """Class that represents ghosts in the maze."""

    state: GhostStates
    corner: tuple[int, int]
    target: tuple[int, int]
    rng: Random

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
            if self.state == GhostStates.EATEN:
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
