"""
06_optimization.py

Replaces the real project's informal "intervene on the top 50% by value_score"
cutoff with a formal budget-constrained assignment: given each account's
predicted churn-mode probabilities (03_predictive_model.py) and the CAUSAL
effect sizes recovered for two of the three interventions (RDD -> RM contact,
DiD -> $100 DD offer), choose which accounts get which intervention to
maximize total expected dollars of deposits protected, subject to:
  - a total retention budget
  - a cap on RM contacts (the scarcest resource -- RM time, not money)
  - at most one intervention per account

The dormant/re-engagement play does NOT have a rigorous causal estimate
behind it in this project (no RDD/DiD design covers it) -- that's flagged
explicitly rather than quietly assumed, exactly the kind of gap the real
project's Q7 answer already owns up to.
"""

import json
import numpy as np
import pandas as pd
import pulp
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
FIG_DIR = os.path.join(os.path.dirname(__file__), "..", "figures")
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")

# ---------------------------------------------------------------------------
# Load predicted risk + causal effect sizes from earlier stages
# ---------------------------------------------------------------------------
scores = pd.read_csv(os.path.join(OUT_DIR, "predictive_scores.csv"))
pred_full = pd.read_csv(os.path.join(DATA_DIR, "predictive_data.csv"))
scores = scores.merge(pred_full[["account_id", "balance", "product_count"]], on="account_id", how="left")

with open(os.path.join(OUT_DIR, "rdd_summary.json")) as f:
    rdd = json.load(f)
with open(os.path.join(OUT_DIR, "did_summary.json")) as f:
    did = json.load(f)

EFFECT_PP = {
    "large_withdrawal": abs(rdd["rdd_robust_coef"]),          # ~0.107, RDD-validated
    "dd_stop": abs(did["cs_style_overall_att"]),               # ~0.077, DiD-validated
    "dormant": 0.03,                                            # ASSUMPTION -- not causally validated here
}
EFFECT_SOURCE = {
    "large_withdrawal": "RDD (rdrobust, robust CI)",
    "dd_stop": "Callaway-Sant'Anna-style DiD",
    "dormant": "ASSUMED (no RDD/DiD design covers this play -- flag for a future A/B test)",
}
COST = {"large_withdrawal": 75, "dd_stop": 100, "dormant": 10}
INTERVENTIONS = list(EFFECT_PP.keys())

BUDGET = 150_000          # total monthly retention spend
RM_CAPACITY = 400         # max large-withdrawal RM contacts the team can actually make in a month

print("=== Inputs to the optimization ===")
for k in INTERVENTIONS:
    print(f"{k:>18s}: effect={EFFECT_PP[k]*100:5.2f}pp  cost=${COST[k]:>4d}  source: {EFFECT_SOURCE[k]}")
print(f"Budget=${BUDGET:,}   RM capacity={RM_CAPACITY} contacts\n")

# ---------------------------------------------------------------------------
# Dollar value at stake per account: deposit balance, scaled up for product
# depth (consistent with the real project's value_score logic -- product
# depth was its single biggest driver of customer value)
# ---------------------------------------------------------------------------
scores["dollar_value_at_risk"] = scores["balance"] * (1 + 0.15 * scores["product_count"])

# expected value protected, per account, per candidate intervention:
# P(that churn mode) * effect_size(pp) * dollar_value_at_risk
for k in INTERVENTIONS:
    scores[f"ev_{k}"] = scores[f"proba_{k}"] * EFFECT_PP[k] * scores["dollar_value_at_risk"]
    scores[f"net_{k}"] = scores[f"ev_{k}"] - COST[k]

