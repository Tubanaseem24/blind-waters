import pytest
from blind_waters.supervised import FEATURES, build_dataset


@pytest.fixture(scope="module")
def rows():
    return build_dataset(games=4)


def test_rows_have_all_columns(rows):
    assert rows
    for row in rows:
        assert set(FEATURES) | {"game", "label", "prob_exact"} <= set(row)


def test_labels_and_probabilities_are_valid(rows):
    assert {r["label"] for r in rows} <= {0, 1}
    assert any(r["label"] == 1 for r in rows)
    assert all(0.0 <= r["prob_exact"] <= 1.0 for r in rows)


def test_features_are_sensible(rows):
    for r in rows:
        assert 0 <= r["dist_edge"] <= 4
        assert 0 <= r["adj_hit"] + r["adj_miss"] + r["adj_sunk"] + r["adj_unknown"] <= 4


def test_same_settings_give_same_data():
    assert build_dataset(games=2) == build_dataset(games=2)


def test_models_can_learn_from_the_rows(rows):
    pytest.importorskip("sklearn")
    from sklearn.naive_bayes import GaussianNB
    model = GaussianNB().fit([[r[f] for f in FEATURES] for r in rows], [r["label"] for r in rows])
    assert len(model.predict([[r[f] for f in FEATURES] for r in rows[:5]])) == 5