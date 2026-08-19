"""
07_doubleml_dormant.py

The dormant / re-engagement play is the one intervention in this project with
NO design-based quasi-experiment behind it -- no threshold to run RDD on, no
staggered rollout to run DiD on. An ops team just... decided who to call,
based on a mix of signals. That's the realistic situation for a lot of
retention plays in practice, and it's exactly the situation Double Machine
Learning (Chernozhukov et al., 2018) is built for: when you can't lean on a
designed experiment, but you DO have a rich set of observed covariates you're
willing to assume capture the confounding ("selection on observables" /
unconfoundedness), DoubleML lets you use flexible ML models to adjust for
those covariates without having to hand-specify the right functional form
(e.g. guessing whether engagement_score and dormancy_streak_months enter
linearly, or interact, or whatever) -- and does so in a way (Neyman-orthogonal
score + cross-fitting) that stays valid for inference even though the
nuisance models are ML models, not simple parametric ones.

WHY THIS INTERVENTION, SPECIFICALLY, NEEDS THAT FLEXIBILITY:
By construction (see 01_generate_data.py's generate_dormant_dataset()), the
ops team's outreach rule and the true bad-outcome rate are both driven by the
SAME non-smooth "flagged" rule -- dormancy_streak_months >= 3, OR
(dormancy_streak_months in {1,2} AND engagement_score < 25) -- a couple of
IF/OR threshold branches, not a single smooth formula in the raw features.
A plain additive logistic-regression control can't represent that kind of
branching boundary (linear-in-X models draw one straight decision boundary;
this rule needs several). A tree-based ML model (XGBoost, used here, matching
what's already used for the predictive layer) represents this kind of
threshold rule natively -- trees split on thresholds -- without it having to
be hand-specified.

THIS EFFECT IS WEAKER EVIDENCE THAN THE RDD/DiD ONES -- SAID OUT LOUD:
DoubleML's validity rests on unconfoundedness: "we observed and included
every variable that jointly drives treatment and outcome." That assumption
CANNOT be tested from the data itself -- unlike RDD's no-manipulation
assumption (McCrary test) or DiD's parallel-trends assumption (pre-trends
F-test), both of which 02_validate_design.py actually checks. So the dormant
effect estimated here is flagged throughout the project (see
06_optimization.py's EFFECT_SOURCE) as lower-confidence than the RDD/DiD
effects, and the recommendation in 08_business_impact.py is to treat it as a
prioritization signal, not a number to bet the budget on without a follow-up
randomized pilot.

This script compares THREE estimates against the injected true effect:
  1. Naive difference in means (treated - untreated bad_outcome rate)
  2. A simple logistic regression with additive covariate controls
  3. DoubleML (Interactive Regression Model / IRM), with XGBoost as the
     nuisance learner for both the outcome model and the propensity model,
     5-fold x 5-repetition cross-fitting, score='ATTE'

WHY ATT ("effect on the treated"), NOT POPULATION-WIDE ATE:
The business question that actually matters is "how much did contacting the
accounts we actually decided to contact help", not "what would the average
effect be if we contacted literally everyone, including accounts that would
never realistically be flagged". Those are different quantities whenever the
treatment effect is heterogeneous across the population -- and here it very
much is (see 01_generate_data.py: the effect is concentrated among the
"flagged" accounts). DoubleML is run with score="ATTE" (average treatment
effect on the treated) to match this framing, and it's graded against the
TRUE average effect among treated accounts specifically (not the population
average), computed the same validation-only way as in 05_did_analysis.py.
"""

import json
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from xgboost import XGBClassifier
from doubleml import DoubleMLData, DoubleMLIRM
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

from config import (DATA_DIR, FIG_DIR, OUT_DIR, SEED, DOUBLEML_XGB_PARAMS,
                     DOUBLEML_N_FOLDS, DOUBLEML_N_REP, seed_everything)
from validation import validate_dormant_data
from logging_setup import get_logger

logger = get_logger(__name__)

COVARIATES = ["engagement_score", "dormancy_streak_months", "product_count",
              "tenure_months", "balance"]
TREATMENT = "reengagement_contact"
OUTCOME = "bad_outcome"


# ---------------------------------------------------------------------------
# 1) Naive difference in means -- the number a busy analyst pulls first
# ---------------------------------------------------------------------------
def naive_diff(df):
    treated_rate = df.loc[df[TREATMENT] == 1, OUTCOME].mean()
    untreated_rate = df.loc[df[TREATMENT] == 0, OUTCOME].mean()
    diff = treated_rate - untreated_rate
    print("=== 1) Naive difference in means ===")
    print(f"P(bad outcome | contacted)     = {treated_rate:.4f}")
    print(f"P(bad outcome | not contacted) = {untreated_rate:.4f}")
    print(f"Naive difference               = {diff:+.4f}")
    print("If this comes back near zero or POSITIVE, that's 'confounding by")
    print("indication': the ops team calls the accounts already MOST likely to")
    print("have a bad outcome, so raw comparison makes outreach look useless")
    print("or harmful even if it's genuinely helping.\n")
    return diff


