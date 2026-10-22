# Blind Waters

A Battleship-style game where a human player and an AI agent each place a hidden fleet on a 10x10 grid and take turns firing at each other's ships. The AI maintains a belief about where the human's ships are, using constraint satisfaction, probability, and heuristic search.

Course: AL-2002 Artificial Intelligence Lab, Fall 2026, FAST-NUCES Karachi

## Team

| Member | Roll No. | Role |
|---|---|---|
| Tuba Naseem (Leader) | 24K-3063 | Game engine, interface, integration |
| Anzeela Shafi | 24K-3082 | CSP placement, hunt-and-target agent |
| Aiza Humayun | 24K-3116 | Probability agent, evaluation harness |

## Project structure

```
blind-waters/
  docs/            Project proposal (PDF, Markdown, Word)
  src/blind_waters/
    cell.py        Cell states: unknown, hit, miss
    ship.py        Ship with length, cells, hits
    board.py       Board: placement rules, receiving shots
    placer.py      CSP placer with backtracking and MRV
    agents.py      Agent base class, Random, HuntTarget, Probability
    game.py        Turn loop, human vs agent
    evaluator.py   Seeded experiments and charts
  tests/           Unit tests per module
  data/            seeds.csv (fixed seeds for all experiments)
  experiments/     Scripts that produce the report charts
```

## Setup

```
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```
python -m blind_waters.game
```

## Test

```
pytest
```

## Evaluation

```
python -m blind_waters.evaluator --seeds data/seeds.csv
```

Every agent is evaluated on the same seeded boards (seeds 0 to 999).

## Contributing

Commit under your own GitHub account with clear messages, for example `placer: add MRV variable selection`. Commit history is part of the contribution record in the final report.
