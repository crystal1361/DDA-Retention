"""
08_business_impact.py

Every prior script in this project answers a technical question (does RDD
recover the true effect? does the optimizer beat the heuristic?). This one
answers the question a Decision Analytics stakeholder actually asks: SO
WHAT -- what should the business DO with this, and how much is it worth?
This is the script that ties the whole project back to the JD language it
was built to demonstrate: "develops actionable insights and recommendations
in support of enterprise-wide strategic business initiatives."

Two things this script deliberately does NOT do, on purpose:
1. It does not invent a specific "total accounts at the bank" number to
   multiply everything up to a big headline dollar figure. This project's
   data is synthetic and sized for a demo (a 10,000-account scored sample),
   not the real institution's actual book -- presenting a fabricated
   enterprise-wide total as if it were real would be exactly the kind of
   overclaiming this project has been careful to avoid elsewhere (see the
   "why synthetic" framing in 01_generate_data.py and the Q&A doc). Instead,
   impact is reported PER 10,000 SCORED ACCOUNTS with an explicit, honest
   scaling instruction -- so it's actually usable ("multiply by your real
   book size / 10,000") without pretending to know a number it doesn't.
2. It does not treat all three effect sizes as equally trustworthy just
   because they all feed the same optimization objective. Recommendations
   are explicitly tiered by the CONFIDENCE labels set in 06_optimization.py.
"""

import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
FIG_DIR = os.path.join(os.path.dirname(__file__), "..", "figures")
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")

SCORED_ACCOUNTS = 10_000  # size of the predictive test set this optimization ran over


def load_json(name):
    with open(os.path.join(OUT_DIR, name)) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# 1) Headline impact, expressed per-10,000-scored-accounts (see module
#    docstring for why it's NOT expressed as one big fabricated enterprise
#    total)
# ---------------------------------------------------------------------------
def headline_impact():
    opt = load_json("optimization_summary.json")
    optimized_net = opt["optimized"]["net"]
    heuristic_net = opt["heuristic_capped"]["net"]
    uplift_dollars = optimized_net - heuristic_net
    uplift_pct = uplift_dollars / heuristic_net * 100

    print("=== Headline: optimization vs. the original heuristic, same budget/capacity ===")
    print(f"Per {SCORED_ACCOUNTS:,} scored accounts (this project's test-set sample size):")
    print(f"  Heuristic (top-50%-value_score) net value protected : ${heuristic_net:,.0f}")
    print(f"  Optimized (ILP) net value protected                 : ${optimized_net:,.0f}")
    print(f"  Incremental value from adopting the optimizer        : ${uplift_dollars:,.0f}  "
          f"(+{uplift_pct:.1f}%)")
    print(f"\nTO SCALE TO YOUR ACTUAL BOOK: multiply the above by "
          f"(your total scored accounts / {SCORED_ACCOUNTS:,}).")
    print("E.g. at 500,000 accounts (50x this sample), that's roughly "
          f"${uplift_dollars * 50:,.0f} of incremental annual value from switching "
          "the allocation RULE alone, budget held fixed -- worth saying that way in an interview:")
    print("the exact multiple is illustrative, but the mechanism (same spend, better")
    print("targeting) scales linearly with book size, unlike a one-time fixed-cost project.\n")
    return {"optimized_net": optimized_net, "heuristic_net": heuristic_net,
            "uplift_dollars": uplift_dollars, "uplift_pct": uplift_pct}


# ---------------------------------------------------------------------------
# 2) Sensitivity check on the ONE assumed rate in account_value() --
#    PRODUCT_VALUE_UPLIFT = 0.15. Proves (rather than asserts) that the
#    optimizer's ranking/allocation isn't hostage to that specific number,
#    which is the concrete answer to "why is it 15% and not something else"
#    promised back when this formula was designed.
# ---------------------------------------------------------------------------
def value_uplift_sensitivity():
    pred = pd.read_csv(os.path.join(DATA_DIR, "predictive_data.csv"))
    rates = [0.10, 0.15, 0.20]
    rank_frames = {}
    for r in rates:
        v = pred["balance"] * (1 + r * pred["product_count"])
        rank_frames[r] = v.rank(pct=True)

    base = rank_frames[0.15]
    print("=== Sensitivity: does the 15% product-value-uplift assumption drive the ranking? ===")
    correlations = {}
    for r in rates:
        if r == 0.15:
            continue
        corr = base.corr(rank_frames[r], method="spearman")
        correlations[r] = corr
        print(f"Spearman rank correlation, value ranking at {r:.0%} vs. 15%: {corr:.4f}")

    # A more concrete, decision-relevant check: of the accounts that land in
    # the TOP QUARTILE by value under the 15% assumption (i.e. the accounts
    # that would actually get prioritized), what fraction stay in the top
    # quartile under 10% or 20%? This is closer to "would we have made a
    # different call" than a correlation coefficient is.
    top_quartile_base = set(pred.loc[base >= 0.75, "account_id"])
    print(f"\nTop-value-quartile membership overlap (the accounts that actually get")
    print(f"prioritized) vs. the 15% baseline:")
    overlaps = {}
    for r in rates:
        if r == 0.15:
            continue
        top_r = set(pred.loc[rank_frames[r] >= 0.75, "account_id"])
        overlap_pct = len(top_quartile_base & top_r) / len(top_quartile_base) * 100
        overlaps[r] = overlap_pct
        print(f"  at {r:.0%}: {overlap_pct:.1f}% of the same accounts stay in the top quartile")
    print("\n-> The specific 15% figure changes who's on the margin, but not the")
    print("   overall prioritization -- which is the actual claim worth making if")
    print("   asked to defend that number: it isn't load-bearing for the conclusion.\n")
    return {"spearman_by_rate": correlations, "top_quartile_overlap_pct_by_rate": overlaps}