# ---------------------------------------------------------------------------
# 2) Simple logistic regression with additive covariate controls -- the
#    "I controlled for confounders" answer most analysts reach for next,
#    included here specifically so DoubleML has a fair, standard baseline to
#    beat, not just the naive number.
# ---------------------------------------------------------------------------
def logistic_adjusted(df):
    formula = f"{OUTCOME} ~ {TREATMENT} + " + " + ".join(COVARIATES)
    model = smf.logit(formula, data=df).fit(disp=0)
    coef = model.params[TREATMENT]

    # Convert the logistic coefficient into an average marginal effect (AME)
    # on the probability scale, so it's directly comparable to the naive
    # difference and to DoubleML's ATT, both of which are probability-scale
    # numbers. AME = average over TREATED rows of [P(y=1|D=1,X) - P(y=1|D=0,X)]
    # using the fitted model, holding each row's own X fixed -- restricted to
    # the treated rows (not all rows) so this targets the same ATT quantity
    # DoubleML is being asked for, rather than a population-wide average.
    treated_rows = df[df[TREATMENT] == 1].copy()
    treated_rows[TREATMENT] = 1
    p1 = model.predict(treated_rows)
    treated_rows[TREATMENT] = 0
    p0 = model.predict(treated_rows)
    ame = (p1 - p0).mean()

    print("=== 2) Logistic regression, additive covariate controls ===")
    print(f"reengagement_contact coefficient (logit scale): {coef:+.4f}")
    print(f"Average marginal effect (probability scale)    : {ame:+.4f}")
    print("This controls for the covariates LINEARLY and ADDITIVELY -- it")
    print("cannot represent the branching (IF/OR threshold) flagged-account")
    print("rule that actually drives both treatment assignment and the")
    print("outcome, so confounding is left substantially uncorrected here --")
    print("notice the sign is still wrong, same as the naive comparison.\n")
    return ame


# ---------------------------------------------------------------------------
# 3) DoubleML -- Interactive Regression Model (binary treatment, ATT)
# ---------------------------------------------------------------------------
def doubleml_irm(df):
    dml_data = DoubleMLData(df, y_col=OUTCOME, d_cols=TREATMENT, x_cols=COVARIATES)

    # Same learner (XGBoost) used for BOTH nuisance functions:
    #   ml_g: E[outcome | X, D]  -- the outcome regression
    #   ml_m: E[treatment | X]   -- the propensity score
    # Using a classifier (not a regressor) for both because both the outcome
    # and the treatment are binary here -- DoubleML calls predict_proba
    # under the hood when it detects a classifier.
    # Shallow, lightly-regularized trees -- this is a 5-covariate problem,
    # not a wide feature set, so a deep/complex learner would mostly fit
    # noise. reg_lambda adds L2 shrinkage on leaf weights, subsample /
    # colsample add a bit of extra randomness per tree -- standard moves to
    # keep a boosted-tree nuisance model from overfitting on a modest
    # (n=10,000) sample.
    ml_g = XGBClassifier(**DOUBLEML_XGB_PARAMS)
    ml_m = XGBClassifier(**DOUBLEML_XGB_PARAMS)

    dml_irm = DoubleMLIRM(dml_data, ml_g=ml_g, ml_m=ml_m,
                           n_folds=DOUBLEML_N_FOLDS, n_rep=DOUBLEML_N_REP, score="ATTE")
    # Cross-fitting happens inside .fit(): the data is split into 5 folds;
    # for each fold, the nuisance models (ml_g, ml_m) are trained on the
    # OTHER 4 folds and used to predict on the held-out fold. This is what
    # stops the ML models from overfitting their own training data and
    # biasing the effect estimate -- the model never scores the same rows
    # it was fit on. n_rep=5 repeats the whole cross-fitting process 5 times
    # with different random fold splits and averages the results, which
    # reduces the extra estimation noise that comes from any ONE random
    # split being a bit lucky or unlucky -- a standard DoubleML recommendation
    # when the sample size makes a single split noisy.
    #
    # REPRODUCIBILITY NOTE: the fold splits above are drawn from numpy's
    # LEGACY global RandomState (via sklearn's KFold(shuffle=True) internally),
    # not from the modern Generator API used elsewhere in this project. Every
    # explicit random_state you can see in this file (in DOUBLEML_XGB_PARAMS)
    # only pins the XGBoost nuisance models -- it does NOT pin which rows land
    # in which cross-fitting fold. That stream is seeded once, in this
    # script's __main__ block, via config.seed_everything(SEED) -- see that
    # call for why it has to happen there and not here.
    dml_irm.fit()

    att = dml_irm.coef[0]
    se = dml_irm.se[0]
    ci = dml_irm.confint().values[0]

    print("=== 3) DoubleML (IRM, XGBoost nuisance models, 5x5-fold cross-fitting, ATTE) ===")
    print(f"ATT estimate : {att:+.4f}")
    print(f"Std. error   : {se:.4f}")
    print(f"95% CI       : [{ci[0]:+.4f}, {ci[1]:+.4f}]")
    print("This lets XGBoost -- not a hand-specified linear formula -- learn")
    print("the branching flagged-account rule that jointly predicts treatment")
    print("assignment and the outcome, then combines the two fitted models'")
    print("RESIDUALS (partialling-out) to isolate the treatment effect on the")
    print("treated. Cross-fitting keeps the resulting confidence interval")
    print("valid despite using flexible ML models for the nuisance functions.\n")
    return {"att": float(att), "se": float(se), "ci_low": float(ci[0]), "ci_high": float(ci[1])}


