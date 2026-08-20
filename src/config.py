"""
config.py

Single source of truth for every constant this project's scripts use --
file paths, the random seed, model hyperparameters, and business
constraints (budget, RM capacity, intervention costs, the product-value
uplift assumption).

WHY THIS FILE EXISTS (this is the "production-readiness" fix for hardcoded
constants):
Before this file existed, SEED / PRODUCT_VALUE_UPLIFT / BUDGET / RM_CAPACITY
/ model hyperparameters were each hardcoded inline in whichever script
happened to need them first. That's a normal way to write a one-off analysis
script, but it's a real gap if you're asked "is this production-ready":
nobody could safely change next month's retention budget without hunting
through 06_optimization.py's body and hoping they found every place it's
used; there was no single place to answer "what config did this run use";
and the SAME constant (e.g. PRODUCT_VALUE_UPLIFT) had to be trusted to stay
in sync across three files by convention, not by construction.

Centralizing them here means every script imports from one place, changing
a business assumption (e.g. RM_CAPACITY for next month) is a one-line diff
in a config file instead of a code edit buried in an analysis script, and
this file itself becomes something you could hand to a non-engineer
stakeholder ("here is every assumption this pipeline runs on") without
making them read code.

This file does NOT change any estimation logic or the data-generating
process -- it is a pure refactor of WHERE constants live, not what they are.
Every value below is unchanged from what was previously hardcoded in each
script, which matters a lot here specifically: 01_generate_data.py's random
draws are sequential and seed-dependent, so if any constant it consumes
silently changed value, the synthetic data (and therefore every number in
the deck and every downstream script) would silently change too.
"""

import os
import numpy as np

# ---------------------------------------------------------------------------
# Paths -- computed relative to THIS file's location, not the current working
# directory, so every script behaves the same whether it's run as
# `python3 01_generate_data.py` from inside src/, as `python3 src/01_....py`
# from the repo root, or imported by a test/service from anywhere else.
# ---------------------------------------------------------------------------
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(SRC_DIR, "..")
DATA_DIR = os.path.join(ROOT_DIR, "data")
FIG_DIR = os.path.join(ROOT_DIR, "figures")
OUT_DIR = os.path.join(ROOT_DIR, "output")
LOG_DIR = os.path.join(ROOT_DIR, "logs")

for _d in (DATA_DIR, FIG_DIR, OUT_DIR, LOG_DIR):
    os.makedirs(_d, exist_ok=True)


# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------
# A single seed, but TWO separate numpy RNG systems have to be seeded for the
# full 8-script pipeline to be bit-for-bit reproducible run to run:
#   1. numpy's new Generator API (np.random.default_rng(SEED)) -- used
#      directly by 01_generate_data.py for the whole synthetic DGP.
#   2. numpy's legacy global RandomState (np.random.seed(SEED)) -- this is
#      what scikit-learn's KFold(shuffle=True) draws from when no explicit
#      random_state is passed to it, and DoubleML's internal cross-fitting
#      fold splits go through exactly that code path. This was a real,
#      previously-present gap in this project: XGBoost's own random_state
#      was always set explicitly, but nothing seeded the legacy global RNG
#      that DoubleML's fold-splitting relies on, so 07_doubleml_dormant.py's
#      ATT estimate could (and did) drift slightly from run to run even
#      though "the seed was 42" everywhere else that mattered.
# seed_everything() sets both and returns the Generator, so a script can do
# `rng = config.seed_everything()` in one line and know both systems are
# locked down.
SEED = 42


def seed_everything(seed=SEED):
    """Seed every RNG system this pipeline touches; return the Generator.

    Call this ONCE, at the very top of a script's execution (inside its
    `if __name__ == "__main__":` block, before any random draws happen).
    Calling it more than once mid-script would reset the stream and quietly
    change later draws -- it's a "call once at the start" contract, not
    something to sprinkle around.
    """
    np.random.seed(seed)          # legacy global RandomState (sklearn / DoubleML)
    return np.random.default_rng(seed)   # modern Generator (this project's own draws)


# ---------------------------------------------------------------------------
# Reproducibility vs. speed: single-threaded XGBoost
# ---------------------------------------------------------------------------
# random_state alone does not guarantee bit-identical XGBoost output across
# runs when training is multi-threaded: histogram-based tree building sums
# gradients across threads, and floating-point addition is not perfectly
# associative, so the sum (and therefore the exact split points chosen) can
# differ by thread-scheduling noise even with the same seed. Pinning
# n_jobs=1 removes that source of nondeterminism entirely, at the cost of
# slower training. For a demo/interview-prep pipeline where "these are
# exactly the numbers in the deck, reproducibly" matters more than shaving a
# few seconds off a fit, that trade is worth making explicitly rather than
# discovering the drift by accident (which is what happened here before this
# fix -- see README.md's prior reproducibility note).
XGB_N_JOBS = 1


