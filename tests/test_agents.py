from placer import Placer
from agents import RandomAgent, HuntTargetAgent
from simulate import play_game, average_shots


def test_random_agent_finishes_game():
    layout = Placer().random_layout(0)
    shots = play_game(RandomAgent(10, seed=0), layout)
    assert 1 <= shots <= 100


def test_hunt_target_finishes_game():
    layout = Placer().random_layout(0)
    shots = play_game(HuntTargetAgent(10, seed=0), layout)
    assert 1 <= shots <= 100


def test_agents_never_fire_twice_on_same_cell():
    # play_game asserts this, so 50 games with no error means it is true
    p = Placer()
    for seed in range(50):
        play_game(RandomAgent(10, seed=seed), p.random_layout(seed))
        play_game(HuntTargetAgent(10, seed=seed), p.random_layout(seed))


def test_same_seed_same_shots():
    layout = Placer().random_layout(3)
    a = play_game(HuntTargetAgent(10, seed=3), layout)
    b = play_game(HuntTargetAgent(10, seed=3), layout)
    assert a == b


def test_hunt_target_targets_neighbours_after_hit():
    agent = HuntTargetAgent(10, seed=0)
    state = [["unknown"] * 10 for _ in range(10)]
    state[5][5] = "hit"
    agent.observe({"cell": (5, 5), "hit": True, "sunk": False})
    assert agent.choose_shot(state) in [(4, 5), (6, 5), (5, 4), (5, 6)]


def test_hunt_target_stays_on_board_in_corner():
    agent = HuntTargetAgent(10, seed=0)
    agent.observe({"cell": (0, 0), "hit": True, "sunk": False})
    for r, c in agent.targets:
        assert 0 <= r < 10 and 0 <= c < 10


def test_hunt_target_beats_random_on_average():
    assert average_shots(HuntTargetAgent, 100) < average_shots(RandomAgent, 100)