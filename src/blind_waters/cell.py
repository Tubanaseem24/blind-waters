"""Cell states for the Blind Waters board."""

UNKNOWN = "unknown"
HIT = "hit"
MISS = "miss"


class Cell:
    def __init__(self, row: int, col: int):
        self.row = row
        self.col = col
        self.state = UNKNOWN

    def is_unknown(self) -> bool:
        return self.state == UNKNOWN

    def mark(self, result: str) -> None:
        if result not in (HIT, MISS):
            raise ValueError(f"invalid result: {result}")
        self.state = result
