"""Lab 10 (Supervised Learning)
"""
import random

from blind_waters.agents import HuntTargetAgent
from blind_waters.placer import Placer
from blind_waters.probability import ProbabilityAgent

FEATURES = ["row", "col", "dist_edge", "adj_hit", "adj_miss", "adj_sunk",
            "adj_unknown", "hits_on_board", "shots_so_far", "line_hits"]


def _features(state, r, c, shots_so_far, hits_on_board):
    n = len(state)
    adj = [state[a][b] for a, b in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
           if 0 <= a < n and 0 <= b < n]
    line_hits = sum(
        1 for d in (-2, -1, 1, 2)
        for a, b in ((r + d, c), (r, c + d))
        if 0 <= a < n and 0 <= b < n and state[a][b] == "hit")
    return [r, c, min(r, c, n - 1 - r, n - 1 - c), adj.count("hit"), adj.count("miss"),
            adj.count("sunk"), adj.count("unknown"), hits_on_board, shots_so_far, line_hits]


def build_dataset(games=200, board_size=10, first_seed=0, cells_per_turn=5, sample_seed=0):
    """Return a list of dict rows (game + FEATURES + label + prob_exact)."""
    n = board_size
    placer = Placer(board_size=n)
    teacher = ProbabilityAgent(n)
    rng = random.Random(sample_seed)
    rows = []
    for seed in range(first_seed, first_seed + games):
        layout = placer.random_layout(seed)
        ship_cells = {cell for ship in layout for cell in ship}
        ship_of = {cell: i for i, ship in enumerate(layout) for cell in ship}
        hits_left = [len(s) for s in layout]
        state = [["unknown"] * n for _ in range(n)]
        agent = HuntTargetAgent(n, seed=seed)
        agent.reset()
        shots = 0
        while sum(hits_left) > 0:
            unknown = [(r, c) for r in range(n) for c in range(n) if state[r][c] == "unknown"]
            hits_on_board = sum(row.count("hit") for row in state)
            exact = teacher.cell_probabilities(state)
            for r, c in rng.sample(unknown, min(cells_per_turn, len(unknown))):
                row = dict(zip(FEATURES, _features(state, r, c, shots, hits_on_board)))
                row.update(game=seed, label=int((r, c) in ship_cells), prob_exact=exact[r][c])
                rows.append(row)
            r, c = agent.choose_shot(state)            # the game moves on
            shots += 1
            hit = (r, c) in ship_of
            sunk = False
            if hit:
                state[r][c] = "hit"
                i = ship_of[(r, c)]
                hits_left[i] -= 1
                if hits_left[i] == 0:
                    sunk = True
                    for sr, sc in layout[i]:
                        state[sr][sc] = "sunk"
            else:
                state[r][c] = "miss"
            agent.observe({"cell": (r, c), "hit": hit, "sunk": sunk})
    return rows