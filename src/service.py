"""
service.py

A thin FastAPI wrapper around this project's already-computed outputs and
its optimization logic -- the "how would this actually get consumed
downstream by product/engineering" piece of the production-readiness
checklist (config, validation, logging, seeding, tests, and this).

WHAT THIS DELIBERATELY DOES AND DOES NOT DO:
This does NOT stand up a live-retraining or live-scoring service that
retrains XGBoost per request -- that would be a different (heavier, stateful)
system, and isn't what "wrap it in a service layer" means for a project at
this stage. What it DOES do is expose the pipeline's existing outputs
(predictive scores, the optimizer, the tiered recommendations) over HTTP,
the same shape a real internal tool consuming this pipeline's results would
actually want: "look up this account's risk profile", "re-run the allocation
under a different budget", "give me the current recommendation list" --
without the caller needing to know this is a collection of numbered
scripts writing CSVs, or having shell access to the project directory at
all. That boundary (HTTP API in front of an analytics pipeline, not a
rewrite of the pipeline into a live service) is itself a normal, defensible
production architecture, and one worth being able to explain: the heavy
model-fitting stays a scheduled/batch job (run monthly, say, via
01-08 in order), and this service serves the CURRENT batch's results plus a
narrow, well-defined "re-optimize under a new constraint" endpoint that's
cheap enough (an ILP solve, not a model refit) to run synchronously.

Run locally with:
    uvicorn service:app --reload --port 8000
(from inside src/, so its relative imports of config/validation/the
numbered scripts resolve the same way every other script here does).
"""

import importlib.util
import os
import sys

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from config import OUT_DIR, BUDGET, RM_CAPACITY
from logging_setup import get_logger

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logger = get_logger(__name__)

