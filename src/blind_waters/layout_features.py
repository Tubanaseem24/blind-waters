"""Lab 11 (Regression and Unsupervised Learning) data: one row per SHIP LAYOUT.

"""
from blind_waters.agents import HuntTargetAgent
from blind_waters.placer import Placer
from blind_waters.simulate import play_game

LAYOUT_FEATURES = ["n_horizontal", "mean_dist_edge", "min_dist_edge", "center_row",
                   "center_col", "spread", "ships_touching", "edge_cells"]


def _touching(a, b):
    return any(abs(r1 - r2) + abs(c1 - c2) == 1 for r1, c1 in a for r2, c2 in b)


def layout_features(layout, board_size=10):
    n = board_size
    cells = [cell for ship in layout for cell in ship]
    dist = [min(r, c, n - 1 - r, n - 1 - c) for r, c in cells]
    center_r = sum(r for r, _ in cells) / len(cells)
    center_c = sum(c for _, c in cells) / len(cells)
    spread = sum(((r - center_r) ** 2 + (c - center_c) ** 2) ** 0.5 for r, c in cells) / len(cells)
    return {
        "n_horizontal": sum(1 for s in layout if len(s) > 1 and s[0][0] == s[1][0]),
        "mean_dist_edge": sum(dist) / len(dist),
        "min_dist_edge": min(dist),
        "center_row": center_r,
        "center_col": center_c,
        "spread": spread,
        "ships_touching": sum(_touching(layout[i], layout[j])
                              for i in range(len(layout)) for j in range(i + 1, len(layout))),
        "edge_cells": sum(1 for d in dist if d == 0),
    }


def build_layout_dataset(layouts=1000, board_size=10, n_games=60, first_seed=0,
                         agent_class=HuntTargetAgent):
    """Rows of layout features plus `avg_shots` and the layout `seed`."""
    placer = Placer(board_size=board_size)
    rows = []
    for seed in range(first_seed, first_seed + layouts):
        layout = placer.random_layout(seed)
        shots = [play_game(agent_class(board_size, seed=10_000 + g), layout, board_size)
                 for g in range(n_games)]
        row = layout_features(layout, board_size)
        row.update(seed=seed, avg_shots=sum(shots) / len(shots))
        rows.append(row)
    return rows