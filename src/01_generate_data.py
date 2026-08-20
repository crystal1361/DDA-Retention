"""
01_generate_data.py

Synthetic data generator for the "DDA Retention Decision Engine" project.

WHY SYNTHETIC (not real / not downloaded):
- Real account-level panel data with a designed quasi-experiment (RDD running
  variable + DiD launch + a randomized dormant holdout) is not publicly
  available for privacy reasons, and using employer data is off the table.
- Building the data-generating process (DGP) ourselves lets us bake in a KNOWN
  ground-truth causal effect for every design. That means we can validate
  that our estimators actually recover the true effect before trusting them
  on a real problem -- standard practice in causal inference methodology
  work / portfolio projects, and a much stronger thing to say in an
  interview than "I ran a package on some CSV."

WHO GETS ANY INTERVENTION AT ALL -- THE SAME LINE, DRAWN ONCE, USED
EVERYWHERE (HV_VALUE_PERCENTILE in config.py):
Every one of the three plays below concentrates the real, funded
intervention on the top 50% of accounts by account_value, and gives the
bottom 50% either nothing or a near-free generic touch. This is not a
statistical choice -- it's the same ROI logic the real project used (see
项目二DDA存款流失挽留.docx Q4: "ranked by value score and drew the line
where the expected return on a retention touch dropped below its cost...
For the top half... the deposits and lifetime value we'd protect clearly
outweighed the cost. Below that the economics got thin, so those accounts
got low-cost automated nudges instead of funded offers"). Drawing this line
ONCE, in config.py, and reusing it for RDD/DiD/dormant, keeps "why 50%" a
single defensible business answer instead of three separately-invented cutoffs.

A CONSEQUENCE OF THAT LINE WORTH STATING OUT LOUD: because only HV accounts
get the withdrawal-trigger RM outreach at all, RDD only has a discontinuity
to study WITHIN the HV population -- an LV account crossing the 30%
withdrawal threshold experiences no change in treatment status, so there's
nothing for RDD to identify there. Similarly, the DiD launch and the
dormant RCT are each run within the population that actually experiences a
processing change. Every one of the three causal designs below is
deliberately restricted to the population where its own treatment
assignment mechanism actually operates -- not because it's convenient, but
because that's the only population where the design has anything to
identify.

Four analytic samples are generated:
  1. predictive_data.csv   - cross-sectional account snapshot -> multi-class
                              churn-mode prediction (mirrors the real project)
  2. rdd_data.csv           - HV-only account-month withdrawal events -> RDD
                              around the 30%-of-balance RM-outreach trigger
  3. did_data.csv           - HV + LV account-level DD-stop events -> a plain
                              2x2 DiD around the "$100 for 2 DDs" offer, which
                              launches for HV accounts on a single calendar
                              month and never launches for LV accounts
  4. dormant_data.csv       - HV + LV dormant-flagged accounts, each tier with
                              its own small randomized holdout -> two clean
                              two-proportion z-tests (HV: cashback offer vs.
                              nothing; LV: SMS/email reminder vs. nothing)

All "true" effect sizes are defined once in TRUTH and reused later to check
whether RDD / DiD / the dormant RCT recover them.

---------------------------------------------------------------------------
A NOTE ON "value_score" / account economic value (read this if you're asked
"why is a customer worth X" in an interview):
---------------------------------------------------------------------------
Earlier drafts of this project scored each account with an unexplained
weighted sum of raw features (e.g. product_count*3 + tenure_months*0.05 +
balance_tier*2). That's indefensible under questioning -- the three
components are in different units (a 1-6 count, a number of months, a 0-4
bucket), so there is no principled way to justify why the weights are 3,
0.05, and 2 specifically. ANY numbers you pick for a formula like that will
draw the same "why these weights" question, because the formula's structure
-- not the specific numbers -- is what's unjustifiable.

The fix used here: anchor "value" in an actual unit of value (dollars), not
an arbitrary index. For a deposit account, the economics are simple and
well understood --
  - balance drives net-interest-margin revenue (the bank lends out / invests
    the deposits and earns a spread on them), so it's the base term and it's
    ALREADY denominated in dollars -- no weight needed.
  - each additional product held brings incremental cross-sell revenue
    (a second product is worth more spend-with-us, not just "more loyalty"),
    modeled as a multiplicative uplift on that base, not an additive term in
    a different unit.
account_value = balance * (1 + PRODUCT_VALUE_UPLIFT * product_count)

PRODUCT_VALUE_UPLIFT below is an assumed rate (15% incremental value per
product held), explicitly labeled as an assumption because real per-product
margin data isn't available here. That's fine to say out loud in an
interview -- the defensible part isn't "I know the exact right number", it's
(a) the formula has an actual economic interpretation you can explain in one
sentence, and (b) 08_business_impact.py runs a sensitivity check showing the
prioritization/optimization conclusions don't flip under a plausible range of
this assumption, so the exact rate isn't load-bearing.

Tenure and engagement are deliberately NOT part of account_value -- they are
RISK/behavioral signals (does this account look like it's about to leave?),
which is a different question from VALUE (what is this account worth if we
keep it?). Conflating value and risk into one blended score is exactly what
made the old formula impossible to defend -- keeping them as two separate,
clearly-labeled concepts (value_score here; churn-mode probabilities from
03_predictive_model.py) is itself a modeling decision worth stating plainly
if asked.
"""

