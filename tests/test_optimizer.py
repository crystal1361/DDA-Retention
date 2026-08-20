"""
Tests for src/06_optimization.py's run_optimization().

Exercises the ILP against small, synthetic, self-contained inputs (not the
real pipeline's output/ files) written to a pytest tmp_path -- this is
exactly what run_optimization()'s out_dir/fig_dir/save parameters exist
for (see 06_optimization.py's refactor notes): before that refactor this
script had no importable function at all, so there was no way to test the
ILP logic without running the full 8-script pipeline first.
"""

import json
import os

import pandas as pd
import pytest

from conftest import load_module

opt_module = load_module("06_optimization.py")


def _write_synthetic_inputs(tmp_path, n=200):
    scores = pd.DataFrame({
        "account_id": [f"A{i:04d}" for i in range(n)],
        "value_score": [1000.0 + 10 * i for i in range(n)],
        "value_group": ["high" if i % 2 == 0 else "low" for i in range(n)],
        "proba_large_withdrawal": [0.5 if i % 10 == 0 else 0.001 for i in range(n)],
        "proba_dd_stop": [0.5 if i % 10 == 1 else 0.001 for i in range(n)],
        "proba_dormant": [0.5 if i % 10 == 2 else 0.001 for i in range(n)],
    })
    scores.to_csv(tmp_path / "predictive_scores.csv", index=False)

    with open(tmp_path / "rdd_summary.json", "w") as f:
        json.dump({"rdd_robust_coef": -0.10}, f)
    with open(tmp_path / "did_summary.json", "w") as f:
        json.dump({"did_regression_coef": -0.04}, f)
    with open(tmp_path / "dormant_summary.json", "w") as f:
        json.dump({"hv_cashback": {"diff": -0.06}, "lv_sms": {"diff": -0.03}}, f)


def test_run_optimization_respects_budget_constraint(tmp_path):
    _write_synthetic_inputs(tmp_path)
    result = opt_module.run_optimization(
        budget=500, rm_capacity=50,
        out_dir=str(tmp_path), fig_dir=str(tmp_path), save=False,
    )
    spend = result["summary"]["optimized"]["spend"]
    assert spend <= 500


def test_run_optimization_respects_rm_capacity_constraint(tmp_path):
    _write_synthetic_inputs(tmp_path)
    result = opt_module.run_optimization(
        budget=1_000_000, rm_capacity=3,
        out_dir=str(tmp_path), fig_dir=str(tmp_path), save=False,
    )
    assert result["summary"]["optimized"]["rm_used"] <= 3


def test_run_optimization_selects_at_most_one_intervention_per_account(tmp_path):
    _write_synthetic_inputs(tmp_path)
    result = opt_module.run_optimization(
        budget=1_000_000, rm_capacity=1_000_000,
        out_dir=str(tmp_path), fig_dir=str(tmp_path), save=False,
    )
    selected = result["selected"]
    counts = selected.groupby("account_id").size()
    assert (counts <= 1).all()


def test_run_optimization_save_false_writes_no_files(tmp_path):
    _write_synthetic_inputs(tmp_path)
    opt_module.run_optimization(
        budget=500, rm_capacity=50,
        out_dir=str(tmp_path), fig_dir=str(tmp_path), save=False,
    )
    assert not (tmp_path / "optimization_summary.json").exists()
    assert not (tmp_path / "optimized_allocation.csv").exists()


def test_run_optimization_raises_on_inconsistent_cost_dict(tmp_path):
    _write_synthetic_inputs(tmp_path)
    from validation import ValidationError
    with pytest.raises(ValidationError):
        opt_module.run_optimization(
            budget=500, rm_capacity=50, cost={"large_withdrawal": 75},  # missing dd_stop/dormant_cashback/dormant_sms
            out_dir=str(tmp_path), fig_dir=str(tmp_path), save=False,
        )


def test_run_optimization_dormant_candidates_respect_tier_eligibility(tmp_path):
    # dormant_cashback should only ever be selected for "high"-tier accounts,
    # dormant_sms only for "low"-tier accounts -- the eligibility split is
    # the whole point of splitting the old single "dormant" intervention
    # into two tier-specific ones (see 06_optimization.py's ELIGIBLE dict).
    _write_synthetic_inputs(tmp_path)
    result = opt_module.run_optimization(
        budget=1_000_000, rm_capacity=1_000_000,
        out_dir=str(tmp_path), fig_dir=str(tmp_path), save=False,
    )
    candidates = result["candidates"]
    scores = pd.read_csv(tmp_path / "predictive_scores.csv")
    tier_map = scores.set_index("account_id")["value_group"]

    cashback = candidates[candidates.intervention == "dormant_cashback"]
    sms = candidates[candidates.intervention == "dormant_sms"]
    assert (cashback["account_id"].map(tier_map) == "high").all()
    assert (sms["account_id"].map(tier_map) == "low").all()
