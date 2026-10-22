"""CSP fleet placer: backtracking with MRV, seeded for reproducibility."""


class Placer:
    def __init__(self, board_size: int = 10, fleet_spec=((5, "Carrier"), (4, "Battleship"), (3, "Cruiser"), (3, "Submarine"), (2, "Destroyer"))):
        self.board_size = board_size
        self.fleet_spec = fleet_spec

    def solve(self, assignment=None):
        raise NotImplementedError

    def select_variable_mrv(self, unassigned):
        raise NotImplementedError

    def is_consistent(self, assignment) -> bool:
        raise NotImplementedError

    def random_layout(self, seed: int):
        raise NotImplementedError
