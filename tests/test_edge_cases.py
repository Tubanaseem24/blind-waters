import pytest
from placer import Placer
from agents import RandomAgent, HuntTargetAgent
from simulate import play_game

AGENTS = [RandomAgent, HuntTargetAgent]


def empty_state(n=10):
    return [["unknown"] * n for _ in range(n)]


@pytest.mark.parametrize("cls", AGENTS)
def test_last_unknown_cell_is_chosen(cls):
    state = [["miss"] * 10 for _ in range(10)]
    state[4][4] = "unknown"
    assert cls(10, seed=0).choose_shot(state) == (4, 4)


@pytest.mark.parametrize("cls", AGENTS)
def test_full_board_gives_clear_error(cls):
    state = [["miss"] * 10 for _ in range(10)]
    with pytest.raises(ValueError):
        cls(10, seed=0).choose_shot(state)


@pytest.mark.parametrize("corner,count", [((0, 0), 2), ((9, 9), 2), ((0, 9), 2), ((9, 0), 2), ((0, 5), 3)])
def test_hit_on_edge_adds_only_cells_on_board(corner, count):
    agent = HuntTargetAgent(10, seed=0)
    agent.observe({"cell": corner, "hit": True, "sunk": False})
    assert len(agent.targets) == count
    assert all(0 <= r < 10 and 0 <= c < 10 for r, c in agent.targets)


def test_miss_adds_no_targets():
    agent = HuntTargetAgent(10, seed=0)
    agent.observe({"cell": (3, 3), "hit": False, "sunk": False})
    assert agent.targets == []


def test_sunk_clears_targets():
    agent = HuntTargetAgent(10, seed=0)
    agent.observe({"cell": (3, 3), "hit": True, "sunk": False})
    agent.observe({"cell": (3, 4), "hit": True, "sunk": True})
    assert agent.targets == []


def test_reset_clears_old_targets():
    agent = HuntTargetAgent(10, seed=0)
    agent.observe({"cell": (3, 3), "hit": True, "sunk": False})
    agent.reset()
    assert agent.targets == []


def test_skips_neighbour_that_was_already_fired():
    agent = HuntTargetAgent(10, seed=0)
    state = empty_state()
    state[5][5] = "hit"
    for cell in [(4, 5), (6, 5), (5, 4)]:
        state[cell[0]][cell[1]] = "miss"
    agent.observe({"cell": (5, 5), "hit": True, "sunk": False})
    assert agent.choose_shot(state) == (5, 6)


@pytest.mark.parametrize("cls", AGENTS)
def test_same_agent_object_repeats_same_game_after_reset(cls):
    layout = Placer().random_layout(2)
    agent = cls(10, seed=2)
    assert play_game(agent, layout) == play_game(agent, layout)


@pytest.mark.parametrize("cls", AGENTS)
@pytest.mark.parametrize("size", [6, 8, 10])
def test_other_board_sizes_finish(cls, size):
    p = Placer(board_size=size)
    for seed in range(20):
        shots = play_game(cls(size, seed=seed), p.random_layout(seed), size)
        assert 1 <= shots <= size * size


@pytest.mark.parametrize("cls", AGENTS)
def test_game_needs_at_least_as_many_shots_as_ship_cells(cls):
    p = Placer()
    for seed in range(20):
        assert play_game(cls(10, seed=seed), p.random_layout(seed)) >= sum(p.fleet_spec)