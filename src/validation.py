"""
validation.py

Data validation ("fail loud and early") for this pipeline.

WHY THIS FILE EXISTS:
Before this file existed, every script trusted its inputs implicitly --
if 01_generate_data.py's output were ever missing a column, had an
out-of-range probability, or silently violated the sharp-RDD assignment
rule it claims to inject, the FIRST place that would surface would be a
confusing downstream error (or worse, a silently wrong number three
scripts later, e.g. an RDD estimate on data that isn't actually sharply
assigned). That's a real production gap: "fail loud, fail early, fail at
the boundary where the bad data entered" is the whole point of a
validation layer, versus finding out from a wrong number in a deck.

Every validator here either returns None (data is valid) or raises
ValidationError with a message specific enough to point at the exact
column/row/assumption that failed -- never a generic "invalid data".

These are deliberately cheap, assertion-style checks (schema, nulls,
ranges, row counts, positivity, assignment-rule consistency) -- NOT a
full statistical validity check. Statistical validity (McCrary
continuity, parallel pre-trends) is a different, more expensive kind of
check and already lives in 02_validate_design.py, which is itself a
validation step in the causal-inference sense, just not this file's
sense.
"""

import numpy as np
import pandas as pd


class ValidationError(Exception):
    """Raised when input data fails a validation check.

    Deliberately a distinct exception type (not a bare AssertionError or
    ValueError) so calling code -- or a test -- can catch validation
    failures specifically, e.g. `pytest.raises(ValidationError)`, without
    also swallowing unrelated ValueErrors from elsewhere in a script.
    """
    pass


# ---------------------------------------------------------------------------
# Generic, reusable checks -- every dataset-specific validator below is
# built out of these instead of hand-rolling its own assertions, so the
# error-message format stays consistent everywhere.
# ---------------------------------------------------------------------------

def require_columns(df, columns, *, context=""):
    """Raise if any of `columns` is missing from df."""
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValidationError(
            f"{context}: missing required column(s) {missing}. "
            f"Present columns: {list(df.columns)}"
        )


def require_no_nulls(df, columns, *, context=""):
    """Raise if any of `columns` contains a null in df."""
    for c in columns:
        n_null = df[c].isna().sum()
        if n_null > 0:
            raise ValidationError(
                f"{context}: column '{c}' has {n_null} null value(s) "
                f"(expected none)."
            )


def require_range(df, column, *, lo=None, hi=None, context=""):
    """Raise if any value in df[column] falls outside [lo, hi]
    (either bound may be None to mean unbounded on that side)."""
    series = df[column]
    if lo is not None and (series < lo).any():
        bad = series[series < lo]
        raise ValidationError(
            f"{context}: column '{column}' has {len(bad)} value(s) below "
            f"the allowed minimum {lo} (min seen: {series.min()})."
        )
    if hi is not None and (series > hi).any():
        bad = series[series > hi]
        raise ValidationError(
            f"{context}: column '{column}' has {len(bad)} value(s) above "
            f"the allowed maximum {hi} (max seen: {series.max()})."
        )


def require_row_count(df, *, min_rows=1, context=""):
    """Raise if df has fewer than min_rows rows."""
    if len(df) < min_rows:
        raise ValidationError(
            f"{context}: expected at least {min_rows} row(s), got {len(df)}."
        )


def require_probabilities(df, columns, *, context=""):
    """Raise if any of `columns` isn't a valid probability in [0, 1]."""
    for c in columns:
        require_range(df, c, lo=0.0, hi=1.0, context=f"{context} (probability column '{c}')")


def require_positivity(series, *, min_share=0.02, max_share=0.98, context=""):
    """Positivity/overlap check for causal inference: the treated share
    must not be too close to 0 or 1, or there's no valid comparison group
    left to estimate a treatment effect against (this is the same
    'positivity assumption' DoubleML and any propensity-score method rely
    on -- it's not optional, it's a precondition for the estimator to mean
    anything)."""
    share = float(pd.Series(series).mean())
    if not (min_share <= share <= max_share):
        raise ValidationError(
            f"{context}: treated share is {share:.3f}, outside the "
            f"[{min_share}, {max_share}] positivity band -- there isn't "
            f"enough overlap between treated and control to estimate a "
            f"causal effect reliably."
        )


# ---------------------------------------------------------------------------
# Dataset-specific validators -- one per script that produces or consumes
# a dataset with its own required shape/assumptions.
# ---------------------------------------------------------------------------

