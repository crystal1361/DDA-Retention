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

Four analytic samples are generated, matching how you'd actually study these
four questions in practice (not one giant table):
  1. predictive_data.csv   - cross-sectional account snapshot -> multi-class
                              churn-mode prediction (mirrors the real project)
  2. rdd_data.csv           - account-month withdrawal events -> RDD around the
                              30%-of-balance RM-outreach trigger
  3. did_data.csv           - account-level DD-stop events -> staggered-rollout
                              DiD around the "$100 for 2 DDs" retention offer,
                              rolled out in PRIORITY WAVES by customer value
                              (highest-value accounts first) because RM/ops
                              capacity to administer the offer is limited --
                              see the "why value-tiered, not random" note below
  4. dormant_data.csv       - accounts flagged as at risk of going dormant,
                              some of which an internal ops rule (not a design
                              we control, not threshold-based, not staggered)
                              selects for a re-engagement outreach call. No
                              RDD- or DiD-style structure exists for this
                              intervention -- that's the point: it's the case
                              that motivates 07_doubleml_dormant.py.

All "true" effect sizes are defined once in TRUTH and reused later to check
whether RDD / DiD / DoubleML recover them.

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

from config import SEED, PRODUCT_VALUE_UPLIFT, account_value, seed_everything, DATA_DIR
from validation import (
    validate_predictive_data, validate_rdd_data, validate_did_data,
    validate_dormant_data,
)
from logging_setup import get_logger

logger = get_logger(__name__)

# seed_everything() sets BOTH numpy RNG systems this pipeline touches (see
# config.py's docstring) and returns the modern Generator this script's own
# draws use. Functionally identical to the old `np.random.default_rng(SEED)`
# call for THIS script's own draws -- the added `np.random.seed(SEED)` call
# seeds a separate (legacy, global) RNG stream that this script doesn't
# itself draw from, so the sequence of values `rng` produces below, and
# therefore every synthetic number in this project, is UNCHANGED by this
# refactor. It matters starting with 03/07, which do draw from that legacy
# stream via scikit-learn/DoubleML.
rng = seed_everything(SEED)

OUT_DIR = DATA_DIR

# PRODUCT_VALUE_UPLIFT and account_value() now live in config.py (see its
# docstring for why) -- imported above rather than redefined here, so this
# script, the predictive dataset, the DiD tiering, and the optimizer are
# all guaranteed to use the exact same formula.


