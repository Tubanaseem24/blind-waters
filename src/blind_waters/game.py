"""Game engine: two boards, turns, win check, and a JSON-friendly state."""
import random

from blind_waters.board import Board, HORIZONTAL, VERTICAL
from blind_waters.cell import HIT, MISS
from blind_waters.ship import Ship

FLEET = [("Carrier", 5), ("Battleship", 4), ("Cruiser", 3), ("Submarine", 3), ("Destroyer", 2)]


def place_fleet_randomly(board, rng, max_tries=1000):
    for name, length in FLEET:
        for _ in range(max_tries):
            start = (rng.randrange(board.size), rng.randrange(board.size))
            orientation = rng.choice([HORIZONTAL, VERTICAL])
            if board.can_place(length, start, orientation):
                board.place_ship(Ship(name, length), start, orientation)
                break
        else:
            raise RuntimeError(f"could not place {name}")


def target_view(board, reveal=False):
    """What a shooter may know about a board: shots and sunk ships, never live ship positions."""
    view = []
    for r in range(board.size):
        row = []
        for c in range(board.size):
            state = board.grid[r][c].state
            if state == HIT and (r, c) in board.occupied and board.occupied[(r, c)].is_sunk():
                row.append("sunk")
            elif state == "unknown" and reveal and (r, c) in board.occupied:
                row.append("ship")
            else:
                row.append(state)
        view.append(row)
    return view


def own_view(board):
    """What the owner sees of their own fleet: ships plus incoming hits and misses."""
    view = []
    for r in range(board.size):
        row = []
        for c in range(board.size):
            state = board.grid[r][c].state
            if state == HIT:
                row.append("hit")
            elif state == MISS:
                row.append("miss")
            elif (r, c) in board.occupied:
                row.append("ship")
            else:
                row.append("water")
        view.append(row)
    return view


def describe(outcome):
    if outcome["result"] == MISS:
        return "miss"
    if outcome["ship_sunk"]:
        return f"hit, {outcome['ship_sunk']} sunk!"
    return "hit"


class RandomShooter:
    """Temporary agent that fires at random unknown squares. Replace with agents.py when ready."""

    def __init__(self, seed=None):
        self.rng = random.Random(seed)

    def choose_shot(self, view):
        options = [(r, c) for r, row in enumerate(view) for c, s in enumerate(row) if s == "unknown"]
        return self.rng.choice(options)

    def observe(self, row, col, result):
        pass


class Game:
    def __init__(self, agent=None, seed=None, size=10):
        self.size = size
        self.rng = random.Random(seed)
        self.human_board = Board(size)   # your fleet; the agent fires here
        self.agent_board = Board(size)   # the agent's fleet; you fire here
        place_fleet_randomly(self.human_board, self.rng)
        place_fleet_randomly(self.agent_board, self.rng)
        self.agent = agent if agent is not None else RandomShooter(seed)
        self.winner = None               # "you", "agent", or None while playing
        self.human_shots = 0
        self.agent_shots = 0
        self.log = []

    def is_over(self):
        return self.winner is not None

    def human_fire(self, row, col):
        if self.is_over():
            raise ValueError("the game is over")
        outcome = self.agent_board.receive_shot(row, col)  # raises on a repeat, before anything changes
        self.human_shots += 1
        self.log.append(f"You fired at ({row}, {col}): {describe(outcome)}")
        if self.agent_board.all_sunk():
            self.winner = "you"
            return {"you": {"row": row, "col": col, **outcome}, "agent": None}
        agent_move = self._agent_turn()
        return {"you": {"row": row, "col": col, **outcome}, "agent": agent_move}

    def _agent_turn(self):
        row, col = self.agent.choose_shot(target_view(self.human_board))
        outcome = self.human_board.receive_shot(row, col)
        self.agent_shots += 1
        self.agent.observe(row, col, outcome["result"])
        self.log.append(f"Agent fired at ({row}, {col}): {describe(outcome)}")
        if self.human_board.all_sunk():
            self.winner = "agent"
        return {"row": row, "col": col, **outcome}

    def to_dict(self):
        return {
            "size": self.size,
            "your_fleet": own_view(self.human_board),
            "enemy_waters": target_view(self.agent_board, reveal=self.is_over()),
            "you_shots": self.human_shots,
            "agent_shots": self.agent_shots,
            "winner": self.winner,
            "log": self.log[-20:],
        }