def validate_predictive_data(df):
    """Validate the panel used by 03_predictive_model.py."""
    context = "predictive dataset"
    require_row_count(df, min_rows=100, context=context)
    require_columns(
        df,
        ["account_id", "engagement_score", "dormancy_streak_months",
         "product_count", "tenure_months", "balance", "churn_mode"],
        context=context,
    )
    require_no_nulls(
        df,
        ["engagement_score", "dormancy_streak_months", "product_count",
         "tenure_months", "balance", "churn_mode"],
        context=context,
    )
    require_range(df, "balance", lo=0, context=context)
    require_range(df, "product_count", lo=0, context=context)
    require_range(df, "tenure_months", lo=0, context=context)


def validate_rdd_data(df, *, cutoff, running_var="withdrawal_pct",
                       treatment_col="rm_contact"):
    """Validate the RDD analysis dataset -- in particular, that treatment
    actually equals the sharp assignment rule (running_var >= cutoff) it
    claims to be. This is the single most important check in the whole
    validation layer: if this rule doesn't hold exactly, the design isn't
    actually a SHARP RDD, and rdrobust's local-linear estimate around the
    cutoff would be estimating something other than what the deck claims
    it estimates."""
    context = "RDD dataset"
    require_columns(df, [running_var, treatment_col], context=context)
    require_no_nulls(df, [running_var, treatment_col], context=context)
    require_row_count(df, min_rows=100, context=context)

    implied = (df[running_var] >= cutoff).astype(int)
    actual = df[treatment_col].astype(int)
    mismatches = int((implied != actual).sum())
    if mismatches > 0:
        raise ValidationError(
            f"{context}: {mismatches} row(s) violate the sharp-RDD "
            f"assignment rule '{treatment_col} == ({running_var} >= "
            f"{cutoff})'. A sharp RDD requires this to hold EXACTLY -- "
            f"any violation means this is actually a fuzzy design and "
            f"needs a different estimator (2SLS / fuzzy rdrobust), not "
            f"the sharp local-linear estimate this script runs."
        )


def validate_did_data(df, *, tier_col="value_tier", expected_tiers=4):
    """Validate the value-tier staggered DiD dataset."""
    context = "DiD dataset"
    require_columns(df, [tier_col], context=context)
    require_no_nulls(df, [tier_col], context=context)
    require_row_count(df, min_rows=100, context=context)

    n_tiers = df[tier_col].nunique()
    if n_tiers != expected_tiers:
        raise ValidationError(
            f"{context}: expected exactly {expected_tiers} value tiers, "
            f"found {n_tiers} distinct value(s) in '{tier_col}': "
            f"{sorted(df[tier_col].unique().tolist())}."
        )


def validate_dormant_data(df, *, treatment_col="dormant_treated"):
    """Validate the DoubleML dormant-play dataset, including the
    positivity assumption DoubleMLIRM's ATT estimate depends on."""
    context = "dormant/DoubleML dataset"
    require_columns(df, [treatment_col], context=context)
    require_no_nulls(df, [treatment_col], context=context)
    require_row_count(df, min_rows=200, context=context)
    require_positivity(df[treatment_col], context=context)


def validate_optimization_inputs(effect_pp, effect_source, cost, *, budget, rm_capacity):
    """Validate the inputs 06_optimization.py's ILP is built from --
    catches the class of bug where a new intervention type gets added to
    one dict (e.g. EFFECT_PP) but forgotten in another (COST), which
    would otherwise surface as a cryptic KeyError deep inside the PuLP
    solve rather than a clear message about which dict is missing what."""
    context = "optimization inputs"
    effect_keys = set(effect_pp.keys())
    source_keys = set(effect_source.keys())
    cost_keys = set(cost.keys())
    if effect_keys != source_keys:
        raise ValidationError(
            f"{context}: effect_pp keys {effect_keys} and effect_source "
            f"keys {source_keys} don't match -- every intervention with "
            f"an effect size needs a labeled source."
        )
    if not effect_keys.issubset(cost_keys):
        raise ValidationError(
            f"{context}: intervention(s) {effect_keys - cost_keys} have "
            f"an effect size but no entry in the cost dict."
        )
    if budget <= 0:
        raise ValidationError(f"{context}: budget must be positive, got {budget}.")
    if rm_capacity <= 0:
        raise ValidationError(f"{context}: rm_capacity must be positive, got {rm_capacity}.")
