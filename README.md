# DDA Retention Decision Engine — Vanguard Interview Demo

A technical rebuild of a real DDA (checking account) retention project, adding
the quasi-experimental causal inference and formal optimization emphasized by
the Vanguard Data Scientist (Decision Analytics) JD. Built for a 20-minute
technical presentation, not a production system.

**Important:** all data here is synthetic, generated with a known
ground-truth causal effect baked in, specifically so the RDD and DiD
estimators could be validated against a known answer before being trusted
conceptually. See `deck/vanguard_dda_deck.pptx` slide 3 and
`output/项目二-延伸-RDD-DiD-优化-QA.docx` Q1 for how to talk about this
honestly in an interview.

## Structure

```
src/    config.py               single source of truth for paths, SEED, model
                                 hyperparameters, and business constants (budget,
                                 RM capacity, costs, the product-value-uplift rate)
        validation.py           "fail loud and early" data validation (schema, nulls,
                                 ranges, positivity, sharp-RDD assignment-rule checks)
        logging_setup.py        structured logging (console + logs/<script>.log),
                                 alongside -- not replacing -- each script's print()
                                 narration
        service.py              FastAPI wrapper exposing the batch pipeline's
                                 outputs + a synchronous /optimize endpoint over HTTP
        01_generate_data.py     synthetic panel data + injected ground truth
                                 (incl. account_value = balance*(1+15%*product_count))
        02_validate_design.py   McCrary manipulation check, DiD parallel-trends check
        03_predictive_model.py  multi-class churn-mode model (XGBoost)
        04_rdd_analysis.py      sharp RDD on the 30%-withdrawal RM-outreach trigger
        05_did_analysis.py      value-tier staggered DiD on the DD-stop offer rollout
                                 (clean-control / stacked estimator vs. naive TWFE)
        06_optimization.py      budget- & RM-capacity-constrained ILP (PuLP) vs.
                                 heuristic, wrapped in run_optimization() so it's
                                 importable/testable without side effects on import
        07_doubleml_dormant.py  DoubleML (IRM, XGBoost nuisance, ATT) on the dormant
                                 play -- the one trigger with no RDD/DiD-exploitable
                                 structure
        08_business_impact.py   translates the optimizer's output into a per-10,000-
                                 account dollar figure + confidence-tiered recommendations
tests/  pytest suite (config, validation, data-generation invariants, the optimizer's
        ILP behavior, and the FastAPI service) -- see "Tests" below
data/   generated CSVs + ground_truth.json (run 01 to produce)
figures/  all chart PNGs used in the deck (run 01-08 to produce)
output/   summary JSON/CSVs + the bilingual Q&A docx + classification report
logs/     per-script structured logs (from logging_setup.py)
deck/   build_deck.js (pptxgenjs) -> vanguard_dda_deck.pptx  (18 slides)
        build_doc.js (docx) -> ../output/项目二-延伸-RDD-DiD-优化-QA.docx
```

## Reproduce

```bash
pip install -r requirements.txt   # incl. doubleml, pytest, fastapi, uvicorn
cd src
python3 01_generate_data.py
python3 02_validate_design.py
python3 03_predictive_model.py
python3 04_rdd_analysis.py
python3 05_did_analysis.py
python3 07_doubleml_dormant.py    # must run before 06 -- optimizer reads its output
python3 06_optimization.py
python3 08_business_impact.py
cd ../deck
node build_deck.js   # requires: npm install -g pptxgenjs (or local node_modules)
node build_doc.js    # requires: npm install -g docx
```

Every random-number source this pipeline touches is seeded via
`config.seed_everything()`: numpy's modern Generator API (used directly by
`01_generate_data.py`) AND numpy's legacy global RandomState (which
scikit-learn's `KFold(shuffle=True)` and, transitively, DoubleML's internal
cross-fitting fold-splitting draw from when no explicit `random_state` is
given -- this was previously unseeded and was the actual source of the
run-to-run drift this section used to warn about). XGBoost training is also
pinned to `n_jobs=1` (see `config.py`'s docstring) to remove multi-threaded
floating-point nondeterminism from histogram gradient summation. Result:
two independent full runs of `01` through `08` produce byte-identical
`data/`, `output/`, and `figures/` -- verified directly before writing this
note. The table below reflects the numbers currently checked into `output/`
and `figures/`, and re-running the pipeline will reproduce them exactly.

## Tests

```bash
pip install -r requirements.txt
cd .. && python3 -m pytest tests/ -v
```

Covers: `config.py`'s `account_value()` formula and the seeding contract
above; every `validation.py` check's pass/fail path (including the
sharp-RDD assignment-rule violation that generation's boundary-rounding fix
addresses); `01_generate_data.py`'s dataset generators (tier counts,
positivity, exact-match to the sharp assignment rule); `06_optimization.py`'s
`run_optimization()` against small synthetic inputs (budget/RM-capacity
constraints honored, at-most-one-intervention-per-account); and
`service.py`'s endpoints (health, 404 on an unknown account, budget honored
by `/optimize`). Scripts are numbered for readability (`01_generate_data.py`
etc.), which isn't a valid Python import name -- `tests/conftest.py`'s
`load_module()` loads them by file path instead; see its docstring.

## Service layer

```bash
cd src && uvicorn service:app --reload --port 8000
# then: curl localhost:8000/health
```

`GET /health`, `GET /accounts/{id}/score`, `GET /recommendations`, and
`POST /optimize` (re-runs the ILP synchronously under a caller-supplied
budget/RM capacity). See `service.py`'s module docstring for the
batch-pipeline-vs-live-service boundary this is deliberately drawn at.

## Headline results (synthetic demo)

| Layer | Result |
|---|---|
| Predictive (multi-class churn mode) | ROC-AUC 0.65-0.72 per mode, 2.8x-3.2x lift at top decile |
| RDD (30% withdrawal -> RM contact) | naive -1.5pp (biased) vs. robust -10.7pp [-14.8, -6.6], p<0.001; within 1.3pp of true injected effect |
| DiD (value-tier staggered DD-stop offer rollout) | naive TWFE -3.5pp vs. clean-control (stacked) -3.7pp (true: -4.7pp) |
| DoubleML (dormant/re-engagement play) | naive +11.2pp (wrong sign) vs. logistic +0.8pp (wrong sign) vs. DoubleML -6.5pp [-8.6, -4.5] (correct sign; true ATT: -9.8pp) |
| Optimization (ILP vs. heuristic) | +63.2% net expected value protected at equal budget & RM capacity ($300,187 vs. $183,976 per 10,000 scored accounts) |
| Business impact | +$116,211 net value per 10,000 scored accounts; scales linearly with book size (see `output/business_impact_summary.json` for the full confidence-tiered recommendation set) |

Every effect size above carries an explicit confidence label (RDD/DiD are
design-based and directly tested; DoubleML is selection-on-observables and
NOT directly testable) -- see the Q&A doc for how each is defended.

The real project's actual, randomized-A/B-test-validated result (-30%
relative churn reduction) is unchanged and stands on its own — see
`项目二DDA 存款流失挽留.docx` in the "面试准备" project.
