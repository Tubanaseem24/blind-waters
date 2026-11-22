
import random

from blind_waters.agents import HuntTargetAgent
from blind_waters.placer import Placer
from blind_waters.simulate import play_game


class LayoutProblem:
    def __init__(self, board_size=10, fleet_spec=None, agent_class=HuntTargetAgent,
                 n_games=20, first_seed=1000):
        self.board_size = board_size
        self.placer = Placer(board_size=board_size, fleet_spec=fleet_spec)
        self.agent_class = agent_class
        self.n_games = n_games
        self.first_seed = first_seed
        self.cache = {}
        self.evaluations = 0          # how many different layouts were scored

    # ---- fitness -----------------------------------------------------------
    def fitness(self, layout):
        key = tuple(tuple(ship) for ship in layout)
        if key not in self.cache:
            self.evaluations += 1
            shots = [play_game(self.agent_class(self.board_size, seed=self.first_seed + g),
                               layout, self.board_size)
                     for g in range(self.n_games)]
            self.cache[key] = sum(shots) / len(shots)
        return self.cache[key]

    # ---- building blocks ---------------------------------------------------
    def random_layout(self, rng):
        return self.placer.random_layout(rng.randrange(10 ** 9))

    def neighbors(self, layout):
        """Layouts reachable by moving ONE ship a little: shift 1 or 3 cells in any
        direction, or turn it 90 degrees. Illegal moves are dropped."""
        result = []
        for i, ship in enumerate(layout):
            others = layout[:i] + layout[i + 1:]
            length = len(ship)
            r0, c0 = ship[0]
            horizontal = length > 1 and ship[0][0] == ship[1][0]
            moves = []
            for step in (1, 3):
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    moves.append([(r + dr * step, c + dc * step) for r, c in ship])
            moves.append([(r0, c0 + k) for k in range(length)] if not horizontal
                         else [(r0 + k, c0) for k in range(length)])
            for cells in moves:
                if self.placer.is_consistent(cells, others):
                    result.append(layout[:i] + [cells] + layout[i + 1:])
        return result

    def mutate(self, layout, rng):
        """Move one random ship to any legal position."""
        i = rng.randrange(len(layout))
        others = layout[:i] + layout[i + 1:]
        options = [c for c in self.placer.domain(len(layout[i]))
                   if self.placer.is_consistent(c, others)]
        return layout[:i] + [rng.choice(options)] + layout[i + 1:]

    def crossover(self, a, b, rng):
        """Single point: first k ships from parent a, the rest from parent b.
        If the mix overlaps, the child is a copy of parent a."""
        k = rng.randint(1, len(a) - 1)
        child = a[:k] + b[k:]
        return child if self.placer.is_fleet_complete(child) else list(a)


# ---------------------------------------------------------------------------
# Hill climbing
# ---------------------------------------------------------------------------
def hill_climbing(problem, rng, start=None, steepest=True, max_steps=200):
    """Returns (best_layout, best_fitness, history). history = best fitness per step."""
    current = start or problem.random_layout(rng)
    score = problem.fitness(current)
    history = [score]
    for _ in range(max_steps):
        neighbours = problem.neighbors(current)
        rng.shuffle(neighbours)
        if steepest:                                   # look at ALL, take the best
            best = max(neighbours, key=problem.fitness, default=None)
            better = best is not None and problem.fitness(best) > score
        else:                                          # simple: first better one
            best = next((n for n in neighbours if problem.fitness(n) > score), None)
            better = best is not None
        if not better:                                 # local maximum or plateau
            break
        current, score = best, problem.fitness(best)
        history.append(score)
    return current, score, history


# ---------------------------------------------------------------------------
# Beam search
# ---------------------------------------------------------------------------
def beam_search(problem, rng, k=5, max_steps=30):
    beam = [problem.random_layout(rng) for _ in range(k)]
    best = max(beam, key=problem.fitness)
    history = [problem.fitness(best)]
    for _ in range(max_steps):
        candidates = {tuple(tuple(s) for s in layout): layout for layout in beam}
        for layout in beam:
            for n in problem.neighbors(layout):
                candidates[tuple(tuple(s) for s in n)] = n
        ranked = sorted(candidates.values(), key=problem.fitness, reverse=True)
        beam = ranked[:k]                              # keep the top k, prune the rest
        if problem.fitness(beam[0]) <= problem.fitness(best):
            break                                      # no improvement
        best = beam[0]
        history.append(problem.fitness(best))
    return best, problem.fitness(best), history


# ---------------------------------------------------------------------------
# Genetic algorithm
# ---------------------------------------------------------------------------
def genetic_algorithm(problem, rng, pop_size=20, max_generations=30,
                      mutation_rate=0.1, stagnation=8):
    population = [problem.random_layout(rng) for _ in range(pop_size)]
    best = max(population, key=problem.fitness)
    history = [problem.fitness(best)]
    stale = 0
    for _ in range(max_generations):
        ranked = sorted(population, key=problem.fitness, reverse=True)
        parents = ranked[:pop_size // 2]               # selection: top 50%
        children = [ranked[0]]                         # keep the best one (elitism)
        while len(children) < pop_size:
            a, b = rng.sample(parents, 2)
            child = problem.crossover(a, b, rng)       # crossover
            if rng.random() < mutation_rate:           # mutation, 10% of the time
                child = problem.mutate(child, rng)
            children.append(child)
        population = children
        generation_best = max(population, key=problem.fitness)
        if problem.fitness(generation_best) > problem.fitness(best):
            best, stale = generation_best, 0
        else:
            stale += 1
        history.append(problem.fitness(best))
        if stale >= stagnation:                        # convergence: no improvement
            break
    return best, problem.fitness(best), history
