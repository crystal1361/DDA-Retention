"""
Tests for src/service.py, using FastAPI's TestClient (no real server/socket
needed). These run against whatever is CURRENTLY in output/ -- i.e. they're
integration tests of the service against the last real pipeline run, not
fully isolated unit tests, which is the right tradeoff here: the interesting
behavior to test (does /health correctly report file presence, does a
missing account 404 instead of 500, does /optimize honor a caller-supplied
budget) is about the service's own logic, not about re-deriving the
pipeline's numbers.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

fastapi_testclient = pytest.importorskip("fastapi.testclient")
import service
from config import OUT_DIR

client = fastapi_testclient.TestClient(service.app)


def test_health_reports_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.skipif(
    not os.path.exists(os.path.join(OUT_DIR, "predictive_scores.csv")),
    reason="predictive_scores.csv not present -- run 03_predictive_model.py first",
)
def test_score_lookup_for_real_account_succeeds():
    import pandas as pd
    scores = pd.read_csv(os.path.join(OUT_DIR, "predictive_scores.csv"))
    account_id = scores.iloc[0]["account_id"]
    r = client.get(f"/accounts/{account_id}/score")
    assert r.status_code == 200
    body = r.json()
    assert body["account_id"] == account_id
    assert 0.0 <= body["proba_none"] <= 1.0
    assert body["value_group"] in ("high", "low")


def test_score_lookup_for_missing_account_404s_not_500s():
    r = client.get("/accounts/DEFINITELY_NOT_A_REAL_ACCOUNT_ID/score")
    assert r.status_code == 404


@pytest.mark.skipif(
    not os.path.exists(os.path.join(OUT_DIR, "optimization_summary.json")),
    reason="optimization_summary.json not present -- run the pipeline through 06 first",
)
def test_optimize_endpoint_honors_requested_budget():
    r = client.post("/optimize", json={"budget": 10_000, "rm_capacity": 20})
    assert r.status_code == 200
    body = r.json()
    assert body["total_spend"] <= 10_000
    assert body["rm_contacts_used"] <= 20
