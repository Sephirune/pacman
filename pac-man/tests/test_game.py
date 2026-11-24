from pathlib import Path

from pacman.config import GameConfig, LevelConfig
from pacman.entities import GhostStates
from pacman.game import (EATEN_RESPAWN, READY_DURATION, Game, GameEvent,
                         GameState, new_game)
from pacman.highscores import HighScores


def small_game(levels: int = 2, lives: int = 3) -> Game:
    cfg = GameConfig(levels=[LevelConfig(14, 10) for _ in range(levels)],
                     lives=lives, level_max_time=30)
    game = new_game(cfg)
    game.ready_timer = 0.0
    return game


def test_new_game_layout() -> None:
    game = small_game()
    assert len(game.ghosts) == 4
    assert len(game.level.super_pacgums) == 4
    assert game.lives == 3
    assert game.level_number == 1


def test_ready_timer_freezes_everything() -> None:
    game = small_game()
    game.ready_timer = READY_DURATION
    start = (game.player.x, game.player.y)
    game.player.queue_direction(1)
    game.update(0.5)
    assert (game.player.x, game.player.y) == start
    assert game.time_elapsed == 0.0


def test_skip_levels_until_victory() -> None:
    game = small_game(levels=2)
    game.cheat_skip = True
    game.update(0.016)
    assert game.level_index == 1
    game.cheat_skip = True
    game.update(0.016)
    assert game.state == GameState.VICTORY
    assert GameEvent.VICTORY in game.pop_events()


def test_eating_all_pacgums_advances() -> None:
    game = small_game()
    game.level.pacgums.clear()
    game.update(0.016)
    assert game.level_index == 1
    assert game.score == 0


def test_touching_ghost_costs_a_life_then_game_over() -> None:
    game = small_game(lives=2)
    for _ in range(2):
        ghost = game.ghosts[0]
        ghost.x, ghost.y = game.player.x, game.player.y
        game.ready_timer = 0.0
        game.cheat_freeze = True
        game.update(0.016)
    assert game.lives == 0
    assert game.state == GameState.GAME_OVER


def test_invincible_cheat() -> None:
    game = small_game()
    game.cheat_invincible = True
    game.cheat_freeze = True
    ghost = game.ghosts[0]
    ghost.x, ghost.y = game.player.x, game.player.y
    game.update(0.016)
    assert game.lives == 3


def test_scared_ghost_is_eaten_and_respawns() -> None:
    game = small_game()
    ghost = game.ghosts[1]
    ghost.state = GhostStates.SCARED
    game.scared_timer = 8.0
    ghost.x, ghost.y = game.player.x, game.player.y
    game.cheat_freeze = True
    game.update(0.016)
    assert ghost.state == GhostStates.EATEN
    assert game.score == game.config.points_per_ghost
    game.update(EATEN_RESPAWN)
    assert game.ghosts[1].state == GhostStates.CHASING
    assert (ghost.x, ghost.y) == ghost.corner


def test_time_limit_costs_a_life() -> None:
    game = small_game()
    game.cheat_freeze = True
    game.time_elapsed = game.config.level_max_time - 0.01
    game.update(0.02)
    assert game.lives == 2
    assert game.time_elapsed == 0.0


def test_long_simulation_does_not_crash() -> None:
    game = small_game(levels=3, lives=99)
    for _ in range(20 * 60):
        game.update(1 / 60)
    assert game.score >= 0


def test_highscores_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "hs.json"
    table = HighScores(str(path))
    warnings: list[str] = []
    for i in range(12):
        table.add(f"P{i}", i * 10)
    assert table.save(warnings)
    again = HighScores(str(path))
    again.load(warnings)
    assert len(again.top()) == 10
    assert again.top()[0].score == 110
    assert warnings == []


def test_corrupt_highscores_moved_to_bak(tmp_path: Path) -> None:
    path = tmp_path / "hs.json"
    path.write_text("{ broken")
    table = HighScores(str(path))
    warnings: list[str] = []
    table.load(warnings)
    assert table.top() == []
    assert (tmp_path / "hs.json.bak").exists()
    assert len(warnings) == 1
