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
src/    01_generate_data.py    synthetic panel data + injected ground truth
        02_validate_design.py  McCrary manipulation check, DiD parallel-trends check
        03_predictive_model.py multi-class churn-mode model (XGBoost)
        04_rdd_analysis.py     sharp RDD on the 30%-withdrawal RM-outreach trigger
        05_did_analysis.py     staggered-adoption DiD on the DD-stop offer rollout
        06_optimization.py     budget-constrained ILP (PuLP) vs. heuristic benchmark
data/   generated CSVs + ground_truth.json (run 01 to produce)
figures/  all chart PNGs used in the deck (run 01-06 to produce)
output/   summary JSON/CSVs + the bilingual Q&A docx + classification report
deck/   build_deck.js (pptxgenjs) -> vanguard_dda_deck.pptx
        build_doc.js (docx) -> ../output/项目二-延伸-RDD-DiD-优化-QA.docx
```

## Reproduce

```bash
pip install -r requirements.txt
cd src
python3 01_generate_data.py
python3 02_validate_design.py
python3 03_predictive_model.py
python3 04_rdd_analysis.py
python3 05_did_analysis.py
python3 06_optimization.py
cd ../deck
node build_deck.js   # requires: npm install -g pptxgenjs (or local node_modules)
node build_doc.js    # requires: npm install -g docx
```

All scripts are seeded (numpy `default_rng(42)` / `(7)`) so re-running
reproduces identical numbers and figures.

## Headline results (synthetic demo)

| Layer | Result |
|---|---|
| Predictive (multi-class churn mode) | ROC-AUC 0.65-0.72 per mode, 2.8x-3.2x lift at top decile |
| RDD (30% withdrawal -> RM contact) | naive -1.5pp (biased) vs. robust -10.7pp [-14.8, -6.6], p<0.001; within 1.3pp of true injected effect |
| DiD (staggered DD-stop offer rollout) | naive TWFE -8.5pp vs. Callaway-Sant'Anna-style -7.7pp (true: -6.4pp) |
| Optimization (ILP vs. heuristic) | +497% net expected value protected at equal budget & RM capacity |

The real project's actual, randomized-A/B-test-validated result (-30%
relative churn reduction) is unchanged and stands on its own — see
`项目二DDA 存款流失挽留.docx` in the "面试准备" project.
