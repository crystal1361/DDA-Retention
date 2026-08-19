const pptxgen = require("pptxgenjs");
const path = require("path");

const FIG = (name) => path.join(__dirname, "..", "figures", name);

// ---------------------------------------------------------------------------
// Palette: "Midnight Executive" navy + ice blue, terracotta accent.
// Navy dominates (title/closing backgrounds, headers, body text).
// Terracotta always marks "the thing to look at" (treatment / optimized /
// the number that matters) so it reads consistently slide to slide.
// ---------------------------------------------------------------------------
const NAVY = "1E2761";
const NAVY_MID = "2C4870";
const ICE = "CADCFC";
const ICE_TINT = "EEF3FC";
const TERRACOTTA = "C1613C";
const WHITE = "FFFFFF";
const MUTED = "5B6B8C";
const TEXT = "1E2761";

const FONT_HEAD = "Cambria";
const FONT_BODY = "Calibri";

function newPres() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.3 x 7.5
  return pres;
}

function darkSlide(pres) {
  const s = pres.addSlide();
  s.background = { color: NAVY };
  return s;
}
function lightSlide(pres) {
  const s = pres.addSlide();
  s.background = { color: WHITE };
  return s;
}

function kicker(s, text, opts = {}) {
  s.addText(text.toUpperCase(), {
    x: opts.x ?? 0.6, y: opts.y ?? 0.4, w: opts.w ?? 8, h: 0.35,
    fontFace: FONT_BODY, fontSize: 12, bold: true, color: TERRACOTTA,
    charSpacing: 2, margin: 0,
  });
}

function slideTitle(s, text, opts = {}) {
  s.addText(text, {
    x: opts.x ?? 0.6, y: opts.y ?? 0.72, w: opts.w ?? 11.8, h: opts.h ?? 0.9,
    fontFace: FONT_HEAD, fontSize: opts.size ?? 28, bold: true, color: opts.color ?? NAVY,
    margin: 0, valign: "top",
  });
}

function pageNum(s, n) {
  s.addText(String(n), {
    x: 12.6, y: 7.05, w: 0.5, h: 0.3, fontFace: FONT_BODY, fontSize: 10,
    color: MUTED, align: "right", margin: 0,
  });
}

function statCard(s, x, y, w, h, value, label, opts = {}) {
  s.addShape("roundRect", {
    x, y, w, h, rectRadius: 0.08,
    fill: { color: opts.fill ?? ICE_TINT }, line: { type: "none" },
    shadow: opts.shadow ?? { type: "outer", color: "1E2761", opacity: 0.12, blur: 6, offset: 2, angle: 90 },
  });
  s.addText(value, {
    x: x + 0.12, y: y + 0.12, w: w - 0.24, h: h * 0.55,
    fontFace: FONT_HEAD, fontSize: opts.valueSize ?? 30, bold: true,
    color: opts.valueColor ?? TERRACOTTA, align: "left", valign: "bottom", margin: 0,
  });
  s.addText(label, {
    x: x + 0.12, y: y + h * 0.6, w: w - 0.24, h: h * 0.38,
    fontFace: FONT_BODY, fontSize: opts.labelSize ?? 11, color: MUTED,
    align: "left", valign: "top", margin: 0,
  });
}

function badge(s, x, y, d, num, color = TERRACOTTA) {
  s.addShape("ellipse", { x, y, w: d, h: d, fill: { color }, line: { type: "none" } });
  s.addText(String(num), {
    x, y, w: d, h: d, fontFace: FONT_HEAD, fontSize: d * 28, bold: true,
    color: WHITE, align: "center", valign: "middle", margin: 0,
  });
}

// ---------------------------------------------------------------------------

const pres = newPres();

// ============================================================ SLIDE 1: TITLE
{
  const s = darkSlide(pres);
  s.addShape("ellipse", { x: 10.6, y: -2.2, w: 6, h: 6, fill: { color: NAVY_MID }, line: { type: "none" } });
  s.addShape("ellipse", { x: 11.8, y: 4.6, w: 3.2, h: 3.2, fill: { color: TERRACOTTA }, line: { type: "none" }, });

  s.addText("DDA RETENTION  ·  DECISION ANALYTICS", {
    x: 0.7, y: 1.55, w: 10, h: 0.4, fontFace: FONT_BODY, fontSize: 13, bold: true,
    color: ICE, charSpacing: 2, margin: 0,
  });
  s.addText("From a Heuristic Rule to a\nCausal, Optimized Decision Engine", {
    x: 0.7, y: 2.05, w: 10.8, h: 2.1, fontFace: FONT_HEAD, fontSize: 40, bold: true,
    color: WHITE, margin: 0, lineSpacingMultiple: 1.08,
  });
  s.addText("Rebuilding a real DDA retention project with quasi-experimental causal inference "
    + "(RDD + value-tier DiD + DoubleML) and formal budget optimization, translated into "
    + "quantified business impact", {
    x: 0.7, y: 4.05, w: 10.8, h: 0.9, fontFace: FONT_BODY, fontSize: 15, italic: true,
    color: ICE, margin: 0,
  });
  s.addText("Presented for: Data Analyst, Senior Specialist / Data Scientist — Decision Analytics & Modeling, Vanguard", {
    x: 0.7, y: 6.55, w: 10, h: 0.4, fontFace: FONT_BODY, fontSize: 12, color: MUTED, margin: 0,
  });
  s.addNotes(
    "Open by framing this as a real project I'm rebuilding to layer in rigor the JD specifically calls for: "
    + "quasi-experimental causal inference and formal optimization under uncertainty. Say up front that today's "
    + "data is synthetic (next slide explains why) but the methods and the underlying real project are real."
  );
}

