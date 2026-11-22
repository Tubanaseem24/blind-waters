"""Charts and summary table for the report (Aiza).

Reads experiments/results.csv (columns: agent, board_size, seed, shots) and saves:
    experiments/chart1_shots_histogram.png      how many shots each agent needs to win
    experiments/chart2_average_shots.png        average shots per agent (per board size)
    experiments/chart3_ships_sunk_curve.png     share of the fleet sunk after N shots
    experiments/summary_table.csv               average, median, spread, best, worst

Chart 3 needs the shot at which each ship sank, which results.csv does not store.
So the script replays the same seeded games and checks that every replayed game
ends with exactly the shot count saved in results.csv. If any game differs, it stops.

Run from the repo root:   python experiments/make_charts.py
"""
import csv
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from plotting import plt, save_figure                      # noqa: E402
from blind_waters.agents import HuntTargetAgent, RandomAgent  # noqa: E402
from blind_waters.placer import Placer                     # noqa: E402
from blind_waters.probability import ProbabilityAgent      # noqa: E402

OUT = Path(__file__).resolve().parent
AGENTS = {"RandomAgent": RandomAgent, "HuntTargetAgent": HuntTargetAgent,
          "ProbabilityAgent": ProbabilityAgent}
LABEL = {"RandomAgent": "Random", "HuntTargetAgent": "Hunt-and-Target",
         "ProbabilityAgent": "Probability"}
COLOUR = {"RandomAgent": "#9ca3af", "HuntTargetAgent": "#f59e0b",
          "ProbabilityAgent": "#2563eb"}


def load_results():
    """-> {(agent, board_size): {seed: shots}}"""
    data = defaultdict(dict)
    with open(OUT / "results.csv") as f:
        for row in csv.DictReader(f):
            data[(row["agent"], int(row["board_size"]))][int(row["seed"])] = int(row["shots"])
    return data


def play_recording_sinks(agent, layout, board_size):
    """Same rules as simulate.play_game, but also returns the shot number of each sinking."""
    state = [["unknown"] * board_size for _ in range(board_size)]
    ship_of = {cell: i for i, ship in enumerate(layout) for cell in ship}
    left = [len(s) for s in layout]
    agent.reset()
    shots, sunk_at = 0, []
    while sum(left) > 0:
        r, c = agent.choose_shot(state)
        shots += 1
        if (r, c) in ship_of:
            i = ship_of[(r, c)]
            left[i] -= 1
            state[r][c] = "hit"
            if left[i] == 0:
                sunk_at.append(shots)
                for sr, sc in layout[i]:
                    state[sr][sc] = "sunk"
            agent.observe({"cell": (r, c), "hit": True, "sunk": left[i] == 0})
        else:
            state[r][c] = "miss"
            agent.observe({"cell": (r, c), "hit": False, "sunk": False})
    return shots, sunk_at


def replay_sinks(agent_name, board_size, seeds, saved):
    placer = Placer(board_size=board_size)
    out = []
    for seed in seeds:
        shots, sunk_at = play_recording_sinks(
            AGENTS[agent_name](board_size, seed=seed), placer.random_layout(seed), board_size)
        if shots != saved[seed]:
            raise SystemExit(f"Replay mismatch: {agent_name} seed {seed} took {shots} shots, "
                             f"results.csv says {saved[seed]}. Rerun run_experiments.py first.")
        out.append(sunk_at)
    return out


def summary_table(data):
    rows = []
    for (agent, size), games in sorted(data.items(), key=lambda kv: (kv[0][1], list(AGENTS).index(kv[0][0]))):
        s = list(games.values())
        rows.append({"agent": LABEL[agent], "board_size": size, "games": len(s),
                     "average": round(statistics.mean(s), 1), "median": statistics.median(s),
                     "std_dev": round(statistics.pstdev(s), 1), "best": min(s), "worst": max(s)})
    with open(OUT / "summary_table.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("\nSummary table (saved as summary_table.csv)")
    print(f"{'agent':<17}{'size':>5}{'games':>7}{'average':>9}{'median':>8}{'std dev':>9}{'best':>6}{'worst':>7}")
    for r in rows:
        print(f"{r['agent']:<17}{r['board_size']:>5}{r['games']:>7}{r['average']:>9}{r['median']:>8}"
              f"{r['std_dev']:>9}{r['best']:>6}{r['worst']:>7}")
    return rows


def chart_histogram(data, size):
    plt.figure(figsize=(8, 4.5))
    top = max(max(g.values()) for (a, s), g in data.items() if s == size)
    bins = list(range(0, top + 6, 5))
    for agent in AGENTS:
        shots = list(data[(agent, size)].values())
        plt.hist(shots, bins=bins, alpha=0.6, color=COLOUR[agent],
                 label=f"{LABEL[agent]} (average {statistics.mean(shots):.1f})")
    plt.xlabel("Shots needed to sink the whole fleet")
    plt.ylabel("Number of games")
    plt.title(f"Shots to win, {size}x{size} board, {len(data[('RandomAgent', size)])} seeded games per agent")
    plt.legend()
    save_figure(OUT / "chart1_shots_histogram.png")


def chart_average(data):
    sizes = sorted({s for _, s in data})
    width = 0.8 / len(AGENTS)
    plt.figure(figsize=(7, 4.5))
    for k, agent in enumerate(AGENTS):
        means, errs = [], []
        for size in sizes:
            s = list(data[(agent, size)].values())
            means.append(statistics.mean(s))
            errs.append(statistics.stdev(s) / len(s) ** 0.5)      # standard error of the mean
        xs = [i + (k - 1) * width for i in range(len(sizes))]
        bars = plt.bar(xs, means, width, yerr=errs, capsize=3, color=COLOUR[agent], label=LABEL[agent])
        for b, m in zip(bars, means):
            plt.text(b.get_x() + b.get_width() / 2, m + 3, f"{m:.1f}", ha="center", fontsize=9)
    plt.xticks(range(len(sizes)), [f"{s}x{s}" for s in sizes])
    plt.ylim(0, 105)
    plt.ylabel("Average shots to win (lower is better)")
    plt.title("Average shots per agent (error bars: standard error)")
    plt.legend()
    save_figure(OUT / "chart2_average_shots.png")


def chart_sunk_curve(data, size):
    plt.figure(figsize=(8, 4.5))
    top = max(max(g.values()) for (a, s), g in data.items() if s == size)   # same x range for every agent
    for agent in AGENTS:
        saved = data[(agent, size)]
        seeds = sorted(saved)
        sinks = replay_sinks(agent, size, seeds, saved)
        n_ships = len(sinks[0])
        curve = [sum(sum(1 for t in g if t <= k) for g in sinks) / (len(sinks) * n_ships)
                 for k in range(top + 1)]
        plt.plot(range(top + 1), curve, color=COLOUR[agent], label=LABEL[agent], linewidth=2)
    plt.xlabel("Shots fired")
    plt.ylabel("Average share of the fleet sunk")
    plt.title(f"Fleet sunk against shots fired, {size}x{size} board")
    plt.ylim(0, 1.02)
    plt.grid(alpha=0.3)
    plt.legend()
    save_figure(OUT / "chart3_ships_sunk_curve.png")


if __name__ == "__main__":
    data = load_results()
    size = max(s for _, s in data)          # the main board size (10)
    summary_table(data)
    chart_histogram(data, size)
    chart_average(data)
    chart_sunk_curve(data, size)
    print("\nDone. Charts are in the experiments folder.")
