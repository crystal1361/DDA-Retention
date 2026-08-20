"""
05_did_analysis.py

Does the "$100 for 2 direct deposits >= $500" offer reduce churn among
accounts that just stopped direct deposit?

REDESIGNED (see 01_generate_data.py's module docstring for the full
rationale): the offer launches for HIGH-VALUE (HV) accounts on a single
calendar month (DID_LAUNCH_MONTH); LOW-VALUE (LV) accounts never receive
it in-window. That is a plain 2-group / single-adoption-date DiD, not a
staggered rollout -- there is exactly one treated group and one
never-treated group, and the treated group's "post" period starts on the
same calendar month for every account in it. That deliberately avoids the
Goodman-Bacon (2021) staggered-adoption bias that a multi-cohort rollout
would introduce (an earlier version of this project did have staggered,
value-tier-prioritized waves, and needed a "clean-control" estimator to
correct for it -- that machinery is gone here because the design itself no
longer needs correcting for).

The estimator is the textbook 2x2 DiD:
    ATT = (post_HV - pre_HV) - (post_LV - pre_LV)
computed two ways that must agree: (1) directly from the four group means,
and (2) as the coefficient on offer_live in a regression that also absorbs
value-group and calendar-month fixed effects (equivalent to the 2x2
differencing, but gives us a standard error/p-value for inference "for
free").

IDENTIFICATION ASSUMPTION -- parallel trends: absent the offer, HV and LV
accounts' churn rates would have moved in parallel (not necessarily at the
same LEVEL -- HV accounts churn less overall regardless of any offer -- but
the same DIRECTION/SLOPE month to month). 02_validate_design.py tests this
directly on the pre-period (event_month < DID_LAUNCH_MONTH), where neither
group has been treated yet.

Graded against the true average post-launch effect implied by the DGP's
ramp function (the offer's effect phases in over ~3 months of
awareness/take-up lag, not an instant jump -- see the event-study plot).
"""

import json
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

from config import DATA_DIR, FIG_DIR, OUT_DIR, DID_LAUNCH_MONTH
from validation import validate_did_data
from logging_setup import get_logger

logger = get_logger(__name__)


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def two_by_two_did(df):
    """The DiD estimate computed the most literal way possible: four group
    means, differenced twice. No regression, no fixed effects -- this is
    the number every other estimate below should exactly reproduce, and
    it's the version that's easiest to defend on a whiteboard if asked
    "how does DiD actually work" in an interview."""
    print("=== 2x2 DiD (four group means) ===")
    hv = df[df.value_group == "high"]
    lv = df[df.value_group == "low"]

    pre_hv = hv[hv.event_month < DID_LAUNCH_MONTH]["churned_within_window"].mean()
    post_hv = hv[hv.event_month >= DID_LAUNCH_MONTH]["churned_within_window"].mean()
    pre_lv = lv[lv.event_month < DID_LAUNCH_MONTH]["churned_within_window"].mean()
    post_lv = lv[lv.event_month >= DID_LAUNCH_MONTH]["churned_within_window"].mean()

    hv_change = post_hv - pre_hv
    lv_change = post_lv - pre_lv
    att = hv_change - lv_change

    print(f"High-value (treated): pre={pre_hv:.4f}  post={post_hv:.4f}  change={hv_change:+.4f}")
    print(f"Low-value  (control): pre={pre_lv:.4f}  post={post_lv:.4f}  change={lv_change:+.4f}")
    print(f"DiD = (HV change) - (LV change) = {hv_change:+.4f} - ({lv_change:+.4f}) = {att:+.4f}\n")
    return {"pre_hv": pre_hv, "post_hv": post_hv, "pre_lv": pre_lv, "post_lv": post_lv, "att": att}


