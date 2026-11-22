"""Labs 8/9: Markov model and Bayesian network for the Hunt-and-Target agent.
"""
import csv
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=FutureWarning)   # pgmpy notice, not an error

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from plotting import plt, save_figure   # saves charts (add --show to open them)

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
    # ---- charts ----
    import seaborn as sns
    plt.figure(figsize=(4.8, 4))
    sns.heatmap(P, annot=True, fmt=".3f", cmap="Blues", vmin=0, vmax=1,
                xticklabels=bm.STATES, yticklabels=bm.STATES)
    plt.xlabel("next shot"); plt.ylabel("this shot")
    plt.title("Markov model: HUNT / TARGET")
    save_figure(out / "markov_transitions.png")

    plt.figure(figsize=(7.5, 4))
    names = [q for q in answers if q != "P(next to a hit | shot was a hit)"]
    plt.barh(names, [answers[q] for q in names], color="#4c72b0")
    plt.gca().invert_yaxis()
    for i, q in enumerate(names):
        plt.text(answers[q] + 0.01, i, f"{answers[q]:.2f}", va="center")
    plt.xlim(0, 0.75); plt.xlabel("probability the shot is a hit")
    plt.title("Bayesian network: a shot next to a hit is far more likely to hit")
    save_figure(out / "bayes_probabilities.png")

    print("\nSaved: markov_transitions.csv, bayes_inference.csv and 2 charts")


if __name__ == "__main__":
    main()