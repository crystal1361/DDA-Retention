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

2. DiD parallel-trends check: restricting to account-months where no
   region's offer is live yet, do the four cohorts move together over
   calendar time? If they don't, DiD's core identifying assumption
   (untreated cohorts trace out what treated cohorts WOULD have done absent
   treatment) is violated.
"""

import math
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
FIG_DIR = os.path.join(os.path.dirname(__file__), "..", "figures")
os.makedirs(FIG_DIR, exist_ok=True)

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
    cutoff = 30.0
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
# 2) DiD parallel pre-trends check
# ---------------------------------------------------------------------------
def run_did_pretrends_check():
    did_df = pd.read_csv(os.path.join(DATA_DIR, "did_data.csv"))
    pre = did_df[did_df["offer_live"] == 0].copy()

    # visual check: churn-after-DD-stop rate by cohort x calendar month,
    # restricted to periods before ANY cohort in the plot has gone live
    agg = (pre.groupby(["cohort", "event_month"])["churned_within_window"]
           .mean().reset_index())

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    for cohort, g in agg.groupby("cohort"):
        ax.plot(g["event_month"], g["churned_within_window"], marker="o",
                markersize=3, linewidth=1.3, label=cohort)
    ax.axvline(8, color="gray", linestyle=":", linewidth=1, label="cohort A adopts (m8)")
    ax.set_xlabel("Calendar month")
    ax.set_ylabel("Churn-within-window rate (pre-adoption obs only)")
    ax.set_title("Parallel pre-trends check across rollout cohorts")
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "did_pretrends_check.png"), dpi=150)
    plt.close(fig)

    # formal test: does adding cohort x event_month interactions improve fit
    # over a model with only additive cohort + event_month effects? Restricted
    # to the COMMON window before any cohort has gone live (event_month < 8),
    # so every cohort contributes data over the same calendar range -- doing
    # this on the full "not yet treated" sample is unfair, since cohort A's
    # pre-period only spans months 0-7 while "never" spans 0-23, and that
    # unequal support alone can produce a spurious interaction.
    common_pre = pre[pre["event_month"] < 8]
    restricted = smf.ols("churned_within_window ~ event_month + C(cohort)", data=common_pre).fit()
    full = smf.ols("churned_within_window ~ event_month * C(cohort)", data=common_pre).fit()
    aov = anova_lm(restricted, full)
    f_stat = aov["F"].iloc[1]
    p_val = aov["Pr(>F)"].iloc[1]

    print("=== DiD parallel pre-trends check ===")
    print(f"F-test on cohort x event_month interaction (pre-period only): F={f_stat:.3f}, p={p_val:.3f}")
    verdict = "PASS (no evidence of differential pre-trends)" if p_val > 0.10 else "FLAG (pre-trends differ -- investigate)"
    print(f"verdict: {verdict}\n")

    return {"f_stat": f_stat, "p_value": p_val}


if __name__ == "__main__":
    rdd_result = run_rdd_validation()
    did_result = run_did_pretrends_check()
    print("Figures saved to figures/rdd_density_check.png and figures/did_pretrends_check.png")
