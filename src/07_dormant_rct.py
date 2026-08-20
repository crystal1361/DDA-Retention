"""
07_dormant_rct.py

The dormant / re-engagement play, REDESIGNED as a genuine randomized
holdout instead of an observational (DoubleML) problem (see
01_generate_data.py's generate_dormant_dataset() docstring for the full
design rationale, and README/deck for why this replaced DoubleML).

DESIGN: two separate plays, one per value tier, each with its own small
randomized holdout --
  - High-value (HV) accounts that get flagged as dormant-risk: 90% receive
    a 90-day / 5%-cashback-on-grocery-spend offer ("cashback"); 10% are
    randomly held out (no offer at all).
  - Low-value (LV) accounts that get flagged: 90% receive an SMS/email
    reminder ("sms"); 10% are randomly held out.
The two tiers are NEVER pooled into one comparison -- doing so would
confound "which offer is more effective" with "which tier is inherently
lower-risk", since HV and LV accounts differ on both dimensions by
construction (see 01_generate_data.py). Each tier's own randomized holdout
is the ONLY valid control for that tier's own offer.

Because treatment is RANDOMIZED within each tier (not selected by an ops
team based on observed signals), this is a real RCT: identification does
NOT rest on an untestable "we controlled for every confounder" assumption
the way the DoubleML version did. That's a genuine identification
upgrade, not just a simpler estimator -- it's the reason dormant moves
from "lower-confidence, prioritization signal only" to "high confidence"
in 06_optimization.py / 08_business_impact.py.

Estimator: a two-proportion z-test per tier (bad_outcome rate: treated vs.
that tier's own holdout). This is the textbook RCT analysis -- no covariate
adjustment needed for an unbiased estimate (randomization already balances
covariates in expectation; 02_validate_design.py checks that balance
actually held here), though we still report it because it's what an
interviewer will expect you to know how to compute by hand.
"""

import json
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

from config import DATA_DIR, FIG_DIR, OUT_DIR
from validation import validate_dormant_data
from logging_setup import get_logger

logger = get_logger(__name__)

OUTCOME = "bad_outcome"


def two_proportion_ztest(treated_outcomes, holdout_outcomes, label):
    """Textbook two-proportion z-test, computed by hand (not just called
    from a library) so every number in this function is traceable to the
    SE -> z -> p formula an interviewer might ask you to derive on a
    whiteboard.

        p1, p2       : observed bad-outcome rate in each arm
        p_pool       : pooled rate, used for the z-test's SE (the test
                        statistic assumes the null p1 == p2, so it pools
                        both arms' data to estimate that single common rate)
        SE_pool      : sqrt(p_pool * (1-p_pool) * (1/n1 + 1/n2))
        z            : (p1 - p2) / SE_pool
        SE_unpooled  : sqrt(p1(1-p1)/n1 + p2(1-p2)/n2) -- used for the CI on
                        the DIFFERENCE itself, not the pooled null test (the
                        standard convention: pooled SE for the test, unpooled
                        SE for the interval).
    """
    x1, n1 = int(treated_outcomes.sum()), len(treated_outcomes)
    x2, n2 = int(holdout_outcomes.sum()), len(holdout_outcomes)
    p1, p2 = x1 / n1, x2 / n2
    diff = p1 - p2

    p_pool = (x1 + x2) / (n1 + n2)
    se_pool = np.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    z = diff / se_pool
    p_value = 2 * (1 - stats.norm.cdf(abs(z)))

    se_unpooled = np.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    ci_low = diff - 1.96 * se_unpooled
    ci_high = diff + 1.96 * se_unpooled

    print(f"=== {label}: two-proportion z-test ===")
    print(f"Treated : n={n1:>5}  bad_outcome rate={p1:.4f}")
    print(f"Holdout : n={n2:>5}  bad_outcome rate={p2:.4f}")
    print(f"Difference (treated - holdout) = {diff:+.4f}")
    print(f"pooled p̄={p_pool:.4f}  SE_pool={se_pool:.4f}  z={z:+.3f}  p={p_value:.2e}")
    print(f"95% CI on the difference (unpooled SE): [{ci_low:+.4f}, {ci_high:+.4f}]\n")

    return {"n_treated": n1, "n_holdout": n2, "p_treated": p1, "p_holdout": p2,
            "diff": diff, "se_pool": se_pool, "z": z, "p_value": p_value,
            "ci_low": ci_low, "ci_high": ci_high}


def run_tier_rct(df, tier, offer_type, label):
    tier_df = df[df.value_group == tier]
    treated = tier_df[tier_df.offer_type == offer_type][OUTCOME]
    holdout = tier_df[tier_df.offer_type == "none"][OUTCOME]
    return two_proportion_ztest(treated, holdout, label)


