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
                                (incl. account_value = balance*(1+15%*product_count))
        02_validate_design.py  McCrary manipulation check, DiD parallel-trends check
        03_predictive_model.py multi-class churn-mode model (XGBoost)
        04_rdd_analysis.py     sharp RDD on the 30%-withdrawal RM-outreach trigger
        05_did_analysis.py     value-tier staggered DiD on the DD-stop offer rollout
                                (clean-control / stacked estimator vs. naive TWFE)
        06_optimization.py     budget- & RM-capacity-constrained ILP (PuLP) vs. heuristic
        07_doubleml_dormant.py DoubleML (IRM, XGBoost nuisance, ATT) on the dormant play
                                -- the one trigger with no RDD/DiD-exploitable structure
        08_business_impact.py  translates the optimizer's output into a per-10,000-
                                account dollar figure + confidence-tiered recommendations
data/   generated CSVs + ground_truth.json (run 01 to produce)
figures/  all chart PNGs used in the deck (run 01-08 to produce)
output/   summary JSON/CSVs + the bilingual Q&A docx + classification report
deck/   build_deck.js (pptxgenjs) -> vanguard_dda_deck.pptx  (18 slides)
        build_doc.js (docx) -> ../output/项目二-延伸-RDD-DiD-优化-QA.docx
```

## Reproduce

```bash
pip install -r requirements.txt   # incl. doubleml
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

Data generation is seeded (numpy `default_rng(42)`), so re-running reproduces
the same synthetic dataset. Downstream model-fitting steps (XGBoost, the
predictive model, DoubleML's cross-fitting) are not all individually seeded,
so headline numbers can drift by roughly a percentage point run to run --
the table below reflects the numbers currently checked into `output/` and
`figures/`.

## Headline results (synthetic demo)

| Layer | Result |
|---|---|
| Predictive (multi-class churn mode) | ROC-AUC 0.65-0.72 per mode, 2.8x-3.2x lift at top decile |
| RDD (30% withdrawal -> RM contact) | naive -1.5pp (biased) vs. robust -10.7pp [-14.8, -6.6], p<0.001; within 1.3pp of true injected effect |
| DiD (value-tier staggered DD-stop offer rollout) | naive TWFE -3.5pp vs. clean-control (stacked) -3.7pp (true: -4.7pp) |
| DoubleML (dormant/re-engagement play) | naive +11.2pp (wrong sign) vs. logistic +0.8pp (wrong sign) vs. DoubleML -6.5pp [-8.6, -4.5] (correct sign; true ATT: -9.8pp) |
| Optimization (ILP vs. heuristic) | +63.2% net expected value protected at equal budget & RM capacity ($302,378 vs. $185,299 per 10,000 scored accounts) |
| Business impact | +$117,079 net value per 10,000 scored accounts; scales linearly with book size (see `output/business_impact_summary.json` for the full confidence-tiered recommendation set) |

Every effect size above carries an explicit confidence label (RDD/DiD are
design-based and directly tested; DoubleML is selection-on-observables and
NOT directly testable) -- see the Q&A doc for how each is defended.

The real project's actual, randomized-A/B-test-validated result (-30%
relative churn reduction) is unchanged and stands on its own — see
`项目二DDA 存款流失挽留.docx` in the "面试准备" project.
