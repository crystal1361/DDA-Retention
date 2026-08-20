# DDA Retention Decision Engine — Vanguard Interview Demo

A purpose-built analytical engine, grounded in a real DDA (checking account)
retention problem, demonstrating the quasi-experimental causal inference and
formal optimization emphasized by the Vanguard Data Scientist (Decision
Analytics) JD. Built for a 20-minute technical presentation, not a
production system, and not presented as a literal retrofit of the original
project's design -- see `deck/vanguard_dda_deck.pptx` slide 3 for the exact
framing.

**Important:** all data here is synthetic, generated with a known
ground-truth causal effect baked in, specifically so the RDD, DiD, and
randomized-holdout RCT estimators could be validated against a known answer
before being trusted conceptually. See
`output/项目二-延伸-RDD-DiD-优化-QA.docx` Q1 for how to talk about this
honestly in an interview.

## Structure

```
src/    config.py               single source of truth for paths, SEED, model
                                 hyperparameters, and business constants (budget,
                                 RM capacity, costs, the HV/LV value-split percentile,
                                 the DiD launch month, the dormant holdout fraction)
        validation.py           "fail loud and early" data validation (schema, nulls,
                                 ranges, positivity, sharp-RDD assignment-rule checks)
        logging_setup.py        structured logging (console + logs/<script>.log),
                                 alongside -- not replacing -- each script's print()
                                 narration
        service.py              FastAPI wrapper exposing the batch pipeline's
                                 outputs + a synchronous /optimize endpoint over HTTP
        01_generate_data.py     synthetic panel data + injected ground truth
                                 (incl. account_value = balance*(1+15%*product_count)
                                 and the shared 50/50 HV/LV split used by RDD, DiD,
                                 and the dormant RCT)
        02_validate_design.py   McCrary manipulation check, DiD parallel-trends check,
                                 and the dormant RCT's randomization-balance ("Table 1") check
        03_predictive_model.py  multi-class churn-mode model (XGBoost)
        04_rdd_analysis.py      sharp RDD on the 30%-withdrawal RM-outreach trigger (HV only)
        05_did_analysis.py      2-group DiD (HV vs. LV, single launch date) on the
                                 DD-stop offer rollout -- 2x2 differencing cross-checked
                                 against a fixed-effects regression
        06_optimization.py      budget- & RM-capacity-constrained ILP (PuLP) vs.
                                 heuristic, wrapped in run_optimization() so it's
                                 importable/testable without side effects on import
        07_dormant_rct.py       tier-stratified randomized-holdout RCT on the dormant
                                 play (HV: cashback vs. holdout; LV: SMS vs. holdout) --
                                 two independent two-proportion z-tests
        08_business_impact.py   translates the optimizer's output into a per-10,000-
                                 account dollar figure + confidence-labeled recommendations
tests/  pytest suite (config, validation, data-generation invariants, the optimizer's
        ILP behavior incl. tier eligibility, and the FastAPI service) -- see "Tests" below
data/   generated CSVs + ground_truth.json (run 01 to produce)
figures/  all chart PNGs used in the deck (run 01-08 to produce)
output/   summary JSON/CSVs + the bilingual Q&A docx + classification report
logs/     per-script structured logs (from logging_setup.py)
deck/   build_deck.js (pptxgenjs) -> vanguard_dda_deck.pptx  (20 slides, incl. 1 appendix)
        build_doc.js (docx) -> ../output/项目二-延伸-RDD-DiD-优化-QA.docx
        build_speech_script.js (docx) -> presentation_speech_script.docx
```

## Reproduce

```bash
pip install -r requirements.txt   # incl. pytest, fastapi, uvicorn
cd src
python3 01_generate_data.py
python3 02_validate_design.py
python3 03_predictive_model.py
python3 04_rdd_analysis.py
python3 05_did_analysis.py
python3 07_dormant_rct.py         # must run before 06 -- optimizer reads its output
python3 06_optimization.py
python3 08_business_impact.py
cd ../deck
node build_deck.js            # requires: npm install -g pptxgenjs (or local node_modules)
node build_doc.js             # requires: npm install -g docx
node build_speech_script.js   # requires: /tmp/slides_script.json (per-slide narration)
```

Every random-number source this pipeline touches is seeded via
`config.seed_everything()`: numpy's modern Generator API (used directly by
`01_generate_data.py`) AND numpy's legacy global RandomState (which
scikit-learn's `shuffle=True` code paths draw from when no explicit
`random_state` is given). XGBoost training is also pinned to `n_jobs=1` (see
`config.py`'s docstring) to remove multi-threaded floating-point
nondeterminism from histogram gradient summation. Result: two independent
full runs of `01` through `08` produce byte-identical `data/`, `output/`,
and `figures/` -- verified directly before writing this note. The table
below reflects the numbers currently checked into `output/` and `figures/`,
and re-running the pipeline will reproduce them exactly.

## Tests

```bash
pip install -r requirements.txt
cd .. && python3 -m pytest tests/ -v
```

Covers: `config.py`'s `account_value()` formula, the HV/LV split and
dormant-holdout constants, and the seeding contract above; every
`validation.py` check's pass/fail path (including the sharp-RDD
assignment-rule violation that generation's boundary-rounding fix
addresses, and the DiD validator's 2-group check); `01_generate_data.py`'s
dataset generators (value-group split, positivity, exact-match to the sharp
assignment rule, dormant offer-type/tier consistency);
`06_optimization.py`'s `run_optimization()` against small synthetic inputs
(budget/RM-capacity constraints honored, at-most-one-intervention-per-account,
dormant tier-eligibility respected); and `service.py`'s endpoints (health,
404 on an unknown account, budget honored by `/optimize`). Scripts are
numbered for readability (`01_generate_data.py` etc.), which isn't a valid
Python import name -- `tests/conftest.py`'s `load_module()` loads them by
file path instead; see its docstring.

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
| RDD (30% withdrawal -> RM contact, HV only) | naive -0.2pp (biased, near zero) vs. robust -8.3pp [-12.3, -4.3], p<0.001; within ~1pp of true injected local effect |
| DiD (2-group, HV vs. LV, single launch date) | 2x2 differencing -5.8pp vs. regression -5.8pp (agree almost exactly; true: -5.1pp) |
| Dormant RCT (tier-stratified randomized holdout) | HV cashback: -10.8pp [-14.5, -7.1], p<0.001 (true: -10.4pp). LV SMS: -5.8pp [-9.8, -1.9], p=0.002 (true: -6.0pp). 0/10 covariate-balance tests flagged. |
| Optimization (ILP vs. heuristic) | +49.4% net expected value protected at equal budget & RM capacity ($405,066 vs. $271,193 per 10,000 scored accounts) |
| Business impact | +$133,873 net value per 10,000 scored accounts; scales linearly with book size (see `output/business_impact_summary.json` for the full recommendation set) |

Every effect size above is now design-based (RDD's no-manipulation check,
DiD's parallel-trends check, and the dormant RCT's randomization-balance
check are all directly testable and all pass) -- see the Q&A doc for how
each is defended, and for the external-validity caveat that every estimate
is scoped to the specific tier it was tested on.

The real project's actual, randomized-A/B-test-validated result (-30%
relative churn reduction) is unchanged and stands on its own — see
`项目二DDA 存款流失挽留.docx` in the "面试准备" project.
