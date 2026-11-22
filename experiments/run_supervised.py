
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")                      # draw to files, no window needed
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_score, recall_score, roc_auc_score, roc_curve)
from sklearn.model_selection import (GroupKFold, LeaveOneGroupOut, cross_val_score,
                                     train_test_split)
from sklearn.naive_bayes import GaussianNB
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from blind_waters.supervised import FEATURES, build_dataset

GAMES = 200


def main():
    # ---- 1. read / write data (Lab 10, section 3.1) ----
    csv_path = ROOT / "data" / "shot_dataset.csv"
    csv_path.parent.mkdir(exist_ok=True)
    pd.DataFrame(build_dataset(games=GAMES)).to_csv(csv_path, index=False)
    df = pd.read_csv(csv_path)
    print(f"Dataset: {len(df)} rows from {df['game'].nunique()} games, "
          f"{df['label'].mean():.1%} of cells hold a ship")
    print("Missing values:", int(df.isnull().sum().sum()), "(all features are numbers, nothing to encode)\n")

    # ---- 2. train-test split: 80/20, split BY GAME so a game is never in both ----
    train_games, test_games = train_test_split(df["game"].unique(), test_size=0.2, random_state=42)
    train, test = df[df["game"].isin(train_games)], df[df["game"].isin(test_games)]
    X_train, y_train, X_test, y_test = train[FEATURES], train["label"], test[FEATURES], test["label"]

    models = {
        "Majority class (baseline)": DummyClassifier(strategy="most_frequent"),
        "Naive Bayes": GaussianNB(),
        "Decision tree": DecisionTreeClassifier(max_depth=6, random_state=0),
        "Logistic regression": make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)),
    }

    # ---- 3. train, predict, evaluate ----
    scores = {}
    results = []
    for name, model in models.items():
        model.fit(X_train, y_train)
        scores[name] = model.predict_proba(X_test)[:, 1]
    scores["Exact counting (ProbabilityAgent)"] = test["prob_exact"].to_numpy()

    for name, prob in scores.items():
        pred = (prob >= 0.5).astype(int)
        results.append({
            "model": name,
            "accuracy": accuracy_score(y_test, pred),
            "precision": precision_score(y_test, pred, zero_division=0),
            "recall": recall_score(y_test, pred, zero_division=0),
            "f1": f1_score(y_test, pred, zero_division=0),
            "roc_auc": roc_auc_score(y_test, prob),
        })

    # ---- 4. cross-validation, by game ----
    for row in results:
        model = models.get(row["model"])
        if model is not None:
            cv = cross_val_score(model, df[FEATURES], df["label"], groups=df["game"],
                                 cv=GroupKFold(n_splits=5), scoring="roc_auc")
            row["cv5_roc_auc"] = cv.mean()
    loo = cross_val_score(GaussianNB(), df[FEATURES], df["label"], groups=df["game"],
                          cv=LeaveOneGroupOut(), scoring="roc_auc")
    for row in results:
        if row["model"] == "Naive Bayes":
            row["loocv_roc_auc"] = loo.mean()       # leave one whole game out, 200 times

    table = pd.DataFrame(results).round(3)
    print(table.to_string(index=False))
    out = ROOT / "experiments"
    out.mkdir(exist_ok=True)
    table.to_csv(out / "supervised_results.csv", index=False)

    # ---- 5. ROC curve and confusion matrix ----
    plt.figure(figsize=(7, 5))
    for name, prob in scores.items():
        fpr, tpr, _ = roc_curve(y_test, prob)
        plt.plot(fpr, tpr, label=f"{name} (AUC = {roc_auc_score(y_test, prob):.2f})")
    plt.plot([0, 1], [0, 1], "--", color="gray")
    plt.xlabel("False positive rate"); plt.ylabel("True positive rate")
    plt.title("Is there a ship in this cell? ROC curves on unseen games")
    plt.legend(loc="lower right", fontsize=8); plt.tight_layout()
    plt.savefig(out / "roc_curve.png", dpi=150); plt.close()

    learned = {k: v for k, v in scores.items() if k in models and "baseline" not in k}
    best = max(learned, key=lambda k: roc_auc_score(y_test, learned[k]))
    cm = confusion_matrix(y_test, (learned[best] >= 0.5).astype(int))
    plt.figure(figsize=(4.5, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=["no ship", "ship"],
                yticklabels=["no ship", "ship"])
    plt.xlabel("Predicted"); plt.ylabel("Actual"); plt.title(f"Confusion matrix: {best}")
    plt.tight_layout(); plt.savefig(out / "confusion_matrix.png", dpi=150); plt.close()
    print(f"\nBest learned model: {best}")
    print("Saved: data/shot_dataset.csv, experiments/supervised_results.csv, "
          "experiments/roc_curve.png, experiments/confusion_matrix.png")


if __name__ == "__main__":
    main()