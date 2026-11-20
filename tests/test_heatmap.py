"""Tests for heatmap.py. Run: pytest tests/test_heatmap.py"""
import json

import pytest

from blind_waters.heatmap import heatmap_data


def empty_view(size=10):
    return [["unknown"] * size for _ in range(size)]


def test_json_ready_and_expected_keys():
    data = heatmap_data(empty_view())
    json.dumps(data)                                    # must not raise
    assert set(data) == {"size", "probabilities", "max", "best_cell", "layouts"}
    assert data["size"] == 10
    assert len(data["probabilities"]) == 10
    assert all(len(row) == 10 for row in data["probabilities"])


def test_empty_board_probabilities_add_up_to_ship_cells():
    data = heatmap_data(empty_view())
    assert sum(map(sum, data["probabilities"])) == pytest.approx(8, abs=0.01)   # 3 + 3 + 2


def test_centre_is_hotter_than_corner_on_empty_board():
    grid = heatmap_data(empty_view())["probabilities"]
    assert grid[4][4] > grid[0][0] > 0


def test_cells_already_fired_are_zero():
    view = empty_view()
    view[0][0], view[1][1], view[2][2] = "miss", "hit", "sunk"
    grid = heatmap_data(view)["probabilities"]
    assert grid[0][0] == grid[1][1] == grid[2][2] == 0.0


def test_after_a_hit_the_hottest_cell_is_next_to_it():
    view = empty_view()
    view[4][4] = "hit"
    data = heatmap_data(view)
    r, c = data["best_cell"]
    assert abs(r - 4) + abs(c - 4) == 1
    assert data["probabilities"][r][c] == data["max"]


def test_max_matches_grid():
    data = heatmap_data(empty_view())
    assert data["max"] == max(max(row) for row in data["probabilities"])


def test_all_ships_sunk_gives_empty_heatmap():
    view = empty_view()
    for r, c in [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)]:
        view[r][c] = "sunk"
    data = heatmap_data(view)
    assert data["max"] == 0.0 and data["best_cell"] is None
    assert sum(map(sum, data["probabilities"])) == 0


def test_contradictory_view_does_not_crash():
    view = empty_view(3)
    view[0][0] = view[2][2] = "hit"       # one 2-ship cannot cover two far-apart hits
    data = heatmap_data(view, fleet=(2,))
    assert data["layouts"] == 0 and data["best_cell"] is None


def test_works_on_a_small_board():
    data = heatmap_data(empty_view(6))
    assert data["size"] == 6 and data["layouts"] > 0
