"""Labs 8/9: Markov model and Bayesian network for the Hunt-and-Target agent.

Run from the project folder:
    python experiments/run_bayes_markov.py
Writes experiments/markov_transitions.csv and experiments/bayes_inference.csv
"""
import csv
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=FutureWarning)   # pgmpy notice, not an error

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from blind_waters import bayes_markov as bm


def main():
    log = bm.collect_log(games=200)
    print(f"Collected {len(log)} shots from 200 games (HuntTargetAgent, seeds 0 to 199)\n")

    # ---- Markov model ----
    P = bm.transition_matrix(log)
    pi = bm.stationary_distribution(P)
    share = sum(r["mode"] == "TARGET" for r in log) / len(log)
    print("MARKOV MODEL: next-shot mode given the current mode")
    print(f"{'':>10}{'HUNT':>10}{'TARGET':>10}")
    for name, row in zip(bm.STATES, P):
        print(f"{name:>10}{row[0]:>10.3f}{row[1]:>10.3f}")
    print(f"\nLong-run share of TARGET shots (stationary): {pi[1]:.3f}")
    print(f"Share of TARGET shots counted in the games : {share:.3f}")
    sim = bm.prob_at_least(P, steps=10, k=3)
    real = bm.observed_at_least(log, steps=10, k=3)
    print(f"P(at least 3 TARGET shots in the first 10): Markov model {sim:.3f}, real games {real:.3f}")

    # ---- Bayesian network ----
    model = bm.build_network(log)
    answers = bm.inference(model)
    print("\nBAYESIAN NETWORK (Variable Elimination)")
    for question, p in answers.items():
        print(f"  {question:<40}{p:.3f}")

    out = ROOT / "experiments"
    out.mkdir(exist_ok=True)
    with open(out / "markov_transitions.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["from", "to_HUNT", "to_TARGET"])
        for name, row in zip(bm.STATES, P):
            w.writerow([name, round(row[0], 4), round(row[1], 4)])
        w.writerow(["stationary", round(pi[0], 4), round(pi[1], 4)])
    with open(out / "bayes_inference.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["question", "probability"])
        for question, p in answers.items():
            w.writerow([question, round(p, 4)])
    print("\nSaved: experiments/markov_transitions.csv, experiments/bayes_inference.csv")


if __name__ == "__main__":
    main()