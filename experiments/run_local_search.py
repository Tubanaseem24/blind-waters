
import csv
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from blind_waters.local_search import (LayoutProblem, hill_climbing, beam_search,
                                       genetic_algorithm)

SEEDS = range(5)          # each method is run 5 times with different random starts
RANDOM_LAYOUTS = 30


def mean(values):
    return sum(values) / len(values)


def main():
    # fresh problem per algorithm so each one counts its own evaluations
    methods = [
        ("Hill climbing (simple)", lambda p, r: hill_climbing(p, r, steepest=False)),
        ("Hill climbing (steepest)", lambda p, r: hill_climbing(p, r, steepest=True)),
        ("Beam search (k=5)", lambda p, r: beam_search(p, r, k=5)),
        ("Genetic algorithm", lambda p, r: genetic_algorithm(p, r)),
    ]
    # validation: agent seeds the search NEVER saw, 100 games per layout
    validation = LayoutProblem(n_games=100, first_seed=5000)

    rng = random.Random(0)
    baseline_train = LayoutProblem()
    random_layouts = [baseline_train.random_layout(rng) for _ in range(RANDOM_LAYOUTS)]
    rows = [["random layouts (baseline)",
             round(mean([baseline_train.fitness(l) for l in random_layouts]), 1),
             "", round(mean([validation.fitness(l) for l in random_layouts]), 1)]]
    ga_history = []

    for name, run in methods:
        trains, evals, vals = [], [], []
        for seed in SEEDS:
            problem = LayoutProblem()
            best, score, history = run(problem, random.Random(seed))
            trains.append(score)
            evals.append(problem.evaluations)
            vals.append(validation.fitness(best))
            if name == "Genetic algorithm" and seed == 0:
                ga_history = history
        rows.append([name, round(mean(trains), 1), round(mean(evals)), round(mean(vals), 1)])

    print()
    print(f"{'method':<28}{'search shots':>13}{'layouts tried':>15}{'new-seed shots':>16}")
    for name, train, evals, val in rows:
        print(f"{name:<28}{train:>13}{str(evals):>15}{val:>16}")

    out = ROOT / "experiments"
    out.mkdir(exist_ok=True)
    with open(out / "local_search_results.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["method", "search_shots", "layouts_tried", "new_seed_shots"])
        w.writerows(rows)
    with open(out / "ga_history.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["generation", "best_fitness"])
        w.writerows(enumerate(ga_history))
    print("\nSaved: experiments/local_search_results.csv, experiments/ga_history.csv")


if __name__ == "__main__":
    main()