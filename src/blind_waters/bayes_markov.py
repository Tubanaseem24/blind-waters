
import numpy as np

from blind_waters.agents import HuntTargetAgent
from blind_waters.placer import Placer

STATES = ("HUNT", "TARGET")


def _neighbours(r, c, n):
    return [(a, b) for a, b in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
            if 0 <= a < n and 0 <= b < n]


# 1. Collect data: one dict per shot

def collect_log(games=200, board_size=10, agent_class=HuntTargetAgent, first_seed=0):
    """Play seeded games and record every shot:
    game, shot, mode (HUNT/TARGET), adjacent_to_hit, on_edge, hit, sunk."""
    n = board_size
    placer = Placer(board_size=n)
    log = []
    for seed in range(first_seed, first_seed + games):
        layout = placer.random_layout(seed)
        ship_of = {cell: i for i, ship in enumerate(layout) for cell in ship}
        hits_left = [len(s) for s in layout]
        state = [["unknown"] * n for _ in range(n)]
        agent = agent_class(n, seed=seed)
        agent.reset()
        shot_no = 0
        while sum(hits_left) > 0:
            queued = set(getattr(agent, "targets", []))
            r, c = agent.choose_shot(state)
            mode = "TARGET" if (r, c) in queued else "HUNT"
            adjacent = any(state[a][b] == "hit" for a, b in _neighbours(r, c, n))
            on_edge = r in (0, n - 1) or c in (0, n - 1)
            hit = (r, c) in ship_of
            sunk = False
            if hit:
                state[r][c] = "hit"
                i = ship_of[(r, c)]
                hits_left[i] -= 1
                if hits_left[i] == 0:
                    sunk = True
                    for sr, sc in layout[i]:
                        state[sr][sc] = "sunk"
            else:
                state[r][c] = "miss"
            agent.observe({"cell": (r, c), "hit": hit, "sunk": sunk})
            log.append({"game": seed, "shot": shot_no, "mode": mode,
                        "adjacent_to_hit": int(adjacent), "on_edge": int(on_edge),
                        "hit": int(hit), "sunk": int(sunk)})
            shot_no += 1
    return log



# 2. Markov model: HUNT <-> TARGET

def transition_matrix(log):
    """P[i][j] = chance the next shot is in mode j, given this shot is in mode i."""
    counts = np.zeros((2, 2))
    for a, b in zip(log, log[1:]):
        if a["game"] == b["game"]:
            counts[STATES.index(a["mode"]), STATES.index(b["mode"])] += 1
    return counts / counts.sum(axis=1, keepdims=True)


def stationary_distribution(P):
    """Long-run share of shots spent in each mode (solves pi = pi P)."""
    values, vectors = np.linalg.eig(P.T)
    pi = np.real(vectors[:, np.argmin(abs(values - 1))])
    return pi / pi.sum()


def simulate_chain(P, steps, rng, start="HUNT"):
    """A made-up sequence of modes of the given length, following P."""
    state = STATES.index(start)
    sequence = [STATES[state]]
    for _ in range(steps - 1):
        state = rng.choice(2, p=P[state])
        sequence.append(STATES[state])
    return sequence


def prob_at_least(P, steps=10, k=3, runs=5000, seed=0):
    """Chance that at least k of the first `steps` shots are TARGET shots,
    estimated by simulating the Markov chain (like the lab's rainy-days task)."""
    rng = np.random.default_rng(seed)
    wins = sum(simulate_chain(P, steps, rng).count("TARGET") >= k for _ in range(runs))
    return wins / runs


def observed_at_least(log, steps=10, k=3):
    """The same chance, counted directly from the real games."""
    games = {}
    for row in log:
        games.setdefault(row["game"], []).append(row)
    hits = sum(sum(r["mode"] == "TARGET" for r in rows[:steps]) >= k
               for rows in games.values())
    return hits / len(games)


# 3. Bayesian network (pgmpy), tables counted from the log

def _rate(rows, condition=lambda r: True):
    """P(hit) among rows satisfying condition, with +1/+2 smoothing."""
    chosen = [r for r in rows if condition(r)]
    return (sum(r["hit"] for r in chosen) + 1) / (len(chosen) + 2)


def build_network(log):
    from pgmpy.factors.discrete import TabularCPD
    from pgmpy.models import DiscreteBayesianNetwork

    model = DiscreteBayesianNetwork([("AdjacentToHit", "ShotHits"), ("OnEdge", "ShotHits")])
    p_adj = (sum(r["adjacent_to_hit"] for r in log) + 1) / (len(log) + 2)
    p_edge = (sum(r["on_edge"] for r in log) + 1) / (len(log) + 2)
    cpd_adj = TabularCPD("AdjacentToHit", 2, [[1 - p_adj], [p_adj]])
    cpd_edge = TabularCPD("OnEdge", 2, [[1 - p_edge], [p_edge]])

    # column order must match evidence order: (adj=0,edge=0), (0,1), (1,0), (1,1)
    p_hit = [_rate(log, lambda r, a=a, e=e: r["adjacent_to_hit"] == a and r["on_edge"] == e)
             for a in (0, 1) for e in (0, 1)]
    cpd_hit = TabularCPD("ShotHits", 2,
                         [[1 - p for p in p_hit], p_hit],
                         evidence=["AdjacentToHit", "OnEdge"], evidence_card=[2, 2])
    model.add_cpds(cpd_adj, cpd_edge, cpd_hit)
    assert model.check_model()
    return model


def inference(model):
    """Variable Elimination answers (all numbers are probabilities of 0..1)."""
    from pgmpy.inference import VariableElimination
    engine = VariableElimination(model)

    def ask(variable, **evidence):
        result = engine.query([variable], evidence=evidence, show_progress=False)
        return float(result.values[1])

    return {
        "P(hit)": ask("ShotHits"),
        "P(hit | next to a hit)": ask("ShotHits", AdjacentToHit=1),
        "P(hit | not next to a hit)": ask("ShotHits", AdjacentToHit=0),
        "P(hit | next to a hit, on edge)": ask("ShotHits", AdjacentToHit=1, OnEdge=1),
        "P(hit | not next to a hit, on edge)": ask("ShotHits", AdjacentToHit=0, OnEdge=1),
        "P(next to a hit | shot was a hit)": ask("AdjacentToHit", ShotHits=1),
    }