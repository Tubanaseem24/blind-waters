"""Run seeded games for every agent and save the results
"""
import argparse
import csv
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))      # so "blind_waters" can be imported

from blind_waters.placer import Placer
from blind_waters.agents import RandomAgent, HuntTargetAgent
from blind_waters.simulate import play_game

AGENTS = [RandomAgent, HuntTargetAgent]

# Aiza's agent. If her file or class has a different name, change this line.
try:
    from blind_waters.probability import ProbabilityAgent
    AGENTS.append(ProbabilityAgent)
except ImportError:
    print("Note: ProbabilityAgent not found yet, running the other agents only.")


def run_experiments(games=200, board_size=10, agents=None):
    """Return a list of rows: [agent_name, board_size, seed, shots]."""
    agents = agents or AGENTS
    placer = Placer(board_size=board_size)
    rows = []
    for seed in range(games):
        layout = placer.random_layout(seed)          # same board for all agents
        for agent_class in agents:
            agent = agent_class(board_size, seed=seed)
            shots = play_game(agent, layout, board_size)
            rows.append([agent_class.__name__, board_size, seed, shots])
    return rows


def save_results(rows, games):
    results_path = ROOT / "experiments" / "results.csv"
    seeds_path = ROOT / "data" / "seeds.csv"
    results_path.parent.mkdir(exist_ok=True)
    seeds_path.parent.mkdir(exist_ok=True)

    with open(results_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["agent", "board_size", "seed", "shots"])
        writer.writerows(rows)

    with open(seeds_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["seed"])
        writer.writerows([[s] for s in range(games)])
    return results_path, seeds_path


def print_summary(rows):
    print(f"{'agent':<18}{'games':>6}{'average':>10}{'median':>8}{'best':>6}{'worst':>7}")
    for name in dict.fromkeys(r[0] for r in rows):       # keeps the order
        shots = [r[3] for r in rows if r[0] == name]
        print(f"{name:<18}{len(shots):>6}{statistics.mean(shots):>10.1f}"
              f"{statistics.median(shots):>8.1f}{min(shots):>6}{max(shots):>7}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=200)
    parser.add_argument("--board-size", type=int, default=10)
    args = parser.parse_args()

    rows = run_experiments(args.games, args.board_size)
    expected = args.games * len(AGENTS)
    assert len(rows) == expected, f"expected {expected} rows, got {len(rows)}"
    results_path, seeds_path = save_results(rows, args.games)
    print_summary(rows)
    print("Saved:", results_path)
    print("Saved:", seeds_path)