app = FastAPI(
    title="DDA Retention Decision Engine API",
    description="Serves this project's predictive scores, optimized "
                 "retention allocation, and tiered business recommendations "
                 "over HTTP.",
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# Response models -- Pydantic gives free request/response validation and an
# auto-generated OpenAPI schema (visible at /docs once the service is
# running), which matters here for the same reason validation.py does:
# a caller gets a clear 422 error naming the exact bad field, not a 500
# from something failing three layers downstream.
# ---------------------------------------------------------------------------
class HealthResponse(BaseModel):
    status: str
    predictive_scores_available: bool
    optimization_summary_available: bool


class AccountScore(BaseModel):
    account_id: str
    value_score: float
    value_group: str
    proba_none: float
    proba_large_withdrawal: float
    proba_dd_stop: float
    proba_dormant: float
    predicted_mode: str


class OptimizeRequest(BaseModel):
    budget: float = BUDGET
    rm_capacity: int = RM_CAPACITY


class OptimizeResponse(BaseModel):
    budget: float
    rm_capacity: int
    accounts_treated: int
    total_spend: float
    rm_contacts_used: int
    total_ev_protected: float
    total_net_value: float


# ---------------------------------------------------------------------------
# Lazy-loaded module/data handles -- imported on first use rather than at
# module import time, so `import service` (e.g. from a test) doesn't
# require output/ files to already exist on disk.
# ---------------------------------------------------------------------------
_optimization_module = None


def _load_optimization_module():
    """06_optimization.py's filename starts with a digit, so it can't be
    imported with a normal `import` statement -- load it by file path
    instead. Same technique, same reason, as tests/conftest.py's
    load_module() helper; duplicated here (in ~6 lines) rather than
    importing that test helper into runtime service code, which would make
    the service depend on the tests/ directory being present."""
    global _optimization_module
    if _optimization_module is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "06_optimization.py")
        spec = importlib.util.spec_from_file_location("opt_06", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _optimization_module = module
    return _optimization_module


def _predictive_scores_path():
    return os.path.join(OUT_DIR, "predictive_scores.csv")


def _optimization_summary_path():
    return os.path.join(OUT_DIR, "optimization_summary.json")


def _business_impact_summary_path():
    return os.path.join(OUT_DIR, "business_impact_summary.json")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/health", response_model=HealthResponse)
def health():
    """Liveness/readiness check: is the service up, AND does it have the
    batch outputs it needs to answer the other endpoints? A real load
    balancer or orchestrator should treat 'up but missing its data' as
    not-yet-ready, not as healthy -- returning both facts here lets a
    caller tell the two apart instead of getting a confusing 404 later."""
    return HealthResponse(
        status="ok",
        predictive_scores_available=os.path.exists(_predictive_scores_path()),
        optimization_summary_available=os.path.exists(_optimization_summary_path()),
    )


@app.get("/accounts/{account_id}/score", response_model=AccountScore)
def get_account_score(account_id: str):
    """Look up one account's predicted churn-mode probabilities and value
    score from the most recent batch scoring run (03_predictive_model.py's
    output). 404s with a clear message if the account isn't in the scored
    test set, rather than a KeyError leaking an internal stack trace."""
    path = _predictive_scores_path()
    if not os.path.exists(path):
        raise HTTPException(status_code=503, detail=(
            "predictive_scores.csv not found -- run the batch pipeline "
            "(03_predictive_model.py) before calling this endpoint."
        ))
    scores = pd.read_csv(path)
    row = scores[scores["account_id"] == account_id]
    if row.empty:
        raise HTTPException(status_code=404, detail=(
            f"account_id '{account_id}' not found in the current scored "
            "batch (it may not be in the test-set sample, or may not "
            "exist)."
        ))
    r = row.iloc[0]
    return AccountScore(
        account_id=r["account_id"],
        value_score=float(r["value_score"]),
        value_group=str(r["value_group"]),
        proba_none=float(r["proba_none"]),
        proba_large_withdrawal=float(r["proba_large_withdrawal"]),
        proba_dd_stop=float(r["proba_dd_stop"]),
        proba_dormant=float(r["proba_dormant"]),
        predicted_mode=str(r["predicted_mode"]),
    )


@app.get("/recommendations")
def get_recommendations():
    """Return the current tiered, confidence-labeled recommendation list
    from 08_business_impact.py's last run -- the same list the deck's
    'Actionable Recommendations' slide is built from, so a downstream
    consumer (a dashboard, a scheduled digest) always reflects the latest
    batch rather than a snapshot baked into a slide."""
    path = _business_impact_summary_path()
    if not os.path.exists(path):
        raise HTTPException(status_code=503, detail=(
            "business_impact_summary.json not found -- run the batch "
            "pipeline (08_business_impact.py) before calling this endpoint."
        ))
    import json
    with open(path) as f:
        summary = json.load(f)
    return summary["recommendations"]


@app.post("/optimize", response_model=OptimizeResponse)
def optimize(req: OptimizeRequest):
    """Re-run the budget/RM-capacity-constrained ILP allocation under a
    CALLER-SUPPLIED budget/RM capacity, using the current batch's
    predictive scores and causal effect sizes. This is the one endpoint
    that does real computation synchronously rather than just serving a
    file -- justified because an ILP solve over ~10-20k candidate pairs is
    a sub-second operation (see run_optimization()'s own timing), not a
    model refit; a caller asking 'what if our budget were $200k instead of
    $150k' gets an answer immediately instead of needing to trigger and
    wait on a batch job."""
    try:
        mod = _load_optimization_module()
        result = mod.run_optimization(budget=req.budget, rm_capacity=req.rm_capacity, save=False)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=(
            f"Required batch output missing ({e}) -- run the full pipeline "
            "(01 through 08) before calling /optimize."
        ))
    opt = result["summary"]["optimized"]
    return OptimizeResponse(
        budget=req.budget,
        rm_capacity=req.rm_capacity,
        accounts_treated=opt["n"],
        total_spend=opt["spend"],
        rm_contacts_used=opt["rm_used"],
        total_ev_protected=opt["ev"],
        total_net_value=opt["net"],
    )


if __name__ == "__main__":
    import uvicorn
    logger.info("service: starting uvicorn on 0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
