"""Lab 6: compare Hill Climbing, Beam Search and the Genetic Algorithm.
Each method runs 5 times; the table shows the average.
(local_search_comparison.png, local_search_convergence.png)
"""
import csv
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from plotting import plt, save_figure   # saves charts (add --show to open them)

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
    histories = {}

    for name, run in methods:
        trains, evals, vals = [], [], []
        for seed in SEEDS:
            problem = LayoutProblem()
            best, score, history = run(problem, random.Random(seed))
            trains.append(score)
            evals.append(problem.evaluations)
            vals.append(validation.fitness(best))
            if seed == 0:
                histories[name] = history
                if name == "Genetic algorithm":
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
    # ---- charts ----
    plt.figure(figsize=(7, 4.5))
    labels = [r[0] for r in rows]
    plt.barh(labels, [r[3] for r in rows], color=["gray"] + ["#4c72b0"] * (len(rows) - 1))
    plt.xlim(0, max(r[3] for r in rows) + 5)
    plt.xlabel("average shots the agent needs on NEW seeds (higher = harder to find)")
    plt.title("Local search: how well hidden are the layouts?")
    save_figure(out / "local_search_comparison.png")

    plt.figure(figsize=(7, 4.5))
    for name, history in histories.items():
        plt.plot(range(len(history)), history, marker="o", label=name)
    plt.xlabel("step / generation"); plt.ylabel("best fitness so far (average shots)")
    plt.title("Convergence of the search methods (first run)"); plt.legend(fontsize=8)
    save_figure(out / "local_search_convergence.png")

    print("\nSaved: experiments/local_search_results.csv, ga_history.csv and 2 charts")


if __name__ == "__main__":
    main()