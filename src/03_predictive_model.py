"""
03_predictive_model.py

Predictive layer: multi-class model predicting WHICH way an at-risk DDA
account is most likely to churn (large_withdrawal / dd_stop / dormant / none),
mirroring the real project's design choice -- a binary flag would tell you
who's at risk, the multi-class model tells you which playbook to pre-stage.

Outputs:
  - classification report + confusion matrix (figures/confusion_matrix.png)
  - feature importance chart (figures/feature_importance.png)
  - output/predictive_scores.csv: per-account predicted class probabilities,
    used downstream by the optimization layer (05_optimization.py)
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import (classification_report, confusion_matrix,
                              roc_auc_score, average_precision_score)
from xgboost import XGBClassifier
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

from config import DATA_DIR, FIG_DIR, OUT_DIR, SEED, TEST_SIZE, PREDICTIVE_MODEL_PARAMS
from validation import validate_predictive_data
from logging_setup import get_logger

logger = get_logger(__name__)

CLASSES = ["none", "large_withdrawal", "dd_stop", "dormant"]
FEATURES = ["tenure_months", "product_count", "balance", "balance_tier",
            "liquidity_need_score", "dd_stability_score", "engagement_score",
            "dormancy_streak_months"]


def main():
    logger.info("03_predictive_model: starting (SEED=%s)", SEED)
    df = pd.read_csv(os.path.join(DATA_DIR, "predictive_data.csv"))
    try:
        validate_predictive_data(df)
    except Exception:
        logger.exception("03_predictive_model: input validation failed")
        raise

    df["region_id"] = df["region_id"].astype("category")
    region_dummies = pd.get_dummies(df["region_id"], prefix="region")
    X = pd.concat([df[FEATURES], region_dummies], axis=1)
    y = df["churn_mode"].map({c: i for i, c in enumerate(CLASSES)})

    X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
        X, y, df.index, test_size=TEST_SIZE, random_state=SEED, stratify=y
    )

    # NOTE on evaluation approach: churn_mode is heavily imbalanced (~89% "none").
    # Forcing balanced class weights + hard argmax classification looks
    # terrible here (precision collapses to ~5-10% because "none" is 89% of
    # the base rate) and isn't how a model like this would be used anyway --
    # in production you rank accounts by predicted probability and act on the
    # top slice your RM/offer capacity allows, exactly like the 30%-withdrawal
    # / top-50%-value cutoffs in the real project. So the primary evaluation
    # here is ranking quality (ROC-AUC, PR-AUC, lift at top decile) per class,
    # with the hard confusion matrix shown only as a secondary, illustrative
    # view.
    model = XGBClassifier(num_class=len(CLASSES), **PREDICTIVE_MODEL_PARAMS)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)

    print("=== Ranking-quality metrics (one-vs-rest, test set) ===")
    ranking_rows = []
    for i, c in enumerate(CLASSES):
        y_bin = (y_test == i).astype(int)
        auc = roc_auc_score(y_bin, y_proba[:, i])
        ap = average_precision_score(y_bin, y_proba[:, i])
        base_rate = y_bin.mean()
        top_decile_cut = np.quantile(y_proba[:, i], 0.90)
        in_top_decile = y_proba[:, i] >= top_decile_cut
        top_decile_rate = y_bin[in_top_decile].mean()
        lift = top_decile_rate / base_rate if base_rate > 0 else np.nan
        ranking_rows.append({"class": c, "base_rate": base_rate, "roc_auc": auc,
                              "pr_auc": ap, "top_decile_rate": top_decile_rate,
                              "lift_at_top_decile": lift})
        print(f"{c:>18s}  base_rate={base_rate:.4f}  ROC-AUC={auc:.3f}  "
              f"PR-AUC={ap:.3f}  top-decile lift={lift:.1f}x")
    ranking_df = pd.DataFrame(ranking_rows)
    ranking_df.to_csv(os.path.join(OUT_DIR, "ranking_metrics.csv"), index=False)

    print("\n=== Hard classification report (argmax, illustrative only) ===")
    report = classification_report(y_test, y_pred, target_names=CLASSES, digits=3)
    print(report)
    with open(os.path.join(OUT_DIR, "classification_report.txt"), "w") as f:
        f.write(report)

    cm = confusion_matrix(y_test, y_pred, normalize="true")
    fig, ax = plt.subplots(figsize=(5.5, 5))
    im = ax.imshow(cm, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(len(CLASSES))); ax.set_xticklabels(CLASSES, rotation=30, ha="right")
    ax.set_yticks(range(len(CLASSES))); ax.set_yticklabels(CLASSES)
    ax.set_xlabel("Predicted"); ax.set_ylabel("Actual")
    ax.set_title("Confusion matrix (row-normalized)")
    for i in range(len(CLASSES)):
        for j in range(len(CLASSES)):
            ax.text(j, i, f"{cm[i, j]:.2f}", ha="center", va="center",
                     color="white" if cm[i, j] > 0.5 else "black", fontsize=9)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "confusion_matrix.png"), dpi=150)
    plt.close(fig)

    importances = pd.Series(model.feature_importances_, index=X.columns).sort_values(ascending=False).head(10)
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    ax.barh(importances.index[::-1], importances.values[::-1], color="#2C4870")
    ax.set_xlabel("XGBoost feature importance (gain)")
    ax.set_title("Top drivers of churn-mode prediction")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "feature_importance.png"), dpi=150)
    plt.close(fig)

    scores_df = df.loc[idx_test, ["account_id", "region_id", "value_score", "churn_mode"]].copy()
    for i, c in enumerate(CLASSES):
        scores_df[f"proba_{c}"] = y_proba[:, i]
    scores_df["predicted_mode"] = [CLASSES[i] for i in y_pred]
    scores_df.to_csv(os.path.join(OUT_DIR, "predictive_scores.csv"), index=False)

    print(f"\nSaved: figures/confusion_matrix.png, figures/feature_importance.png, "
          f"output/predictive_scores.csv ({len(scores_df)} test-set accounts)")
    logger.info("03_predictive_model: done, wrote predictive_scores.csv (%d rows)", len(scores_df))


if __name__ == "__main__":
    main()
