"""Tests for src/config.py -- the account_value() formula and the
reproducibility contract seed_everything() is supposed to provide."""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import config


def test_account_value_formula():
    # balance * (1 + uplift * product_count), spelled out explicitly here
    # (not by calling the function twice) so this test would actually
    # catch someone changing the formula's STRUCTURE, not just its output.
    balance = 1000.0
    product_count = 2
    expected = 1000.0 * (1 + 0.15 * 2)
    assert config.account_value(balance, product_count) == expected


def test_account_value_zero_products_equals_balance():
    # With zero products, the uplift term vanishes entirely -- account_value
    # should reduce to exactly the raw balance, no residual scaling.
    assert config.account_value(5000.0, 0) == 5000.0


def test_account_value_custom_uplift_overrides_default():
    assert config.account_value(1000.0, 1, uplift=0.5) == 1500.0


def test_account_value_vectorized_with_numpy_arrays():
    balance = np.array([100.0, 200.0])
    product_count = np.array([1, 3])
    result = config.account_value(balance, product_count)
    expected = np.array([100 * (1 + 0.15 * 1), 200 * (1 + 0.15 * 3)])
    np.testing.assert_allclose(result, expected)


def test_seed_everything_returns_generator_seeded_correctly():
    gen = config.seed_everything(999)
    draw = gen.random(5)
    expected = np.random.default_rng(999).random(5)
    np.testing.assert_array_equal(draw, expected)


def test_seed_everything_also_seeds_legacy_global_random_state():
    # This is the actual bug fix under test: seed_everything must seed
    # numpy's LEGACY global RandomState too (np.random.seed), not just
    # return a fresh modern Generator -- that legacy stream is what
    # sklearn's KFold(shuffle=True) / DoubleML's cross-fitting draw from
    # internally, and it was never seeded before this fix existed.
    config.seed_everything(123)
    a = np.random.permutation(10)
    config.seed_everything(123)
    b = np.random.permutation(10)
    np.testing.assert_array_equal(a, b)


def test_seed_everything_is_reproducible_across_repeated_calls():
    gen1 = config.seed_everything(config.SEED)
    draws1 = gen1.normal(size=10)
    gen2 = config.seed_everything(config.SEED)
    draws2 = gen2.normal(size=10)
    np.testing.assert_array_equal(draws1, draws2)


def test_xgb_n_jobs_pinned_to_one_for_determinism():
    # See config.py's docstring: multi-threaded XGBoost training is not
    # guaranteed bit-identical across runs even with a fixed random_state,
    # because histogram gradient summation isn't perfectly associative
    # across threads. n_jobs=1 is the fix, and it needs to actually be
    # wired into both hyperparameter dicts that feed XGBoost, not just
    # exist as an unused constant.
    assert config.XGB_N_JOBS == 1
    assert config.PREDICTIVE_MODEL_PARAMS["n_jobs"] == 1
    assert config.DOUBLEML_XGB_PARAMS["n_jobs"] == 1


def test_paths_exist_after_import():
    for d in (config.DATA_DIR, config.FIG_DIR, config.OUT_DIR, config.LOG_DIR):
        assert os.path.isdir(d)