# ---------------------------------------------------------------------------
# Business economics: the account-value formula
# ---------------------------------------------------------------------------
# See 01_generate_data.py's module docstring for the full "why this formula,
# why 15%, how is 15% defended" writeup. Kept here, not buried in a formula,
# specifically so it's the one place you'd change it and the one place
# 08_business_impact.py's sensitivity check knows to test around.
PRODUCT_VALUE_UPLIFT = 0.15


def account_value(balance, product_count, uplift=PRODUCT_VALUE_UPLIFT):
    """Dollar-denominated proxy for 'what is this account worth'.

    balance * (1 + uplift * product_count) -- both terms stay in dollar
    units throughout, deliberately, so this number always means "roughly
    how many dollars of relationship value", not an unlabeled index. Used
    consistently everywhere "value" is needed: the predictive dataset, the
    DiD rollout-priority ordering, and the optimization objective. Defined
    ONCE, here, and imported everywhere else -- see the module docstring for
    why that single-source-of-truth property matters.
    """
    return balance * (1 + uplift * product_count)


# ---------------------------------------------------------------------------
# RDD design
# ---------------------------------------------------------------------------
RDD_CUTOFF = 30.0   # withdrawal % of balance that triggers RM outreach


# ---------------------------------------------------------------------------
# High-value / low-value split -- used consistently by RDD, DiD, and the
# dormant RCT to decide who gets the real (funded) intervention vs. nothing
# or a cheap generic touch. Not a statistical choice -- it's the same ROI
# logic the real project used (see 项目二DDA存款流失挽留.docx Q4: "ranked by
# value score and drew the line where the expected return on a retention
# touch dropped below its cost... For the top half... the deposits and
# lifetime value we'd protect clearly outweighed the cost. Below that the
# economics got thin"). Kept as ONE constant, imported everywhere the split
# is needed, so "why 50%" always traces back to the same single business
# answer instead of three separately-justified cutoffs.
# ---------------------------------------------------------------------------
HV_VALUE_PERCENTILE = 0.50   # top 50% by account_value = "high value" (HV); bottom 50% = "low value" (LV)


# ---------------------------------------------------------------------------
# DiD design: the DD-stop $100 offer launches for HV accounts on a single
# calendar month (LV accounts never get it in-window -- same ROI logic as
# above). Injected true effects and ramp still live in data/ground_truth.json
# (written by 01_generate_data.py), because they are OUTPUTS of the DGP that
# later scripts read back -- ground_truth.json is the single source of truth
# for "what did the DGP actually inject".
# ---------------------------------------------------------------------------
DID_LAUNCH_MONTH = 12   # calendar month (0-23) the offer goes live for HV accounts


# ---------------------------------------------------------------------------
# Dormant re-engagement RCT: two different plays, one per value tier, each
# with its own small randomized holdout (see 01_generate_data.py's
# generate_dormant_dataset() for the full design rationale).
# ---------------------------------------------------------------------------
DORMANT_HOLDOUT_FRAC = 0.10   # share of each value tier randomly held out (no offer at all)


# ---------------------------------------------------------------------------
# Predictive model (03_predictive_model.py)
# ---------------------------------------------------------------------------
PREDICTIVE_MODEL_PARAMS = dict(
    objective="multi:softprob",
    n_estimators=300,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    eval_metric="mlogloss",
    random_state=SEED,
    n_jobs=XGB_N_JOBS,
)
TEST_SIZE = 0.25


# ---------------------------------------------------------------------------
# Optimization layer (06_optimization.py)
# ---------------------------------------------------------------------------
BUDGET = 150_000          # total monthly retention spend
RM_CAPACITY = 400         # max large-withdrawal RM contacts the team can make in a month
INTERVENTION_COST = {
    "large_withdrawal": 75,     # RM staff time, proxy $ cost
    "dd_stop": 100,              # flat $100 offer
    # dormant_cashback: 90-day, 5% cashback on grocery-category spend, HV tier
    # only. Assumed ~$1,200 of grocery spend over 90 days ($400/mo median)
    # times 5% = $60 MAX exposure per account if fully spent and redeemed;
    # assumed ~60% uptake/redemption in practice -> ~$36, rounded to a clean
    # $35. Documented as an assumption (same pattern as PRODUCT_VALUE_UPLIFT)
    # -- the exact number isn't load-bearing for the optimizer's targeting
    # decision as long as it's in the right ballpark; see 08_business_impact.py.
    "dormant_cashback": 35,
    "dormant_sms": 1,            # SMS/email reminder, LV tier only -- near-zero marginal cost
}
CANDIDATE_MIN_PROBA = 0.01     # floor below which an account-intervention pair isn't worth modeling


# ---------------------------------------------------------------------------
# Business impact layer (08_business_impact.py)
# ---------------------------------------------------------------------------
SCORED_ACCOUNTS = 10_000       # size of the predictive test set this optimization ran over
VALUE_UPLIFT_SENSITIVITY_RATES = [0.10, 0.15, 0.20]   # alt. rates tested against PRODUCT_VALUE_UPLIFT
