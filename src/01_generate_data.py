"""
01_generate_data.py

Synthetic data generator for the "DDA Retention Decision Engine" demo project.

WHY SYNTHETIC (not real / not downloaded):
- Real account-level panel data with a designed quasi-experiment (RDD running
  variable + staggered DiD rollout) is not publicly available for privacy
  reasons, and using employer data is off the table.
- Building the data-generating process (DGP) ourselves lets us bake in a KNOWN
  ground-truth causal effect for both the RDD and the DiD design. That means
  we can validate that our estimators actually recover the true effect before
  trusting them on a real problem -- this is standard practice in causal
  inference methodology work / portfolio projects, and it's a much stronger
  thing to say in an interview than "I ran a package on some CSV."

Three analytic samples are generated, matching how you'd actually study these
three questions in practice (not one giant table):
  1. predictive_data.csv   - cross-sectional account snapshot -> multi-class
                              churn-mode prediction (mirrors the real project)
  2. rdd_data.csv           - account-month withdrawal events -> RDD around the
                              30%-of-balance RM-outreach trigger
  3. did_data.csv           - account-level DD-stop events -> staggered-rollout
                              DiD around the "$100 for 2 DDs" retention offer

All "true" effect sizes are defined once in TRUTH and reused later to check
whether RDD / DiD recover them.
"""

import numpy as np
import pandas as pd
import json
import os

