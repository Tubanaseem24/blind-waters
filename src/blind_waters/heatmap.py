"""Heatmap data for the web page (Day 3).

heatmap_data(view) turns the AI's belief into plain numbers the browser can draw.
It only ever reads `view` (shots fired and sunk ships, as game.target_view
returns), so it can never leak where the live ships are.
"""
from blind_waters.probability import DEFAULT_FLEET, belief

PRECISION = 4   # decimal places kept in the JSON


def heatmap_data(view, fleet=DEFAULT_FLEET):
    """Return a JSON-ready dict describing how likely each cell is to hold a ship.

    {
      "size": 10,
      "probabilities": [[0.0412, ...], ...],   # size x size; 0.0 for cells already fired at
      "max": 0.2731,                            # highest probability (use it to scale colours)
      "best_cell": [4, 5] or None,              # where the agent would fire first
      "layouts": 3848040,                       # how many layouts fit what is known
    }
    """
    counts = belief(view, tuple(fleet))
    size = len(view)
    grid, best, best_cell = [], 0.0, None
    for r, row in enumerate(view):
        out = []
        for c, state in enumerate(row):
            p = counts.cells[r][c] / counts.total if counts.total and state == "unknown" else 0.0
            if p > best:
                best, best_cell = p, [r, c]
            out.append(round(p, PRECISION))
        grid.append(out)
    return {
        "size": size,
        "probabilities": grid,
        "max": round(best, PRECISION),
        "best_cell": best_cell,
        "layouts": counts.total,
    }
