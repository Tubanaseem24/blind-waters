"""CSP ship placer for Blind Waters
"""
import random


# 3-ship game. Change the lengths here if your team uses different ones.
STANDARD_FLEET = [3, 3, 2]


class Placer:
    def __init__(self, board_size=10, fleet_spec=None):
        self.board_size = board_size
        self.fleet_spec = list(fleet_spec or STANDARD_FLEET)

    # ---- domain: every possible position of one ship ----
    def domain(self, length):
        """All (cells) lists for a ship of this length, ignoring other ships."""
        n = self.board_size
        options = []
        for r in range(n):
            for c in range(n):
                if c + length <= n:                       # horizontal
                    options.append([(r, c + i) for i in range(length)])
                if r + length <= n and length > 1:        # vertical
                    options.append([(r + i, c) for i in range(length)])
        return options

    def is_consistent(self, cells, placed):
        """True if `cells` is inside the board and overlaps no placed ship."""
        n = self.board_size
        taken = {cell for ship in placed for cell in ship}
        for r, c in cells:
            if not (0 <= r < n and 0 <= c < n):
                return False
            if (r, c) in taken:
                return False
        return True

    def select_variable_mrv(self, unplaced, placed):
        best_index = None
        best_count = None
        for i in unplaced:
            count = 0
            for cells in self.domain(self.fleet_spec[i]):
                if self.is_consistent(cells, placed):
                    count += 1
            if best_count is None or count < best_count:
                best_index = i
                best_count = count
        return best_index

    def solve(self, assignment, unplaced, rng, forbidden=frozenset()):
        if not unplaced:
            return assignment

        placed = list(assignment.values())
        i = self.select_variable_mrv(unplaced, placed)

        options = []
        for cells in self.domain(self.fleet_spec[i]):
            if self.is_consistent(cells, placed):
                options.append(cells)
        rng.shuffle(options)

        for cells in options:
            assignment[i] = cells
            result = self.solve(assignment, unplaced - {i}, rng)
            if result is not None:
                return result
            del assignment[i]
        return None

    def random_layout(self, seed):
        """Same seed -> same layout. Returns list of ships (list of cells)."""
        rng = random.Random(seed)
        result = self.solve({}, set(range(len(self.fleet_spec))), rng)
        if result is None:
            raise ValueError("No valid layout for this board/fleet")
        return [result[i] for i in range(len(self.fleet_spec))]