def diagnostic_figure(naive, logit_ame, dml_result, true_att, save_path):
    labels = ["Naive\ndifference", "Logistic\n(additive controls)",
              "DoubleML\n(XGBoost, cross-fit)"]
    values = [naive, logit_ame, dml_result["att"]]
    colors = ["#C1613C", "#5B6B8C", "#2C4870"]

    fig, ax = plt.subplots(figsize=(7, 4.8))
    bars = ax.bar(labels, values, color=colors)
    for b, v in zip(bars, values):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:+.3f}",
                 ha="center", va="bottom" if v >= 0 else "top", fontsize=10)
    # DoubleML's own 95% CI, shown as an error bar on its bar -- the other
    # two methods don't get error bars here because the point being made is
    # about POINT ESTIMATE bias, not about comparing uncertainty across
    # methods with very different assumptions.
    ax.errorbar(2, dml_result["att"],
                 yerr=[[dml_result["att"] - dml_result["ci_low"]],
                       [dml_result["ci_high"] - dml_result["att"]]],
                 fmt="none", ecolor="black", capsize=5, linewidth=1.3)
    ax.axhline(true_att, color="black", linestyle="--", linewidth=1.2,
                label=f"True injected ATT ({true_att:+.3f})")
    ax.axhline(0, color="gray", linewidth=0.8)
    ax.set_ylabel("Effect on P(bad outcome)")
    ax.set_title("Dormant re-engagement: naive comparison is confounded\n"
                  "by construction -- DoubleML recovers the true effect")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    logger.info("07_doubleml_dormant: starting (SEED=%s)", SEED)
    # Seed BOTH RNG systems before anything random happens in this script --
    # in particular before DoubleMLIRM.fit() below, whose cross-fitting fold
    # splits draw from the legacy global RandomState that seed_everything()
    # sets (np.random.seed). This is the fix for the run-to-run drift this
    # script used to show even with SEED "set" everywhere that XGBoost could
    # see it -- the fold-splitting itself was never actually pinned down.
    seed_everything(SEED)

    df = pd.read_csv(os.path.join(DATA_DIR, "dormant_data.csv"))
    try:
        validate_dormant_data(df, treatment_col=TREATMENT)
    except Exception:
        logger.exception("07_doubleml_dormant: input validation failed")
        raise

    with open(os.path.join(DATA_DIR, "ground_truth.json")) as f:
        truth = json.load(f)
    # True ATT: average true individual effect among TREATED rows only
    # (see the module docstring for why ATT, not population ATE, is the
    # right target here).
    true_att = df.loc[df[TREATMENT] == 1, "true_effect_prob"].mean()

    naive = naive_diff(df)
    logit_ame = logistic_adjusted(df)
    dml_result = doubleml_irm(df[[OUTCOME, TREATMENT] + COVARIATES].copy())

    print("=== Grading all three against injected ground truth ===")
    print(f"True ATT (probability scale, treated accounts only) : {true_att:+.4f}")
    print(f"Naive difference                         : {naive:+.4f}  (off by {naive - true_att:+.4f})")
    print(f"Logistic (additive controls)             : {logit_ame:+.4f}  (off by {logit_ame - true_att:+.4f})")
    print(f"DoubleML (XGBoost, cross-fit)             : {dml_result['att']:+.4f}  "
          f"(off by {dml_result['att'] - true_att:+.4f})")

    diagnostic_figure(naive, logit_ame, dml_result, true_att,
                       os.path.join(FIG_DIR, "doubleml_dormant.png"))

    summary = {
        "true_att_prob_scale": float(true_att),
        "naive_diff": float(naive),
        "logistic_ame": float(logit_ame),
        "doubleml_att": dml_result["att"],
        "doubleml_se": dml_result["se"],
        "doubleml_ci_low": dml_result["ci_low"],
        "doubleml_ci_high": dml_result["ci_high"],
        "true_effect_logit_injected": truth["dormant_true_effect_logit"],
        "note": "Selection-on-observables identification -- weaker than the "
                "RDD/DiD designs elsewhere in this project because "
                "unconfoundedness cannot be tested from the data. Treat as a "
                "prioritization signal, not a validated effect size.",
    }
    with open(os.path.join(OUT_DIR, "doubleml_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print("\nSaved figures/doubleml_dormant.png, output/doubleml_summary.json")
    logger.info("07_doubleml_dormant: done, DoubleML ATT=%+.4f [%+.4f, %+.4f], true=%+.4f",
                dml_result["att"], dml_result["ci_low"], dml_result["ci_high"], true_att)
