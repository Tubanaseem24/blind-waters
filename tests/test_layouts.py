"""Tests for layouts.py (belief model). Run: pytest tests/test_layouts.py"""
import random
import time
from itertools import product

import pytest

from blind_waters.layouts import (
    cell_probabilities, count_layouts, placements, view_to_shots,
)


def brute_force(size, fleet, hits, misses):
    """Independent check: try every combination of positions, no pruning."""
    def positions(n):
        out = []
        for r in range(size):
            for c in range(size):
                if c + n <= size:
                    out.append([(r, c + i) for i in range(n)])
                if n > 1 and r + n <= size:
                    out.append([(r + i, c) for i in range(n)])
        return out

    total, cover = 0, {}
    for combo in product(*[positions(n) for n in fleet]):
        cells = [c for ship in combo for c in ship]
        if len(cells) != len(set(cells)):
            continue
        if any(m in cells for m in misses):
            continue
        if any(h not in cells for h in hits):
            continue
        total += 1
        for c in cells:
            cover[c] = cover.get(c, 0) + 1
    return total, cover


def test_placements_count():
    assert len(placements(3, 2)) == 12      # 6 horizontal + 6 vertical
    assert len(placements(10, 5)) == 120    # 60 + 60
    assert len(placements(4, 1)) == 16      # length 1 is not double counted


def test_single_ship_3x3_known_values():
    counts = count_layouts(3, fleet=[2])
    assert counts.total == 12
    assert counts.cells[1][1] == 4          # centre
    assert counts.cells[0][0] == 2          # corner
    assert counts.cells[0][1] == 3          # edge


def test_every_layout_covers_fleet_size_cells():
    counts = count_layouts(5, fleet=[3, 2])
    assert sum(sum(row) for row in counts.cells) == counts.total * 5


def test_miss_removes_cell():
    counts = count_layouts(4, fleet=[3, 2], misses=[(1, 1)])
    assert counts.cells[1][1] == 0
    assert counts.total < count_layouts(4, fleet=[3, 2]).total


def test_hit_cell_covered_by_every_layout():
    counts = count_layouts(4, fleet=[3, 2], hits=[(1, 1)])
    assert counts.cells[1][1] == counts.total > 0


def test_hit_raises_neighbours():
    before = count_layouts(5, fleet=[3, 2])
    after = count_layouts(5, fleet=[3, 2], hits=[(2, 2)])
    assert after.cells[2][3] / after.total > before.cells[2][3] / before.total


def test_impossible_evidence_gives_zero():
    counts = count_layouts(3, fleet=[2], hits=[(0, 0), (2, 2)])
    assert counts.total == 0
    assert all(v == 0 for row in counts.cells for v in row)


def test_hit_and_miss_same_cell_rejected():
    with pytest.raises(ValueError):
        count_layouts(3, fleet=[2], hits=[(0, 0)], misses=[(0, 0)])


@pytest.mark.parametrize("seed", range(8))
def test_matches_brute_force(seed):
    rng = random.Random(seed)
    size, fleet = 4, [3, 2]
    all_cells = [(r, c) for r in range(size) for c in range(size)]
    shots = rng.sample(all_cells, rng.randint(0, 5))
    hits = shots[: len(shots) // 2]
    misses = shots[len(shots) // 2:]
    expected_total, expected_cover = brute_force(size, fleet, hits, misses)
    got = count_layouts(size, fleet, hits, misses)
    assert got.total == expected_total
    for (r, c) in all_cells:
        assert got.cells[r][c] == expected_cover.get((r, c), 0)


def test_three_ship_fleet_matches_brute_force():
    expected_total, expected_cover = brute_force(4, [2, 2, 2], [(0, 0)], [(3, 3)])
    got = count_layouts(4, [2, 2, 2], hits=[(0, 0)], misses=[(3, 3)])
    assert got.total == expected_total
    assert got.cells[0][0] == expected_cover[(0, 0)]


def test_probabilities_sum_to_fleet_size():
    probs = cell_probabilities(count_layouts(5, fleet=[3, 2]))
    assert sum(sum(row) for row in probs) == pytest.approx(5)


def test_probabilities_zero_when_no_layout():
    probs = cell_probabilities(count_layouts(3, fleet=[2], hits=[(0, 0), (2, 2)]))
    assert all(v == 0.0 for row in probs for v in row)


def test_view_to_shots():
    view = [["unknown", "hit", "miss"], ["sunk", "unknown", "unknown"], ["miss", "unknown", "unknown"]]
    hits, misses = view_to_shots(view)
    assert sorted(hits) == [(0, 1), (1, 0)]
    assert sorted(misses) == [(0, 2), (2, 0)]


def test_6x6_three_ship_game_is_fast_enough():
    start = time.time()
    counts = count_layouts(6, fleet=[3, 3, 2], hits=[(2, 2)], misses=[(0, 0), (5, 5)])
    assert counts.total > 0
    assert time.time() - start < 10
