"""
Tests for src/01_generate_data.py's dataset generators.

Loaded via conftest.load_module() rather than a normal import statement --
see conftest.py's docstring for why numbered filenames need that. Importing
this module has ONE side effect worth knowing about: it (re)writes
data/ground_truth.json at import time (a documented, accepted quirk -- see
the module's own comments) -- harmless for tests since it writes the exact
same TRUTH dict every time and no test here depends on that file's prior
contents.
"""

import numpy as np

from conftest import load_module

gen = load_module("01_generate_data.py")


def test_generate_predictive_dataset_shape_and_no_nulls():
    df = gen.generate_predictive_dataset(n=500)
    assert len(df) == 500
    assert df["balance"].isna().sum() == 0
    assert df["churn_mode"].isin(["none", "large_withdrawal", "dd_stop", "dormant"]).all()


def test_generate_rdd_dataset_treatment_matches_sharp_rule_exactly():
    # The exact bug this test guards against: 01_generate_data.py used to
    # compute `treated` from the UNROUNDED withdrawal_pct but store the
    # ROUNDED value, which could disagree for boundary rows. Regenerating
    # with a decent sample size and checking every row catches any
    # regression of that fix directly, the same way validate_rdd_data()
    # does at pipeline run time.
    df = gen.generate_rdd_dataset(n=5000)
    cutoff = gen.TRUTH["rdd_cutoff"]
    implied = (df["withdrawal_pct"] >= cutoff).astype(int)
    assert (implied == df["treated_rm_contact"]).all()


def test_generate_did_dataset_has_exactly_two_value_groups():
    # Redesigned from 4 staggered-adoption value tiers to a plain 2-group
    # (HV/LV) design -- see 01_generate_data.py's module docstring.
    df = gen.generate_did_dataset(n=2000)
    assert df["value_group"].nunique() == 2
    assert set(df["value_group"].unique()) == {"high", "low"}


def test_generate_did_dataset_low_value_group_is_never_treated():
    # LV accounts never receive the offer in-window, by construction --
    # only HV accounts do, starting at DID_LAUNCH_MONTH.
    df = gen.generate_did_dataset(n=2000)
    low = df[df["value_group"] == "low"]
    assert (low["offer_live"] == 0).all()


def test_generate_did_dataset_high_value_group_treated_only_after_launch():
    df = gen.generate_did_dataset(n=2000)
    high = df[df["value_group"] == "high"]
    pre_launch = high[high["event_month"] < gen.TRUTH["did_launch_month"]]
    post_launch = high[high["event_month"] >= gen.TRUTH["did_launch_month"]]
    assert (pre_launch["offer_live"] == 0).all()
    assert post_launch["offer_live"].mean() > 0.9  # effectively all post-launch HV rows are offer_live==1


def test_generate_dormant_dataset_positivity_holds():
    df = gen.generate_dormant_dataset(n=2000)
    treated_share = df["treated"].mean()
    assert 0.02 < treated_share < 0.98


def test_generate_dormant_dataset_offer_type_matches_tier():
    # HV tier only ever gets "cashback" or holdout ("none"); LV tier only
    # ever gets "sms" or holdout -- the two plays should never cross tiers.
    df = gen.generate_dormant_dataset(n=2000)
    hv = df[df["value_group"] == "high"]
    lv = df[df["value_group"] == "low"]
    assert set(hv["offer_type"].unique()) <= {"cashback", "none"}
    assert set(lv["offer_type"].unique()) <= {"sms", "none"}


def test_generate_dormant_dataset_holdout_frac_roughly_matches_config():
    df = gen.generate_dormant_dataset(n=20_000)
    for tier in ["high", "low"]:
        tier_df = df[df["value_group"] == tier]
        holdout_share = (tier_df["treated"] == 0).mean()
        # Random draw around DORMANT_HOLDOUT_FRAC -- generous tolerance since
        # this is a Bernoulli draw, not an exact split.
        assert abs(holdout_share - gen.TRUTH["dormant_holdout_frac"]) < 0.03


def test_split_value_group_is_a_50_50_split_by_rank():
    rng = np.random.default_rng(0)
    values = rng.exponential(1000, size=10_000)
    groups = gen.split_value_group(values, percentile=0.5)
    assert set(groups) == {"high", "low"}
    high_share = (groups == "high").mean()
    assert abs(high_share - 0.5) < 0.01


def test_account_value_matches_config_formula():
    # 01_generate_data.py imports account_value from config.py rather than
    # defining its own copy (see the refactor) -- this test would catch
    # either module silently drifting from the other if that import were
    # ever removed in favor of a local redefinition.
    import config
    assert gen.account_value is config.account_value