# ---------------------------------------------------------------------------
# Candidate filtering: only worth modeling as a decision variable if the raw
# EV is positive AND the predicted probability clears a small floor -- keeps
# the ILP a reasonable size without changing the optimal answer (accounts
# below the floor would never be selected anyway)
# ---------------------------------------------------------------------------
candidates = []
for k in INTERVENTIONS:
    sub = scores[(scores[f"proba_{k}"] > 0.01) & (scores[f"net_{k}"] > -COST[k])].copy()
    sub["intervention"] = k
    sub["ev"] = sub[f"ev_{k}"]
    sub["net"] = sub[f"net_{k}"]
    candidates.append(sub[["account_id", "intervention", "ev", "net"]])
cand_df = pd.concat(candidates, ignore_index=True)
print(f"Candidate account-intervention pairs considered: {len(cand_df):,}")

# ---------------------------------------------------------------------------
# ILP: multiple-choice knapsack -- at most one intervention per account,
# subject to total budget and RM-capacity constraints
# ---------------------------------------------------------------------------
prob = pulp.LpProblem("dda_retention_allocation", pulp.LpMaximize)
x = {i: pulp.LpVariable(f"x_{i}", cat="Binary") for i in cand_df.index}

prob += pulp.lpSum(x[i] * cand_df.loc[i, "net"] for i in cand_df.index)

cost_map = cand_df["intervention"].map(COST)
prob += pulp.lpSum(x[i] * cost_map[i] for i in cand_df.index) <= BUDGET, "budget"

rm_idx = cand_df.index[cand_df.intervention == "large_withdrawal"]
prob += pulp.lpSum(x[i] for i in rm_idx) <= RM_CAPACITY, "rm_capacity"

for acct, grp in cand_df.groupby("account_id"):
    if len(grp) > 1:
        prob += pulp.lpSum(x[i] for i in grp.index) <= 1, f"one_per_account_{acct}"

solver = pulp.PULP_CBC_CMD(msg=0)
prob.solve(solver)

cand_df["selected"] = [int(pulp.value(x[i])) for i in cand_df.index]
selected = cand_df[cand_df.selected == 1]

opt_spend = selected["intervention"].map(COST).sum()
opt_value = selected["ev"].sum()
opt_net = selected["net"].sum()
opt_rm = (selected.intervention == "large_withdrawal").sum()

print(f"\n=== Optimized allocation ===")
print(f"Status: {pulp.LpStatus[prob.status]}")
print(selected.groupby("intervention").agg(n=("account_id", "size"), ev=("ev", "sum"), net=("net", "sum")))
print(f"\nTotal accounts treated : {len(selected):,}")
print(f"Total spend            : ${opt_spend:,.0f}  (budget ${BUDGET:,})")
print(f"RM contacts used       : {opt_rm} / {RM_CAPACITY}")
print(f"Total EV protected     : ${opt_value:,.0f}")
print(f"Total NET value (EV - cost): ${opt_net:,.0f}")

# ---------------------------------------------------------------------------
# Benchmark: the real project's original heuristic -- intervene on
# everyone in the top 50% by value_score, matched to each account's single
# MOST LIKELY risk mode (no budget/capacity logic, no ranking by expected
# payoff). Note: the heuristic's "most likely risk mode" is the argmax over
# the three AT-RISK probabilities only (large_withdrawal/dd_stop/dormant),
# not a 4-way argmax including "none" -- with churn this rare, a 4-way
# argmax predicts "none" for virtually everyone (see 03's hard-classification
# report), which would make this comparison meaningless. This is the fairer
# reading of the real project's design: every top-50%-value account gets
# SOME play, whichever mode looks most likely for them -- the heuristic's
# actual weakness is that it doesn't discriminate on risk LEVEL at all
# within that top-50% pool, only on value, which is exactly what the
# optimizer fixes.
# ---------------------------------------------------------------------------
scores["value_rank_pct"] = scores["value_score"].rank(pct=True)
risk_cols = [f"proba_{k}" for k in INTERVENTIONS]
scores["predicted_risk_mode"] = scores[risk_cols].idxmax(axis=1).str.replace("proba_", "", regex=False)

