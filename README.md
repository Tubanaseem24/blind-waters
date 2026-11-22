# Blind Waters

A Battleship-style game where a human player and an AI agent each place a hidden fleet on a 10x10 grid and take turns firing at each other's ships. The repository contains the Python game engine and a browser-based tactical interface.

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
  web/
    index.html       Browser game interface
    style.css        Naval tactical UI styles
    game.js          Browser interaction and API calls
  src/blind_waters/
    cell.py          Cell states: unknown, hit, miss
    ship.py          Ship with length, cells, hits
    board.py         Board: placement rules, receiving shots
    placer.py        CSP placer with backtracking and MRV
    agents.py        Agent base class, Random, HuntTarget, Probability
    game.py          Turn loop, human vs agent
    web_api.py       FastAPI adapter for the browser game
    evaluator.py     Seeded experiments and charts
  tests/             Unit tests per module
  data/              seeds.csv (fixed seeds for all experiments)
  experiments/       Scripts that produce the report charts
```

## Setup

Create and activate a virtual environment, then install dependencies:

```bash
python -m venv .venv
# Windows PowerShell:
.venv\\Scripts\\Activate.ps1
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

## Run the browser game

From the repository root, start the FastAPI server:

```bash
uvicorn blind_waters.web_api:app --app-dir src --reload
```

Open **http://127.0.0.1:8000** in your browser. The frontend is served by FastAPI, so the browser and Python game engine communicate through the same local server.

The current web opponent is the existing `RandomShooter` baseline. The `HuntTargetAgent` and `ProbabilityAgent` classes in `agents.py` are still placeholders; the interface labels this accurately and does not display fabricated probability predictions.

## Run the Python game

```bash
python -m blind_waters.game
```

## Test

```bash
pytest
```

## Evaluation

```bash
python -m blind_waters.evaluator --seeds data/seeds.csv
```

Every agent is evaluated on the same seeded boards (seeds 0 to 999).

## Contributing

Commit under your own GitHub account with clear messages, for example `placer: add MRV variable selection`. Commit history is part of the contribution record in the final report.
