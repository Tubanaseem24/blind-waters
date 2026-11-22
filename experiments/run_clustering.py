"""Lab 11, part 3 (Unsupervised):
"""
import random
import sys
from pathlib import Path

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from plotting import plt, save_figure   # saves charts (add --show to open them)

from blind_waters.layout_features import LAYOUT_FEATURES, layout_features
from blind_waters.local_search import LayoutProblem, genetic_algorithm

K = 3


def main():
    csv_path = ROOT / "data" / "layout_dataset.csv"
    if not csv_path.exists():
        sys.exit("Run python experiments/run_regression.py first (it creates the data).")
    df = pd.read_csv(csv_path)
    print("Shape:", df.shape, "| missing values:", int(df.isnull().sum().sum()))

    # ---- scale, then the elbow method (WCSS for k = 1..10) ----
    scaler = StandardScaler()
    X = scaler.fit_transform(df[LAYOUT_FEATURES])
    wcss = [KMeans(n_clusters=k, random_state=42, n_init=10).fit(X).inertia_ for k in range(1, 11)]
    plt.figure(figsize=(6, 4))
    plt.plot(range(1, 11), wcss, marker="o")
    plt.xlabel("Number of clusters"); plt.ylabel("WCSS"); plt.title("Elbow method")
    save_figure(ROOT / "experiments" / "elbow_method.png")
    print("\nk   silhouette (higher = better separated)")
    for k in range(2, 7):
        labels = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(X)
        print(f"{k}   {silhouette_score(X, labels):.3f}")

    # ---- fit K-Means with k = 3 ----
    kmeans = KMeans(n_clusters=K, random_state=42, n_init=10).fit(X)
    df["cluster"] = kmeans.labels_
    print(f"\nLayouts per cluster (k={K}):")
    print(df["cluster"].value_counts().sort_index().to_string())

    summary = df.groupby("cluster")[LAYOUT_FEATURES + ["avg_shots"]].mean().round(2)
    summary.insert(0, "layouts", df["cluster"].value_counts().sort_index())
    print("\nAverage of each feature per cluster:")
    print(summary.T.to_string())
    summary.to_csv(ROOT / "experiments" / "cluster_summary.csv")

    # ---- picture: PCA squeezes 8 features into 2 so the clusters can be drawn ----
    points = PCA(n_components=2, random_state=0).fit_transform(X)
    plt.figure(figsize=(7, 5))
    scatter = plt.scatter(points[:, 0], points[:, 1], c=df["cluster"], cmap="viridis", s=12)
    plt.legend(*scatter.legend_elements(), title="cluster")
    plt.xlabel("PCA component 1"); plt.ylabel("PCA component 2")
    plt.title("Layout types found by K-Means"); save_figure(ROOT / "experiments" / "layout_clusters.png")

    plt.figure(figsize=(6.5, 5))
    scatter = plt.scatter(df["mean_dist_edge"], df["spread"], c=df["cluster"], cmap="viridis", s=12)
    plt.legend(*scatter.legend_elements(), title="cluster")
    plt.xlabel("mean distance from edge"); plt.ylabel("spread of the fleet")
    plt.title("Clusters on two raw features (like Alcohol vs Malic Acid in the lab)")
    save_figure(ROOT / "experiments" / "clusters_raw_features.png")

    plt.figure(figsize=(5.5, 4))
    plt.bar([str(c) for c in summary.index], summary["avg_shots"], color=["#4c72b0", "#dd8452", "#55a868"])
    plt.ylim(0, summary["avg_shots"].max() + 8)
    plt.xlabel("cluster"); plt.ylabel("average shots to find the layout")
    plt.title("Hard-to-find layouts? Clusters differ by only about 1 shot")
    save_figure(ROOT / "experiments" / "cluster_shots.png")

    # ---- link to Lab 6: which cluster do the GA's hardest layouts fall in? ----
    evolved = []
    for seed in range(5):
        problem = LayoutProblem(n_games=20)
        best, _, _ = genetic_algorithm(problem, random.Random(seed))
        evolved.append(layout_features(best))
    evolved_clusters = kmeans.predict(scaler.transform(pd.DataFrame(evolved)[LAYOUT_FEATURES]))
    shots = summary["avg_shots"]
    print(f"\nAverage shots per cluster: { {int(k): float(v) for k, v in shots.items()} }")
    print(f"Easiest to find: cluster {shots.idxmin()} ({shots.min()} shots), "
          f"hardest: cluster {shots.idxmax()} ({shots.max()} shots), "
          f"difference only {shots.max() - shots.min():.1f} shots")
    print("Cluster of 5 layouts evolved by the genetic algorithm (Lab 6):",
          [int(c) for c in evolved_clusters])
    print("\nSaved: experiments/cluster_summary.csv, 4 charts")


if __name__ == "__main__":
    main()