def regression_did(df):
    """Same estimate, via regression, with value-group and calendar-month
    fixed effects absorbed and an HC1 robust SE attached -- this is what
    lets us report a p-value / CI, not just a point estimate. The
    offer_live coefficient here should match two_by_two_did()'s att almost
    exactly (any tiny gap is float rounding), because with only 2 groups
    and 1 adoption date, offer_live IS the treated*post interaction --
    there's no additional cohort-averaging step for the regression to do
    differently."""
    print("=== Regression DiD (value-group FE + calendar-month FE, HC1 robust SE) ===")
    model = smf.ols("churned_within_window ~ offer_live + C(value_group) + C(event_month)",
                     data=df).fit(cov_type="HC1")
    coef = model.params["offer_live"]
    se = model.bse["offer_live"]
    p = model.pvalues["offer_live"]
    ci_low, ci_high = model.conf_int().loc["offer_live"]
    print(f"offer_live coefficient: {coef:+.4f}  (HC1 robust SE={se:.4f}, "
          f"95% CI [{ci_low:+.4f}, {ci_high:+.4f}], p={p:.4f})\n")
    return {"coef": coef, "se": se, "p": p, "ci_low": ci_low, "ci_high": ci_high}


def event_study_plot(df, save_path):
    """Two things in one plot: (1) do HV and LV move in parallel BEFORE
    the launch month (visual check backing 02_validate_design.py's formal
    pre-trends test), and (2) does the post-launch gap open up gradually
    over ~3 months (the ramp) rather than jumping instantly, which is what
    the DGP actually injects."""
    agg = (df.groupby(["value_group", "event_month"])["churned_within_window"]
           .mean().reset_index())

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    for grp, color, label in [("high", "#C1613C", "High-value (treated)"),
                               ("low", "#2C4870", "Low-value (control)")]:
        g = agg[agg.value_group == grp]
        ax.plot(g["event_month"], g["churned_within_window"], marker="o",
                 color=color, label=label)
    ax.axvline(DID_LAUNCH_MONTH - 0.5, color="black", linestyle="--", linewidth=1.2,
                label="Offer launch (HV only)")
    ax.set_xlabel("Calendar month")
    ax.set_ylabel("Churn-within-window rate")
    ax.set_title("DiD: HV vs. LV churn before/after the offer launches for HV\n"
                  "(pre-launch: should move in parallel -- see 02_validate_design.py)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)


def grade_against_ground_truth(df, two_by_two, reg_result):
    # True average post-launch effect, on the probability scale, averaged
    # over treated (offer_live==1) observations. Read directly from the
    # 'true_effect_prob' column 01_generate_data.py computed row-by-row --
    # exact, not an approximation borrowed from some other group's rate.
    treated = df[df["offer_live"] == 1].copy()
    true_effect_prob_scale = treated["true_effect_prob"].mean()

    print("=== Grading against injected ground truth ===")
    print(f"True average post-launch effect (probability scale) : {true_effect_prob_scale:+.4f}")
    print(f"2x2 DiD (four group means)                           : {two_by_two['att']:+.4f}  "
          f"(off by {two_by_two['att'] - true_effect_prob_scale:+.4f})")
    print(f"Regression DiD (offer_live coefficient)              : {reg_result['coef']:+.4f}  "
          f"(off by {reg_result['coef'] - true_effect_prob_scale:+.4f})")
    return true_effect_prob_scale


if __name__ == "__main__":
    logger.info("05_did_analysis: starting")
    df = pd.read_csv(os.path.join(DATA_DIR, "did_data.csv"))
    try:
        validate_did_data(df, value_col="value_group")
    except Exception:
        logger.exception("05_did_analysis: input validation failed")
        raise

    two_by_two = two_by_two_did(df)
    reg_result = regression_did(df)
    event_study_plot(df, os.path.join(FIG_DIR, "did_event_study.png"))
    true_effect = grade_against_ground_truth(df, two_by_two, reg_result)

    summary = {
        "did_2x2_pre_hv": two_by_two["pre_hv"],
        "did_2x2_post_hv": two_by_two["post_hv"],
        "did_2x2_pre_lv": two_by_two["pre_lv"],
        "did_2x2_post_lv": two_by_two["post_lv"],
        "did_2x2_att": two_by_two["att"],
        "did_regression_coef": reg_result["coef"],
        "did_regression_se": reg_result["se"],
        "did_regression_p": reg_result["p"],
        "did_regression_ci_low": reg_result["ci_low"],
        "did_regression_ci_high": reg_result["ci_high"],
        "true_effect_prob_scale": true_effect,
    }
    with open(os.path.join(OUT_DIR, "did_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSaved figures/did_event_study.png, output/did_summary.json")
    logger.info("05_did_analysis: done, 2x2 ATT=%+.4f, regression coef=%+.4f, true=%+.4f",
                two_by_two["att"], reg_result["coef"], true_effect)
