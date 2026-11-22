"""ProbabilityAgent: fires at the cell covered by the most consistent layouts.

Each turn the agent looks at the board view (what it knows: misses, hits, sunk
ships) and asks: "in how many complete, legal fleet layouts is each cell a ship?"
It then fires at the unknown cell with the highest count.

How the counting works (exact, no guessing):
  * A layout is consistent if no ship sits on a miss or on a sunk ship, and every
    hit cell (a hit on a ship that is not yet sunk) is covered by some ship.
  * Sunk ships are removed from the fleet, so the agent stops hunting near them.
  * For a fleet of up to 3 ships the count uses matrix multiplication over all
    ship positions, which is exact and takes a few milliseconds.
  * "Every hit must be covered" is handled by inclusion-exclusion: count layouts
    that avoid each subset of the hit cells and add/subtract.

The agent keeps no memory between turns: it rebuilds its belief from the view
every time, so it does not depend on how `observe` is called.
"""
import random
from functools import lru_cache
from itertools import combinations

import numpy as np

from blind_waters.layouts import LayoutCounts, placements

DEFAULT_FLEET = (3, 3, 2)   # the team's fleet (changed from the proposal's 5 ships)
MAX_SHIPS = 3               # the fast counter handles up to 3 ships


# Fast exact counting (up to 3 ships)
@lru_cache(maxsize=None)
def _tables(size, fleet):
    """Precompute, once per board size and fleet: every position of every ship as
    a 0/1 row over the board's cells, and which pairs of positions do not overlap.
    Fleets shorter than 3 are padded with 'empty ships' that cover nothing."""
    lengths = list(fleet) + [0] * (MAX_SHIPS - len(fleet))
    masks = []
    for n in lengths:
        if n == 0:
            masks.append(np.zeros((1, size * size)))
            continue
        rows = []
        for cells in placements(size, n):
            row = np.zeros(size * size)
            for r, c in cells:
                row[r * size + c] = 1.0
            rows.append(row)
        masks.append(np.array(rows))
    disjoint = lambda a, b: ((masks[a] @ masks[b].T) == 0).astype(float)
    return masks, disjoint(0, 1), disjoint(0, 2), disjoint(1, 2)


def _count_avoiding(tables, blocked):
    """Layouts with no ship on any blocked cell -> (total, cells vector).

    Works out, for every position of every ship, how many ways the other two
    ships can complete the layout, then adds those up per cell."""
    masks, d01, d02, d12 = tables
    keep = []
    for m in masks:
        if len(blocked):
            keep.append(np.flatnonzero(m[:, blocked].sum(axis=1) == 0))
        else:
            keep.append(np.arange(len(m)))
    k0, k1, k2 = keep
    if min(len(k0), len(k1), len(k2)) == 0:
        return 0.0, np.zeros(masks[0].shape[1])

    a01 = d01[np.ix_(k0, k1)]
    a02 = d02[np.ix_(k0, k2)]
    a12 = d12[np.ix_(k1, k2)]

    third = a02 @ a12.T          # [a, b] = positions of ship 2 clear of both a and b
    ways = a01 * third           # [a, b] = complete layouts using positions a and b
    total = ways.sum()
    w0 = ways.sum(axis=1)        # layouts using position a of ship 0
    w1 = ways.sum(axis=0)        # layouts using position b of ship 1
    w2 = (a02 * (a01 @ a12)).sum(axis=0)   # layouts using position c of ship 2
    cells = masks[0][k0].T @ w0 + masks[1][k1].T @ w1 + masks[2][k2].T @ w2
    return total, cells


def count_layouts_fast(size, fleet=DEFAULT_FLEET, hits=(), misses=()):
    """Same answer as layouts.count_layouts, but fast, for fleets of up to 3 ships."""
    fleet = tuple(fleet)
    if len(fleet) > MAX_SHIPS:
        raise ValueError("count_layouts_fast supports at most 3 ships")
    hits = sorted({tuple(h) for h in hits})
    misses = {tuple(m) for m in misses}
    if set(hits) & misses:
        raise ValueError("a cell cannot be both a hit and a miss")

    tables = _tables(size, fleet)
    total = 0.0
    cells = np.zeros(size * size)
    for mask in range(1 << len(hits)):                 # inclusion-exclusion over hits
        avoided = [hits[j] for j in range(len(hits)) if mask >> j & 1]
        blocked = np.array(sorted(r * size + c for r, c in misses | set(avoided)), dtype=int)
        t, c = _count_avoiding(tables, blocked)
        sign = -1.0 if len(avoided) % 2 else 1.0
        total += sign * t
        cells += sign * c
    grid = np.rint(cells).astype(int).reshape(size, size).tolist()
    return LayoutCounts(int(round(total)), grid)


