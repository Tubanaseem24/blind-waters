
import random


class Agent:
    def __init__(self, board_size=10, seed=None):
        self.board_size = board_size
        self.seed = seed
        self.reset()

    def reset(self):
        """Start a new game"""
        self.rng = random.Random(self.seed)

    def unknown_cells(self, state):
        """List of all cells that are not fired at yet."""
        n = self.board_size
        return [(r, c) for r in range(n) for c in range(n)
                if state[r][c] == "unknown"]

    def random_unknown(self, state):
        """Pick random cell. Error if the board is already full."""
        cells = self.unknown_cells(state)
        if not cells:
            raise ValueError("No unknown cells left to fire at")
        return self.rng.choice(cells)

    def choose_shot(self, state):
        raise NotImplementedError

    def observe(self, result):
        pass


class RandomAgent(Agent):
    """Baseline: fire at a random unknown cell."""

    def choose_shot(self, state):
        return self.random_unknown(state)


class HuntTargetAgent(Agent):
    """HUNT: fire randomly. TARGET: after a hit, try the 4 neighbours."""

    def reset(self):
        super().reset()
        self.targets = []          # cells to try next (neighbours of hits)

    def neighbours(self, cell):
        r, c = cell
        return [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]

    def choose_shot(self, state):
        # TARGET mode: use the queue of neighbour cells first
        while self.targets:
            cell = self.targets.pop()
            if state[cell[0]][cell[1]] == "unknown":
                return cell
        # HUNT mode: queue is empty, fire at a random unknown cell
        return self.random_unknown(state)

    def observe(self, result):
        if result["sunk"]:
            self.targets = []      # ship finished, go back to hunting
            return
        if result["hit"]:
            for r, c in self.neighbours(result["cell"]):
                if 0 <= r < self.board_size and 0 <= c < self.board_size:
                    self.targets.append((r, c))