import numpy as np
import pandas as pd
import json
import os

from config import (SEED, PRODUCT_VALUE_UPLIFT, account_value, seed_everything,
                     DATA_DIR, HV_VALUE_PERCENTILE, DID_LAUNCH_MONTH,
                     DORMANT_HOLDOUT_FRAC)
from validation import (
    validate_predictive_data, validate_rdd_data, validate_did_data,
    validate_dormant_data,
)
from logging_setup import get_logger

logger = get_logger(__name__)

# seed_everything() sets BOTH numpy RNG systems this pipeline touches (see
# config.py's docstring) and returns the modern Generator this script's own
# draws use.
rng = seed_everything(SEED)

OUT_DIR = DATA_DIR

# PRODUCT_VALUE_UPLIFT and account_value() now live in config.py (see its
# docstring for why) -- imported above rather than redefined here, so this
# script, the predictive dataset, the DiD split, and the optimizer are all
# guaranteed to use the exact same formula.


# ---------------------------------------------------------------------------
# Ground-truth effects baked into the DGP (kept in one place so later scripts
# can grade the RDD / DiD / dormant-RCT estimators against them).
#
# OUTCOME WINDOW: every outcome column in this file (churn_within_60d,
# churned_within_window, bad_outcome) represents "did the bad outcome happen
# within 60 days / ~2 months of the triggering event or observation point."
# This is deliberately matched to the REAL project's actual A/B test, which
# ran a 2-month observation window (see 项目二DDA存款流失挽留.docx Q6).
# ---------------------------------------------------------------------------
TRUTH = {
    "hv_value_percentile": HV_VALUE_PERCENTILE,   # top X% by account_value = "high value" (HV)

    "rdd_cutoff": 30.0,                     # withdrawal % of balance that triggers RM outreach (HV accounts only)
    "rdd_true_effect_logit": -0.90,         # jump in logit(churn_within_60d) caused by RM contact

    "did_launch_month": DID_LAUNCH_MONTH,   # calendar month (0-23) the $100 offer goes live for HV accounts
    "did_true_effect_logit_max": -0.90,     # steady-state effect once the offer is fully ramped up (HV accounts)
    "did_ramp_months": 3,                   # months for the effect to ramp from 0 to steady-state

    "dormant_holdout_frac": DORMANT_HOLDOUT_FRAC,   # share of each value tier randomly held out
    "dormant_cashback_effect_logit": -0.75,   # HV tier: 90-day 5% grocery cashback vs. nothing
    "dormant_sms_effect_logit": -0.35,        # LV tier: SMS/email reminder vs. nothing (cheaper, weaker)
}

with open(os.path.join(OUT_DIR, "ground_truth.json"), "w") as f:
    json.dump(TRUTH, f, indent=2)


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def split_value_group(acct_value, percentile=HV_VALUE_PERCENTILE):
    """Return an array of 'high'/'low' labels: top `percentile` of acct_value
    (by RANK within this dataset's own population) is 'high', the rest is
    'low'. Rank-based (not an absolute dollar cutoff) so the split is exactly
    50/50 regardless of how a given dataset's balance/product_count happens
    to be distributed -- the business rule is "the top half of THIS
    population", not "above some fixed dollar amount".
    """
    pct_rank = pd.Series(acct_value).rank(pct=True).values
    return np.where(pct_rank > (1 - percentile), "high", "low")


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

    balance_tier = pd.qcut(balance, 5, labels=False)  # 0-4, kept as a MODEL FEATURE (a coarse,
    # nonlinear-friendly version of balance for the XGBoost classifier) -- distinct from
    # value_score below, which needs to stay in actual dollars, not a 0-4 bucket.
    value_score = account_value(balance, product_count)
    value_group = split_value_group(value_score)   # "high"/"low" -- same 50/50 line optimization uses

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
        "value_group": value_group,   # "high"/"low" -- feeds 06_optimization.py's
                                       # dormant_cashback/dormant_sms eligibility filter
        "churn_mode": churn_mode,
    })
    return df