def unequal_allocation_backup(df, tier, offer_type, label):
    """Backup-slide computation: WHY doesn't a 90/10 split (versus a 50/50
    split) cripple our ability to detect the effect? Holding the SAME total
    n and the SAME observed rates fixed, recompute SE / z / power under a
    few different treated:holdout splits, using the 'design effect' shortcut
    -- for a two-proportion test at FIXED total n, unequal allocation
    inflates the variance of the difference by a factor of
        1 / (4 * r * (1 - r))
    relative to the 50/50 case, where r = the treated-arm share of n. r=0.5
    gives a design effect of exactly 1 (no penalty); r=0.9 (this project's
    actual split) gives 1/(4*0.9*0.1) = 2.78x the variance a 50/50 split of
    the SAME total n would have had -- worse, but only ~1.67x wider SE
    (sqrt(2.78)), not a multiple-of-10 disaster, because holdout, though
    small in SHARE, still isn't small in absolute n (n_holdout in the ~500-
    600 range here) -- and it's the ABSOLUTE size of the smaller arm, not
    its share, that ultimately sets the floor on precision.
    """
    tier_df = df[df.value_group == tier]
    treated = tier_df[tier_df.offer_type == offer_type][OUTCOME]
    holdout = tier_df[tier_df.offer_type == "none"][OUTCOME]
    n_total = len(treated) + len(holdout)
    p_pool = (treated.sum() + holdout.sum()) / n_total
    effect = treated.mean() - holdout.mean()

    print(f"=== {label}: design-effect sensitivity (fixed total n={n_total}, "
          f"fixed observed effect={effect:+.4f}) ===")
    rows = []
    for r in [0.5, 0.7, 0.8, 0.9, 0.95]:
        n1 = int(round(n_total * r))
        n2 = n_total - n1
        se = np.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
        z = effect / se
        design_effect = 1 / (4 * r * (1 - r))
        power = stats.norm.cdf(abs(z) - 1.96)  # approx, two-sided alpha=0.05
        rows.append({"treated_share": r, "n_treated": n1, "n_holdout": n2,
                      "se": se, "z": z, "design_effect": design_effect, "power": power})
        marker = "  <- actual design" if abs(r - 0.9) < 1e-6 else ""
        print(f"treated_share={r:.2f}  n_treated={n1:>5}  n_holdout={n2:>5}  "
              f"SE={se:.4f}  z={z:+.2f}  design_effect={design_effect:.2f}x  "
              f"power~={power:.3f}{marker}")
    print()
    return pd.DataFrame(rows)


def diagnostic_figure(hv_result, lv_result, truth, save_path):
    labels = ["HV: cashback\nvs. holdout", "LV: SMS\nvs. holdout"]
    diffs = [hv_result["diff"], lv_result["diff"]]
    true_effects = [truth["hv_true"], truth["lv_true"]]
    ci_err = [
        [hv_result["diff"] - hv_result["ci_low"], lv_result["diff"] - lv_result["ci_low"]],
        [hv_result["ci_high"] - hv_result["diff"], lv_result["ci_high"] - lv_result["diff"]],
    ]

    fig, ax = plt.subplots(figsize=(7, 4.8))
    x = np.arange(len(labels))
    bars = ax.bar(x, diffs, color=["#C1613C", "#2C4870"], width=0.5)
    ax.errorbar(x, diffs, yerr=ci_err, fmt="none", ecolor="black", capsize=6, linewidth=1.3)
    for xi, t in zip(x, true_effects):
        ax.plot([xi - 0.28, xi + 0.28], [t, t], color="black", linestyle="--", linewidth=1.2)
    ax.axhline(0, color="gray", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Effect on P(bad outcome)  [treated - randomized holdout]")
    ax.set_title("Dormant re-engagement: two tier-specific randomized holdouts\n"
                  "(dashed line = true injected effect; error bars = 95% CI)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    logger.info("07_dormant_rct: starting")
    df = pd.read_csv(os.path.join(DATA_DIR, "dormant_data.csv"))
    try:
        validate_dormant_data(df, treatment_col="treated")
    except Exception:
        logger.exception("07_dormant_rct: input validation failed")
        raise

    with open(os.path.join(DATA_DIR, "ground_truth.json")) as f:
        truth = json.load(f)

    hv_result = run_tier_rct(df, "high", "cashback", "HV tier: cashback offer")
    lv_result = run_tier_rct(df, "low", "sms", "LV tier: SMS reminder")

    unequal_allocation_backup(df, "high", "cashback", "HV tier")
    unequal_allocation_backup(df, "low", "sms", "LV tier")

    # True average effect among each tier's TREATED accounts, read directly
    # from true_effect_prob (same validation-only ground-truth approach used
    # in 04_rdd_analysis.py / 05_did_analysis.py) -- exact, not approximated.
    hv_true = df[(df.value_group == "high") & (df.offer_type == "cashback")]["true_effect_prob"].mean()
    lv_true = df[(df.value_group == "low") & (df.offer_type == "sms")]["true_effect_prob"].mean()

    print("=== Grading against injected ground truth ===")
    print(f"HV cashback: true effect={hv_true:+.4f}  estimated diff={hv_result['diff']:+.4f}  "
          f"(off by {hv_result['diff'] - hv_true:+.4f})")
    print(f"LV SMS     : true effect={lv_true:+.4f}  estimated diff={lv_result['diff']:+.4f}  "
          f"(off by {lv_result['diff'] - lv_true:+.4f})")

    diagnostic_figure(hv_result, lv_result, {"hv_true": hv_true, "lv_true": lv_true},
                       os.path.join(FIG_DIR, "dormant_rct.png"))

    summary = {
        "hv_cashback": {**hv_result, "true_effect_prob_scale": float(hv_true)},
        "lv_sms": {**lv_result, "true_effect_prob_scale": float(lv_true)},
        "note": "Randomized within-tier holdout -- identification does not "
                "rest on an unconfoundedness assumption (unlike the prior "
                "DoubleML version of this play), so this is treated as "
                "HIGH-confidence evidence, on par with RDD/DiD, not a "
                "prioritization signal only.",
    }
    with open(os.path.join(OUT_DIR, "dormant_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print("\nSaved figures/dormant_rct.png, output/dormant_summary.json")
    logger.info("07_dormant_rct: done, HV diff=%+.4f (true %+.4f), LV diff=%+.4f (true %+.4f)",
                hv_result["diff"], hv_true, lv_result["diff"], lv_true)
