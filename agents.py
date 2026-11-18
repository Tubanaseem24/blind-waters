"""Random and Hunt-and-Target agents for Blind Waters.
"""
import random


class Agent:
    def __init__(self, board_size=10, seed=None):
        self.board_size = board_size
        self.seed = seed
        self.reset()

    def reset(self):
        self.rng = random.Random(self.seed)

    def unknown_cells(self, state):
        """ all cells that have not been fired"""
        n = self.board_size
        return [(r, c) for r in range(n) for c in range(n)
                if state[r][c] == "unknown"]

    def choose_shot(self, state):
        raise NotImplementedError

    def observe(self, result):
        pass


class RandomAgent(Agent):
    """ fire at a random cell."""

    def choose_shot(self, state):
        return self.rng.choice(self.unknown_cells(state))


class HuntTargetAgent(Agent):
    """HUNT: fire randomly, target: after a hit try the 4 neighbours."""

    def reset(self):
        super().reset()
        self.targets = []          

    def neighbours(self, cell):
        r, c = cell
        return [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]

    def choose_shot(self, state):
       
        while self.targets:
            cell = self.targets.pop()
            if state[cell[0]][cell[1]] == "unknown":
                return cell
       
        return self.rng.choice(self.unknown_cells(state))

    def observe(self, result):
        if result["sunk"]:
            self.targets = []      # ship finished, go back to hunting
            return
        if result["hit"]:
            for r, c in self.neighbours(result["cell"]):
                if 0 <= r < self.board_size and 0 <= c < self.board_size:
                    self.targets.append((r, c))