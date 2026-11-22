"""Lab 11, part 2 (Regression): predict how many shots a layout takes to find.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Lasso, LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeRegressor

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from plotting import plt, save_figure   # saves charts (add --show to open them)

from blind_waters.layout_features import LAYOUT_FEATURES, build_layout_dataset


def main():
    # ---- read / write data, basic info, missing values ----
    csv_path = ROOT / "data" / "layout_dataset.csv"
    csv_path.parent.mkdir(exist_ok=True)
    pd.DataFrame(build_layout_dataset(layouts=1000)).to_csv(csv_path, index=False)
    df = pd.read_csv(csv_path)
    print("Shape:", df.shape)
    print(df[LAYOUT_FEATURES + ["avg_shots"]].describe().round(2).to_string())
    print("\nMissing values:", int(df.isnull().sum().sum()))
    print("Categorical columns:", list(df.select_dtypes(include="object").columns) or "none (no encoding needed)")

    out = ROOT / "experiments"
    out.mkdir(exist_ok=True)

    # ---- plots: correlation matrix, target distribution, one scatter ----
    plt.figure(figsize=(8, 6.5))
    sns.heatmap(df[LAYOUT_FEATURES + ["avg_shots"]].corr(), annot=True, fmt=".2f", cmap="coolwarm")
    plt.title("Correlation matrix of layout features"); save_figure(out / "layout_correlation.png")

    df[LAYOUT_FEATURES].hist(figsize=(11, 7), bins=15)
    plt.suptitle("Layout feature distributions")
    save_figure(out / "layout_feature_histograms.png")

    best_feature = df[LAYOUT_FEATURES].corrwith(df["avg_shots"]).abs().idxmax()
    plt.figure(figsize=(6, 4))
    sns.regplot(x=df[best_feature], y=df["avg_shots"], scatter_kws={"s": 8, "alpha": 0.5},
                line_kws={"color": "red"})
    plt.title(f"Average shots vs {best_feature}")
    save_figure(out / "shots_vs_feature.png")

    plt.figure(figsize=(6, 4))
    sns.histplot(df["avg_shots"], kde=True)
    plt.title("Average shots needed to find a layout"); plt.xlabel("average shots")
    save_figure(out / "shots_distribution.png")

    # ---- split 80/20, train all six regressors, score with R2 ----
    X, y = df[LAYOUT_FEATURES], df["avg_shots"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    scaled = lambda model: make_pipeline(StandardScaler(), model)   # scale first
    models = {
        "Linear Regression": scaled(LinearRegression()),
        "Ridge": scaled(Ridge()),
        "Lasso": scaled(Lasso(alpha=0.1)),
        "Decision Tree": DecisionTreeRegressor(max_depth=5, random_state=0),
        "Random Forest": RandomForestRegressor(n_estimators=200, random_state=0),
        "KNN": scaled(KNeighborsRegressor()),
    }
    rows = []
    for name, model in models.items():
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        rows.append({"model": name,
                     "train_r2": r2_score(y_train, model.predict(X_train)),
                     "test_r2": r2_score(y_test, pred),
                     "test_mae_shots": mean_absolute_error(y_test, pred)})
        print(f"{name:<18} R2 = {rows[-1]['test_r2']:.3f}")
    table = pd.DataFrame(rows).round(3)
    print("\n" + table.to_string(index=False))
    table.to_csv(out / "regression_results.csv", index=False)

    plt.figure(figsize=(7, 4))
    plt.barh(table["model"], table["test_r2"])
    plt.xlabel("R2 score on unseen layouts"); plt.title("Regression models")
    save_figure(out / "regression_r2.png")

    best_name = table.loc[table["test_r2"].idxmax(), "model"]
    predicted = models[best_name].predict(X_test)
    plt.figure(figsize=(5.5, 5))
    plt.scatter(y_test, predicted, s=10, alpha=0.6)
    low, high = min(y_test.min(), predicted.min()), max(y_test.max(), predicted.max())
    plt.plot([low, high], [low, high], "r--", label="perfect prediction")
    plt.xlabel("actual average shots"); plt.ylabel("predicted average shots")
    plt.title(f"{best_name}: predicted vs actual (unseen layouts)"); plt.legend()
    save_figure(out / "predicted_vs_actual.png")

    forest = models["Random Forest"]
    importance = pd.Series(forest.feature_importances_, index=LAYOUT_FEATURES).sort_values(ascending=False)
    print("\nMost useful features (Random Forest):")
    print(importance.round(3).to_string())
    print("\nSaved: data/layout_dataset.csv, experiments/regression_results.csv and 6 charts")


if __name__ == "__main__":
    main()