# ---------------------------------------------------------------------------
# 2) RDD dataset: withdrawal events around the 30% trigger -- HV ACCOUNTS ONLY
# ---------------------------------------------------------------------------
# WHY HV-ONLY: only HV accounts get RM outreach at all when they cross 30%
# (an LV account crossing the same threshold gets nothing -- same ROI line
# as everywhere else in this project). That means an LV account experiences
# NO discontinuity in treatment status at the cutoff, so there's no RDD to
# run on that population -- including it would just add rows with no local
# jump to estimate, diluting the design rather than strengthening it. This
# dataset is generated directly on the HV population only.
def generate_rdd_dataset(n=15_000):
    cutoff = TRUTH["rdd_cutoff"]

    tenure_months = rng.gamma(shape=2.2, scale=28, size=n).clip(1, 300)
    product_count = rng.choice([1, 2, 3, 4, 5, 6], size=n,
                                p=[0.28, 0.27, 0.20, 0.14, 0.08, 0.03])
    # HV-only population: draw from the upper half of the balance
    # distribution so that, combined with product_count, this population's
    # account_value sits (by construction) in the top half of the book --
    # matching how it's actually reached in practice (HV accounts are the
    # ones the RM-outreach program is switched on for at all).
    balance = np.exp(rng.normal(8.9, 0.85, size=n))
    acct_value = account_value(balance, product_count)

    # running variable: withdrawal as % of balance in the event month.
    # Truncated-normal-ish, centered near the cutoff so we have good density
    # on both sides (needed for local linear regression). No bunching is
    # introduced by construction -> McCrary test should come back clean,
    # consistent with "withdrawal size isn't something customers manipulate
    # to dodge/trigger an RM call" (customers don't know this internal
    # threshold exists in the first place).
    withdrawal_pct = rng.normal(30, 18, size=n)
    withdrawal_pct = withdrawal_pct.clip(0, 95)
    # Round BEFORE deriving treatment, not after -- see validate_rdd_data():
    # rounding withdrawal_pct to 2dp for storage but computing `treated` from
    # the unrounded value could produce boundary rows where the SAVED running
    # variable and the SAVED treatment flag silently disagree about which
    # side of the cutoff a row is on.
    withdrawal_pct = withdrawal_pct.round(2)

    treated = (withdrawal_pct >= cutoff).astype(int)

    # smooth baseline (no-treatment potential outcome): risk rises continuously
    # with withdrawal size. This is the confound -- naive treated-vs-control
    # comparison is biased because bigger withdrawals are already higher risk
    # BEFORE any RM outreach. RDD isolates the effect by comparing only the
    # narrow window right around the cutoff.
    baseline_logit = (-2.3 + 0.028 * withdrawal_pct
                       - 0.008 * tenure_months - 0.04 * product_count
                       + rng.normal(0, 0.35, n))

    final_logit = baseline_logit + treated * TRUTH["rdd_true_effect_logit"]
    churn_within_60d = rng.binomial(1, sigmoid(final_logit))

    df = pd.DataFrame({
        "account_id": [f"W{i:06d}" for i in range(n)],
        "withdrawal_pct": withdrawal_pct,
        "treated_rm_contact": treated,
        "tenure_months": tenure_months.round(1),
        "product_count": product_count,
        "balance": balance.round(2),
        "account_value": acct_value.round(2),
        "churn_within_60d": churn_within_60d,
    })
    return df


