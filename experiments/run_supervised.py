
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")                      # draw to files, no window needed
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix,
                             f1_score, precision_score, recall_score, roc_auc_score, roc_curve)
from sklearn.model_selection import (GroupKFold, LeaveOneGroupOut, cross_val_score,
                                     train_test_split)
from sklearn.naive_bayes import GaussianNB
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from plotting import plt, save_figure   # saves charts (add --show to open them)

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

    # ---- 1b. look at the data (Lab 11: class distribution, correlation) ----
    out = ROOT / "experiments"
    out.mkdir(exist_ok=True)
    df["label"].value_counts().sort_index().plot(kind="bar", color=["#4c72b0", "#dd8452"])
    plt.xticks([0, 1], ["no ship (0)", "ship (1)"], rotation=0)
    plt.title("Class distribution (very unbalanced)"); plt.ylabel("cells")
    save_figure(out / "class_distribution.png")
    df[FEATURES].hist(figsize=(11, 7), bins=15)
    plt.suptitle("Shot feature distributions")
    save_figure(out / "shot_feature_histograms.png")
    fig, axes = plt.subplots(2, 5, figsize=(13, 6))
    for ax, feature in zip(axes.ravel(), FEATURES):
        sns.boxplot(x="label", y=feature, data=df, ax=ax)
        ax.set_xlabel("ship in cell (1) or not (0)")
    plt.suptitle("Each feature split by class")
    save_figure(out / "shot_feature_boxplots.png")
    plt.figure(figsize=(8, 6.5))
    sns.heatmap(df[FEATURES + ["label"]].corr(), annot=True, fmt=".2f", cmap="coolwarm")
    plt.title("Correlation matrix of shot features"); save_figure(out / "shot_features_correlation.png")

    # ---- 2. train-test split: 80/20, split BY GAME so a game is never in both ----
    train_games, test_games = train_test_split(df["game"].unique(), test_size=0.2, random_state=42)
    train, test = df[df["game"].isin(train_games)], df[df["game"].isin(test_games)]
    X_train, y_train, X_test, y_test = train[FEATURES], train["label"], test[FEATURES], test["label"]

    models = {
        "Majority class (baseline)": DummyClassifier(strategy="most_frequent"),
        "Naive Bayes": GaussianNB(),
        "Decision tree": DecisionTreeClassifier(max_depth=6, random_state=0),
        "Logistic regression": make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)),
        "SVM (RBF kernel)": make_pipeline(StandardScaler(), SVC(kernel="rbf", C=1, gamma="scale")),
    }

    # ---- 3. train, predict, evaluate ----
    scores, preds, results = {}, {}, []
    for name, model in models.items():
        if name.startswith("SVM"):               # SVM is slow on 40,000 rows: use 8,000
            rows = X_train.sample(8000, random_state=0).index
            model.fit(X_train.loc[rows], y_train.loc[rows])
            scores[name] = model.decision_function(X_test)
        else:
            model.fit(X_train, y_train)
            scores[name] = model.predict_proba(X_test)[:, 1]
        preds[name] = model.predict(X_test)
    scores["Exact counting (ProbabilityAgent)"] = test["prob_exact"].to_numpy()
    preds["Exact counting (ProbabilityAgent)"] = (scores["Exact counting (ProbabilityAgent)"] >= 0.5).astype(int)

    for name, score in scores.items():
        pred = preds[name]
        model = models.get(name)
        results.append({
            "model": name,
            "train_accuracy": accuracy_score(y_train, model.predict(X_train)) if model else None,
            "accuracy": accuracy_score(y_test, pred),
            "precision": precision_score(y_test, pred, zero_division=0),
            "recall": recall_score(y_test, pred, zero_division=0),
            "f1": f1_score(y_test, pred, zero_division=0),
            "roc_auc": roc_auc_score(y_test, score),
        })

    # ---- 4. cross-validation, by game ----
    for row in results:
        model = models.get(row["model"])
        if model is not None and not row["model"].startswith("SVM"):
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
    table.to_csv(out / "supervised_results.csv", index=False)

    # ---- 5. ROC curve and confusion matrix ----
    plt.figure(figsize=(7, 5))
    for name, prob in scores.items():
        fpr, tpr, _ = roc_curve(y_test, prob)
        plt.plot(fpr, tpr, label=f"{name} (AUC = {roc_auc_score(y_test, prob):.2f})")
    plt.plot([0, 1], [0, 1], "--", color="gray")
    plt.xlabel("False positive rate"); plt.ylabel("True positive rate")
    plt.title("Is there a ship in this cell? ROC curves on unseen games")
    plt.legend(loc="lower right", fontsize=8); save_figure(out / "roc_curve.png")

    learned = {k: v for k, v in scores.items() if k in models and "baseline" not in k}
    best = max(learned, key=lambda k: roc_auc_score(y_test, learned[k]))
    cm = confusion_matrix(y_test, preds[best])
    print(f"\nClassification report for {best}:")
    print(classification_report(y_test, preds[best], target_names=["no ship", "ship"], zero_division=0))
    plt.figure(figsize=(4.5, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=["no ship", "ship"],
                yticklabels=["no ship", "ship"])
    plt.xlabel("Predicted"); plt.ylabel("Actual"); plt.title(f"Confusion matrix: {best}")
    save_figure(out / "confusion_matrix.png")
    print(f"Best learned model (by ROC-AUC): {best}")
    print("Saved: data/shot_dataset.csv, experiments/supervised_results.csv, "
          "7 charts")


if __name__ == "__main__":
    main()