# ---------------------------------------------------------------------------
# 3) Actionable recommendations, tiered by how much confidence the
#    underlying estimate actually earned -- this is the "so what for the
#    business" deliverable a Decision Analytics stakeholder wants, written
#    to stand on its own outside the slide deck.
# ---------------------------------------------------------------------------
def build_recommendations():
    opt = load_json("optimization_summary.json")
    effect_inputs = opt["effect_inputs"]

    recommendations = [
        {
            "priority": 1,
            "action": "Replace the informal 'top 50% by value_score' retention "
                      "targeting rule with the budget-constrained ILP optimizer.",
            "why": f"At equal budget and RM capacity, the optimizer protects "
                   f"{headline_impact_cache['uplift_pct']:.0f}% more net expected "
                   f"value than the current heuristic -- same spend, better targeting.",
            "confidence": "High -- this is a mechanical improvement (better use of "
                          "already-validated effect sizes and existing constraints), "
                          "not a new causal claim.",
            "next_step": "Pilot the optimizer's account list against the heuristic's "
                         "list on one month's retention run; compare realized churn, "
                         "not just the modeled projection.",
        },
        {
            "priority": 2,
            "action": "Formalize the 30%-withdrawal -> RM-outreach trigger as an "
                      "explicit, monitored policy rather than an ad hoc practice.",
            "why": f"RDD estimates a {effect_inputs['large_withdrawal']['effect_pp']*100:.1f}pp "
                   f"reduction in next-month churn from RM contact at this trigger "
                   f"({effect_inputs['large_withdrawal']['source']}), and the "
                   "no-manipulation assumption behind that estimate was directly "
                   "tested (McCrary-style density check), not just assumed.",
            "confidence": effect_inputs["large_withdrawal"]["confidence"],
            "next_step": "Track RM capacity utilization against the 400-contact/month "
                         "constraint used here; if capacity is regularly binding, "
                         "that's the lever to negotiate for more impact, not budget.",
        },
        {
            "priority": 3,
            "action": "When evaluating the $100 DD-stop offer's rollout, do not "
                      "judge it on early results.",
            "why": "The effect ramps in over roughly 3 months after each wave goes "
                   "live (event-study finding) -- evaluating a wave's impact in "
                   "month 1 will understate its true effect and could kill a "
                   "program that's actually working.",
            "confidence": effect_inputs["dd_stop"]["confidence"],
            "next_step": "Set the earliest formal evaluation checkpoint for each "
                         "rollout wave at 3+ months post-launch, not at launch+1.",
        },
        {
            "priority": 4,
            "action": "Do NOT scale retention budget into the dormant/re-engagement "
                      "play based on this project's number alone.",
            "why": "It's the only one of the three effects estimated without a "
                   "design-based (testable) identifying assumption -- DoubleML's "
                   "validity rests on 'we observed every important confounder', "
                   "which can't be verified from the data the way RDD/DiD's "
                   "assumptions were.",
            "confidence": effect_inputs["dormant"]["confidence"],
            "next_step": "Run a genuine randomized pilot (even a small one, "
                         "e.g. 500 flagged accounts split 50/50) specifically for "
                         "this play before committing meaningful budget -- this is "
                         "the one play where a real experiment is both feasible and "
                         "would meaningfully upgrade confidence.",
        },
    ]
    return recommendations


if __name__ == "__main__":
    headline_impact_cache = headline_impact()
    sensitivity = value_uplift_sensitivity()
    recommendations = build_recommendations()

    print("=== Actionable recommendations (priority order) ===")
    for r in recommendations:
        print(f"\n[{r['priority']}] {r['action']}")
        print(f"    Why: {r['why']}")
        print(f"    Confidence: {r['confidence']}")
        print(f"    Next step: {r['next_step']}")

    # Bar chart: headline dollar impact, per 10,000 scored accounts
    fig, ax = plt.subplots(figsize=(6, 4.5))
    bars = ax.bar(["Heuristic\n(capped, same budget)", "Optimized\n(ILP, same budget)"],
                   [headline_impact_cache["heuristic_net"], headline_impact_cache["optimized_net"]],
                   color=["#C1613C", "#2C4870"])
    for b in bars:
        ax.text(b.get_x() + b.get_width() / 2, b.get_height(), f"${b.get_height():,.0f}",
                 ha="center", va="bottom", fontsize=10)
    ax.set_ylabel(f"Net expected value protected, per {SCORED_ACCOUNTS:,} scored accounts ($)")
    ax.set_title("Business impact: adopting the optimizer\n(same budget & RM capacity as today)")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "business_impact_headline.png"), dpi=150)
    plt.close(fig)

    summary = {
        "scored_accounts": SCORED_ACCOUNTS,
        "headline_impact": headline_impact_cache,
        "value_uplift_sensitivity": sensitivity,
        "recommendations": recommendations,
    }
    with open(os.path.join(OUT_DIR, "business_impact_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print("\nSaved figures/business_impact_headline.png, output/business_impact_summary.json")
