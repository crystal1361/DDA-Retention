"""
05_did_analysis.py

Staggered-rollout DiD: does the "$100 for 2 direct deposits >= $500" offer
reduce churn among accounts that just stopped direct deposit?

The offer went live region-by-region at different times (cohorts adopting at
month 8, 14, 20; two regions never adopted in-window). That staggered timing
is exactly the situation where the textbook two-way-fixed-effects (TWFE) DiD
regression can be BIASED, because it implicitly uses already-treated cohorts
as part of the "control" trend for later-treated cohorts (Goodman-Bacon 2021).
The bias shows up specifically when the treatment effect isn't flat over time
-- and here it isn't: the DGP has the offer's effect ramp up over its first
3 months (awareness/take-up lag), so an early-adopting cohort's partially-
matured effect contaminates the comparison used for a later cohort.

This script estimates two things and compares them:
  1. Naive static TWFE: churn ~ offer_live + region FE + calendar-month FE
  2. A Callaway-Sant'Anna-style estimator: for each cohort, a clean 2x2
     DiD against ONLY the never-treated regions (never contaminated by
     treatment at any horizon), aggregated across cohorts.
Both are graded against the true average post-adoption effect implied by the
DGP's ramp function.
"""

import json
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
FIG_DIR = os.path.join(os.path.dirname(__file__), "..", "figures")
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def naive_twfe(df):
    print("=== Naive static TWFE DiD (region FE + calendar-month FE) ===")
    model = smf.ols("churned_within_window ~ offer_live + C(region_id) + C(event_month)",
                     data=df).fit(cov_type="cluster", cov_kwds={"groups": df["region_id"]})
    coef = model.params["offer_live"]
    se = model.bse["offer_live"]
    p = model.pvalues["offer_live"]
    print(f"offer_live coefficient: {coef:+.4f}  (cluster-robust SE={se:.4f}, p={p:.4f})")
    print("This pools ALL post-adoption observations under one flat 'offer_live' effect,")
    print("and implicitly leans on already-treated cohorts as part of the comparison")
    print("trend for later cohorts -- exactly the setup Goodman-Bacon shows can bias TWFE")
    print("when the effect isn't constant over time.\n")
    return {"coef": coef, "se": se, "p": p}


def callaway_santanna_style(df):
    print("=== Callaway-Sant'Anna-style estimator (never-treated as clean control) ===")
    never = df[df["cohort"] == "never"]
    cohorts = {"cohortA_m8": 8, "cohortB_m14": 14, "cohortC_m20": 20}

    rows = []
    for cohort_name, g in cohorts.items():
        treat_g = df[df["cohort"] == cohort_name]
        pre_g = treat_g[treat_g.event_month < g]["churned_within_window"].mean()
        post_g = treat_g[treat_g.event_month >= g]["churned_within_window"].mean()
        pre_c = never[never.event_month < g]["churned_within_window"].mean()
        post_c = never[never.event_month >= g]["churned_within_window"].mean()

        att_g = (post_g - pre_g) - (post_c - pre_c)
        n_post = (treat_g.event_month >= g).sum()
        rows.append({"cohort": cohort_name, "adoption_month": g,
                      "pre": pre_g, "post": post_g, "att": att_g, "n_post": n_post})
        print(f"{cohort_name}: pre={pre_g:.4f} post={post_g:.4f} | "
              f"control pre={pre_c:.4f} post={post_c:.4f} -> ATT(g)={att_g:+.4f}  (n_post={n_post})")

    cs_df = pd.DataFrame(rows)
    overall_att = np.average(cs_df["att"], weights=cs_df["n_post"])
    print(f"\nAggregate ATT (weighted by cohort post-period size): {overall_att:+.4f}\n")
    return cs_df, overall_att


def event_study_plot(df, save_path):
    treated = df[df["offer_live"] == 1].copy()
    agg = (treated.groupby("months_since_adoption")["churned_within_window"]
           .agg(["mean", "count"]).reset_index())
    agg = agg[agg["count"] >= 30]  # drop sparse tail bins

    never_baseline = df[df["cohort"] == "never"]["churned_within_window"].mean()

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.plot(agg["months_since_adoption"], agg["mean"], marker="o", color="#C1613C",
             label="Treated accounts (post-adoption), by months since offer went live")
    ax.axhline(never_baseline, color="#2C4870", linestyle="--",
                label=f"Never-treated baseline ({never_baseline:.3f})")
    ax.set_xlabel("Months since offer went live in the account's region")
    ax.set_ylabel("Churn-within-window rate")
    ax.set_title("Event study: the offer's effect ramps in over ~3 months\n(not an instant jump)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)


def grade_against_ground_truth(df, naive_result, overall_att):
    with open(os.path.join(DATA_DIR, "ground_truth.json")) as f:
        truth = json.load(f)

    # true average effect realized in the data: average the ramp function
    # over the months_since_adoption values actually observed among treated obs
    treated = df[df["offer_live"] == 1].copy()
    ramp_frac = np.clip(treated["months_since_adoption"] / truth["did_ramp_months"], 0, 1)
    true_effect_logit = ramp_frac * truth["did_true_effect_logit_max"]

    # convert to an approximate probability-scale average effect using each
    # observation's own baseline rate (never-treated, same calendar month) as reference
    never = df[df["cohort"] == "never"]
    p0_by_month = never.groupby("event_month")["churned_within_window"].mean()
    p0 = treated["event_month"].map(p0_by_month).fillna(never["churned_within_window"].mean())
    logit0 = np.log(p0 / (1 - p0))
    p1 = sigmoid(logit0 + true_effect_logit)
    true_effect_prob_scale = (p1 - p0).mean()

    print("=== Grading both estimators against injected ground truth ===")
    print(f"True average post-adoption effect (probability scale): {true_effect_prob_scale:+.4f}")
    print(f"Naive static TWFE estimate                            : {naive_result['coef']:+.4f}  "
          f"(off by {naive_result['coef'] - true_effect_prob_scale:+.4f})")
    print(f"Callaway-Sant'Anna-style aggregate ATT                : {overall_att:+.4f}  "
          f"(off by {overall_att - true_effect_prob_scale:+.4f})")
    return true_effect_prob_scale


if __name__ == "__main__":
    df = pd.read_csv(os.path.join(DATA_DIR, "did_data.csv"))

    naive_result = naive_twfe(df)
    cs_df, overall_att = callaway_santanna_style(df)
    event_study_plot(df, os.path.join(FIG_DIR, "did_event_study.png"))
    true_effect = grade_against_ground_truth(df, naive_result, overall_att)

    cs_df.to_csv(os.path.join(OUT_DIR, "did_cohort_att.csv"), index=False)
    summary = {
        "naive_twfe_coef": naive_result["coef"],
        "naive_twfe_p": naive_result["p"],
        "cs_style_overall_att": overall_att,
        "true_effect_prob_scale": true_effect,
    }
    with open(os.path.join(OUT_DIR, "did_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSaved figures/did_event_study.png, output/did_cohort_att.csv, output/did_summary.json")