# ---------------------------------------------------------------------------
# 3) DiD dataset: DD-stop events, a plain 2x2 design -- HV accounts get the
#    offer starting a single launch month, LV accounts never get it
# ---------------------------------------------------------------------------
# WHY 2 GROUPS, ONE LAUNCH MONTH (not a staggered multi-tier rollout):
# The same 50/50 ROI line used everywhere in this project applies here too --
# HV accounts get the $100 offer once it launches, LV accounts don't get it
# at all. That's a plain 2x2 DiD: one treated group (HV), one never-treated
# control group (LV), one calendar split point (DID_LAUNCH_MONTH). HV's own
# baseline churn is lower than LV's (higher-value accounts are stickier on
# their own, offer or no offer) -- that's fine and expected, DiD doesn't
# require the two groups to start at the same LEVEL, only that their trends
# would have moved in parallel absent the offer (checked directly in
# 02_validate_design.py).
def generate_did_dataset(n=12_000):
    tenure_months = rng.gamma(shape=2.2, scale=28, size=n).clip(1, 300)
    product_count = rng.choice([1, 2, 3, 4, 5, 6], size=n,
                                p=[0.28, 0.27, 0.20, 0.14, 0.08, 0.03])
    balance = np.exp(rng.normal(8.2, 1.1, size=n))
    acct_value = account_value(balance, product_count)
    value_group = split_value_group(acct_value)   # "high"/"low"

    event_month = rng.integers(0, 24, size=n)  # calendar month (0-23) of the DD-stop event
    launch_month = TRUTH["did_launch_month"]

    offer_live = ((value_group == "high") & (event_month >= launch_month)).astype(int)

    # Value-group level FIXED intercept (a level shift only, never interacted
    # with event_month, so pre-trends stay parallel BY CONSTRUCTION -- the
    # parallel-trends check in 02_validate_design.py is testing whether the
    # construction actually delivers what it's supposed to, not something
    # rigged to always pass).
    value_effect = np.where(value_group == "high", -0.55, 0.0)   # HV: lower baseline churn
    common_trend = -0.01 * event_month  # slow, shared decline in post-DD-stop churn risk over time

    baseline_logit = (-1.0 + common_trend + value_effect
                       - 0.03 * product_count - 0.006 * tenure_months
                       + rng.normal(0, 0.35, n))

    # DYNAMIC (ramping) treatment effect: the offer doesn't hit full strength
    # the instant it launches -- RM awareness, customer take-up, and workflow
    # kinks all take a few months to mature.
    months_since_launch = np.where(offer_live == 1, event_month - launch_month, 0)
    ramp_frac = np.clip(months_since_launch / TRUTH["did_ramp_months"], 0, 1)
    effect_logit = offer_live * ramp_frac * TRUTH["did_true_effect_logit_max"]

    final_logit = baseline_logit + effect_logit
    churned_within_window = rng.binomial(1, sigmoid(final_logit))

    # Row-level TRUE causal effect on the probability scale -- see
    # 05_did_analysis.py's grade_against_ground_truth() for how this is used.
    true_effect_prob = sigmoid(final_logit) - sigmoid(baseline_logit)

    df = pd.DataFrame({
        "account_id": [f"D{i:06d}" for i in range(n)],
        "value_group": value_group,
        "account_value": acct_value.round(2),
        "event_month": event_month,
        "offer_live": offer_live,
        "months_since_launch": np.where(offer_live == 1, months_since_launch, np.nan),
        "tenure_months": tenure_months.round(1),
        "product_count": product_count,
        "churned_within_window": churned_within_window,
        "true_effect_prob": true_effect_prob.round(6),
    })
    return df