heuristic_pool = scores[scores["value_rank_pct"] >= 0.50].copy()
heuristic_pool["intervention"] = heuristic_pool["predicted_risk_mode"]
heuristic_pool["cost"] = heuristic_pool["intervention"].map(COST)
heuristic_pool["ev"] = heuristic_pool.apply(lambda r: r[f"ev_{r['intervention']}"], axis=1)
heuristic_pool["net"] = heuristic_pool["ev"] - heuristic_pool["cost"]

heur_spend = heuristic_pool["cost"].sum()
heur_value = heuristic_pool["ev"].sum()
heur_net = heuristic_pool["net"].sum()
heur_rm = (heuristic_pool.intervention == "large_withdrawal").sum()

print(f"\n=== Heuristic benchmark (original 'top 50% by value_score' rule) ===")
print(f"Total accounts treated : {len(heuristic_pool):,}")
print(f"Total spend            : ${heur_spend:,.0f}  (no budget cap applied)")
print(f"RM contacts used       : {heur_rm}  (no capacity cap applied)")
print(f"Total EV protected     : ${heur_value:,.0f}")
print(f"Total NET value         : ${heur_net:,.0f}")

# scale the comparison fairly: cap the heuristic pool at the SAME budget by
# processing it in the heuristic's own (value_score) order, to show the
# efficiency gap at equal spend, not just a "we spent more" story
heuristic_pool_sorted = heuristic_pool.sort_values("value_rank_pct", ascending=False).copy()
heuristic_pool_sorted["cum_cost"] = heuristic_pool_sorted["cost"].cumsum()
heuristic_pool_sorted["cum_rm"] = (heuristic_pool_sorted.intervention == "large_withdrawal").cumsum()
capped = heuristic_pool_sorted[(heuristic_pool_sorted["cum_cost"] <= BUDGET) &
                                (heuristic_pool_sorted["cum_rm"] <= RM_CAPACITY)]
capped_net = capped["net"].sum()
capped_spend = capped["cost"].sum()

print(f"\n=== Fair comparison: heuristic capped at the SAME budget/RM capacity ===")
print(f"Heuristic (capped) net value : ${capped_net:,.0f}   (spend ${capped_spend:,.0f}, n={len(capped):,})")
print(f"Optimized net value          : ${opt_net:,.0f}   (spend ${opt_spend:,.0f}, n={len(selected):,})")
if capped_net > 0:
    print(f"Efficiency gain from optimization: {(opt_net / capped_net - 1) * 100:+.1f}%")

# ---------------------------------------------------------------------------
# Figure: net value protected, heuristic (capped) vs. optimized, at equal spend
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(6, 4.5))
bars = ax.bar(["Heuristic\n(top 50% value_score,\nsame budget)", "Optimized\n(ILP, same budget)"],
               [capped_net, opt_net], color=["#C1613C", "#2C4870"])
for b in bars:
    ax.text(b.get_x() + b.get_width() / 2, b.get_height(), f"${b.get_height():,.0f}",
             ha="center", va="bottom", fontsize=10)
ax.set_ylabel("Net expected value protected ($)")
ax.set_title("Same budget, same RM capacity:\noptimization vs. the original heuristic rule")
fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "optimization_comparison.png"), dpi=150)
plt.close(fig)

selected.to_csv(os.path.join(OUT_DIR, "optimized_allocation.csv"), index=False)
summary = {
    "budget": BUDGET, "rm_capacity": RM_CAPACITY,
    "optimized": {"n": int(len(selected)), "spend": float(opt_spend), "rm_used": int(opt_rm),
                  "ev": float(opt_value), "net": float(opt_net)},
    "heuristic_capped": {"n": int(len(capped)), "spend": float(capped_spend), "net": float(capped_net)},
}
with open(os.path.join(OUT_DIR, "optimization_summary.json"), "w") as f:
    json.dump(summary, f, indent=2)
print(f"\nSaved figures/optimization_comparison.png, output/optimized_allocation.csv, output/optimization_summary.json")