// ============================================================ SLIDE 2: SITUATION
{
  const s = lightSlide(pres);
  kicker(s, "Situation");
  slideTitle(s, "We were losing checking accounts —\nand only found out after they'd already closed");
  pageNum(s, 2);

  const items = [
    ["No early-warning system", "Attrition was visible only in the rear-view mirror: the account was already closed by the time it showed up in a report."],
    ["One-size-fits-all retention", "Every at-risk account got the same generic outreach, regardless of why it was actually at risk."],
    ["DDA is the low-cost funding base", "Every checking relationship lost isn't just a balance — it's lifetime value and future cross-sell, gone."],
  ];
  let y = 2.3;
  items.forEach(([h, b], i) => {
    badge(s, 0.7, y, 0.5, i + 1, NAVY_MID);
    s.addText(h, { x: 1.45, y: y - 0.05, w: 10.5, h: 0.4, fontFace: FONT_HEAD, fontSize: 17, bold: true, color: NAVY, margin: 0 });
    s.addText(b, { x: 1.45, y: y + 0.38, w: 10.6, h: 0.7, fontFace: FONT_BODY, fontSize: 13, color: MUTED, margin: 0 });
    y += 1.5;
  });
  s.addNotes(
    "This is the real situation from my actual project. RMs and the retention team had no forward-looking signal, "
    + "and the retention motion that did exist wasn't differentiated by WHY someone was at risk."
  );
}

// ============================================================ SLIDE 3: TASK / FRAMING
{
  const s = lightSlide(pres);
  kicker(s, "Task — and what you're about to see");
  slideTitle(s, "Two things layered together: a real project,\nand a rebuild that adds the rigor this role asks for");
  pageNum(s, 3);

  s.addShape("roundRect", {
    x: 0.6, y: 2.2, w: 5.9, h: 4.35, rectRadius: 0.08,
    fill: { color: ICE_TINT }, line: { type: "none" },
  });
  s.addText("WHAT I ACTUALLY BUILT", { x: 0.95, y: 2.45, w: 5.2, h: 0.35, fontFace: FONT_BODY, fontSize: 12, bold: true, color: TERRACOTTA, charSpacing: 1.5, margin: 0 });
  s.addText([
    { text: "Multi-class model predicting HOW an at-risk account would churn (large withdrawal / DD stop / dormant)", options: { bullet: true, breakLine: true } },
    { text: "Trigger-based interventions, one per churn mode", options: { bullet: true, breakLine: true } },
    { text: "Validated with a randomized A/B test: 30% relative churn reduction", options: { bullet: true, breakLine: true } },
    { text: "Gap I owned at the time: validation leaned on the A/B test alone — no quasi-experimental analysis, no formal budget optimization, no quantified business case", options: { bullet: true, breakLine: true } },
  ], { x: 0.95, y: 2.9, w: 5.2, h: 3.5, fontFace: FONT_BODY, fontSize: 12.5, color: NAVY, lineSpacingMultiple: 1.15, margin: 0, paraSpaceAfter: 8 });

  s.addShape("roundRect", {
    x: 6.8, y: 2.2, w: 5.9, h: 4.35, rectRadius: 0.08,
    fill: { color: NAVY }, line: { type: "none" },
  });
  s.addText("WHAT I'M WALKING THROUGH TODAY", { x: 7.15, y: 2.45, w: 5.2, h: 0.35, fontFace: FONT_BODY, fontSize: 12, bold: true, color: TERRACOTTA, charSpacing: 1.5, margin: 0 });
  s.addText([
    { text: "A rebuild that closes that gap, on my own time, with synthetic data (real account data obviously can't leave the bank)", options: { bullet: true, breakLine: true } },
    { text: "None of the three triggers were randomized — RDD, a value-tier staggered DiD, and DoubleML (for the one trigger with no exploitable design at all) identify each one's causal effect instead", options: { bullet: true, breakLine: true } },
    { text: "The old \"top 50% by value\" cutoff becomes a formal budget- and capacity-constrained optimization", options: { bullet: true, breakLine: true } },
    { text: "Every result is translated into a quantified, confidence-tiered business recommendation — and I know the true effect I built into the data, so I can grade whether my own methods recover it", options: { bullet: true, breakLine: true } },
  ], { x: 7.15, y: 2.9, w: 5.2, h: 3.5, fontFace: FONT_BODY, fontSize: 12.5, color: WHITE, lineSpacingMultiple: 1.15, margin: 0, paraSpaceAfter: 8 });

  s.addNotes(
    "Be very explicit and upfront here: this is honest framing, not a trick. The real project and its real "
    + "A/B-tested result are true. Today's code/slides are a demonstration I built to show the additional analytical "
    + "engine skills this role asks for -- quasi-experimental causal inference, formal optimization, and business "
    + "translation -- using synthetic data with a KNOWN ground truth so I can validate my own methods before ever "
    + "trusting them on a real problem."
  );
}

