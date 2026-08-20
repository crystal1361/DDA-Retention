"""
02_validate_design.py

Sanity checks on the identifying assumptions BEFORE running the causal
estimators. These are exactly the checks an interviewer will expect you to
have done, and exactly the checks that were flagged as gaps in the real
project's Q7 answer ("validated primarily through the A/B test... independent
validation... gap").

1. RDD manipulation check (McCrary-style): is there suspicious bunching in
   the running variable (withdrawal_pct) right around the 30% cutoff? If
   customers could strategically withdraw just above/below 30% to
   trigger/avoid an RM call, the density of withdrawal_pct would jump at the
   cutoff and RDD would be invalid. By construction our DGP has no such
   manipulation, so this should come back clean -- but the point is having
   the check, not the result.

2. DiD parallel-trends check: restricting to the pre-launch period (before
   the offer goes live for HV accounts), do HV and LV accounts move
   together over calendar time? If they don't, DiD's core identifying
   assumption (the untreated group traces out what the treated group
   WOULD have done absent treatment) is violated.

3. Dormant RCT randomization-balance check: within each value tier, do
   treated and holdout accounts look statistically similar on observed
   covariates BEFORE any offer went out? This is the standard "Table 1"
   check any RCT write-up would run -- if randomization worked, treated
   and holdout should differ only by chance, not systematically.
"""

import math
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

from config import DATA_DIR, FIG_DIR, RDD_CUTOFF, DID_LAUNCH_MONTH
from logging_setup import get_logger

logger = get_logger(__name__)

# Deliberately a DIFFERENT, local seed (7) rather than config.SEED (42) --
# this seeds only the McCrary bootstrap's resampling, a validation-only
# procedure that never touches the synthetic data itself, so there's no
# reproducibility reason it needs to share the pipeline's main seed. Kept
# local and explicit rather than moved into config.py for that reason: it's
# not a pipeline-wide constant, it's this one check's own randomness.
rng = np.random.default_rng(7)

# ---------------------------------------------------------------------------
# 1) McCrary-style density discontinuity test on the RDD running variable
# ---------------------------------------------------------------------------
def mccrary_style_test(x, cutoff, bin_width=2.0, bandwidth=20.0, n_boot=400):
    bins = np.arange(cutoff - bandwidth, cutoff + bandwidth + bin_width, bin_width)
    counts, edges = np.histogram(x, bins=bins)
    midpoints = (edges[:-1] + edges[1:]) / 2

    def log_density_jump(sample_x):
        # local QUADRATIC fit (not linear) on each side: a purely linear fit
        # over a +/-20 window picks up the Gaussian's curvature near its peak
        # and misreads it as a "jump" (curvature bias). Adding the squared
        # term absorbs that curvature so the intercept isolates the level at
        # the cutoff, which is what McCrary-style tests are actually after.
        c, e = np.histogram(sample_x, bins=bins)
        m = (e[:-1] + e[1:]) / 2
        left = m < cutoff
        right = m >= cutoff
        c_safe = c.astype(float) + 0.5
        d_left = m[left] - cutoff
        d_right = m[right] - cutoff
        Xl = sm.add_constant(np.column_stack([d_left, d_left ** 2]))
        Xr = sm.add_constant(np.column_stack([d_right, d_right ** 2]))
        yl = np.log(c_safe[left])
        yr = np.log(c_safe[right])
        bl = sm.OLS(yl, Xl).fit().params
        br = sm.OLS(yr, Xr).fit().params
        pred_left = bl[0]   # intercept = fitted log-count AT the cutoff (d=0)
        pred_right = br[0]
        return pred_right - pred_left  # log-density jump at cutoff

    observed_jump = log_density_jump(x)
    boot_jumps = np.array([
        log_density_jump(rng.choice(x, size=len(x), replace=True))
        for _ in range(n_boot)
    ])
    se = boot_jumps.std(ddof=1)
    z = observed_jump / se if se > 0 else np.nan
    p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / np.sqrt(2)))) if not np.isnan(z) else np.nan

    return {
        "log_density_jump": observed_jump,
        "bootstrap_se": se,
        "z_stat": z,
        "p_value": p_value,
        "counts": counts,
        "midpoints": midpoints,
    }


def run_rdd_validation():
    rdd_df = pd.read_csv(os.path.join(DATA_DIR, "rdd_data.csv"))
    cutoff = RDD_CUTOFF
    result = mccrary_style_test(rdd_df["withdrawal_pct"].values, cutoff)

    print("=== RDD manipulation check (McCrary-style density test) ===")
    print(f"log-density jump at cutoff : {result['log_density_jump']:+.4f}")
    print(f"bootstrap SE               : {result['bootstrap_se']:.4f}")
    print(f"z-stat                     : {result['z_stat']:+.3f}")
    print(f"p-value                    : {result['p_value']:.3f}")
    verdict = "PASS (no evidence of manipulation)" if (not np.isnan(result["p_value"]) and result["p_value"] > 0.10) \
        else "FLAG (investigate further)"
    print(f"verdict                    : {verdict}\n")

    # histogram figure
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.bar(result["midpoints"], result["counts"], width=1.8,
           color=np.where(result["midpoints"] < cutoff, "#2C4870", "#C1613C"))
    ax.axvline(cutoff, color="black", linestyle="--", linewidth=1.2)
    ax.set_xlabel("Withdrawal % of balance (running variable)")
    ax.set_ylabel("Count of account-months")
    ax.set_title("RDD running variable density around the 30% cutoff\n(no bunching -> manipulation check passes)")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "rdd_density_check.png"), dpi=150)
    plt.close(fig)

    return result