# Reading the board view
def _can_tile(cells, lengths):
    """Can these cells be split exactly into straight ships of the given lengths?"""
    if not cells:
        return not lengths
    if not lengths:
        return False
    r, c = min(cells)                  # the top-left-most cell starts a ship
    for n in set(lengths):
        for ship in ({(r, c + i) for i in range(n)}, {(r + i, c) for i in range(n)}):
            if ship <= cells:
                rest = list(lengths)
                rest.remove(n)
                if _can_tile(cells - ship, rest):
                    return True
    return False


def remaining_fleet(sunk_cells, fleet):
    """The ship lengths still afloat, given the cells of ships already sunk."""
    sunk_cells = frozenset(sunk_cells)
    if not sunk_cells:
        return tuple(fleet)
    for count in range(1, len(fleet) + 1):
        for idx in combinations(range(len(fleet)), count):
            lengths = [fleet[i] for i in idx]
            if sum(lengths) == len(sunk_cells) and _can_tile(sunk_cells, lengths):
                left = [n for i, n in enumerate(fleet) if i not in idx]
                return tuple(left)
    return tuple(fleet)                # view does not match the fleet: change nothing


def read_view(view):
    """Split a board view into (hits, misses, sunk) lists of (row, col).

    "hit" = hit on a ship that is still afloat; "sunk" = cell of a sunk ship."""
    hits, misses, sunk = [], [], []
    for r, row in enumerate(view):
        for c, state in enumerate(row):
            if state == "hit":
                hits.append((r, c))
            elif state == "miss":
                misses.append((r, c))
            elif state == "sunk":
                sunk.append((r, c))
    return hits, misses, sunk


def belief(view, fleet=DEFAULT_FLEET):
    """LayoutCounts for everything consistent with this board view."""
    hits, misses, sunk = read_view(view)
    afloat = remaining_fleet(sunk, tuple(fleet))
    # Ships still afloat cannot overlap ships already sunk, so treat those cells like misses.
    return count_layouts_fast(len(view), afloat, hits, misses + sunk)


# The agent
class ProbabilityAgent:
    """Fires at the unknown cell that appears in the most consistent layouts.

    Same interface as the other agents: choose_shot(view), observe(...), reset()."""

    def __init__(self, board_size=10, seed=None, fleet=DEFAULT_FLEET):
        self.board_size = board_size
        self.seed = seed
        self.fleet = tuple(fleet)
        self.reset()

    def reset(self):
        self.rng = random.Random(self.seed)

    def observe(self, *args, **kwargs):
        """Nothing to remember: the belief is rebuilt from the view each turn."""

    def cell_counts(self, view):
        return belief(view, self.fleet)

    def cell_probabilities(self, view):
        """Per-cell chance of a ship, 0.0 for cells already fired at (for the heatmap)."""
        counts = belief(view, self.fleet)
        grid = []
        for r, row in enumerate(view):
            grid.append([
                counts.cells[r][c] / counts.total if counts.total and state == "unknown" else 0.0
                for c, state in enumerate(row)
            ])
        return grid

    def choose_shot(self, view):
        unknown = [(r, c) for r, row in enumerate(view) for c, s in enumerate(row) if s == "unknown"]
        if not unknown:
            raise ValueError("no unknown cells left to fire at")
        counts = belief(view, self.fleet)
        best = max(counts.cells[r][c] for r, c in unknown)
        if best == 0:                       # evidence contradicts the fleet: fall back to random
            return self.rng.choice(unknown)
        return self.rng.choice([(r, c) for r, c in unknown if counts.cells[r][c] == best])
