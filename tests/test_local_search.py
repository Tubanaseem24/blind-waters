
import random
import pytest
from blind_waters.local_search import (LayoutProblem, hill_climbing, beam_search,
                                       genetic_algorithm)


@pytest.fixture
def problem():
    return LayoutProblem(n_games=3)


def test_neighbors_are_valid_and_different(problem):
    layout = problem.random_layout(random.Random(0))
    neighbours = problem.neighbors(layout)
    assert neighbours
    for n in neighbours:
        assert problem.placer.is_fleet_complete(n)
        assert n != layout


def test_mutate_and_crossover_give_valid_layouts(problem):
    rng = random.Random(1)
    a, b = problem.random_layout(rng), problem.random_layout(rng)
    for _ in range(30):
        assert problem.placer.is_fleet_complete(problem.mutate(a, rng))
        assert problem.placer.is_fleet_complete(problem.crossover(a, b, rng))


def test_fitness_is_repeatable(problem):
    layout = problem.random_layout(random.Random(2))
    assert problem.fitness(layout) == problem.fitness(layout)


@pytest.mark.parametrize("steepest", [True, False])
def test_hill_climbing_never_gets_worse(problem, steepest):
    rng = random.Random(3)
    start = problem.random_layout(rng)
    best, score, history = hill_climbing(problem, rng, start=start, steepest=steepest)
    assert problem.placer.is_fleet_complete(best)
    assert score >= problem.fitness(start)
    assert history == sorted(history)


def test_beam_search_gives_valid_layout_and_improves(problem):
    best, score, history = beam_search(problem, random.Random(4), k=3, max_steps=5)
    assert problem.placer.is_fleet_complete(best)
    assert history == sorted(history)


def test_genetic_algorithm_gives_valid_layout_and_improves(problem):
    best, score, history = genetic_algorithm(problem, random.Random(5), pop_size=8,
                                             max_generations=5)
    assert problem.placer.is_fleet_complete(best)
    assert history == sorted(history)
    assert score == history[-1]


def test_same_seed_same_result():
    a = genetic_algorithm(LayoutProblem(n_games=3), random.Random(6), pop_size=8, max_generations=4)
    b = genetic_algorithm(LayoutProblem(n_games=3), random.Random(6), pop_size=8, max_generations=4)
    assert a[0] == b[0] and a[1] == b[1]