// ============================================================ SLIDE 4: ARCHITECTURE
{
  const s = lightSlide(pres);
  kicker(s, "Approach");
  slideTitle(s, "The analytical engine: three layers, one decision");
  pageNum(s, 4);

  const boxes = [
    ["1", "PREDICT", "Multi-class model: which churn mode is this account heading toward?", NAVY_MID],
    ["2", "EXPLAIN (CAUSAL)", "RDD, value-tier DiD, and DoubleML: what's the true effect of each intervention, isolated from confounds — picking the method that fits each trigger's actual structure?", TERRACOTTA],
    ["3", "OPTIMIZE", "Budget & capacity-constrained ILP: given effects and costs, who gets what, this month?", NAVY_MID],
  ];
  let x = 0.7;
  const w = 3.85, gap = 0.35;
  boxes.forEach(([num, head, body, color], i) => {
    s.addShape("roundRect", { x, y: 2.35, w, h: 3.6, rectRadius: 0.08, fill: { color: ICE_TINT }, line: { type: "none" } });
    badge(s, x + 0.3, 2.65, 0.55, num, color);
    s.addText(head, { x: x + 0.3, y: 3.4, w: w - 0.6, h: 0.4, fontFace: FONT_HEAD, fontSize: 16, bold: true, color: NAVY, margin: 0 });
    s.addText(body, { x: x + 0.3, y: 3.85, w: w - 0.6, h: 1.9, fontFace: FONT_BODY, fontSize: 12.5, color: MUTED, margin: 0, lineSpacingMultiple: 1.2 });
    if (i < 2) {
      s.addText("→", { x: x + w + 0.02, y: 3.7, w: gap - 0.04, h: 0.6, fontFace: FONT_BODY, fontSize: 26, bold: true, color: TERRACOTTA, align: "center", margin: 0 });
    }
    x += w + gap;
  });
  s.addText("Same structure as the real project (predict → trigger-matched action) — the new layers make the "
    + "\"why,\" the \"how much to spend,\" and the \"so what for the business\" rigorous instead of assumed.", {
    x: 0.7, y: 6.15, w: 11.9, h: 0.6, fontFace: FONT_BODY, fontSize: 12.5, italic: true, color: MUTED, margin: 0,
  });
  s.addNotes(
    "This maps directly to the JD language: 'design the analytical engine... how relationships are modeled... how "
    + "outputs are generated for decision-making.' Predict/Explain/Optimize is that engine; the business-impact "
    + "layer at the end is what turns the engine's output into something a stakeholder can act on."
  );
}

// ============================================================ SLIDE 5: PREDICTIVE LAYER
{
  const s = lightSlide(pres);
  kicker(s, "Layer 1 — Predict");
  slideTitle(s, "Which way is this account most likely to churn?");
  pageNum(s, 5);

  s.addImage({ path: FIG("feature_importance.png"), x: 0.6, y: 2.15, w: 6.7, h: 4.75 });

  statCard(s, 7.55, 2.15, 5.15, 1.1, "0.65 – 0.72", "ROC-AUC per churn mode (one-vs-rest)");
  statCard(s, 7.55, 3.4, 5.15, 1.1, "2.8x – 3.2x", "Lift at top decile vs. base rate");
  s.addText("Churn is rare (~11% combined across modes) and driven by noisy human behavior — this isn't a "
    + "0.95-AUC problem. In production you rank and act on the top slice your capacity allows, not hard-classify "
    + "at a single threshold, exactly like the 30%-withdrawal cutoff on the next slides.", {
    x: 7.55, y: 4.75, w: 5.15, h: 2.1, fontFace: FONT_BODY, fontSize: 12.5, color: MUTED, margin: 0, lineSpacingMultiple: 1.25,
  });
  s.addNotes(
    "Engagement, DD stability, and liquidity-need scores dominate, as expected -- and region importance sits at "
    + "noise level, a good sanity check that the model isn't picking up spurious geography effects. I evaluate by "
    + "ranking quality, not hard-classification accuracy, because forcing balanced weights on an 89%-none target "
    + "produces garbage precision numbers that don't reflect how the model is actually used."
  );
}

// ============================================================ SLIDE 6: CAUSAL LAYER INTRO
{
  const s = lightSlide(pres);
  kicker(s, "Layer 2 — Explain (Causal)");
  slideTitle(s, "Three triggers. None of them were randomized.");
  pageNum(s, 6);

  const rows = [
    ["Large withdrawal > 30% of balance\n→ RM calls, pitches alternatives",
     "Deterministic rule, not a coin flip",
     "Regression Discontinuity (RDD)",
     "Compare accounts just above vs.\njust below the 30% line"],
    ["Direct deposit stops\n→ $100 offer for 2 new DDs $500+",
     "Rolled out by customer-value tier — RM capacity is the real constraint, not geography",
     "Clean-control (stacked) DiD",
     "Compare not-yet-treated value\ntiers to already-treated tiers"],
    ["Dormancy signal\n→ re-engagement reminder",
     "No design at all to exploit — account gets flagged and treated together, no threshold or rollout",
     "DoubleML (selection-on-observables)",
     "ML-adjusted comparison,\nconditioning on everything observed"],
  ];
  let y = 2.15;
  const rh = 1.55;
  rows.forEach(([trigger, why, method, how]) => {
    s.addShape("roundRect", { x: 0.6, y, w: 11.9, h: rh, rectRadius: 0.07, fill: { color: ICE_TINT }, line: { type: "none" } });
    s.addText(trigger, { x: 0.9, y: y + 0.14, w: 4.5, h: rh - 0.28, fontFace: FONT_BODY, fontSize: 12.5, bold: true, color: NAVY, margin: 0, lineSpacingMultiple: 1.15, valign: "middle" });
    s.addText(why, { x: 5.45, y: y + 0.14, w: 2.7, h: rh - 0.28, fontFace: FONT_BODY, fontSize: 10.8, italic: true, color: MUTED, margin: 0, lineSpacingMultiple: 1.18, valign: "middle" });
    s.addText(method, { x: 8.25, y: y + 0.18, w: 4.05, h: 0.5, fontFace: FONT_HEAD, fontSize: 14, bold: true, color: TERRACOTTA, margin: 0 });
    s.addText(how, { x: 8.25, y: y + 0.65, w: 4.05, h: 0.85, fontFace: FONT_BODY, fontSize: 10.8, color: MUTED, margin: 0, lineSpacingMultiple: 1.18 });
    y += rh + 0.2;
  });
  s.addNotes(
    "This is the core of what the JD is asking for: causal inference 'in situations where randomized testing is "
    + "not feasible, practical, or cost-effective.' All three are real, non-randomized business situations, so I "
    + "pick the quasi-experimental design that fits each one's structure rather than forcing one method on all "
    + "three. The third row is deliberately the weakest identification of the three -- I say that openly, both "
    + "here and later on the limitations slide."
  );
}

