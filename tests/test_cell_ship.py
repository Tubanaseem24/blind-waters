from blind_waters.cell import Cell, HIT, MISS
from blind_waters.ship import Ship


def test_cell_starts_unknown_and_marks():
    c = Cell(0, 0)
    assert c.is_unknown()
    c.mark(HIT)
    assert not c.is_unknown()


def test_ship_sinks_when_all_cells_hit():
    s = Ship("Destroyer", 2)
    a, b = Cell(0, 0), Cell(0, 1)
    s.place([a, b])
    s.register_hit(a)
    assert not s.is_sunk()
    s.register_hit(b)
    assert s.is_sunk()