SEED = 42
rng = np.random.default_rng(SEED)

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Ground-truth effects baked into the DGP (kept in one place so later scripts
# can grade the RDD/DiD estimators against them).
# ---------------------------------------------------------------------------
TRUTH = {
    "rdd_cutoff": 30.0,                     # withdrawal % of balance that triggers RM outreach
    "rdd_true_effect_logit": -0.90,         # jump in logit(churn_next_month) caused by RM contact
    "did_adoption_months": {                # calendar month (0-23) each region's offer goes live
        "R00": 8, "R01": 8, "R02": 8,       # cohort A
        "R03": 14, "R04": 14, "R05": 14,    # cohort B
        "R06": 20, "R07": 20,               # cohort C
        "R08": None, "R09": None,           # never-treated (within the 24-month window)
    },
    "did_true_effect_logit_max": -0.90,     # steady-state effect once the offer is fully ramped up
    "did_ramp_months": 3,                   # months for the effect to ramp from 0 to steady-state
}

with open(os.path.join(OUT_DIR, "ground_truth.json"), "w") as f:
    json.dump(TRUTH, f, indent=2)


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


# ---------------------------------------------------------------------------
# 1) Predictive dataset: multi-class churn-mode target
# ---------------------------------------------------------------------------
def generate_predictive_dataset(n=40_000):
    tenure_months = rng.gamma(shape=2.2, scale=28, size=n).clip(1, 300)
    product_count = rng.choice([1, 2, 3, 4, 5, 6], size=n,
                                p=[0.28, 0.27, 0.20, 0.14, 0.08, 0.03])
    balance = np.exp(rng.normal(8.2, 1.1, size=n))          # lognormal, ~$3k median
    region_id = rng.choice([f"R{i:02d}" for i in range(10)], size=n)

    # latent behavioral drivers (unobserved "propensity" style features)
    liquidity_need_score = rng.normal(50, 20, size=n).clip(0, 100)   # drives large-withdrawal risk
    dd_stability_score = rng.normal(50, 20, size=n).clip(0, 100)     # higher = more stable DD
    engagement_score = rng.normal(50, 20, size=n).clip(0, 100)       # higher = more engaged/active
    dormancy_streak_months = rng.poisson(0.4, size=n).clip(0, 6)

    balance_tier = pd.qcut(balance, 5, labels=False)  # 0-4
    value_score = (product_count * 3 + tenure_months * 0.05 + balance_tier * 2)

    # class-specific logits, "none" (stay) is the reference category (logit 0).
    # Intercepts are set low so the overall churn rate lands in the low
    # single digits (the real project's baseline was ~0.8%; we target
    # somewhat higher, ~4-6%, so there are enough positive examples of each
    # mode to train/evaluate a classifier on -- documented as a deliberate
    # modeling choice, not a claim about the true institutional churn rate).
    logit_large_wd = (-5.4 + 0.045 * liquidity_need_score
                       - 0.08 * product_count - 0.01 * tenure_months
                       + rng.normal(0, 0.4, n))
    logit_dd_stop = (-5.6 + 0.045 * (100 - dd_stability_score)
                      - 0.10 * product_count - 0.005 * tenure_months
                      + rng.normal(0, 0.4, n))
    logit_dormant = (-5.4 + 0.045 * (100 - engagement_score)
                      - 0.05 * product_count + 0.25 * dormancy_streak_months
                      + rng.normal(0, 0.4, n))
    logit_none = np.zeros(n)

    logits = np.vstack([logit_none, logit_large_wd, logit_dd_stop, logit_dormant]).T
    probs = np.exp(logits) / np.exp(logits).sum(axis=1, keepdims=True)
    classes = np.array(["none", "large_withdrawal", "dd_stop", "dormant"])
    churn_mode = np.array([rng.choice(classes, p=probs[i]) for i in range(n)])

    df = pd.DataFrame({
        "account_id": [f"A{i:06d}" for i in range(n)],
        "region_id": region_id,
        "tenure_months": tenure_months.round(1),
        "product_count": product_count,
        "balance": balance.round(2),
        "balance_tier": balance_tier,
        "liquidity_need_score": liquidity_need_score.round(1),
        "dd_stability_score": dd_stability_score.round(1),
        "engagement_score": engagement_score.round(1),
        "dormancy_streak_months": dormancy_streak_months,
        "value_score": value_score.round(2),
        "churn_mode": churn_mode,
    })
    return df


# ---------------------------------------------------------------------------
# 2) RDD dataset: withdrawal events around the 30% trigger
# ---------------------------------------------------------------------------
def generate_rdd_dataset(n=15_000):
    cutoff = TRUTH["rdd_cutoff"]

    # running variable: withdrawal as % of balance in the event month.
    # Truncated-normal-ish, centered near the cutoff so we have good density
    # on both sides (needed for local linear regression). No bunching is
    # introduced by construction -> McCrary test should come back clean,
    # consistent with "withdrawal size isn't something customers manipulate
    # to dodge/trigger an RM call."
    withdrawal_pct = rng.normal(30, 18, size=n)
    withdrawal_pct = withdrawal_pct.clip(0, 95)

    tenure_months = rng.gamma(shape=2.2, scale=28, size=n).clip(1, 300)
    product_count = rng.choice([1, 2, 3, 4, 5, 6], size=n,
                                p=[0.28, 0.27, 0.20, 0.14, 0.08, 0.03])
    balance = np.exp(rng.normal(8.2, 1.1, size=n))

    treated = (withdrawal_pct >= cutoff).astype(int)

    # smooth baseline (no-treatment potential outcome): risk rises continuously
    # with withdrawal size. This is the confound -- naive treated-vs-control
    # comparison is biased because bigger withdrawals are already higher risk
    # BEFORE any RM outreach. RDD isolates the effect by comparing only the
    # narrow window right around the cutoff.
    baseline_logit = (-2.1 + 0.028 * withdrawal_pct
                       - 0.008 * tenure_months - 0.04 * product_count
                       + rng.normal(0, 0.35, n))

    final_logit = baseline_logit + treated * TRUTH["rdd_true_effect_logit"]
    churn_next_month = rng.binomial(1, sigmoid(final_logit))

    df = pd.DataFrame({
        "account_id": [f"W{i:06d}" for i in range(n)],
        "withdrawal_pct": withdrawal_pct.round(2),
        "treated_rm_contact": treated,
        "tenure_months": tenure_months.round(1),
        "product_count": product_count,
        "balance": balance.round(2),
        "churn_next_month": churn_next_month,
    })
    return df


# ---------------------------------------------------------------------------
# 3) DiD dataset: DD-stop events, staggered offer rollout across regions
# ---------------------------------------------------------------------------
def generate_did_dataset(n=12_000):
    regions = list(TRUTH["did_adoption_months"].keys())
    region_id = rng.choice(regions, size=n)
    event_month = rng.integers(0, 24, size=n)  # calendar month (0-23) of the DD-stop event

    adoption_month = np.array([
        TRUTH["did_adoption_months"][r] if TRUTH["did_adoption_months"][r] is not None else 999
        for r in region_id
    ])
    offer_live = (event_month >= adoption_month).astype(int)

    tenure_months = rng.gamma(shape=2.2, scale=28, size=n).clip(1, 300)
    product_count = rng.choice([1, 2, 3, 4, 5, 6], size=n,
                                p=[0.28, 0.27, 0.20, 0.14, 0.08, 0.03])

    # region-level FIXED intercepts only (level shifts) -- deliberately NOT
    # interacted with event_month, so pre-trends stay parallel across cohorts
    # by construction. A common, gentle calendar-time trend is shared by
    # every region.
    region_fx = {r: v for r, v in zip(regions, rng.normal(0, 0.20, size=len(regions)))}
    region_effect = np.array([region_fx[r] for r in region_id])
    common_trend = -0.01 * event_month  # slow, shared decline in post-DD-stop churn risk over time

    baseline_logit = (-1.0 + common_trend + region_effect
                       - 0.03 * product_count - 0.006 * tenure_months
                       + rng.normal(0, 0.35, n))

    # DYNAMIC (ramping) treatment effect: the offer doesn't hit full strength
    # the instant it launches -- RM awareness, customer take-up, and workflow
    # kinks all take a few months to mature. months_since_adoption is 0 the
    # month the offer goes live, growing from there for treated obs.
    months_since_adoption = np.where(offer_live == 1, event_month - adoption_month, 0)
    ramp_frac = np.clip(months_since_adoption / TRUTH["did_ramp_months"], 0, 1)
    effect_logit = offer_live * ramp_frac * TRUTH["did_true_effect_logit_max"]

    final_logit = baseline_logit + effect_logit
    churned_within_window = rng.binomial(1, sigmoid(final_logit))

    cohort = np.where(adoption_month == 999, "never",
              np.where(adoption_month == 8, "cohortA_m8",
              np.where(adoption_month == 14, "cohortB_m14", "cohortC_m20")))

    df = pd.DataFrame({
        "account_id": [f"D{i:06d}" for i in range(n)],
        "region_id": region_id,
        "cohort": cohort,
        "event_month": event_month,
        "adoption_month": np.where(adoption_month == 999, np.nan, adoption_month),
        "offer_live": offer_live,
        "months_since_adoption": np.where(offer_live == 1, months_since_adoption, np.nan),
        "tenure_months": tenure_months.round(1),
        "product_count": product_count,
        "churned_within_window": churned_within_window,
    })
    return df


if __name__ == "__main__":
    pred_df = generate_predictive_dataset()
    rdd_df = generate_rdd_dataset()
    did_df = generate_did_dataset()

    pred_df.to_csv(os.path.join(OUT_DIR, "predictive_data.csv"), index=False)
    rdd_df.to_csv(os.path.join(OUT_DIR, "rdd_data.csv"), index=False)
    did_df.to_csv(os.path.join(OUT_DIR, "did_data.csv"), index=False)

    print("=== predictive_data.csv ===")
    print(pred_df["churn_mode"].value_counts(normalize=True).round(4))
    print(f"n = {len(pred_df)}\n")

    print("=== rdd_data.csv ===")
    print(f"n = {len(rdd_df)}, treated share = {rdd_df['treated_rm_contact'].mean():.3f}")
    naive_diff = (rdd_df.loc[rdd_df.treated_rm_contact == 1, "churn_next_month"].mean()
                  - rdd_df.loc[rdd_df.treated_rm_contact == 0, "churn_next_month"].mean())
    print(f"NAIVE (biased) treated-vs-control diff in churn_next_month: {naive_diff:+.4f}")
    print("(expect this to look WRONG/small or even positive -- that's the confound RDD fixes)\n")

    print("=== did_data.csv ===")
    print(did_df.groupby("cohort")["offer_live"].mean())
    print(f"n = {len(did_df)}\n")

    print("Ground truth written to data/ground_truth.json:")
    print(json.dumps(TRUTH, indent=2))