// ============================================================ SLIDE 7: RDD DESIGN
{
  const s = lightSlide(pres);
  kicker(s, "RDD — Design & Validation");
  slideTitle(s, "The identifying assumption: no one can “game” the 30% line");
  pageNum(s, 7);

  s.addImage({ path: FIG("rdd_density_check.png"), x: 0.6, y: 2.15, w: 7.0, h: 4.7 });
  s.addText("McCrary-style density test", { x: 7.9, y: 2.3, w: 4.8, h: 0.4, fontFace: FONT_HEAD, fontSize: 15, bold: true, color: NAVY, margin: 0 });
  s.addText("If customers could nudge a withdrawal just above/below 30% to trigger or dodge an RM call, "
    + "the density of the running variable would jump at the cutoff — and RDD would be invalid.", {
    x: 7.9, y: 2.75, w: 4.8, h: 1.3, fontFace: FONT_BODY, fontSize: 12, color: MUTED, margin: 0, lineSpacingMultiple: 1.25,
  });
  statCard(s, 7.9, 4.2, 4.8, 1.0, "p = 0.151", "Local log-density jump at cutoff (bootstrap test)", { valueSize: 24 });
  s.addText("No evidence of manipulation — withdrawal size is a real economic behavior, not something dialed "
    + "in to dodge a phone call.", {
    x: 7.9, y: 5.35, w: 4.8, h: 1.3, fontFace: FONT_BODY, fontSize: 12, color: MUTED, margin: 0, lineSpacingMultiple: 1.25,
  });
  s.addNotes(
    "This check matters because RDD's validity hinges entirely on people not being able to precisely manipulate "
    + "which side of the cutoff they land on. I run this BEFORE trusting any effect estimate."
  );
}

// ============================================================ SLIDE 8: RDD RESULT
{
  const s = lightSlide(pres);
  kicker(s, "RDD — Result");
  slideTitle(s, "RM outreach cuts next-month churn by ~11 points at the margin");
  pageNum(s, 8);

  s.addImage({ path: FIG("rdd_effect_plot.png"), x: 0.6, y: 2.15, w: 7.5, h: 4.75 });

  statCard(s, 8.35, 2.15, 4.35, 1.05, "-1.5 pp", "Naive treated-vs-control (biased by confound)", { valueColor: MUTED, valueSize: 24 });
  statCard(s, 8.35, 3.35, 4.35, 1.05, "-10.7 pp", "RDD robust estimate  ·  95% CI [-14.8, -6.6]  ·  p<0.001", { valueSize: 26 });
  s.addText("Bandwidth sensitivity: stable between -9.4pp and -10.7pp across h = 4 to 20 months. Graded "
    + "against the effect I built into the simulation: RDD lands within 1.3pp of the true value — the naive "
    + "comparison doesn't.", {
    x: 8.35, y: 4.6, w: 4.35, h: 2.0, fontFace: FONT_BODY, fontSize: 12, color: MUTED, margin: 0, lineSpacingMultiple: 1.25,
  });
  s.addNotes(
    "The naive comparison looks almost nothing like the true effect because bigger withdrawals were already "
    + "higher-risk before any outreach -- that confound roughly cancels out the real negative effect of the call. "
    + "RDD isolates it by comparing only the narrow window right around the cutoff, where the confound is "
    + "approximately constant on both sides."
  );
}

// ============================================================ SLIDE 9: DID DESIGN
{
  const s = lightSlide(pres);
  kicker(s, "DiD — Design & Validation");
  slideTitle(s, "The offer rolled out by customer-value tier — a staggered natural experiment");
  pageNum(s, 9);

  s.addImage({ path: FIG("did_pretrends_check.png"), x: 0.6, y: 2.15, w: 7.4, h: 4.6 });
  s.addText("Parallel pre-trends check", { x: 8.15, y: 2.3, w: 4.55, h: 0.4, fontFace: FONT_HEAD, fontSize: 15, bold: true, color: NAVY, margin: 0 });
  s.addText("RM capacity is limited, so the offer rolled out to the top-value tier first, then the next, "
    + "then the next — tier 4 (bottom 25% by value) hadn't gone live by the end of the observation window. "
    + "DiD's core assumption: before any tier goes live, they should trend together.", {
    x: 8.15, y: 2.75, w: 4.55, h: 1.6, fontFace: FONT_BODY, fontSize: 11.5, color: MUTED, margin: 0, lineSpacingMultiple: 1.22,
  });
  statCard(s, 8.15, 4.55, 4.55, 1.0, "p = 0.951", "F-test on tier × month interaction, common pre-period", { valueSize: 24 });
  s.addText("No evidence of differential pre-trends. (Restricted to the common window before ANY tier "
    + "adopts — mixing in tiers with unequal pre-period length would bias this test.)", {
    x: 8.15, y: 5.65, w: 4.55, h: 1.1, fontFace: FONT_BODY, fontSize: 11, italic: true, color: MUTED, margin: 0, lineSpacingMultiple: 1.2,
  });
  s.addNotes(
    "Point out the deliberate design choice: staggering by CUSTOMER VALUE TIER rather than region is the more "
    + "realistic mechanism for a bank -- ops/RM bandwidth is genuinely scarce, so a phased rollout by value tier "
    + "is exactly how a program like this would actually go out the door. It also makes the naive-TWFE bias "
    + "sharper and easier to explain: high-value tiers already tend to have different baseline churn than "
    + "low-value tiers, so which tier you're in is correlated with both treatment timing AND the outcome -- "
    + "textbook confound structure for staggered-adoption bias. I also restricted the interaction test to the "
    + "common pre-period window, because comparing tiers with very different amounts of pre-period data would "
    + "itself create a spurious 'differential trend' finding unrelated to the actual assumption being tested."
  );
}