# ---------------------------------------------------------------------------
# 4) Dormant-reengagement dataset: two tier-specific plays, each with its own
#    small randomized holdout -- a genuine RCT, not an observational design
# ---------------------------------------------------------------------------
# STORY: an ops team flags accounts as dormant using a rule that's genuinely
# NON-SMOOTH -- "if dormancy_streak is 3+ months regardless of engagement, OR
# dormancy_streak is 1-2 months AND engagement is quite low, flag it". That's
# deliberately written as IF/OR branches because that's how real ops
# eligibility rules usually look. This rule determines who's ELIGIBLE to be
# in this study (the population this dataset represents) -- it does NOT
# determine who gets treated within that population.
#
# WHAT MAKES THIS DESIGN CLEAN (unlike an earlier version of this project
# that used DoubleML here): once an account is flagged, WHICH offer it gets
# is fixed by its value tier (HV -> cashback offer, LV -> SMS reminder --
# same 50/50 ROI line as RDD/DiD), but WHETHER it gets that offer at all is
# governed by a small, genuinely RANDOM holdout WITHIN each tier
# (DORMANT_HOLDOUT_FRAC). Because assignment to holdout is i.i.d. random and
# independent of dormancy_streak/engagement_score, those variables can
# still realistically drive baseline risk (more severe dormancy -> higher
# baseline bad-outcome rate) WITHOUT creating any confounding -- confounding
# requires treatment assignment itself to correlate with those variables,
# and here it deliberately doesn't. That's what lets this be evaluated with
# a plain two-proportion z-test per tier instead of an
# selection-on-observables method like DoubleML.
def generate_dormant_dataset(n=12_000):
    engagement_score = rng.normal(45, 20, size=n).clip(0, 100)   # this population skews
    dormancy_streak_months = rng.poisson(1.6, size=n).clip(0, 5)  # more disengaged than the
    # general book -- these are accounts that already tripped some low-activity screen,
    # not a random sample of all accounts.
    product_count = rng.choice([1, 2, 3, 4, 5, 6], size=n,
                                p=[0.28, 0.27, 0.20, 0.14, 0.08, 0.03])
    tenure_months = rng.gamma(shape=2.2, scale=28, size=n).clip(1, 300)
    balance = np.exp(rng.normal(8.0, 1.1, size=n))
    acct_value = account_value(balance, product_count)
    value_group = split_value_group(acct_value)   # "high" -> cashback play, "low" -> SMS play

    # Eligibility flag: a couple of threshold branches, not one smooth
    # formula (see module note above). Kept as descriptive context for how
    # this population is identified operationally -- it no longer needs to
    # be a LINEAR-representable confound, because treatment assignment below
    # doesn't depend on it.
    flagged = (
        (dormancy_streak_months >= 3)
        | ((dormancy_streak_months >= 1) & (dormancy_streak_months <= 2) & (engagement_score < 25))
    ).astype(int)

    # ---------------------------------------------------------------------
    # Randomized holdout, WITHIN each value tier -- this is the actual
    # treatment-assignment mechanism, and it's independent of flagged/
    # engagement/dormancy_streak by construction (rng.random() draws are
    # unrelated to those columns), which is exactly what makes this a clean
    # RCT rather than an observational design.
    # ---------------------------------------------------------------------
    holdout_frac = TRUTH["dormant_holdout_frac"]
    is_holdout = rng.random(n) < holdout_frac
    treated = (~is_holdout).astype(int)

    arm = np.where(value_group == "high", "cashback", "sms")
    # treated==0 (holdout) accounts get NO offer at all, regardless of tier.
    offer_type = np.where(treated == 1, arm, "none")

    # Baseline risk realistically driven by dormancy severity / engagement
    # (this is fine now -- it doesn't create confounding, because `treated`
    # above doesn't depend on it) plus a tier-level intercept (HV accounts
    # are stickier on their own, same story as the DiD dataset).
    value_effect = np.where(value_group == "high", -0.35, 0.0)
    baseline_logit = (-1.1 + value_effect + 1.9 * flagged
                       - 0.04 * product_count - 0.004 * tenure_months
                       + rng.normal(0, 0.35, n))

    cashback_eff = TRUTH["dormant_cashback_effect_logit"]
    sms_eff = TRUTH["dormant_sms_effect_logit"]
    effect_logit = np.where(offer_type == "cashback", cashback_eff,
                    np.where(offer_type == "sms", sms_eff, 0.0))

    final_logit = baseline_logit + effect_logit
    # same 60-day / ~2-month follow-up window as churn_within_60d and
    # churned_within_window -- see the OUTCOME WINDOW note on TRUTH above.
    bad_outcome = rng.binomial(1, sigmoid(final_logit))

    # Row-level true individual effect on the probability scale -- 0 for
    # holdout rows by construction (no offer given, so no effect to have).
    # Only computable because we control the DGP -- validation-only.
    true_effect_prob = sigmoid(final_logit) - sigmoid(baseline_logit)

    df = pd.DataFrame({
        "account_id": [f"M{i:06d}" for i in range(n)],
        "value_group": value_group,
        "account_value": acct_value.round(2),
        "engagement_score": engagement_score.round(1),
        "dormancy_streak_months": dormancy_streak_months,
        "flagged": flagged,
        "product_count": product_count,
        "tenure_months": tenure_months.round(1),
        "balance": balance.round(2),
        "offer_type": offer_type,          # "cashback" / "sms" / "none" (holdout)
        "treated": treated,                # 1 = got the tier-appropriate offer, 0 = holdout
        "bad_outcome": bad_outcome,
        "true_effect_prob": true_effect_prob.round(6),
    })
    return df


