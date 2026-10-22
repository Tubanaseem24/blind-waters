"""10x10 board with placement rules and shot handling."""


class Board:
    def __init__(self, size: int = 10):
        self.size = size
        self.ships = []

    def can_place(self, ship, start, orientation) -> bool:
        raise NotImplementedError

    def place_ship(self, ship, start, orientation) -> None:
        raise NotImplementedError

    def receive_shot(self, cell):
        raise NotImplementedError

    def all_sunk(self) -> bool:
        return all(s.is_sunk() for s in self.ships)
