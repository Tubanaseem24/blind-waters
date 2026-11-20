"""Layout counting: the belief model behind the ProbabilityAgent.

A *layout* is one complete legal fleet placement (no overlap, inside the board).
A layout is *consistent* with the shots so far if:
  - every cell already fired at and marked "miss" is NOT covered by any ship, and
  - every cell already fired at and marked "hit" (or "sunk") IS covered by a ship.

count_layouts() enumerates every consistent layout exactly and reports, for each
cell, how many consistent layouts cover it. More layouts covering a cell means a
higher chance of a hit there. Exact enumeration is only practical on small boards;
on 10x10 with the full fleet the ProbabilityAgent samples layouts instead.

Ships are treated as distinct (the two 3-length ships are different ships), so
swapping them gives a different layout. This does not change which cell is best.
"""
from collections import namedtuple

FLEET_LENGTHS = (5, 4, 3, 3, 2)

LayoutCounts = namedtuple("LayoutCounts", ["total", "cells"])
# total: number of consistent layouts
# cells: size x size list of ints, cells[r][c] = layouts covering (r, c)


def placements(size, length):
    """Every position of one ship of `length`, as a frozenset of (row, col)."""
    found = []
    for r in range(size):
        for c in range(size):
            if c + length <= size:                      # horizontal
                found.append(frozenset((r, c + i) for i in range(length)))
            if length > 1 and r + length <= size:       # vertical
                found.append(frozenset((r + i, c) for i in range(length)))
    return found


def count_layouts(size, fleet=FLEET_LENGTHS, hits=(), misses=()):
    """Count consistent layouts and how many cover each cell.

    hits / misses are iterables of (row, col). Returns LayoutCounts.
    If no layout fits the evidence, total is 0 and every cell count is 0.
    """
    hits = frozenset(tuple(h) for h in hits)
    misses = frozenset(tuple(m) for m in misses)
    if hits & misses:
        raise ValueError("a cell cannot be both a hit and a miss")

    # A ship can never sit on a miss, so drop those positions up front.
    ships = []
    for n in fleet:
        opts = [p for p in placements(size, n) if not (p & misses)]
        ships.append((n, opts))
    ships.sort(key=lambda s: len(s[1]))  # fewest options first (fails fast); counts unaffected
    options = [opts for _, opts in ships]

    # remaining[i] = total cells that ships i.. can still cover (used to prune)
    remaining = [0] * (len(ships) + 1)
    for i in range(len(ships) - 1, -1, -1):
        remaining[i] = remaining[i + 1] + ships[i][0]

    cells = [[0] * size for _ in range(size)]
    total = 0
    chosen = []

    def recurse(i, used, uncovered):
        nonlocal total
        if len(uncovered) > remaining[i]:      # not enough ship left to explain the hits
            return
        if i == len(options):
            total += 1
            for p in chosen:
                for r, c in p:
                    cells[r][c] += 1
            return
        for p in options[i]:
            if p & used:
                continue
            chosen.append(p)
            recurse(i + 1, used | p, uncovered - p)
            chosen.pop()

    if all(options):
        recurse(0, frozenset(), hits)
    return LayoutCounts(total, cells)


def cell_probabilities(counts):
    """Turn LayoutCounts into per-cell hit probabilities (all 0.0 if no layout fits)."""
    if counts.total == 0:
        return [[0.0 for _ in row] for row in counts.cells]
    return [[v / counts.total for v in row] for row in counts.cells]


def view_to_shots(view):
    """Split a board view (as game.target_view returns) into (hits, misses).

    "hit" and "sunk" cells are hits; "miss" cells are misses; "unknown" is ignored.
    """
    hits, misses = [], []
    for r, row in enumerate(view):
        for c, state in enumerate(row):
            if state in ("hit", "sunk"):
                hits.append((r, c))
            elif state == "miss":
                misses.append((r, c))
    return hits, misses