if __name__ == "__main__":
    logger.info("01_generate_data: starting synthetic data generation (SEED=%s)", SEED)

    pred_df = generate_predictive_dataset()
    rdd_df = generate_rdd_dataset()
    did_df = generate_did_dataset()
    dormant_df = generate_dormant_dataset()

    # Validate before writing to disk -- "fail loud, fail at the boundary
    # where bad data would otherwise silently enter the rest of the
    # pipeline" (see validation.py's docstring).
    try:
        validate_predictive_data(pred_df)
        validate_rdd_data(rdd_df, cutoff=TRUTH["rdd_cutoff"],
                           running_var="withdrawal_pct", treatment_col="treated_rm_contact")
        validate_did_data(did_df, value_col="value_group")
        validate_dormant_data(dormant_df, treatment_col="treated")
    except Exception:
        logger.exception("01_generate_data: validation failed before write")
        raise
    logger.info("01_generate_data: all four datasets passed validation")

    pred_df.to_csv(os.path.join(OUT_DIR, "predictive_data.csv"), index=False)
    rdd_df.to_csv(os.path.join(OUT_DIR, "rdd_data.csv"), index=False)
    did_df.to_csv(os.path.join(OUT_DIR, "did_data.csv"), index=False)
    dormant_df.to_csv(os.path.join(OUT_DIR, "dormant_data.csv"), index=False)

    print("=== predictive_data.csv ===")
    print(pred_df["churn_mode"].value_counts(normalize=True).round(4))
    print(f"n = {len(pred_df)}, HV share = {(pred_df.value_group == 'high').mean():.3f}")
    print(f"account_value (=value_score) range: ${pred_df['value_score'].min():,.0f} - "
          f"${pred_df['value_score'].max():,.0f}, median ${pred_df['value_score'].median():,.0f}\n")

    print("=== rdd_data.csv (HV accounts only) ===")
    print(f"n = {len(rdd_df)}, treated share = {rdd_df['treated_rm_contact'].mean():.3f}")
    naive_diff = (rdd_df.loc[rdd_df.treated_rm_contact == 1, "churn_within_60d"].mean()
                  - rdd_df.loc[rdd_df.treated_rm_contact == 0, "churn_within_60d"].mean())
    print(f"NAIVE (biased) treated-vs-control diff in churn_within_60d: {naive_diff:+.4f}")
    print("(expect this to look WRONG/small or even positive -- that's the confound RDD fixes)\n")

    print("=== did_data.csv ===")
    print(did_df.groupby("value_group")["offer_live"].mean())
    print(f"n = {len(did_df)}")
    naive_did_diff = (did_df.loc[did_df.offer_live == 1, "churned_within_window"].mean()
                       - did_df.loc[did_df.offer_live == 0, "churned_within_window"].mean())
    print(f"NAIVE (biased) offer_live vs. not diff in churn: {naive_did_diff:+.4f}")
    print("(the true effect is negative -- if this naive number looks smaller/positive,")
    print(" that's the value-group confound at work: HV accounts got the offer AND were")
    print(" already less likely to churn regardless)\n")

    print("=== dormant_data.csv ===")
    print(f"n = {len(dormant_df)}")
    for vg, label in [("high", "HV (cashback play)"), ("low", "LV (SMS play)")]:
        sub = dormant_df[dormant_df.value_group == vg]
        t = sub[sub.treated == 1]["bad_outcome"].mean()
        h = sub[sub.treated == 0]["bad_outcome"].mean()
        print(f"  {label}: n={len(sub)}, treated n={ (sub.treated==1).sum() }, "
              f"holdout n={ (sub.treated==0).sum() }, "
              f"treated bad_outcome={t:.4f}, holdout bad_outcome={h:.4f}, "
              f"naive diff={t - h:+.4f}")
    print()

    print("Ground truth written to data/ground_truth.json:")
    print(json.dumps(TRUTH, indent=2))

    logger.info("01_generate_data: done -- wrote predictive(%d)/rdd(%d)/did(%d)/dormant(%d) rows",
                len(pred_df), len(rdd_df), len(did_df), len(dormant_df))
