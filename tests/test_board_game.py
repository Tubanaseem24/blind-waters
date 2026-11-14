import json

from blind_waters.board import Board, HORIZONTAL, VERTICAL
from blind_waters.game import Game, own_view, target_view
from blind_waters.ship import Ship


class InOrder:
    """Fires at every square in order: a predictable agent for tests."""

    def __init__(self):
        self.next = 0

    def choose_shot(self, view):
        i = self.next
        self.next += 1
        return divmod(i, len(view))

    def observe(self, row, col, result):
        pass


def test_placement_rules():
    board = Board(10)
    assert not board.can_place(5, (0, 8), HORIZONTAL)  # runs off the edge
    board.place_ship(Ship("Cruiser", 3), (0, 0), HORIZONTAL)
    assert not board.can_place(2, (0, 2), VERTICAL)     # overlaps at (0, 2)


def test_hit_miss_and_sink():
    board = Board(10)
    board.place_ship(Ship("Destroyer", 2), (0, 0), HORIZONTAL)
    assert board.receive_shot(5, 5) == {"result": "miss", "ship_sunk": None}
    assert board.receive_shot(0, 0) == {"result": "hit", "ship_sunk": None}
    assert board.receive_shot(0, 1) == {"result": "hit", "ship_sunk": "Destroyer"}
    assert board.all_sunk()


def test_repeat_shot_rejected():
    board = Board(10)
    board.receive_shot(3, 3)
    try:
        board.receive_shot(3, 3)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_game_reaches_a_winner():
    game = Game(agent=InOrder(), seed=1)
    for i in range(100):
        if game.is_over():
            break
        game.human_fire(*divmod(i, 10))
    assert game.is_over()
    assert game.winner in ("you", "agent")


def test_enemy_ships_hidden_at_start():
    game = Game(seed=2)
    view = target_view(game.agent_board)
    assert all(s == "unknown" for row in view for s in row)


def test_own_fleet_has_17_ship_squares():
    game = Game(seed=2)
    flat = [s for row in own_view(game.human_board) for s in row]
    assert flat.count("ship") == 17  # 5 + 4 + 3 + 3 + 2


def test_state_is_json_serializable():
    game = Game(seed=3)
    json.dumps(game.to_dict())
