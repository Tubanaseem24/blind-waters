"""A ship occupying a set of consecutive cells."""


class Ship:
    def __init__(self, name: str, length: int):
        self.name = name
        self.length = length
        self.cells = []
        self.hits = set()

    def place(self, cells) -> None:
        self.cells = list(cells)

    def register_hit(self, cell) -> None:
        if cell in self.cells:
            self.hits.add(cell)

    def is_sunk(self) -> bool:
        return len(self.cells) == self.length and len(self.hits) == self.length