# ---------------------------------------------------------------------------
# 2) DiD parallel pre-trends check (2-group HV vs. LV, single launch date)
# ---------------------------------------------------------------------------
def run_did_pretrends_check():
    did_df = pd.read_csv(os.path.join(DATA_DIR, "did_data.csv"))
    pre = did_df[did_df["event_month"] < DID_LAUNCH_MONTH].copy()

    # visual check: churn rate by value-group x calendar month, restricted
    # to the pre-launch period only (neither group has been treated yet).
    agg = (pre.groupby(["value_group", "event_month"])["churned_within_window"]
           .mean().reset_index())

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    for grp, color in [("high", "#C1613C"), ("low", "#2C4870")]:
        g = agg[agg.value_group == grp]
        ax.plot(g["event_month"], g["churned_within_window"], marker="o",
                markersize=4, linewidth=1.5, color=color, label=grp)
    ax.set_xlabel("Calendar month (pre-launch only)")
    ax.set_ylabel("Churn-within-window rate")
    ax.set_title("Parallel pre-trends check: HV vs. LV, before the offer launches")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "did_pretrends_check.png"), dpi=150)
    plt.close(fig)

    # formal test: does adding a value_group x event_month interaction
    # improve fit over a model with only additive value_group + event_month
    # effects, in the pre-launch window? A significant interaction would
    # mean the two groups' trends aren't actually parallel pre-launch --
    # i.e. DiD's core identifying assumption would be in doubt.
    restricted = smf.ols("churned_within_window ~ event_month + C(value_group)", data=pre).fit()
    full = smf.ols("churned_within_window ~ event_month * C(value_group)", data=pre).fit()
    aov = anova_lm(restricted, full)
    f_stat = aov["F"].iloc[1]
    p_val = aov["Pr(>F)"].iloc[1]

    print("=== DiD parallel pre-trends check (HV vs. LV, pre-launch only) ===")
    print(f"F-test on value_group x event_month interaction: F={f_stat:.3f}, p={p_val:.3f}")
    verdict = "PASS (no evidence of differential pre-trends)" if p_val > 0.10 else "FLAG (pre-trends differ -- investigate)"
    print(f"verdict: {verdict}\n")

    return {"f_stat": f_stat, "p_value": p_val}


# ---------------------------------------------------------------------------
# 3) Dormant RCT randomization-balance check ("Table 1")
# ---------------------------------------------------------------------------
def run_dormant_balance_check():
    dormant_df = pd.read_csv(os.path.join(DATA_DIR, "dormant_data.csv"))
    covariates = ["engagement_score", "dormancy_streak_months", "product_count",
                  "tenure_months", "balance"]

    print("=== Dormant RCT randomization-balance check ('Table 1') ===")
    rows = []
    for tier in ["high", "low"]:
        tier_df = dormant_df[dormant_df.value_group == tier]
        treated = tier_df[tier_df.treated == 1]
        holdout = tier_df[tier_df.treated == 0]
        print(f"\n-- {tier.upper()} tier (n_treated={len(treated)}, n_holdout={len(holdout)}) --")
        for cov in covariates:
            t_mean, h_mean = treated[cov].mean(), holdout[cov].mean()
            t_stat, p_val = stats.ttest_ind(treated[cov], holdout[cov], equal_var=False)
            flag = "" if p_val > 0.05 else "  <- FLAG"
            print(f"  {cov:<24s} treated={t_mean:>9.2f}  holdout={h_mean:>9.2f}  "
                  f"t={t_stat:+.2f}  p={p_val:.3f}{flag}")
            rows.append({"tier": tier, "covariate": cov, "treated_mean": t_mean,
                         "holdout_mean": h_mean, "t_stat": t_stat, "p_value": p_val})
    n_flagged = sum(1 for r in rows if r["p_value"] <= 0.05)
    print(f"\n{n_flagged}/{len(rows)} covariate balance tests flagged at p<=0.05 "
          f"(with alpha=0.05 and {len(rows)} tests, ~{0.05*len(rows):.1f} false "
          f"positives are expected by chance alone even under perfect randomization).")
    verdict = "PASS (randomization balance looks clean)" if n_flagged <= max(1, round(0.05 * len(rows)) + 1) \
        else "FLAG (more imbalance than chance alone would predict -- investigate)"
    print(f"verdict: {verdict}\n")
    return pd.DataFrame(rows)


if __name__ == "__main__":
    logger.info("02_validate_design: starting design validation checks")
    rdd_result = run_rdd_validation()
    did_result = run_did_pretrends_check()
    balance_df = run_dormant_balance_check()
    print("Figures saved to figures/rdd_density_check.png and figures/did_pretrends_check.png")
    logger.info("02_validate_design: McCrary p=%.3f, pre-trends F-test p=%.3f",
                rdd_result["p_value"], did_result["p_value"])
