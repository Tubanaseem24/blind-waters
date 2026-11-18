from placer import Placer

def valid(layout, p):
    cells = [c for s in layout for c in s]
    return (len(cells) == len(set(cells))
            and all(0 <= r < p.board_size and 0 <= c < p.board_size for r, c in cells)
            and sorted(len(s) for s in layout) == sorted(p.fleet_spec))

def test_100_seeds_valid():
    p = Placer()
    for seed in range(100):
        assert valid(p.random_layout(seed), p)

def test_same_seed_same_layout():
    p = Placer()
    assert p.random_layout(7) == p.random_layout(7)

def test_rejects_overlap():
    p = Placer()
    assert not p.is_consistent([(0, 0), (0, 1)], placed=[[(0, 1), (0, 2)]])

def test_rejects_out_of_bounds():
    p = Placer()
    assert not p.is_consistent([(0, 9), (0, 10)], placed=[])

def test_small_board_works():
    p = Placer(board_size=6)
    assert valid(p.random_layout(1), p)

def test_game_uses_exactly_3_ships():
    p = Placer()
    layout = p.random_layout(0)
    assert len(layout) == 3