
from placer import Placer
from agents import RandomAgent, HuntTargetAgent


def play_game(agent, layout, board_size=10):
    """Agent fires until all ships are sunk. Returns number of shots."""
    state = [["unknown"] * board_size for _ in range(board_size)]
    ship_of = {cell: i for i, ship in enumerate(layout) for cell in ship}
    hits_left = [len(ship) for ship in layout]
    agent.reset()
    shots = 0
    while sum(hits_left) > 0:
        r, c = agent.choose_shot(state)
        assert state[r][c] == "unknown", "agent fired at the same cell twice"
        shots += 1
        if (r, c) in ship_of:
            state[r][c] = "hit"
            i = ship_of[(r, c)]
            hits_left[i] -= 1
            agent.observe({"cell": (r, c), "hit": True, "sunk": hits_left[i] == 0})
        else:
            state[r][c] = "miss"
            agent.observe({"cell": (r, c), "hit": False, "sunk": False})
    return shots


def average_shots(agent_class, games=100, board_size=10):
    placer = Placer(board_size=board_size)
    total = 0
    for seed in range(games):
        layout = placer.random_layout(seed)
        total += play_game(agent_class(board_size, seed=seed), layout, board_size)
    return total / games


if __name__ == "__main__":
    for cls in (RandomAgent, HuntTargetAgent):
        print(cls.__name__, "average shots over 100 games:", average_shots(cls))