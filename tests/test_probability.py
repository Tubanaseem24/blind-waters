"""Tests for probability.py. Run: pytest tests/test_probability.py"""
import random

import pytest

from blind_waters.layouts import count_layouts
from blind_waters.probability import (
    DEFAULT_FLEET, ProbabilityAgent, belief, count_layouts_fast,
    read_view, remaining_fleet,
)

FLEET = DEFAULT_FLEET


# ---------- helpers: a tiny self-contained game so these tests need no teammate code ----------
def random_layout(size, fleet, rng):
    while True:
        taken, layout = set(), []
        for n in fleet:
            for _ in range(200):
                horizontal = rng.random() < 0.5
                r = rng.randrange(size if horizontal else size - n + 1)
                c = rng.randrange(size - n + 1 if horizontal else size)
                cells = [(r, c + i) if horizontal else (r + i, c) for i in range(n)]
                if not taken & set(cells):
                    taken |= set(cells)
                    layout.append(cells)
                    break
            else:
                break
        else:
            return layout


def play(agent, layout, size=10):
    """Agent fires until every ship is sunk. Returns shot count. Fails on a repeat shot."""
    view = [["unknown"] * size for _ in range(size)]
    ship_of = {cell: i for i, ship in enumerate(layout) for cell in ship}
    left = [len(s) for s in layout]
    shots = 0
    while sum(left):
        r, c = agent.choose_shot(view)
        assert view[r][c] == "unknown", "agent fired at a cell twice"
        shots += 1
        if (r, c) in ship_of:
            i = ship_of[(r, c)]
            left[i] -= 1
            view[r][c] = "hit"
            if left[i] == 0:
                for cell in layout[i]:
                    view[cell[0]][cell[1]] = "sunk"
        else:
            view[r][c] = "miss"
    return shots


# ---------- the fast counter must equal the slow exact counter ----------
@pytest.mark.parametrize("seed", range(10))
def test_fast_matches_exact(seed):
    rng = random.Random(seed)
    size = 6
    cells = [(r, c) for r in range(size) for c in range(size)]
    shots = rng.sample(cells, rng.randint(0, 6))
    hits, misses = shots[: len(shots) // 2], shots[len(shots) // 2:]
    slow = count_layouts(size, FLEET, hits, misses)
    fast = count_layouts_fast(size, FLEET, hits, misses)
    assert fast.total == slow.total
    assert fast.cells == slow.cells


@pytest.mark.parametrize("fleet", [(2,), (3, 2), (2, 2, 2), ()])
def test_fast_handles_smaller_fleets(fleet):
    slow = count_layouts(5, fleet, [(2, 2)] if fleet else [], [(0, 0)])
    fast = count_layouts_fast(5, fleet, [(2, 2)] if fleet else [], [(0, 0)])
    assert (fast.total, fast.cells) == (slow.total, slow.cells)


def test_fast_known_total_8x8():
    assert count_layouts_fast(8, FLEET).total == 773368   # value from exact enumeration


def test_fast_rejects_too_many_ships():
    with pytest.raises(ValueError):
        count_layouts_fast(10, (5, 4, 3, 3, 2))


def test_fast_rejects_hit_and_miss_same_cell():
    with pytest.raises(ValueError):
        count_layouts_fast(5, FLEET, hits=[(1, 1)], misses=[(1, 1)])


def test_fast_impossible_evidence_gives_zero():
    assert count_layouts_fast(3, (2,), hits=[(0, 0), (2, 2)]).total == 0


# ---------- reading the view ----------
def test_read_view():
    view = [["unknown", "hit", "miss"], ["sunk", "sunk", "unknown"], ["unknown"] * 3]
    hits, misses, sunk = read_view(view)
    assert hits == [(0, 1)] and misses == [(0, 2)] and sorted(sunk) == [(1, 0), (1, 1)]


def test_remaining_fleet():
    assert remaining_fleet([], FLEET) == (3, 3, 2)
    assert remaining_fleet([(0, 0), (0, 1)], FLEET) == (3, 3)                       # destroyer sunk
    assert remaining_fleet([(0, 0), (0, 1), (0, 2)], FLEET) == (3, 2)              # a 3-ship sunk
    adjacent = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1)]                             # 3-ship + destroyer side by side
    assert remaining_fleet(adjacent, FLEET) == (3,)


# ---------- agent behaviour ----------
def test_after_one_hit_agent_fires_next_to_it():
    view = [["unknown"] * 10 for _ in range(10)]
    view[4][4] = "hit"
    r, c = ProbabilityAgent(seed=1).choose_shot(view)
    assert abs(r - 4) + abs(c - 4) == 1


def test_agent_finishes_line_after_two_hits():
    view = [["unknown"] * 10 for _ in range(10)]
    view[4][4] = view[4][5] = "hit"
    r, c = ProbabilityAgent(seed=1).choose_shot(view)
    assert (r, c) in [(4, 3), (4, 6)]


def test_agent_ignores_sunk_ship_neighbours_less_than_open_water():
    # a sunk destroyer alone: the two remaining 3-ships should not make its neighbours special
    view = [["unknown"] * 10 for _ in range(10)]
    view[0][0] = view[0][1] = "sunk"
    probs = ProbabilityAgent(seed=1).cell_probabilities(view)
    assert probs[0][0] == 0.0 and probs[0][1] == 0.0       # already fired
    assert probs[5][5] > probs[0][2]                        # centre beats the cell beside the sunk ship


def test_heatmap_probabilities_sum_to_afloat_ship_cells():
    view = [["unknown"] * 10 for _ in range(10)]
    view[0][0] = "miss"
    probs = ProbabilityAgent().cell_probabilities(view)
    assert sum(map(sum, probs)) == pytest.approx(8)         # 3 + 3 + 2 ship cells


def test_same_seed_same_shot():
    view = [["unknown"] * 10 for _ in range(10)]
    assert ProbabilityAgent(seed=5).choose_shot(view) == ProbabilityAgent(seed=5).choose_shot(view)


def test_choose_shot_raises_when_board_full():
    with pytest.raises(ValueError):
        ProbabilityAgent().choose_shot([["miss"] * 3 for _ in range(3)])


def test_observe_accepts_either_call_style():
    agent = ProbabilityAgent()
    agent.observe(1, 2, "hit")
    agent.observe({"cell": (1, 2), "hit": True, "sunk": False})
    agent.observe((1, 2), "hit")


def test_full_games_finish_without_repeat_shots():
    for seed in range(10):
        layout = random_layout(10, FLEET, random.Random(seed))
        shots = play(ProbabilityAgent(seed=seed), layout)
        assert 8 <= shots <= 100


def test_beats_random_shooting():
    class RandomShooter:
        def __init__(self, seed):
            self.rng = random.Random(seed)

        def choose_shot(self, view):
            return self.rng.choice([(r, c) for r, row in enumerate(view)
                                    for c, s in enumerate(row) if s == "unknown"])

    prob = rand = 0
    for seed in range(12):
        layout = random_layout(10, FLEET, random.Random(seed))
        prob += play(ProbabilityAgent(seed=seed), layout)
        rand += play(RandomShooter(seed), layout)
    assert prob < rand * 0.75
