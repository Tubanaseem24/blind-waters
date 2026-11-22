import numpy as np
import pytest
from blind_waters import bayes_markov as bm


@pytest.fixture(scope="module")
def log():
    return bm.collect_log(games=30)


def test_log_has_one_row_per_shot_and_valid_values(log):
    assert all(r["mode"] in bm.STATES for r in log)
    assert all(r["hit"] in (0, 1) and r["sunk"] in (0, 1) for r in log)
    assert log[0]["mode"] == "HUNT" and log[0]["shot"] == 0
    assert sum(r["sunk"] for r in log) == 30 * 3          # 3 ships sunk in every game


def test_transition_rows_sum_to_one(log):
    P = bm.transition_matrix(log)
    assert P.shape == (2, 2)
    assert np.allclose(P.sum(axis=1), 1.0)


def test_stationary_distribution_is_valid(log):
    P = bm.transition_matrix(log)
    pi = bm.stationary_distribution(P)
    assert np.isclose(pi.sum(), 1.0) and (pi >= 0).all()
    assert np.allclose(pi @ P, pi)


def test_prob_at_least_bounds_and_reproducible(log):
    P = bm.transition_matrix(log)
    assert bm.prob_at_least(P, steps=10, k=0) == 1.0
    assert bm.prob_at_least(P, steps=10, k=11) == 0.0
    assert bm.prob_at_least(P, 10, 3, seed=1) == bm.prob_at_least(P, 10, 3, seed=1)


def test_bayesian_network_matches_counted_frequencies(log):
    pytest.importorskip("pgmpy")
    answers = bm.inference(bm.build_network(log))
    near = [r["hit"] for r in log if r["adjacent_to_hit"] == 1]
    assert answers["P(hit | next to a hit)"] == pytest.approx(sum(near) / len(near), abs=0.02)


def test_shot_next_to_a_hit_is_more_likely_to_hit(log):
    pytest.importorskip("pgmpy")
    answers = bm.inference(bm.build_network(log))
    assert answers["P(hit | next to a hit)"] > 3 * answers["P(hit | not next to a hit)"]