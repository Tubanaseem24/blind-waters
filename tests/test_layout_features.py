import pytest
from blind_waters.layout_features import LAYOUT_FEATURES, build_layout_dataset, layout_features

LAYOUT = [[(0, 0), (0, 1), (0, 2)], [(5, 5), (6, 5), (7, 5)], [(9, 8), (9, 9)]]


def test_features_of_a_known_layout():
    f = layout_features(LAYOUT)
    assert f["n_horizontal"] == 2          # ship 1 and ship 3 lie in a row
    assert f["min_dist_edge"] == 0
    assert f["edge_cells"] == 5            # (0,0) (0,1) (0,2) (9,8) (9,9)
    assert f["ships_touching"] == 0


def test_touching_ships_are_counted():
    touching = [[(2, 2), (2, 3), (2, 4)], [(3, 2), (3, 3)], [(8, 8), (8, 9)]]
    assert layout_features(touching)["ships_touching"] == 1


def test_all_features_present():
    assert set(LAYOUT_FEATURES) <= set(layout_features(LAYOUT))


def test_dataset_rows_are_valid_and_repeatable():
    rows = build_layout_dataset(layouts=5, n_games=3)
    assert len(rows) == 5
    assert all(set(LAYOUT_FEATURES) | {"seed", "avg_shots"} <= set(r) for r in rows)
    assert all(8 <= r["avg_shots"] <= 100 for r in rows)
    assert rows == build_layout_dataset(layouts=5, n_games=3)


def test_kmeans_groups_layouts_into_three_clusters():
    pytest.importorskip("sklearn")
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    rows = build_layout_dataset(layouts=40, n_games=2)
    X = StandardScaler().fit_transform([[r[f] for f in LAYOUT_FEATURES] for r in rows])
    labels = KMeans(n_clusters=3, random_state=42, n_init=10).fit_predict(X)
    assert set(labels) == {0, 1, 2}
    assert list(labels) == list(KMeans(n_clusters=3, random_state=42, n_init=10).fit_predict(X))