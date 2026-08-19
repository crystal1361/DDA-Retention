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


def test_generate_did_dataset_has_exactly_four_value_tiers():
    df = gen.generate_did_dataset(n=2000)
    assert df["value_tier"].nunique() == 4
    assert set(df["value_tier"].unique()) == set(gen.TRUTH["did_value_tier_labels"])


def test_generate_did_dataset_bottom_tier_is_never_treated():
    # tier4_bottom25pct's adoption_month is None in TRUTH -- those accounts
    # should never show offer_live == 1, by construction.
    df = gen.generate_did_dataset(n=2000)
    bottom = df[df["value_tier"] == "tier4_bottom25pct"]
    assert (bottom["offer_live"] == 0).all()


def test_generate_dormant_dataset_positivity_holds():
    df = gen.generate_dormant_dataset(n=2000)
    treated_share = df["reengagement_contact"].mean()
    assert 0.02 < treated_share < 0.98


def test_account_value_matches_config_formula():
    # 01_generate_data.py imports account_value from config.py rather than
    # defining its own copy (see the refactor) -- this test would catch
    # either module silently drifting from the other if that import were
    # ever removed in favor of a local redefinition.
    import config
    assert gen.account_value is config.account_value