// ============================================================ SLIDE 10: DID RESULT
{
  const s = lightSlide(pres);
  kicker(s, "DiD — Result");
  slideTitle(s, "The naive estimator and a clean-control one — and why I check both");
  pageNum(s, 10);

  s.addImage({ path: FIG("did_event_study.png"), x: 0.6, y: 2.15, w: 7.4, h: 4.55 });

  statCard(s, 8.15, 2.15, 4.55, 0.95, "-3.5 pp", "Naive static TWFE (tier + month FE)", { valueColor: MUTED, valueSize: 22 });
  statCard(s, 8.15, 3.25, 4.55, 0.95, "-3.7 pp", "Clean-control (stacked) DiD", { valueSize: 24 });
  s.addText("Effect ramps in over ~3 months as RM awareness and take-up build. Naive TWFE pools all tiers "
    + "and periods into one regression, so already-treated tiers implicitly contaminate the comparison trend "
    + "for later tiers (Goodman-Bacon 2021 negative-weighting bias). The clean-control estimator instead "
    + "compares each newly-treated tier only to tiers that are NOT YET treated at that point (in the spirit "
    + "of Cengiz et al. 2019's stacked-regression approach) and lands closer to the true simulated effect "
    + "(-4.7pp).", {
    x: 8.15, y: 4.35, w: 4.55, h: 2.6, fontFace: FONT_BODY, fontSize: 11.5, color: MUTED, margin: 0, lineSpacingMultiple: 1.22,
  });
  s.addNotes(
    "Be honest here if pressed: the gap between naive and clean-control is real but not huge in this simulation -- "
    + "I'd say the point isn't that naive TWFE blew up spectacularly here, it's that you can't assume it won't. "
    + "With more tiers, longer ramps, or more heterogeneity, that gap widens, so checking for it is the "
    + "discipline, not the headline number. If asked whether this is Callaway-Sant'Anna: no -- it's a simpler "
    + "clean-control comparison that captures the same intuition (don't let already-treated units bias the "
    + "control group) without CS's full doubly-robust, bootstrapped machinery. I'd reach for the real CS "
    + "estimator (or DoubleML-based staggered-DiD tools) if I needed the extra robustness in production."
  );
}

// ============================================================ SLIDE 11: DOUBLEML (DORMANT)
{
  const s = lightSlide(pres);
  kicker(s, "Layer 2 (cont.) — dormant play: no design to exploit");
  slideTitle(s, "No cutoff, no rollout — adjust for confounders directly with ML");
  pageNum(s, 11);

  s.addImage({ path: FIG("doubleml_dormant.png"), x: 0.6, y: 2.15, w: 6.6, h: 4.75 });

  s.addText("Why this one's different", { x: 7.5, y: 2.15, w: 5.2, h: 0.4, fontFace: FONT_HEAD, fontSize: 14.5, bold: true, color: NAVY, margin: 0 });
  s.addText("Accounts get flagged (dormancy streak, or a low-engagement + short dormancy combination) and "
    + "treated together — no threshold like RDD, no phased rollout like DiD. The flagging rule itself is the "
    + "confound: the accounts most likely to be flagged are also the ones most likely to churn anyway "
    + "(\"confounding by indication\"). That's WHY the naive and even logistic-adjusted comparisons below get "
    + "the wrong sign.", {
    x: 7.5, y: 2.55, w: 5.2, h: 1.85, fontFace: FONT_BODY, fontSize: 11.5, color: MUTED, margin: 0, lineSpacingMultiple: 1.22,
  });
  statCard(s, 7.5, 4.45, 2.5, 0.95, "+11.2pp", "Naive diff — wrong sign", { valueColor: MUTED, valueSize: 18 });
  statCard(s, 10.2, 4.45, 2.5, 0.95, "+0.8pp", "Logistic AME — wrong sign", { valueColor: MUTED, valueSize: 18 });
  statCard(s, 7.5, 5.5, 5.2, 1.1, "-6.5 pp", "DoubleML (IRM, XGBoost nuisance, ATT) — correct sign  ·  95% CI [-8.6, -4.5]  ·  true value -9.8pp", { valueSize: 24 });
  s.addNotes(
    "This is the deliberately weakest-identification method of the three, and I say so explicitly: DoubleML's "
    + "validity rests on selection-on-observables -- 'we captured every important confounder' -- which, unlike "
    + "RDD's no-manipulation check or DiD's pre-trends check, is NOT directly testable from the data. I include "
    + "it anyway because it's genuinely the right tool for a trigger with no design-based structure, and because "
    + "showing naive and logistic regression BOTH getting the wrong sign is a clean, defensible demonstration of "
    + "why simple methods fail under this kind of threshold-based confounding, and why tree-based nuisance models "
    + "(which can represent a branching rule; linear logistic regression can't) recover the correct sign. I target "
    + "ATT not ATE here on purpose -- the true effect is concentrated in the ~30% of accounts that get flagged, "
    + "so the population-average effect is small and noisy, while the effect ON THE TREATED is the number that "
    + "actually matters for deciding whether to keep running this play on exactly those accounts."
  );
}