# ---------------------------------------------------------------------------
# Ground-truth effects baked into the DGP (kept in one place so later scripts
# can grade the RDD/DiD/DoubleML estimators against them).
#
# OUTCOME WINDOW: every outcome column in this file (churn_within_60d,
# churned_within_window, bad_outcome) represents "did the bad outcome happen
# within 60 days / ~2 months of the triggering event or observation point."
# This is deliberately matched to the REAL project's actual A/B test, which
# ran a 2-month observation window (see 项目二DDA存款流失挽留.docx Q6). The
# whole point of this rebuild is to show that each individual trigger's
# causal effect is consistent with, and helps explain, the -30% relative
# churn the real test measured over that same 2-month window -- using a
# 1-month outcome here (an earlier version of this script did) would be
# measuring a different quantity than what the real test validated, which
# is exactly the kind of inconsistency a careful reviewer would catch.
# ---------------------------------------------------------------------------
TRUTH = {
    "rdd_cutoff": 30.0,                     # withdrawal % of balance that triggers RM outreach
    "rdd_true_effect_logit": -0.90,         # jump in logit(churn_within_60d) caused by RM contact
    "did_value_tier_labels": [              # ordered highest-value -> lowest-value; see
        "tier1_top25pct",                   # generate_did_dataset() for why rollout is
        "tier2_next25pct",                  # value-PRIORITIZED rather than random/regional
        "tier3_next25pct",
        "tier4_bottom25pct",
    ],
    "did_adoption_months": {                # calendar month (0-23) each value tier's offer
        "tier1_top25pct": 8,                # goes live -- highest value first, because RM/ops
        "tier2_next25pct": 14,              # capacity to administer the offer can't reach
        "tier3_next25pct": 20,              # everyone on day one
        "tier4_bottom25pct": None,          # never reached in-window -- capacity ran out
    },
    "did_true_effect_logit_max": -0.90,     # steady-state effect once the offer is fully ramped up
    "did_ramp_months": 3,                   # months for the effect to ramp from 0 to steady-state
    "dormant_true_effect_logit": -0.50,     # effect of re-engagement outreach on
                                             # logit(bad_outcome); smaller than the other two
                                             # plays' effects, and -- unlike them -- estimated
                                             # with a weaker (selection-on-observables) design;
                                             # see 07_doubleml_dormant.py
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

    balance_tier = pd.qcut(balance, 5, labels=False)  # 0-4, kept as a MODEL FEATURE (a coarse,
    # nonlinear-friendly version of balance for the XGBoost classifier) -- distinct from
    # value_score below, which needs to stay in actual dollars, not a 0-4 bucket.
    value_score = account_value(balance, product_count)

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
    # Round BEFORE deriving treatment, not after: rounding withdrawal_pct to
    # 2dp for storage but computing `treated` from the unrounded value could
    # produce a handful of boundary rows (e.g. raw 29.996 -> treated=0, but
    # stored as 30.00) where the SAVED running variable and the SAVED
    # treatment flag silently disagree about which side of the cutoff a row
    # is on. That's not a sharp RDD anymore for those rows -- validate_rdd_
    # data() below is what originally caught this. Rounding first means the
    # persisted running variable IS the value treatment was assigned from.
    withdrawal_pct = withdrawal_pct.round(2)

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
    churn_within_60d = rng.binomial(1, sigmoid(final_logit))

    df = pd.DataFrame({
        "account_id": [f"W{i:06d}" for i in range(n)],
        "withdrawal_pct": withdrawal_pct,
        "treated_rm_contact": treated,
        "tenure_months": tenure_months.round(1),
        "product_count": product_count,
        "balance": balance.round(2),
        "churn_within_60d": churn_within_60d,
    })
    return df


# ---------------------------------------------------------------------------
# 3) DiD dataset: DD-stop events, staggered offer rollout by CUSTOMER VALUE
#    TIER (not region)
# ---------------------------------------------------------------------------
# WHY VALUE-TIERED, NOT RANDOM / NOT REGIONAL:
# The real constraint that makes this a staggered rollout in the first place
# is RM/ops capacity -- see RM_CAPACITY in 06_optimization.py, the same
# constraint shows up here as the reason NOT everyone gets the offer on day
# one. Given that constraint, a bank prioritizes: highest-value accounts get
# the offer first, the lowest-value quartile never gets reached inside the
# observed window. That's a believable, motivated staggering mechanism (a
# region-by-region rollout for a call-center-administered retention offer is
# a weaker story -- why would geography determine rollout order here?).
#
# This choice has a real consequence for identification that's worth stating
# out loud: treatment TIMING is now correlated with account_value, and
# account_value is independently correlated with churn risk (higher-value
# accounts -- more products, bigger balances -- are stickier on their own,
# offer or no offer). That means a NAIVE comparison of "early-treated
# (high-value) vs. late/never-treated (low-value)" accounts is confounded by
# value itself, not just by the offer. This is deliberate: it's what makes
# naive static TWFE break in an intuitive, explainable way (see
# 05_did_analysis.py), and it's exactly the kind of "already-treated cohorts
# get used as part of the comparison for later cohorts" bias that
# Goodman-Bacon (2021) describes for staggered-adoption designs.
#
# The DGP still keeps the tier's effect on churn as a pure LEVEL shift (not
# interacted with event_month), so -- exactly as with the earlier
# region-based version -- pre-trends stay parallel across tiers BY
# CONSTRUCTION. That is intentional: it means the parallel-trends check in
# 02_validate_design.py is still testing something real (whether the
# construction actually delivers what it's supposed to), not something
# rigged to always pass.
def generate_did_dataset(n=12_000):
    tier_labels = TRUTH["did_value_tier_labels"]

    # Generate the SAME underlying account characteristics used elsewhere,
    # so that account_value() here means the same thing it means in
    # predictive_data.csv and in 06_optimization.py.
    tenure_months = rng.gamma(shape=2.2, scale=28, size=n).clip(1, 300)
    product_count = rng.choice([1, 2, 3, 4, 5, 6], size=n,
                                p=[0.28, 0.27, 0.20, 0.14, 0.08, 0.03])
    balance = np.exp(rng.normal(8.2, 1.1, size=n))
    acct_value = account_value(balance, product_count)

    # Bucket into value quartiles -- this is the ONLY thing that determines
    # which wave an account is rolled into. Computed on this account's own
    # (pre-period, static) balance/product_count -- i.e. on characteristics
    # observed BEFORE the offer could have changed anything -- so this is
    # not conditioning on a post-treatment-affected variable ("bad control").
    # In this cross-sectional DGP balance/product_count are exogenous by
    # construction, but the principle is one worth stating in an interview
    # regardless: never tier customers on a metric the treatment itself could
    # have already moved.
    # NOTE: pd.qcut assigns labels[0] to the LOWEST-value bin and labels[-1]
    # to the HIGHEST-value bin (ascending order) -- tier_labels is written
    # highest-value-first for readability elsewhere, so it has to be
    # reversed here to land "tier1_top25pct" on the accounts that actually
    # have the highest account_value.
    value_tier = pd.qcut(acct_value, 4, labels=list(reversed(tier_labels)))

    event_month = rng.integers(0, 24, size=n)  # calendar month (0-23) of the DD-stop event

    adoption_month_map = TRUTH["did_adoption_months"]
    adoption_month = np.array([
        adoption_month_map[t] if adoption_month_map[t] is not None else 999
        for t in value_tier
    ])
    offer_live = (event_month >= adoption_month).astype(int)

    # Tier-level FIXED intercepts (level shifts only, never interacted with
    # event_month -- see the module note above on why that preserves
    # parallel pre-trends by construction). Deliberately correlated with
    # account_value's rank so that higher tiers -> lower baseline churn,
    # which is what makes the naive early-vs-late comparison confounded.
    tier_rank = {t: i for i, t in enumerate(tier_labels)}  # 0=top tier ... 3=bottom tier
    tier_effect = np.array([-0.25 * (3 - tier_rank[t]) for t in value_tier])  # top tier: -0.75, bottom: 0
    common_trend = -0.01 * event_month  # slow, shared decline in post-DD-stop churn risk over time

    baseline_logit = (-1.0 + common_trend + tier_effect
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
    # "window" here is the same 60-day / ~2-month window as churn_within_60d
    # and bad_outcome below -- see the OUTCOME WINDOW note on TRUTH above.
    churned_within_window = rng.binomial(1, sigmoid(final_logit))

    # Row-level TRUE causal effect on the probability scale: sigmoid(with
    # treatment) - sigmoid(without), computed directly from the DGP's own
    # baseline_logit for THIS row (not approximated from some other group's
    # average, which would be wrong once tiers differ substantially in
    # baseline level -- exactly the situation this dataset deliberately
    # creates). Stored so 05_did_analysis.py can grade estimators against an
    # exact number instead of an approximation. This is only knowable
    # because we, the simulator, control the DGP -- it's a validation-only
    # convenience, not something you'd ever have in a real dataset.
    true_effect_prob = sigmoid(final_logit) - sigmoid(baseline_logit)

    # "cohort" is kept as the column name (rather than renaming it everywhere)
    # so 02_validate_design.py's pre-trends check and 05_did_analysis.py's
    # clean-control estimator work unchanged -- they only ever cared that
    # "cohort" partitions accounts into rollout-timing groups, never that the
    # groups were regions specifically.
    cohort = value_tier.astype(str)
    cohort = np.where(cohort == "tier4_bottom25pct", "never", cohort)

    df = pd.DataFrame({
        "account_id": [f"D{i:06d}" for i in range(n)],
        "value_tier": value_tier.astype(str),
        "account_value": acct_value.round(2),
        "cohort": cohort,
        "event_month": event_month,
        "adoption_month": np.where(adoption_month == 999, np.nan, adoption_month),
        "offer_live": offer_live,
        "months_since_adoption": np.where(offer_live == 1, months_since_adoption, np.nan),
        "tenure_months": tenure_months.round(1),
        "product_count": product_count,
        "churned_within_window": churned_within_window,
        "true_effect_prob": true_effect_prob.round(6),
    })
    return df


# ---------------------------------------------------------------------------
# 4) Dormant-reengagement dataset: NO design-based structure available here
#    (no threshold, no staggered rollout) -- built specifically to motivate
#    and validate 07_doubleml_dormant.py.
# ---------------------------------------------------------------------------
# STORY: an ops team informally flags accounts for a re-engagement phone call
# using a rule that's genuinely NON-SMOOTH -- something closer to "if
# dormancy_streak is 3+ months regardless of engagement, OR dormancy_streak
# is 1-2 months AND engagement is quite low, flag it" than to any single
# smooth formula. That's deliberately written as a couple of IF/OR branches
# because that's how real ops/eligibility rules usually actually look (a
# handful of thresholds someone encoded from experience), and it's a
# textbook case of something a LINEAR-additive logistic regression on the
# raw features can't represent well (linear-in-X models can't produce this
# kind of "AND"/"OR" branching decision boundary), but that a tree-based
# model like XGBoost represents natively -- trees split on thresholds, which
# is exactly this rule's shape.
#
# Crucially, the SAME underlying signal ALSO independently drives the bad
# outcome (further disengagement / churn) -- accounts that would be flagged
# for outreach are, on their own, already more likely to end up with a bad
# outcome regardless of whether anyone calls them. This is "confounding by
# indication" -- a term borrowed from epidemiology/health economics, where
# the people most likely to be treated are also the people most likely to
# have a bad outcome anyway, so a naive treated-vs-untreated comparison makes
# the treatment look neutral or even harmful even when it truly helps. It's a
# standard, intuitive way to explain why this specific play needs adjustment
# for confounding rather than a simple average comparison.
def generate_dormant_dataset(n=12_000):
    engagement_score = rng.normal(45, 20, size=n).clip(0, 100)   # this population skews
    dormancy_streak_months = rng.poisson(1.6, size=n).clip(0, 5)  # more disengaged than the
    # general book -- these are accounts that already tripped some low-activity screen,
    # not a random sample of all accounts.
    product_count = rng.choice([1, 2, 3, 4, 5, 6], size=n,
                                p=[0.28, 0.27, 0.20, 0.14, 0.08, 0.03])
    tenure_months = rng.gamma(shape=2.2, scale=28, size=n).clip(1, 300)
    balance = np.exp(rng.normal(8.0, 1.1, size=n))

    # The confounding "risk flag": a couple of threshold branches, not one
    # smooth formula -- see the note above on why this shape specifically
    # motivates a tree-based (not linear) nuisance model.
    flagged = (
        (dormancy_streak_months >= 3)
        | ((dormancy_streak_months >= 1) & (dormancy_streak_months <= 2) & (engagement_score < 25))
    ).astype(int)

    # Treatment assignment (ops team's informal outreach rule) -- driven by
    # the SAME flag that also drives the outcome below, plus noise, so it's
    # NOT a deterministic rule (real ops processes are noisy: capacity,
    # analyst judgment, timing all add randomness on top of the rule).
    # Coefficients tuned so propensities stay away from the 0/1 extremes
    # (max ~0.95) -- a real positivity check, not just "whatever falls out".
    # Wildly confident propensities (accounts ~100% certain to be contacted)
    # create instability for ANY observational method, DoubleML included --
    # worth designing around rather than discovering by accident.
    treat_logit = -1.6 + 2.3 * flagged - 0.08 * product_count + rng.normal(0, 0.6, n)
    reengagement_contact = rng.binomial(1, sigmoid(treat_logit))

    # Outcome: 1 = bad outcome (churned or still dormant at the end of the
    # follow-up window), 0 = good outcome (reactivated / retained). Kept on
    # the same "1 = bad" sign convention as the RDD/DiD outcomes so effect
    # signs are comparable across the whole project (all three true effects
    # are negative -- each intervention REDUCES the bad-outcome probability).
    baseline_logit = (-0.6 + 2.0 * flagged - 0.04 * product_count
                       - 0.004 * tenure_months + rng.normal(0, 0.35, n))
    final_logit = baseline_logit + reengagement_contact * TRUTH["dormant_true_effect_logit"]
    # same 60-day / ~2-month follow-up window as churn_within_60d and
    # churned_within_window -- see the OUTCOME WINDOW note on TRUTH above.
    bad_outcome = rng.binomial(1, sigmoid(final_logit))

    # Row-level true individual treatment effect on the probability scale --
    # "if this specific account HAD been contacted vs. hadn't", holding its
    # own characteristics fixed. 07_doubleml_dormant.py averages this over
    # just the TREATED rows to get the true ATT (average effect on the
    # treated) -- deliberately ATT rather than population-wide ATE, because
    # "how much did contacting the accounts we actually contacted help" is
    # both the more natural business question here (most never-flagged
    # accounts would never realistically be called anyway) and, with an
    # effect this concentrated in a ~30% subgroup, a materially easier
    # target to estimate precisely than an average smeared across a huge
    # majority with a true effect close to zero. DoubleML is run with
    # score="ATTE" to match. Same validation-only logic as did_data.csv's
    # true_effect_prob column: only computable here because we control the DGP.
    true_effect_prob = sigmoid(final_logit) - sigmoid(baseline_logit)

    df = pd.DataFrame({
        "account_id": [f"M{i:06d}" for i in range(n)],
        "engagement_score": engagement_score.round(1),
        "dormancy_streak_months": dormancy_streak_months,
        "product_count": product_count,
        "tenure_months": tenure_months.round(1),
        "balance": balance.round(2),
        "reengagement_contact": reengagement_contact,
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
    # pipeline" (see validation.py's docstring). In particular,
    # validate_rdd_data re-derives the sharp assignment rule from
    # withdrawal_pct and checks it against treated_rm_contact exactly --
    # if the DGP above is ever edited in a way that breaks the sharp
    # design, this is where it gets caught, not three scripts later in a
    # confusing rdrobust error.
    try:
        validate_predictive_data(pred_df)
        validate_rdd_data(rdd_df, cutoff=TRUTH["rdd_cutoff"],
                           running_var="withdrawal_pct", treatment_col="treated_rm_contact")
        validate_did_data(did_df, tier_col="value_tier")
        validate_dormant_data(dormant_df, treatment_col="reengagement_contact")
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
    print(f"n = {len(pred_df)}")
    print(f"account_value (=value_score) range: ${pred_df['value_score'].min():,.0f} - "
          f"${pred_df['value_score'].max():,.0f}, median ${pred_df['value_score'].median():,.0f}\n")

    print("=== rdd_data.csv ===")
    print(f"n = {len(rdd_df)}, treated share = {rdd_df['treated_rm_contact'].mean():.3f}")
    naive_diff = (rdd_df.loc[rdd_df.treated_rm_contact == 1, "churn_within_60d"].mean()
                  - rdd_df.loc[rdd_df.treated_rm_contact == 0, "churn_within_60d"].mean())
    print(f"NAIVE (biased) treated-vs-control diff in churn_within_60d: {naive_diff:+.4f}")
    print("(expect this to look WRONG/small or even positive -- that's the confound RDD fixes)\n")

    print("=== did_data.csv ===")
    print(did_df.groupby("cohort")["offer_live"].mean())
    print(f"n = {len(did_df)}")
    naive_did_diff = (did_df.loc[did_df.offer_live == 1, "churned_within_window"].mean()
                       - did_df.loc[did_df.offer_live == 0, "churned_within_window"].mean())
    print(f"NAIVE (biased) offer_live vs. not diff in churn: {naive_did_diff:+.4f}")
    print("(the true effect is negative -- if this naive number looks smaller/positive,")
    print(" that's the value-tier confound at work: high-value accounts got the offer")
    print(" FIRST and were already less likely to churn regardless)\n")

    print("=== dormant_data.csv ===")
    print(f"n = {len(dormant_df)}, treated share = {dormant_df['reengagement_contact'].mean():.3f}")
    naive_dormant_diff = (dormant_df.loc[dormant_df.reengagement_contact == 1, "bad_outcome"].mean()
                           - dormant_df.loc[dormant_df.reengagement_contact == 0, "bad_outcome"].mean())
    print(f"NAIVE (confounded) treated-vs-untreated diff in bad_outcome: {naive_dormant_diff:+.4f}")
    print("(expect this to look near-zero or even POSITIVE -- 'confounding by indication':")
    print(" the ops team calls the accounts already most likely to have a bad outcome,")
    print(" so raw comparison makes outreach look useless or harmful even though the true")
    print(f" injected effect is {TRUTH['dormant_true_effect_logit']:+.2f} logit, i.e. genuinely helpful)\n")

    print("Ground truth written to data/ground_truth.json:")
    print(json.dumps(TRUTH, indent=2))

    logger.info("01_generate_data: done -- wrote predictive(%d)/rdd(%d)/did(%d)/dormant(%d) rows",
                len(pred_df), len(rdd_df), len(did_df), len(dormant_df))
