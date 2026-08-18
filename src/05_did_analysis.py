"""
05_did_analysis.py

Staggered-rollout DiD: does the "$100 for 2 direct deposits >= $500" offer
reduce churn among accounts that just stopped direct deposit?

The offer is rolled out in VALUE-PRIORITIZED WAVES, not all at once -- see
01_generate_data.py's generate_did_dataset() docstring for the business
reason (limited RM/ops capacity, so highest-value accounts get reached
first; the lowest value quartile never gets reached in-window). That
staggered timing is exactly the situation where the textbook two-way-
fixed-effects (TWFE) DiD regression can be BIASED, because it implicitly
uses already-treated cohorts as part of the "control" trend for later-
treated cohorts (Goodman-Bacon 2021) -- and here that bias is compounded by
the fact that WHICH cohort a tier is (i.e. how early it's treated) is itself
correlated with account value, which independently predicts lower churn.
The bias shows up specifically when the treatment effect isn't flat over
time -- and here it isn't: the DGP has the offer's effect ramp up over its
first 3 months (awareness/take-up lag), so an early-adopting cohort's
partially-matured effect contaminates the comparison used for a later
cohort.

This script estimates two things and compares them:
  1. Naive static TWFE: churn ~ offer_live + value-tier FE + calendar-month FE
  2. A "clean-control" (a.k.a. stacked) DiD estimator: for each value tier
     that ever adopts the offer, run a plain 2x2 DiD against ONLY the
     never-treated tier (never contaminated by treatment at any horizon),
     then aggregate across tiers. This is deliberately described in plain
     language rather than by citing a specific named estimator (e.g.
     Callaway & Sant'Anna 2021) -- the actual computation here is the
     simple, intuitive version of "only ever compare a treated group to a
     group that was never treated", closer in spirit to the "stacked
     regression" approach in Cengiz et al. (2019) than to the full
     Callaway-Sant'Anna machinery (which additionally does doubly-robust
     estimation and a multiplier-bootstrap for inference -- machinery this
     script does not implement, so it shouldn't be name-dropped as if it
     did). Simpler claim, fully defensible, and it's exactly what the code
     below does.
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
    print("=== Naive static TWFE DiD (value-tier FE + calendar-month FE) ===")
    # Robust (HC1) rather than cluster-robust SEs here: there are only 4
    # value tiers, and cluster-robust standard errors need a reasonably
    # large NUMBER of clusters to be trustworthy asymptotically -- 4 is too
    # few to lean on. HC1 (heteroskedasticity-robust) is the honest choice
    # given that constraint, and it's what a careful analyst would actually
    # do here rather than clustering just because "that's what you do in
    # panel DiD" -- the right robust-SE choice depends on how many clusters
    # you actually have.
    model = smf.ols("churned_within_window ~ offer_live + C(value_tier) + C(event_month)",
                     data=df).fit(cov_type="HC1")
    coef = model.params["offer_live"]
    se = model.bse["offer_live"]
    p = model.pvalues["offer_live"]
    print(f"offer_live coefficient: {coef:+.4f}  (HC1 robust SE={se:.4f}, p={p:.4f})")
    print("This pools ALL post-adoption observations under one flat 'offer_live' effect,")
    print("and implicitly leans on already-treated (higher-value) tiers as part of the")
    print("comparison trend for later (lower-value) tiers -- exactly the setup")
    print("Goodman-Bacon shows can bias TWFE when the effect isn't constant over time,")
    print("made worse here because tier ALSO independently predicts baseline churn.\n")
    return {"coef": coef, "se": se, "p": p}


def clean_control_did(df):
    print("=== Clean-control (stacked) DiD -- never-treated tier as the only control ===")
    never = df[df["cohort"] == "never"]

    with open(os.path.join(DATA_DIR, "ground_truth.json")) as f:
        truth = json.load(f)
    # Pull adoption months from ground truth rather than hardcoding them a
    # second time here -- one source of truth, so a future change to the
    # rollout schedule in 01_generate_data.py can't silently desync from
    # what this script assumes.
    cohorts = {tier: month for tier, month in truth["did_adoption_months"].items()
               if month is not None}

    rows = []
    for cohort_name, g in cohorts.items():
        treat_g = df[df["cohort"] == cohort_name]
        pre_g = treat_g[treat_g.event_month < g]["churned_within_window"].mean()
        post_g = treat_g[treat_g.event_month >= g]["churned_within_window"].mean()
        pre_c = never[never.event_month < g]["churned_within_window"].mean()
        post_c = never[never.event_month >= g]["churned_within_window"].mean()

        # This is a plain 2x2 DiD, done once per adoption cohort:
        #   (post-treated - pre-treated) - (post-control - pre-control)
        # The ONLY thing that makes this different from a textbook 2x2 DiD
        # is that "control" here is ALWAYS the never-treated tier, never
        # another (already-treated) cohort -- that's the one change that
        # avoids the staggered-adoption bias entirely.
        att_g = (post_g - pre_g) - (post_c - pre_c)
        n_post = (treat_g.event_month >= g).sum()
        rows.append({"cohort": cohort_name, "adoption_month": g,
                      "pre": pre_g, "post": post_g, "att": att_g, "n_post": n_post})
        print(f"{cohort_name}: pre={pre_g:.4f} post={post_g:.4f} | "
              f"control pre={pre_c:.4f} post={post_c:.4f} -> ATT(g)={att_g:+.4f}  (n_post={n_post})")

    cs_df = pd.DataFrame(rows)
    # Aggregate the per-cohort ATTs into one overall number, weighting each
    # cohort by how many post-adoption observations it contributes -- a
    # cohort we've observed for longer / with more accounts should count
    # for more than a cohort we've barely started observing.
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
    ax.set_xlabel("Months since offer went live for the account's value tier")
    ax.set_ylabel("Churn-within-window rate")
    ax.set_title("Event study: the offer's effect ramps in over ~3 months\n(not an instant jump)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)


def grade_against_ground_truth(df, naive_result, overall_att):
    # True average post-adoption effect, on the probability scale, averaged
    # over treated (offer_live==1) observations. Read directly from the
    # 'true_effect_prob' column that 01_generate_data.py computed row-by-row
    # from its own baseline_logit -- i.e. this is EXACT, not an
    # approximation borrowed from some other group's average rate.
    #
    # (An earlier version of this script approximated it using the
    # never-treated tier's calendar-month-matched average rate as a stand-in
    # baseline. That approximation quietly assumed treated and never-treated
    # groups share the same baseline level, which is fine when the grouping
    # variable barely affects the baseline (as with the old region-based
    # design) but breaks once the grouping variable is STRONGLY related to
    # baseline risk by construction -- exactly what value-tiering does here.
    # Using each row's own DGP-implied counterfactual avoids that mismatch
    # entirely, which matters because we deliberately want the confound to
    # be large enough that naive TWFE visibly struggles with it.)
    treated = df[df["offer_live"] == 1].copy()
    true_effect_prob_scale = treated["true_effect_prob"].mean()

    print("=== Grading both estimators against injected ground truth ===")
    print(f"True average post-adoption effect (probability scale): {true_effect_prob_scale:+.4f}")
    print(f"Naive static TWFE estimate                            : {naive_result['coef']:+.4f}  "
          f"(off by {naive_result['coef'] - true_effect_prob_scale:+.4f})")
    print(f"Clean-control (stacked) DiD aggregate ATT             : {overall_att:+.4f}  "
          f"(off by {overall_att - true_effect_prob_scale:+.4f})")
    return true_effect_prob_scale


if __name__ == "__main__":
    df = pd.read_csv(os.path.join(DATA_DIR, "did_data.csv"))

    naive_result = naive_twfe(df)
    cc_df, overall_att = clean_control_did(df)
    event_study_plot(df, os.path.join(FIG_DIR, "did_event_study.png"))
    true_effect = grade_against_ground_truth(df, naive_result, overall_att)

    cc_df.to_csv(os.path.join(OUT_DIR, "did_cohort_att.csv"), index=False)
    summary = {
        "naive_twfe_coef": naive_result["coef"],
        "naive_twfe_p": naive_result["p"],
        "clean_control_overall_att": overall_att,
        "true_effect_prob_scale": true_effect,
    }
    with open(os.path.join(OUT_DIR, "did_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSaved figures/did_event_study.png, output/did_cohort_att.csv, output/did_summary.json")