// ============================================================ SLIDE 12: OPTIMIZATION FORMULATION
{
  const s = lightSlide(pres);
  kicker(s, "Layer 3 — Optimize");
  slideTitle(s, "From “top 50% by value” to a formal budget allocation");
  pageNum(s, 12);

  s.addShape("roundRect", { x: 0.6, y: 2.2, w: 5.7, h: 4.35, rectRadius: 0.08, fill: { color: ICE_TINT }, line: { type: "none" } });
  s.addText("OBJECTIVE", { x: 0.95, y: 2.45, w: 5, h: 0.35, fontFace: FONT_BODY, fontSize: 12, bold: true, color: TERRACOTTA, charSpacing: 1.5, margin: 0 });
  s.addText("Maximize total net expected value protected:\nP(churn mode) × causal effect (pp) × dollars at "
    + "risk − intervention cost, summed across every account-intervention pair selected.", {
    x: 0.95, y: 2.85, w: 5.05, h: 1.35, fontFace: FONT_BODY, fontSize: 13, color: NAVY, margin: 0, lineSpacingMultiple: 1.25,
  });
  s.addText("\"Dollars at risk\" = account_value = balance × (1 + 15% × product_count) — a dollar-denominated, "
    + "sensitivity-tested proxy for relationship value (see Business Impact), not an arbitrary weighted score.", {
    x: 0.95, y: 4.15, w: 5.05, h: 0.85, fontFace: FONT_BODY, fontSize: 10.5, italic: true, color: MUTED, margin: 0, lineSpacingMultiple: 1.2,
  });
  s.addText("CONSTRAINTS", { x: 0.95, y: 5.0, w: 5, h: 0.35, fontFace: FONT_BODY, fontSize: 12, bold: true, color: TERRACOTTA, charSpacing: 1.5, margin: 0 });
  s.addText([
    { text: "Total spend ≤ monthly retention budget", options: { bullet: true, breakLine: true } },
    { text: "RM contacts ≤ RM capacity (the real scarce resource)", options: { bullet: true, breakLine: true } },
    { text: "At most one intervention per account", options: { bullet: true, breakLine: true } },
  ], { x: 0.95, y: 5.4, w: 5.05, h: 1.1, fontFace: FONT_BODY, fontSize: 12, color: NAVY, margin: 0, lineSpacingMultiple: 1.15, paraSpaceAfter: 3 });

  s.addShape("roundRect", { x: 6.6, y: 2.2, w: 5.9, h: 4.35, rectRadius: 0.08, fill: { color: NAVY }, line: { type: "none" } });
  s.addText("EFFECT SIZES FEEDING THE OPTIMIZER", { x: 6.95, y: 2.45, w: 5.2, h: 0.35, fontFace: FONT_BODY, fontSize: 12, bold: true, color: TERRACOTTA, charSpacing: 1, margin: 0 });
  const effRows = [
    ["Large withdrawal → RM call", "10.7 pp", "RDD — high confidence"],
    ["DD stop → $100 offer", "3.7 pp", "clean-control DiD — high confidence"],
    ["Dormant → reminder", "6.5 pp", "DoubleML — moderate confidence (untestable assumption)"],
  ];
  let ey = 2.95;
  effRows.forEach(([name, eff, src]) => {
    s.addText(name, { x: 6.95, y: ey, w: 3.3, h: 0.4, fontFace: FONT_BODY, fontSize: 12.5, bold: true, color: WHITE, margin: 0 });
    s.addText(eff, { x: 10.2, y: ey, w: 1.1, h: 0.4, fontFace: FONT_HEAD, fontSize: 14, bold: true, color: TERRACOTTA, align: "right", margin: 0 });
    s.addText(src, { x: 6.95, y: ey + 0.38, w: 5.2, h: 0.55, fontFace: FONT_BODY, fontSize: 10.5, italic: true, color: ICE, margin: 0, lineSpacingMultiple: 1.1 });
    ey += 1.25;
  });
  s.addNotes(
    "This is a multiple-choice knapsack problem, solved with PuLP (CBC solver): each account can get at most one "
    + "intervention, subject to a total budget and a separate RM-capacity constraint, since RM time -- not dollars "
    + "-- is actually the binding resource for the withdrawal play. Every effect size here now comes from an "
    + "actual estimation script, not a hardcoded assumption -- including the dormant number, which used to be a "
    + "flat 3pp guess and is now DoubleML's estimate, carried into the optimizer with its own honestly-labeled "
    + "lower confidence tier rather than being treated as equally solid."
  );
}

// ============================================================ SLIDE 13: OPTIMIZATION RESULT
{
  const s = lightSlide(pres);
  kicker(s, "Optimize — Result");
  slideTitle(s, "Same budget, same RM capacity: 63% more value protected");
  pageNum(s, 13);

  s.addImage({ path: FIG("optimization_comparison.png"), x: 0.6, y: 2.15, w: 6.7, h: 4.75 });

  statCard(s, 7.55, 2.15, 5.15, 1.15, "+63%", "Net value protected vs. the heuristic, at equal budget & RM capacity");
  statCard(s, 7.55, 3.45, 5.15, 1.15, "297 / 400", "RM contacts used — the optimizer stops once marginal expected value turns negative, not when capacity runs out");
  s.addText("The heuristic doesn't discriminate by risk LEVEL within the top-50%-value pool — it spends on "
    + "high-value accounts whether they're actually at risk or not, and it has no notion of an RM-capacity limit "
    + "at all. The optimizer ranks by expected payoff per dollar and per RM-minute directly, and it's disciplined "
    + "enough to leave budget and capacity on the table rather than fund a marginal account that isn't worth it.", {
    x: 7.55, y: 4.85, w: 5.15, h: 2.0, fontFace: FONT_BODY, fontSize: 12, color: MUTED, margin: 0, lineSpacingMultiple: 1.22,
  });
  s.addNotes(
    "Walk through this carefully: the heuristic, run without any cap, actually overspends the RM capacity on its "
    + "own -- that's itself a finding worth surfacing to the business, since it means the original process needed "
    + "an unwritten manual cap that the optimization now formalizes. Also worth noting if asked: the +63% figure "
    + "went down from an earlier draft's +497% once I fixed the dollar-at-risk formula and the DiD/dormant effect "
    + "sizes to be properly estimated rather than assumed -- I'd rather present the more defensible, smaller "
    + "number than an inflated one I can't fully stand behind."
  );
}

