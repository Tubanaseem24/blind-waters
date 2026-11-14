"""Board: owns the grid of cells, places ships, and resolves shots."""
from blind_waters.cell import Cell, HIT, MISS, UNKNOWN
from blind_waters.ship import Ship

HORIZONTAL = "H"
VERTICAL = "V"


class Board:
    def __init__(self, size=10):
        self.size = size
        self.grid = [[Cell(r, c) for c in range(size)] for r in range(size)]
        self.ships = []
        self.occupied = {}  # (row, col) -> Ship covering that square

    def in_bounds(self, row, col):
        return 0 <= row < self.size and 0 <= col < self.size

    def ship_coords(self, length, start, orientation):
        row, col = start
        if orientation == HORIZONTAL:
            return [(row, col + i) for i in range(length)]
        if orientation == VERTICAL:
            return [(row + i, col) for i in range(length)]
        raise ValueError(f"orientation must be H or V, got {orientation!r}")

    def can_place(self, length, start, orientation):
        for row, col in self.ship_coords(length, start, orientation):
            if not self.in_bounds(row, col):
                return False
            if (row, col) in self.occupied:
                return False
        return True

    def place_ship(self, ship, start, orientation):
        if not self.can_place(ship.length, start, orientation):
            raise ValueError(f"cannot place {ship.name} at {start} ({orientation})")
        coords = self.ship_coords(ship.length, start, orientation)
        ship.place([self.grid[r][c] for r, c in coords])
        for coord in coords:
            self.occupied[coord] = ship
        self.ships.append(ship)

    def receive_shot(self, row, col):
        if not self.in_bounds(row, col):
            raise ValueError(f"({row}, {col}) is off the board")
        cell = self.grid[row][col]
        if cell.state != UNKNOWN:
            raise ValueError(f"({row}, {col}) was already fired at")
        ship = self.occupied.get((row, col))
        if ship is None:
            cell.mark(MISS)
            return {"result": MISS, "ship_sunk": None}
        cell.mark(HIT)
        ship.register_hit(cell)
        sunk_name = ship.name if ship.is_sunk() else None
        return {"result": HIT, "ship_sunk": sunk_name}

    def all_sunk(self):
        return all(ship.is_sunk() for ship in self.ships)
