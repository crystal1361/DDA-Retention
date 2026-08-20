"""Tests for src/validation.py -- each validator's pass and fail paths."""

import sys
import os

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from validation import (
    ValidationError, require_columns, require_no_nulls, require_range,
    require_row_count, require_probabilities, require_positivity,
    validate_rdd_data, validate_did_data, validate_dormant_data,
    validate_optimization_inputs,
)


def test_require_columns_passes_when_present():
    df = pd.DataFrame({"a": [1], "b": [2]})
    require_columns(df, ["a", "b"], context="t")  # should not raise


def test_require_columns_raises_when_missing():
    df = pd.DataFrame({"a": [1]})
    with pytest.raises(ValidationError, match="missing required column"):
        require_columns(df, ["a", "b"], context="t")


def test_require_no_nulls_raises_on_null():
    df = pd.DataFrame({"a": [1, None, 3]})
    with pytest.raises(ValidationError, match="null"):
        require_no_nulls(df, ["a"], context="t")


def test_require_range_raises_below_minimum():
    df = pd.DataFrame({"a": [-1, 2, 3]})
    with pytest.raises(ValidationError, match="below"):
        require_range(df, "a", lo=0, context="t")


def test_require_range_raises_above_maximum():
    df = pd.DataFrame({"a": [1, 2, 300]})
    with pytest.raises(ValidationError, match="above"):
        require_range(df, "a", hi=100, context="t")


def test_require_row_count_raises_when_too_few():
    df = pd.DataFrame({"a": [1, 2]})
    with pytest.raises(ValidationError, match="at least"):
        require_row_count(df, min_rows=5, context="t")


def test_require_probabilities_raises_on_out_of_range_value():
    df = pd.DataFrame({"p": [0.1, 1.5]})
    with pytest.raises(ValidationError):
        require_probabilities(df, ["p"], context="t")


def test_require_positivity_raises_when_treated_share_too_low():
    series = pd.Series([0] * 99 + [1])  # 1% treated
    with pytest.raises(ValidationError, match="positivity"):
        require_positivity(series, min_share=0.02, max_share=0.98, context="t")


def test_require_positivity_passes_in_band():
    series = pd.Series([0] * 70 + [1] * 30)  # 30% treated
    require_positivity(series, context="t")  # should not raise


def test_validate_rdd_data_passes_on_exact_sharp_assignment():
    df = pd.DataFrame({
        "withdrawal_pct": [10.0, 20.0, 30.0, 40.0] * 30,
        "treated_rm_contact": [0, 0, 1, 1] * 30,
    })
    validate_rdd_data(df, cutoff=30.0, treatment_col="treated_rm_contact")


def test_validate_rdd_data_raises_on_fuzzy_violation():
    # one row (withdrawal_pct=30, i.e. AT the cutoff) has treated=0, which
    # violates the sharp assignment rule (>=cutoff must imply treated=1) --
    # this is exactly the class of bug the boundary-rounding fix in
    # 01_generate_data.py addresses.
    df = pd.DataFrame({
        "withdrawal_pct": [10.0, 20.0, 30.0, 40.0] * 30,
        "treated_rm_contact": [0, 0, 0, 1] * 30,
    })
    with pytest.raises(ValidationError, match="sharp-RDD"):
        validate_rdd_data(df, cutoff=30.0, treatment_col="treated_rm_contact")


def test_validate_did_data_raises_on_wrong_group_count():
    df = pd.DataFrame({"value_group": ["a", "b", "c", "d"] * 30})
    with pytest.raises(ValidationError, match="value groups"):
        validate_did_data(df, value_col="value_group", expected_groups=2)


def test_validate_did_data_passes_with_two_groups():
    df = pd.DataFrame({"value_group": ["high", "low", "high", "low"] * 30})
    validate_did_data(df, value_col="value_group", expected_groups=2)


def test_validate_dormant_data_raises_on_positivity_violation():
    df = pd.DataFrame({"dormant_treated": [0] * 199 + [1]})
    with pytest.raises(ValidationError, match="positivity"):
        validate_dormant_data(df, treatment_col="dormant_treated")


def test_validate_optimization_inputs_raises_on_mismatched_keys():
    effect_pp = {"a": 0.1, "b": 0.2}
    effect_source = {"a": "src"}  # missing "b"
    cost = {"a": 10, "b": 20}
    with pytest.raises(ValidationError, match="don't match"):
        validate_optimization_inputs(effect_pp, effect_source, cost, budget=100, rm_capacity=10)


def test_validate_optimization_inputs_raises_on_missing_cost():
    effect_pp = {"a": 0.1}
    effect_source = {"a": "src"}
    cost = {}  # missing "a"
    with pytest.raises(ValidationError, match="no entry in the cost"):
        validate_optimization_inputs(effect_pp, effect_source, cost, budget=100, rm_capacity=10)


def test_validate_optimization_inputs_raises_on_nonpositive_budget():
    effect_pp = {"a": 0.1}
    effect_source = {"a": "src"}
    cost = {"a": 10}
    with pytest.raises(ValidationError, match="budget"):
        validate_optimization_inputs(effect_pp, effect_source, cost, budget=0, rm_capacity=10)


def test_validate_optimization_inputs_passes_on_consistent_inputs():
    effect_pp = {"a": 0.1, "b": 0.2}
    effect_source = {"a": "src_a", "b": "src_b"}
    cost = {"a": 10, "b": 20}
    validate_optimization_inputs(effect_pp, effect_source, cost, budget=100, rm_capacity=10)