// ============================================================ SLIDE 14: BUSINESS IMPACT
{
  const s = lightSlide(pres);
  kicker(s, "So what — business impact");
  slideTitle(s, "Translating the model into a dollar figure a stakeholder can act on");
  pageNum(s, 14);

  s.addImage({ path: FIG("business_impact_headline.png"), x: 0.6, y: 2.15, w: 6.1, h: 4.75 });

  statCard(s, 7.05, 2.15, 5.65, 1.25, "+$116,211", "Incremental net value protected, per 10,000 scored accounts (+63.2%)");
  s.addText("Deliberately NOT scaled to a fabricated \"total accounts at the bank\" number — this project's "
    + "data is a sized demo, not the real book. Reported per 10,000 scored accounts with an explicit scaling "
    + "instruction instead: multiply by (your real scored-account count / 10,000). The mechanism — same spend, "
    + "better targeting — scales linearly with book size, unlike a one-time fixed-cost project.", {
    x: 7.05, y: 3.55, w: 5.65, h: 1.7, fontFace: FONT_BODY, fontSize: 11.5, color: MUTED, margin: 0, lineSpacingMultiple: 1.22,
  });
  statCard(s, 7.05, 5.4, 5.65, 1.15,
    "98.2% / 98.3%",
    "Top-value-quartile membership overlap if the 15% product-value-uplift assumption were 10% / 20% instead — the specific number isn't load-bearing for who gets prioritized",
    { valueSize: 22 });
  s.addNotes(
    "This slide is the direct answer to 'so what' -- it's also where I address the weight-formula criticism head "
    + "on. Rather than asserting the 15% product-value-uplift number is right, I show it doesn't matter much: "
    + "ranking is nearly identical (Spearman ~0.999) whether it's 10%, 15%, or 20%, and over 98% of the accounts "
    + "that get prioritized stay prioritized either way. That's the concrete, defensible answer to 'how did you "
    + "pick that weight' -- I picked a reasonable one and then proved the conclusion doesn't hinge on it."
  );
}

// ============================================================ SLIDE 15: ACTIONABLE RECOMMENDATIONS
{
  const s = lightSlide(pres);
  kicker(s, "So what — recommendations");
  slideTitle(s, "Four actions, tiered by how much confidence each estimate actually earned");
  pageNum(s, 15);

  const recs = [
    ["1", "Adopt the ILP optimizer", "in place of the informal \"top 50% by value\" rule.",
      "High — mechanical improvement on already-validated inputs, not a new causal claim.", NAVY_MID],
    ["2", "Formalize the 30%-withdrawal → RM-outreach trigger", "as an explicit, monitored policy.",
      "High — RDD, no-manipulation assumption directly tested.", NAVY_MID],
    ["3", "Don't evaluate the DD-stop offer's rollout before month 3", "of each wave — the effect ramps in.",
      "High — DiD, parallel pre-trends directly tested.", NAVY_MID],
    ["4", "Do NOT scale budget into the dormant play", "on this estimate alone — run a real randomized pilot first.",
      "Moderate — DoubleML's unconfoundedness assumption isn't testable from data.", TERRACOTTA],
  ];
  let y = 2.15;
  recs.forEach(([n, action, detail, conf, color]) => {
    s.addShape("roundRect", { x: 0.6, y, w: 11.9, h: 1.05, rectRadius: 0.06, fill: { color: ICE_TINT }, line: { type: "none" } });
    badge(s, 0.8, y + 0.22, 0.55, n, color);
    s.addText([
      { text: action + " ", options: { bold: true, color: NAVY } },
      { text: detail, options: { color: MUTED } },
    ], { x: 1.55, y: y + 0.08, w: 7.6, h: 0.9, fontFace: FONT_BODY, fontSize: 12, margin: 0, valign: "middle", lineSpacingMultiple: 1.15 });
    s.addText("CONFIDENCE", { x: 9.3, y: y + 0.12, w: 3.05, h: 0.3, fontFace: FONT_BODY, fontSize: 9.5, bold: true, color: TERRACOTTA, charSpacing: 1, margin: 0 });
    s.addText(conf, { x: 9.3, y: y + 0.4, w: 3.05, h: 0.6, fontFace: FONT_BODY, fontSize: 10, color: NAVY, margin: 0, lineSpacingMultiple: 1.1 });
    y += 1.22;
  });
  s.addText("Priority order follows confidence, not effect size — the dormant play's 6.5pp is the second-largest "
    + "estimated effect, but it's ranked last because its identifying assumption is the one that can't be checked.", {
    x: 0.6, y: 6.95, w: 11.9, h: 0.4, fontFace: FONT_BODY, fontSize: 11, italic: true, color: MUTED, margin: 0,
  });
  s.addNotes(
    "This is the deliverable a Decision Analytics stakeholder actually wants, and it's deliberately not just "
    + "'here are three effect sizes' -- it's prioritized, and the priority order is driven by how much I trust "
    + "each identifying assumption, not by which number is biggest. Recommendation 4 is the one I'd expect the "
    + "most pushback on, and I want to be the one raising the caveat before anyone else does."
  );
}

