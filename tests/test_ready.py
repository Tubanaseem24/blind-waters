from blind_waters.placer import Placer

def test_full_layout_is_complete():
    p = Placer()
    assert p.is_fleet_complete(p.random_layout(0))

def test_missing_ship_is_not_complete():
    p = Placer()
    assert not p.is_fleet_complete(p.random_layout(0)[:2])

def test_empty_layout_is_not_complete():
    assert not Placer().is_fleet_complete([])

def test_overlapping_ships_not_complete():
    p = Placer()
    layout = [[(0, 0), (0, 1), (0, 2)], [(0, 0), (1, 0), (2, 0)], [(5, 5), (5, 6)]]
    assert not p.is_fleet_complete(layout)

def test_wrong_ship_length_not_complete():
    p = Placer()
    layout = [[(0, 0), (0, 1)], [(2, 0), (2, 1), (2, 2)], [(5, 5), (5, 6)]]
    assert not p.is_fleet_complete(layout)