// ============================================================ SLIDE 16: TYING BACK
{
  const s = lightSlide(pres);
  kicker(s, "Result — tying it back");
  slideTitle(s, "The real project already worked. This is how I'd make it rigorous.");
  pageNum(s, 16);

  s.addShape("roundRect", { x: 0.6, y: 2.25, w: 5.8, h: 4.3, rectRadius: 0.08, fill: { color: ICE_TINT }, line: { type: "none" } });
  s.addText("WHAT ACTUALLY HAPPENED", { x: 0.95, y: 2.5, w: 5.1, h: 0.35, fontFace: FONT_BODY, fontSize: 12, bold: true, color: TERRACOTTA, charSpacing: 1.5, margin: 0 });
  statCard(s, 0.95, 2.95, 5.1, 1.15, "-30%", "Relative churn reduction, randomized A/B test vs. blanket outreach", { fill: WHITE });
  s.addText("Validated the only way we had time and buy-in to validate: an outcomes-based A/B test. That's a "
    + "real, defensible result — and it's also the limit of what we did.", {
    x: 0.95, y: 4.3, w: 5.1, h: 2.0, fontFace: FONT_BODY, fontSize: 12.5, color: MUTED, margin: 0, lineSpacingMultiple: 1.25,
  });

  s.addShape("roundRect", { x: 6.7, y: 2.25, w: 5.8, h: 4.3, rectRadius: 0.08, fill: { color: NAVY }, line: { type: "none" } });
  s.addText("WHAT THIS ADDS", { x: 7.05, y: 2.5, w: 5.1, h: 0.35, fontFace: FONT_BODY, fontSize: 12, bold: true, color: TERRACOTTA, charSpacing: 1.5, margin: 0 });
  s.addText([
    { text: "Causal identification for triggers that CAN'T be A/B tested, not just the ones that can", options: { bullet: true, breakLine: true } },
    { text: "A formal, re-runnable optimization instead of a fixed value-score cutoff — it flexes with budget", options: { bullet: true, breakLine: true } },
    { text: "A quantified, confidence-tiered business case instead of a technical result that stops at the model", options: { bullet: true, breakLine: true } },
    { text: "Every method graded against a known ground truth before I'd trust it on a real decision", options: { bullet: true, breakLine: true } },
  ], { x: 7.05, y: 2.95, w: 5.15, h: 3.4, fontFace: FONT_BODY, fontSize: 12.5, color: WHITE, margin: 0, lineSpacingMultiple: 1.2, paraSpaceAfter: 8 });

  s.addNotes(
    "This slide is the bridge back to the STAR story: the real result stands on its own, and everything in this "
    + "deck is presented as the next iteration of that same project, not a replacement for what actually happened."
  );
}

// ============================================================ SLIDE 17: LIMITATIONS + WHY VANGUARD
{
  const s = lightSlide(pres);
  kicker(s, "Limitations — and why this role");
  slideTitle(s, "What I'd still want before this touches production");
  pageNum(s, 17);

  const limits = [
    ["Dormant-play effect rests on an untestable assumption", "DoubleML corrects the sign vs. naive/logistic, but its selection-on-observables identification can't be checked the way RDD's no-manipulation test or DiD's pre-trends test can — needs a real randomized pilot before scaling spend."],
    ["No formal independent model-risk validation", "Today's validation is outcomes-based (A/B test) and, here, grading against a KNOWN synthetic truth — a real deployment needs an independent conceptual-soundness review per SR 11-7."],
    ["Synthetic data throughout", "Built specifically so I could validate method correctness with a known ground truth — real deployment validates differently, without that luxury."],
  ];
  let y = 2.25;
  limits.forEach(([h, b]) => {
    s.addShape("roundRect", { x: 0.6, y, w: 11.9, h: 1.15, rectRadius: 0.06, fill: { color: ICE_TINT }, line: { type: "none" } });
    s.addText(h, { x: 0.9, y: y + 0.1, w: 4.2, h: 0.95, fontFace: FONT_BODY, fontSize: 13, bold: true, color: NAVY, margin: 0, valign: "middle", lineSpacingMultiple: 1.1 });
    s.addText(b, { x: 5.25, y: y + 0.1, w: 7.05, h: 0.95, fontFace: FONT_BODY, fontSize: 12, color: MUTED, margin: 0, valign: "middle", lineSpacingMultiple: 1.15 });
    y += 1.35;
  });

  s.addText("That gap between “validated by outcome” and “validated by design, before launch” is exactly "
    + "what draws me to this role — building the analytical engine where that rigor is the default, not a stretch goal.", {
    x: 0.6, y: 6.35, w: 11.9, h: 0.75, fontFace: FONT_BODY, fontSize: 13, italic: true, color: NAVY, margin: 0,
  });
  s.addNotes(
    "This slide is deliberate honesty, matching how I handled similar gap questions in the real project's prep -- "
    + "own the gap, and turn it into the motivation for the role rather than hiding it."
  );
}

// ============================================================ SLIDE 18: CLOSING
{
  const s = darkSlide(pres);
  s.addShape("ellipse", { x: -2, y: 4.5, w: 5.5, h: 5.5, fill: { color: NAVY_MID }, line: { type: "none" } });
  s.addText("Thank you", {
    x: 0.7, y: 2.5, w: 10, h: 1.2, fontFace: FONT_HEAD, fontSize: 42, bold: true, color: WHITE, margin: 0,
  });
  s.addText("Predict → Explain (causally) → Optimize → Act — one decision engine, four layers of rigor.", {
    x: 0.7, y: 3.6, w: 10.5, h: 0.6, fontFace: FONT_BODY, fontSize: 15, italic: true, color: ICE, margin: 0,
  });
  s.addText("Questions welcome.", {
    x: 0.7, y: 4.35, w: 8, h: 0.5, fontFace: FONT_BODY, fontSize: 14, color: ICE, margin: 0,
  });
  s.addNotes("Invite questions; have the bandwidth-sensitivity table, cohort-level ATT table, and DoubleML CI ready if asked to go deeper.");
}

pres.writeFile({ fileName: path.join(__dirname, "vanguard_dda_deck.pptx") }).then(() => {
  console.log("Deck written.");
});
