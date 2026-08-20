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
    x: opts.x ?? 0.6, y: opts.y ?? 0.4, w: opts.w ?? 10, h: 0.35,
    fontFace: FONT_BODY, fontSize: 12, bold: true, color: opts.color ?? TERRACOTTA,
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
  s.addText("A decision engine built with quasi-experimental causal inference (sharp RDD, 2-group DiD, and a "
    + "tier-stratified randomized-holdout RCT) plus formal ILP budget optimization, translated into quantified, "
    + "actionable business impact", {
    x: 0.7, y: 4.05, w: 10.8, h: 0.9, fontFace: FONT_BODY, fontSize: 15, italic: true,
    color: ICE, margin: 0,
  });
  s.addText("Presented for: Data Analyst, Senior Specialist / Data Scientist — Decision Analytics & Modeling, Vanguard", {
    x: 0.7, y: 6.55, w: 10, h: 0.4, fontFace: FONT_BODY, fontSize: 12, color: MUTED, margin: 0,
  });
  s.addNotes(
    "Open by framing this as a purpose-built demonstration of the analytical engine this JD calls for: causal "
    + "inference where randomization isn't feasible, plus formal optimization under uncertainty. Say up front "
    + "that today's data is synthetic (next slide explains why) and that the project is grounded in real DDA "
    + "retention work I led, but isn't presented as a literal retrofit of that project's original test design."
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
    "This is the real situation from my actual DDA retention work. RMs and the retention team had no "
    + "forward-looking signal, and the retention motion that did exist wasn't differentiated by WHY someone "
    + "was at risk."
  );
}

// ============================================================ SLIDE 3: TASK / FRAMING
{
  const s = lightSlide(pres);
  kicker(s, "Task — how to read what you're about to see");
  slideTitle(s, "Grounded in a real retention problem;\nbuilt, end to end, to demonstrate this role's engine");
  pageNum(s, 3);

  s.addShape("roundRect", {
    x: 0.6, y: 2.2, w: 5.9, h: 4.35, rectRadius: 0.08,
    fill: { color: ICE_TINT }, line: { type: "none" },
  });
  s.addText("WHAT'S REAL", { x: 0.95, y: 2.45, w: 5.2, h: 0.35, fontFace: FONT_BODY, fontSize: 12, bold: true, color: TERRACOTTA, charSpacing: 1.5, margin: 0 });
  s.addText([
    { text: "The business problem: DDA churn, no early warning, undifferentiated outreach", options: { bullet: true, breakLine: true } },
    { text: "The three churn triggers (large withdrawal, DD stop, dormancy) and the multi-class predictive layer that routes each account to the right playbook", options: { bullet: true, breakLine: true } },
    { text: "The retention economics — funded outreach only pencils out above a value cutoff; below it, cheaper touches make more sense (see slide 4)", options: { bullet: true, breakLine: true } },
  ], { x: 0.95, y: 2.9, w: 5.2, h: 3.5, fontFace: FONT_BODY, fontSize: 12.5, color: NAVY, lineSpacingMultiple: 1.15, margin: 0, paraSpaceAfter: 8 });

  s.addShape("roundRect", {
    x: 6.8, y: 2.2, w: 5.9, h: 4.35, rectRadius: 0.08,
    fill: { color: NAVY }, line: { type: "none" },
  });
  s.addText("WHAT'S PURPOSE-BUILT FOR THIS ROLE", { x: 7.15, y: 2.45, w: 5.2, h: 0.35, fontFace: FONT_BODY, fontSize: 12, bold: true, color: TERRACOTTA, charSpacing: 1.5, margin: 0 });
  s.addText([
    { text: "Everything from here on — the RDD, the DiD, the randomized dormant-play holdout, the ILP optimizer, and the business-impact translation — was designed from scratch on synthetic data (known account data can't leave the bank, or be posted to a public repo)", options: { bullet: true, breakLine: true } },
    { text: "No extra A/B test was proposed. Instead: for each trigger, the analysis plan was fixed FIRST — which comparison, which population, which test — before ever looking at outcomes, the same discipline as pre-registration", options: { bullet: true, breakLine: true } },
    { text: "The DD-stop offer and both dormant plays roll out to everyone eligible in-window; only a small randomized holdout is withheld, purely for measurement — nothing is delayed or denied just to run a test", options: { bullet: true, breakLine: true } },
    { text: "Because the ground truth is injected, every method here can be graded against a known answer before I'd ever trust it on a real decision", options: { bullet: true, breakLine: true } },
  ], { x: 7.15, y: 2.9, w: 5.2, h: 3.5, fontFace: FONT_BODY, fontSize: 12.5, color: WHITE, lineSpacingMultiple: 1.15, margin: 0, paraSpaceAfter: 8 });

  s.addNotes(
    "Be very explicit and upfront here: this is honest framing, not a trick. If asked 'is this the exact project "
    + "you shipped' -- no, and I don't present it that way. It's a from-scratch analytical engine, built to "
    + "demonstrate the causal-inference-under-non-randomization plus optimization skillset this JD asks for, using "
    + "the same real business problem and triggers I actually worked on. The 'analysis plan fixed before looking "
    + "at outcomes' point matters: it's what separates this from p-hacking a result out of data I already had --  "
    + "RDD's cutoff, DiD's launch date and comparison groups, and the dormant RCT's holdout design were all "
    + "decided before computing a single effect size."
  );
}

// ============================================================ SLIDE 4: ARCHITECTURE
{
  const s = lightSlide(pres);
  kicker(s, "Approach");
  slideTitle(s, "One decision engine, four layers — each one earning its place in the final call");
  pageNum(s, 4);

  const boxes = [
    ["1", "PREDICT", "Which churn mode is this account heading toward? Routes each account to the right causal layer.", NAVY_MID],
    ["2", "EXPLAIN\n(CAUSAL)", "Sharp RDD, 2-group DiD, tier-stratified randomized-holdout RCT: the true effect of each intervention, isolated from confounds.", TERRACOTTA],
    ["3", "OPTIMIZE", "Budget & capacity-constrained ILP: given real effects and real costs, who gets what, this month?", NAVY_MID],
    ["4", "ACT", "Tiered, quantified recommendations a stakeholder can approve and a team can execute.", NAVY_MID],
  ];
  let x = 0.6;
  const w = 2.92, gap = 0.24;
  boxes.forEach(([num, head, body, color], i) => {
    s.addShape("roundRect", { x, y: 2.3, w, h: 3.3, rectRadius: 0.08, fill: { color: ICE_TINT }, line: { type: "none" } });
    badge(s, x + 0.25, 2.58, 0.5, num, color);
    s.addText(head, { x: x + 0.25, y: 3.24, w: w - 0.5, h: 0.55, fontFace: FONT_HEAD, fontSize: 14.5, bold: true, color: NAVY, margin: 0 });
    s.addText(body, { x: x + 0.25, y: 3.8, w: w - 0.5, h: 1.65, fontFace: FONT_BODY, fontSize: 11, color: MUTED, margin: 0, lineSpacingMultiple: 1.18 });
    if (i < 3) {
      s.addText("→", { x: x + w + 0.01, y: 3.6, w: gap - 0.02, h: 0.6, fontFace: FONT_BODY, fontSize: 22, bold: true, color: TERRACOTTA, align: "center", margin: 0 });
    }
    x += w + gap;
  });

  s.addShape("roundRect", { x: 0.6, y: 5.85, w: 11.9, h: 1.15, rectRadius: 0.07, fill: { color: NAVY }, line: { type: "none" } });
  s.addText("ONE SPLIT, REUSED EVERYWHERE", { x: 0.9, y: 6.0, w: 3.0, h: 0.85, fontFace: FONT_BODY, fontSize: 11.5, bold: true, color: TERRACOTTA, charSpacing: 1, valign: "middle", margin: 0 });
  s.addText("RDD's population, DiD's treated/control groups, and both dormant-play RCT arms all use the SAME "
    + "high-value / low-value account split (top/bottom 50% by account_value) — a business ROI cutoff, not a "
    + "statistical one (next slide). One reused definition of \"who's worth a funded intervention,\" instead of "
    + "three separately-justified cutoffs.", {
    x: 3.95, y: 5.95, w: 8.4, h: 1.0, fontFace: FONT_BODY, fontSize: 11.5, color: WHITE, margin: 0, lineSpacingMultiple: 1.2, valign: "middle",
  });

  s.addNotes(
    "This maps directly to the JD language: 'design the analytical engine... how relationships are modeled... how "
    + "outputs are generated for decision-making.' Predict/Explain/Optimize is that engine; Act is what turns the "
    + "engine's output into something a stakeholder can approve. The callout at the bottom is deliberate -- it "
    + "previews that every causal design from here forward shares one reused business split, so it doesn't look "
    + "like three separately-invented cutoffs when RDD/DiD/dormant each show up."
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
    + "at a single threshold, exactly like the causal layer's HV/LV split on the next slides.", {
    x: 7.55, y: 4.75, w: 5.15, h: 2.1, fontFace: FONT_BODY, fontSize: 12.5, color: MUTED, margin: 0, lineSpacingMultiple: 1.25,
  });
  s.addNotes(
    "Engagement, DD stability, and liquidity-need scores dominate, as expected -- and region importance sits at "
    + "noise level, a good sanity check that the model isn't picking up spurious geography effects. I evaluate by "
    + "ranking quality, not hard-classification accuracy, because forcing balanced weights on an 89%-none target "
    + "produces garbage precision numbers that don't reflect how the model is actually used. This layer's job is "
    + "purely routing: WHICH causal-layer estimate applies to this account."
  );
}

// ============================================================ SLIDE 6: CAUSAL LAYER INTRO
{
  const s = lightSlide(pres);
  kicker(s, "Layer 2 — Explain (Causal)");
  slideTitle(s, "Three triggers, none of them randomized — one shared value split");
  pageNum(s, 6);

  s.addShape("roundRect", { x: 0.6, y: 2.05, w: 11.9, h: 0.85, rectRadius: 0.06, fill: { color: ICE_TINT }, line: { type: "none" } });
  s.addText([
    { text: "Why 50/50 by account value: ", options: { bold: true, color: NAVY } },
    { text: "a ROI cutoff, not a statistical one — \"for the top half, the deposits and lifetime value protected "
      + "clearly outweighed the cost; below that the economics got thin,\" so only the top half gets a funded, "
      + "randomized intervention. Same split, all three rows below.", options: { color: MUTED } },
  ], { x: 0.85, y: 2.16, w: 11.4, h: 0.65, fontFace: FONT_BODY, fontSize: 11.5, margin: 0, valign: "middle", lineSpacingMultiple: 1.15 });

  const rows = [
    ["Large withdrawal > 30% of balance\n→ RM calls, pitches alternatives (HV only)",
     "Deterministic rule, not a coin flip",
     "Sharp Regression Discontinuity (RDD)",
     "Compare accounts just above vs.\njust below the 30% line"],
    ["Direct deposit stops\n→ $100 offer for 2 new DDs $500+ (HV only)",
     "Rolled out to HV accounts on one launch date; LV never gets it in-window",
     "2-group Difference-in-Differences",
     "Compare HV's before/after change\nto LV's before/after change"],
    ["Dormancy signal\n→ cashback offer (HV) / SMS reminder (LV)",
     "No natural threshold or rollout date — so a small randomized holdout is built into the design itself",
     "Tier-stratified randomized-holdout RCT",
     "Compare each tier's treated\naccounts to that tier's own holdout"],
  ];
  let y = 3.05;
  const rh = 1.32;
  rows.forEach(([trigger, why, method, how]) => {
    s.addShape("roundRect", { x: 0.6, y, w: 11.9, h: rh, rectRadius: 0.07, fill: { color: ICE_TINT }, line: { type: "none" } });
    s.addText(trigger, { x: 0.9, y: y + 0.12, w: 4.5, h: rh - 0.24, fontFace: FONT_BODY, fontSize: 12, bold: true, color: NAVY, margin: 0, lineSpacingMultiple: 1.12, valign: "middle" });
    s.addText(why, { x: 5.45, y: y + 0.12, w: 2.7, h: rh - 0.24, fontFace: FONT_BODY, fontSize: 10.2, italic: true, color: MUTED, margin: 0, lineSpacingMultiple: 1.15, valign: "middle" });
    s.addText(method, { x: 8.25, y: y + 0.15, w: 4.05, h: 0.5, fontFace: FONT_HEAD, fontSize: 13, bold: true, color: TERRACOTTA, margin: 0 });
    s.addText(how, { x: 8.25, y: y + 0.58, w: 4.05, h: 0.65, fontFace: FONT_BODY, fontSize: 10.2, color: MUTED, margin: 0, lineSpacingMultiple: 1.15 });
    y += rh + 0.15;
  });
  s.addNotes(
    "This is the core of what the JD is asking for: causal inference 'in situations where randomized testing is "
    + "not feasible, practical, or cost-effective.' All three are real, non-randomized business situations, so I "
    + "pick the quasi-experimental design that fits each one's actual structure rather than forcing one method on "
    + "all three. The third row is the one place a real experiment IS feasible and cheap -- a small randomized "
    + "holdout -- so that's what it uses, rather than reaching for an observational method just because the other "
    + "two triggers needed one."
  );
}

// ============================================================ SLIDE 7: RDD DESIGN
{
  const s = lightSlide(pres);
  kicker(s, "RDD — Design & Validation");
  slideTitle(s, "The identifying assumption: the running variable isn't manipulated");
  pageNum(s, 7);

  s.addImage({ path: FIG("rdd_density_check.png"), x: 0.6, y: 2.15, w: 7.0, h: 4.7 });
  s.addText("McCrary-style density test — HV population only", { x: 7.9, y: 2.3, w: 4.8, h: 0.55, fontFace: FONT_HEAD, fontSize: 14, bold: true, color: NAVY, margin: 0, lineSpacingMultiple: 1.1 });
  s.addText("Customers don't know this internal 30% threshold exists, so deliberate dodging isn't the "
    + "realistic risk — the real risk is any OTHER unknown reason withdrawal size might bunch near 30% "
    + "(round-number withdrawal habits, an unrelated internal rule). This test checks for that directly "
    + "instead of just asserting it away.", {
    x: 7.9, y: 2.85, w: 4.8, h: 1.4, fontFace: FONT_BODY, fontSize: 11.5, color: MUTED, margin: 0, lineSpacingMultiple: 1.2,
  });
  statCard(s, 7.9, 4.45, 4.8, 1.0, "p = 0.828", "Local log-density jump at cutoff (bootstrap test)", { valueSize: 24 });
  s.addText("No jump in the density at 30% — consistent with a smooth, unmanipulated running variable. "
    + "(Restricted to HV accounts, the only population RM outreach applies to under the value split.)", {
    x: 7.9, y: 5.6, w: 4.8, h: 1.0, fontFace: FONT_BODY, fontSize: 11.5, color: MUTED, margin: 0, lineSpacingMultiple: 1.22,
  });
  s.addNotes(
    "If asked 'why check this at all, customers don't know the 30% rule exists' -- that's exactly right, and it's "
    + "why I don't expect INTENTIONAL gaming. But the McCrary test isn't only a test for intentional gaming; it's "
    + "a general smoothness check on the running variable's density, which would also catch unrelated sources of "
    + "bunching that could bias the comparison even without anyone trying to dodge OUR rule specifically. It's "
    + "also the standard, expected validation step for any RDD -- skipping it is what would actually raise "
    + "questions. Restricting to HV accounts here matters for external validity too: this estimate speaks to the "
    + "HV population it was tested on, not a claim about how RM outreach would work on LV accounts."
  );
}

// ============================================================ SLIDE 8: RDD RESULT
{
  const s = lightSlide(pres);
  kicker(s, "RDD — Result");
  slideTitle(s, "RM outreach cuts 60-day churn by ~8 points at the margin");
  pageNum(s, 8);

  s.addImage({ path: FIG("rdd_effect_plot.png"), x: 0.6, y: 2.15, w: 7.5, h: 4.75 });

  statCard(s, 8.35, 2.15, 4.35, 1.05, "-0.2 pp", "Naive treated-vs-control (biased by confound)", { valueColor: MUTED, valueSize: 26 });
  statCard(s, 8.35, 3.35, 4.35, 1.05, "-8.3 pp", "RDD robust estimate  ·  95% CI [-12.3, -4.3]  ·  p<0.001", { valueSize: 26 });
  s.addText("Bandwidth sensitivity: stable in the high single digits across h = 4 to 20 months. Graded against "
    + "the effect I built into the simulation: RDD lands within 1.3pp of the true local value near the cutoff — "
    + "the naive comparison, near zero, doesn't come close.", {
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
  slideTitle(s, "One launch date, one treated group — parallel pre-trends is the assumption to check");
  pageNum(s, 9);

  s.addImage({ path: FIG("did_pretrends_check.png"), x: 0.6, y: 2.15, w: 7.4, h: 4.6 });
  s.addText("Parallel pre-trends check", { x: 8.15, y: 2.3, w: 4.55, h: 0.4, fontFace: FONT_HEAD, fontSize: 15, bold: true, color: NAVY, margin: 0 });
  s.addText("HV and LV accounts differ in baseline churn LEVEL (HV churns less overall regardless of any "
    + "offer) — DiD doesn't need them equal, it needs them moving in the same DIRECTION before the offer "
    + "launches. That's what this checks, restricted to the pre-launch months only.", {
    x: 8.15, y: 2.75, w: 4.55, h: 1.5, fontFace: FONT_BODY, fontSize: 11.5, color: MUTED, margin: 0, lineSpacingMultiple: 1.22,
  });
  statCard(s, 8.15, 4.4, 4.55, 1.0, "p = 0.633", "F-test on value-group × month interaction, pre-launch only", { valueSize: 24 });
  s.addText("No evidence of differential pre-trends. Because there's exactly one treated group and one launch "
    + "date, this design also sidesteps the staggered-adoption bias (Goodman-Bacon 2021) that a multi-wave "
    + "rollout would introduce — there's no already-treated cohort to contaminate the comparison.", {
    x: 8.15, y: 5.5, w: 4.55, h: 1.3, fontFace: FONT_BODY, fontSize: 11, italic: true, color: MUTED, margin: 0, lineSpacingMultiple: 1.2,
  });
  s.addNotes(
    "The offer launches for the whole HV group on ONE calendar month, and LV never gets it in-window -- a plain "
    + "2-group, single-adoption-date design, deliberately simpler than a multi-wave rollout. That's a design "
    + "choice worth being able to defend if asked 'why not stagger it': staggering by tier would have introduced "
    + "exactly the kind of already-treated-cohort contamination Goodman-Bacon (2021) warns about, and there's no "
    + "operational reason (RM capacity, say) that requires phasing HERE the way there was for the withdrawal "
    + "trigger's RM contacts -- an offer code can go out to everyone at once."
  );
}

// ============================================================ SLIDE 10: DID RESULT
{
  const s = lightSlide(pres);
  kicker(s, "DiD — Result");
  slideTitle(s, "The textbook 2x2 estimator — and the regression that reproduces it");
  pageNum(s, 10);

  s.addImage({ path: FIG("did_event_study.png"), x: 0.6, y: 2.15, w: 7.4, h: 4.55 });

  statCard(s, 8.15, 2.15, 4.55, 0.95, "-5.8 pp", "2x2 DiD: (HV change) − (LV change)", { valueSize: 24 });
  statCard(s, 8.15, 3.25, 4.55, 0.95, "-5.8 pp", "Regression DiD, HC1 robust SE  ·  p<0.001", { valueSize: 24 });
  s.addText("HV: 11.9% → 5.8% churn (change -6.1pp). LV: 17.8% → 17.5% (change -0.3pp). The regression "
    + "coefficient matches the four-group-means number almost exactly, as it should with one treated group and "
    + "one adoption date — no cohort-averaging step for the two to disagree on. The effect ramps in over "
    + "roughly 3 months as awareness and take-up build; graded against the true simulated effect (-5.1pp), both "
    + "estimators land within a point.", {
    x: 8.15, y: 4.35, w: 4.55, h: 2.6, fontFace: FONT_BODY, fontSize: 11.2, color: MUTED, margin: 0, lineSpacingMultiple: 1.2,
  });
  s.addNotes(
    "This is deliberately the most 'textbook' estimator in the deck, and I say so if asked: with a clean 2-group, "
    + "single-adoption-date design, there's no staggered-rollout machinery needed -- the four-group-means "
    + "differencing and the fixed-effects regression are two ways of computing the SAME number, which is itself "
    + "a good sanity check to show working. If this were a multi-wave rollout instead, I'd reach for a "
    + "clean-control / stacked estimator or the real Callaway-Sant'Anna package -- worth knowing when you'd need "
    + "that extra machinery and when you wouldn't."
  );
}

// ============================================================ SLIDE 11: DORMANT RCT DESIGN
{
  const s = lightSlide(pres);
  kicker(s, "Layer 2 (cont.) — dormant plays: no natural design, so build one in");
  slideTitle(s, "A small randomized holdout, inside each value tier");
  pageNum(s, 11);

  s.addShape("roundRect", { x: 0.6, y: 2.15, w: 5.75, h: 4.6, rectRadius: 0.08, fill: { color: ICE_TINT }, line: { type: "none" } });
  s.addText("THE DESIGN", { x: 0.9, y: 2.35, w: 5.1, h: 0.35, fontFace: FONT_BODY, fontSize: 12, bold: true, color: TERRACOTTA, charSpacing: 1.5, margin: 0 });
  s.addText([
    { text: "HV tier: 90% get a 90-day, 5%-cashback-on-grocery-spend offer; 10% randomly held out (no offer)", options: { bullet: true, breakLine: true } },
    { text: "LV tier: 90% get an SMS/email reminder; 10% randomly held out", options: { bullet: true, breakLine: true } },
    { text: "The two tiers are NEVER pooled — HV and LV differ on both risk level and which offer they get, so mixing them would confound \"which offer works\" with \"which tier is lower-risk\"", options: { bullet: true, breakLine: true } },
    { text: "Randomization within tier — not the ops team's judgment — decides who's held out, so treated vs. holdout is a clean comparison by construction", options: { bullet: true, breakLine: true } },
  ], { x: 0.9, y: 2.75, w: 5.15, h: 3.9, fontFace: FONT_BODY, fontSize: 12, color: NAVY, lineSpacingMultiple: 1.18, margin: 0, paraSpaceAfter: 7 });

  s.addShape("roundRect", { x: 6.6, y: 2.15, w: 5.9, h: 4.6, rectRadius: 0.08, fill: { color: NAVY }, line: { type: "none" } });
  s.addText("RANDOMIZATION-BALANCE CHECK (\"TABLE 1\")", { x: 6.95, y: 2.35, w: 5.2, h: 0.35, fontFace: FONT_BODY, fontSize: 11.5, bold: true, color: TERRACOTTA, charSpacing: 1, margin: 0 });
  s.addText("Before trusting the comparison, check that randomization actually balanced the two arms on "
    + "observed covariates — engagement score, dormancy streak, product count, tenure, balance — within each "
    + "tier, BEFORE any offer went out.", {
    x: 6.95, y: 2.75, w: 5.2, h: 1.15, fontFace: FONT_BODY, fontSize: 11.5, color: ICE, margin: 0, lineSpacingMultiple: 1.2,
  });
  statCard(s, 6.95, 4.0, 5.2, 1.05, "0 / 10", "Covariate balance tests flagged at p≤0.05 (both tiers, 5 covariates each)", { fill: WHITE, valueSize: 26 });
  s.addText("This is the standard \"Table 1\" any RCT write-up would run — the randomized-holdout design earns "
    + "its high-confidence label because this is directly testable, unlike the observational method it replaces.", {
    x: 6.95, y: 5.2, w: 5.2, h: 1.35, fontFace: FONT_BODY, fontSize: 11.2, italic: true, color: ICE, margin: 0, lineSpacingMultiple: 1.2,
  });
  s.addNotes(
    "This trigger used to have NO exploitable design at all -- an ops team just decided who to call, based on a "
    + "mix of signals, which is exactly a selection-on-observables problem an earlier version of this project "
    + "handled with DoubleML. The redesign here is deliberate: rather than reach for a heavier observational "
    + "estimator, build the missing randomization directly into the rollout -- a small (10%) holdout is cheap, "
    + "doesn't meaningfully change who gets helped, and converts an untestable identifying assumption into a "
    + "directly-testable one. The balance check is what proves the randomization actually worked, not just that "
    + "it was intended to."
  );
}

// ============================================================ SLIDE 12: DORMANT RCT RESULT
{
  const s = lightSlide(pres);
  kicker(s, "Dormant RCT — Result");
  slideTitle(s, "Two tier-specific tests — both correctly signed, both statistically decisive");
  pageNum(s, 12);

  s.addImage({ path: FIG("dormant_rct.png"), x: 0.6, y: 2.15, w: 6.7, h: 4.75 });

  statCard(s, 7.55, 2.15, 5.15, 1.35, "-10.8 pp", "HV: cashback vs. holdout  ·  95% CI [-14.5, -7.1]  ·  p<0.001  ·  true effect -10.4pp", { valueSize: 24 });
  statCard(s, 7.55, 3.65, 5.15, 1.35, "-5.8 pp", "LV: SMS vs. holdout  ·  95% CI [-9.8, -1.9]  ·  p=0.002  ·  true effect -6.0pp", { valueSize: 24 });
  s.addText("Both estimates land within half a point of the true simulated effect. The HV cashback play has "
    + "both the larger effect AND the larger sample — it turns out to be the single largest driver of value in "
    + "the optimizer's allocation (see Optimize).", {
    x: 7.55, y: 5.15, w: 5.15, h: 1.7, fontFace: FONT_BODY, fontSize: 12, color: MUTED, margin: 0, lineSpacingMultiple: 1.22,
  });
  s.addNotes(
    "Note the two tiers are never pooled -- each has its own two-proportion z-test against its own holdout. The "
    + "LV test has a visibly wider CI and a less extreme z (bring up the backup slide's design-effect table if "
    + "asked why a 90/10 split still has enough power here -- short answer: it's the ABSOLUTE size of the "
    + "smaller arm, ~600 accounts, not its SHARE, that sets the precision floor, and 600 is enough to detect an "
    + "effect this size). If asked why ATT-style framing isn't needed here the way it was for the old DoubleML "
    + "version: randomization already IS the comparison being asked for -- there's no separate 'effect on the "
    + "treated' vs. population question when treatment assignment was randomized within the exact population "
    + "being measured."
  );
}

// ============================================================ SLIDE 13: OPTIMIZATION FORMULATION
{
  const s = lightSlide(pres);
  kicker(s, "Layer 3 — Optimize");
  slideTitle(s, "From “top 50% by value” to a formal budget allocation");
  pageNum(s, 13);

  s.addShape("roundRect", { x: 0.6, y: 2.05, w: 5.9, h: 4.6, rectRadius: 0.08, fill: { color: ICE_TINT }, line: { type: "none" } });
  s.addText("OBJECTIVE", { x: 0.95, y: 2.25, w: 5, h: 0.35, fontFace: FONT_BODY, fontSize: 12, bold: true, color: TERRACOTTA, charSpacing: 1.5, margin: 0 });
  s.addText("Maximize total net expected value protected:\nP(churn mode) × causal effect (pp) × dollars at "
    + "risk − intervention cost, summed across every account-intervention pair selected.", {
    x: 0.95, y: 2.62, w: 5.3, h: 1.25, fontFace: FONT_BODY, fontSize: 12.5, color: NAVY, margin: 0, lineSpacingMultiple: 1.22,
  });
  s.addText("CONSTRAINTS (3)", { x: 0.95, y: 3.85, w: 5, h: 0.35, fontFace: FONT_BODY, fontSize: 12, bold: true, color: TERRACOTTA, charSpacing: 1.5, margin: 0 });
  s.addText([
    { text: "Total spend ≤ monthly retention budget", options: { bullet: true, breakLine: true } },
    { text: "RM contacts ≤ RM capacity (the real scarce resource for the withdrawal play)", options: { bullet: true, breakLine: true } },
    { text: "At most one intervention per account — plus each account is only a candidate for the interventions its tier is actually eligible for (cashback: HV only; SMS: LV only)", options: { bullet: true, breakLine: true } },
  ], { x: 0.95, y: 4.22, w: 5.35, h: 2.3, fontFace: FONT_BODY, fontSize: 11.5, color: NAVY, margin: 0, lineSpacingMultiple: 1.18, paraSpaceAfter: 4 });

  s.addShape("roundRect", { x: 6.7, y: 2.05, w: 5.9, h: 2.55, rectRadius: 0.08, fill: { color: NAVY }, line: { type: "none" } });
  s.addText("EFFECT SIZES FEEDING THE OPTIMIZER (ALL HIGH-CONFIDENCE)", { x: 7.05, y: 2.22, w: 5.2, h: 0.55, fontFace: FONT_BODY, fontSize: 10.8, bold: true, color: TERRACOTTA, charSpacing: 0.5, margin: 0, lineSpacingMultiple: 1.1 });
  const effRows = [
    ["Large withdrawal → RM call (HV)", "8.3 pp"],
    ["DD stop → $100 offer (HV)", "5.8 pp"],
    ["Dormant → cashback (HV)", "10.8 pp"],
    ["Dormant → SMS (LV)", "5.8 pp"],
  ];
  let ey = 2.85;
  effRows.forEach(([name, eff]) => {
    s.addText(name, { x: 7.05, y: ey, w: 3.9, h: 0.35, fontFace: FONT_BODY, fontSize: 11.5, bold: true, color: WHITE, margin: 0 });
    s.addText(eff, { x: 10.6, y: ey, w: 0.9, h: 0.35, fontFace: FONT_HEAD, fontSize: 13, bold: true, color: TERRACOTTA, align: "right", margin: 0 });
    ey += 0.4;
  });

  s.addShape("roundRect", { x: 6.7, y: 4.75, w: 5.9, h: 1.9, rectRadius: 0.08, fill: { color: ICE_TINT }, line: { type: "none" } });
  s.addText("WHEN THIS APPROACH DOES / DOESN'T APPLY", { x: 7.0, y: 4.9, w: 5.3, h: 0.35, fontFace: FONT_BODY, fontSize: 11, bold: true, color: TERRACOTTA, charSpacing: 0.5, margin: 0 });
  s.addText("Fits: a handful of discrete, mutually-exclusive interventions with known effect sizes and hard "
    + "resource caps — exactly this shape. Wouldn't fit: continuous decisions (how MUCH to offer, not just "
    + "whether), interventions with interaction effects between accounts, or effect sizes too uncertain to plug "
    + "into a point-estimate objective without first running a sensitivity/robustness check.", {
    x: 7.0, y: 5.25, w: 5.3, h: 1.3, fontFace: FONT_BODY, fontSize: 10.5, color: NAVY, margin: 0, lineSpacingMultiple: 1.18,
  });

  s.addNotes(
    "This is a multiple-choice knapsack problem, solved with PuLP (CBC solver): each account can get at most one "
    + "intervention, subject to a total budget and a separate RM-capacity constraint, since RM time -- not "
    + "dollars -- is actually the binding resource for the withdrawal play. Every effect size here now comes "
    + "from a design-based estimate with a checked identifying assumption -- RDD's no-manipulation test, DiD's "
    + "pre-trends test, and the dormant RCT's balance check -- so, unlike an earlier version of this project, "
    + "there's no separate lower-confidence tier to flag in the objective. If asked when NOT to reach for an "
    + "ILP: when the decision isn't actually discrete (e.g. setting a continuous discount rate), or when the "
    + "input effect sizes themselves are too uncertain to trust as point estimates -- you'd want a robust/ "
    + "distributionally-aware formulation first, not a plain linear objective."
  );
}

// ============================================================ SLIDE 14: OPTIMIZATION RESULT
{
  const s = lightSlide(pres);
  kicker(s, "Optimize — Result");
  slideTitle(s, "Same budget, same RM capacity: ~49% more value protected");
  pageNum(s, 14);

  s.addImage({ path: FIG("optimization_comparison.png"), x: 0.6, y: 2.15, w: 6.7, h: 4.75 });

  statCard(s, 7.55, 2.15, 5.15, 1.15, "+49.4%", "Net value protected vs. the heuristic, at equal budget & RM capacity");
  statCard(s, 7.55, 3.45, 5.15, 1.15, "160 / 400", "RM contacts used — the optimizer stops once marginal expected value turns negative, not when capacity runs out");
  s.addText("The heuristic doesn't discriminate by risk LEVEL within the top-50%-value pool, and it has no "
    + "notion of an RM-capacity limit at all (uncapped, it actually overspends both budget and RM capacity on "
    + "its own). The optimizer ranks by expected payoff per dollar and per RM-minute directly, and is disciplined "
    + "enough to leave budget and capacity on the table rather than fund a marginal account that isn't worth it.", {
    x: 7.55, y: 4.85, w: 5.15, h: 2.0, fontFace: FONT_BODY, fontSize: 12, color: MUTED, margin: 0, lineSpacingMultiple: 1.22,
  });
  s.addNotes(
    "Walk through this carefully: the heuristic, run without any cap, overspends both the budget and the RM "
    + "capacity on its own -- that's itself a finding worth surfacing to the business, since it means the "
    + "original process needed an unwritten manual cap that the optimization now formalizes. The dormant "
    + "cashback play alone accounts for the majority of the optimizer's total net value ($328k of $405k) -- worth "
    + "calling out since it's also the play with the most causal-identification headroom gained in this redesign."
  );
}

// ============================================================ SLIDE 15: BUSINESS IMPACT
{
  const s = lightSlide(pres);
  kicker(s, "So what — business impact");
  slideTitle(s, "Translating the model into a dollar figure a stakeholder can act on");
  pageNum(s, 15);

  s.addImage({ path: FIG("business_impact_headline.png"), x: 0.6, y: 2.15, w: 6.1, h: 4.75 });

  statCard(s, 7.05, 2.15, 5.65, 1.25, "+$133,873", "Incremental net value protected, per 10,000 scored accounts (+49.4%)");
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

// ============================================================ SLIDE 16: ACTIONABLE RECOMMENDATIONS
{
  const s = lightSlide(pres);
  kicker(s, "So what — recommendations");
  slideTitle(s, "Four actions — all built on high-confidence, design-based evidence");
  pageNum(s, 16);

  const recs = [
    ["1", "Adopt the ILP optimizer", "in place of the informal \"top 50% by value\" rule.",
      "High — mechanical improvement on already-validated inputs, not a new causal claim.", NAVY_MID],
    ["2", "Formalize the 30%-withdrawal → RM-outreach trigger", "as an explicit, monitored policy.",
      "High — RDD, no-manipulation assumption directly tested.", NAVY_MID],
    ["3", "Scale both dormant plays (HV cashback, LV SMS)", "to the full flagged population — no longer a pilot-first recommendation.",
      "High — randomized within-tier holdout, balance checked.", TERRACOTTA],
    ["4", "Don't evaluate the DD-stop offer's rollout before month 3", "the effect ramps in as awareness/take-up build.",
      "High — DiD, parallel pre-trends directly tested.", NAVY_MID],
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
  s.addText("Every effect size behind these four is now design-based and high-confidence — the redesign's "
    + "point wasn't to make one number bigger, it was to close the identification gap the old observational "
    + "dormant estimate carried. Priority here follows practical sequencing (adopt the mechanical win first, "
    + "then the largest-impact scaled plays), not a confidence hierarchy — that gap no longer exists.", {
    x: 0.6, y: 6.85, w: 11.9, h: 0.55, fontFace: FONT_BODY, fontSize: 11, italic: true, color: MUTED, margin: 0,
  });
  s.addNotes(
    "This is the deliverable a Decision Analytics stakeholder actually wants. Point out explicitly, if not asked, "
    + "that recommendation 3 moved from 'don't scale on this alone, pilot first' in an earlier version of this "
    + "project to 'scale it, it's high-confidence now' -- that shift is the direct, concrete payoff of redesigning "
    + "the dormant play as a randomized holdout instead of an observational estimate. I want to be the one "
    + "pointing out that shift, not waiting to be asked why it changed."
  );
}

// ============================================================ SLIDE 17: TYING BACK
{
  const s = lightSlide(pres);
  kicker(s, "Result — tying it back");
  slideTitle(s, "The real project already worked. This is the engine underneath it, made rigorous.");
  pageNum(s, 17);

  s.addShape("roundRect", { x: 0.6, y: 2.25, w: 5.8, h: 4.3, rectRadius: 0.08, fill: { color: ICE_TINT }, line: { type: "none" } });
  s.addText("WHAT ACTUALLY HAPPENED", { x: 0.95, y: 2.5, w: 5.1, h: 0.35, fontFace: FONT_BODY, fontSize: 12, bold: true, color: TERRACOTTA, charSpacing: 1.5, margin: 0 });
  statCard(s, 0.95, 2.95, 5.1, 1.15, "-30%", "Relative churn reduction, randomized A/B test vs. blanket outreach", { fill: WHITE });
  s.addText("Validated the only way we had time and buy-in to validate: an outcomes-based A/B test on the "
    + "overall trigger-and-outreach program. That's a real, defensible result — and it's also the limit of "
    + "what we did at the time.", {
    x: 0.95, y: 4.3, w: 5.1, h: 2.0, fontFace: FONT_BODY, fontSize: 12.5, color: MUTED, margin: 0, lineSpacingMultiple: 1.25,
  });

  s.addShape("roundRect", { x: 6.7, y: 2.25, w: 5.8, h: 4.3, rectRadius: 0.08, fill: { color: NAVY }, line: { type: "none" } });
  s.addText("WHAT THIS ENGINE ADDS", { x: 7.05, y: 2.5, w: 5.1, h: 0.35, fontFace: FONT_BODY, fontSize: 12, bold: true, color: TERRACOTTA, charSpacing: 1.5, margin: 0 });
  s.addText([
    { text: "Per-trigger causal identification, including for the one trigger a blanket A/B test never isolates on its own", options: { bullet: true, breakLine: true } },
    { text: "A formal, re-runnable optimization instead of a fixed value-score cutoff — it flexes with budget", options: { bullet: true, breakLine: true } },
    { text: "A quantified, confidence-labeled business case instead of a technical result that stops at the model", options: { bullet: true, breakLine: true } },
    { text: "Every method graded against a known ground truth before I'd trust it on a real decision", options: { bullet: true, breakLine: true } },
  ], { x: 7.05, y: 2.95, w: 5.15, h: 3.4, fontFace: FONT_BODY, fontSize: 12.5, color: WHITE, margin: 0, lineSpacingMultiple: 1.2, paraSpaceAfter: 8 });

  s.addNotes(
    "This slide is the bridge back to the STAR story: the real result stands on its own, and everything in this "
    + "deck is presented as the analytical engine underneath that kind of program — the part the original A/B "
    + "test alone couldn't show, not a replacement for what actually happened."
  );
}

// ============================================================ SLIDE 18: LIMITATIONS + WHY VANGUARD
{
  const s = lightSlide(pres);
  kicker(s, "Limitations — and why this role");
  slideTitle(s, "What I'd still want before this touches production");
  pageNum(s, 18);

  const limits = [
    ["Every estimate is scoped to the population it was tested on", "RDD and the DiD offer are HV-only; the cashback play is HV-only and SMS is LV-only. None of these effect sizes should be assumed to generalize across tiers without testing there directly — extrapolating the cashback effect to LV accounts, for instance, would not be valid."],
    ["No formal independent model-risk validation", "Today's validation is design-based (McCrary, pre-trends, randomization balance) and, here, grading against a KNOWN synthetic truth — a real deployment needs an independent conceptual-soundness review per SR 11-7."],
    ["Synthetic data throughout", "Built specifically so I could validate method correctness with a known ground truth — real deployment validates differently, without that luxury, and needs its own live monitoring for effect decay over time."],
  ];
  let y = 2.25;
  limits.forEach(([h, b]) => {
    s.addShape("roundRect", { x: 0.6, y, w: 11.9, h: 1.15, rectRadius: 0.06, fill: { color: ICE_TINT }, line: { type: "none" } });
    s.addText(h, { x: 0.9, y: y + 0.1, w: 4.2, h: 0.95, fontFace: FONT_BODY, fontSize: 12.5, bold: true, color: NAVY, margin: 0, valign: "middle", lineSpacingMultiple: 1.1 });
    s.addText(b, { x: 5.25, y: y + 0.1, w: 7.05, h: 0.95, fontFace: FONT_BODY, fontSize: 11.3, color: MUTED, margin: 0, valign: "middle", lineSpacingMultiple: 1.15 });
    y += 1.35;
  });

  s.addText("That gap between “validated by outcome” and “validated by design, before launch” is exactly "
    + "what draws me to this role — building the analytical engine where that rigor is the default, not a stretch goal.", {
    x: 0.6, y: 6.35, w: 11.9, h: 0.75, fontFace: FONT_BODY, fontSize: 13, italic: true, color: NAVY, margin: 0,
  });
  s.addNotes(
    "This slide is deliberate honesty, matching how I handled similar gap questions in the real project's prep -- "
    + "own the gap, and turn it into the motivation for the role rather than hiding it. The external-validity "
    + "point is the one I'd expect an interviewer with a stats background to probe hardest -- it's a genuine "
    + "limitation of doing everything through one shared HV/LV split rather than testing every combination."
  );
}

// ============================================================ SLIDE 19: CLOSING
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
  s.addNotes("Invite questions; have the bandwidth-sensitivity numbers, the 2x2 DiD table, and the appendix "
    + "SE→z→power backup slide ready if asked to go deeper.");
}

// ============================================================ SLIDE 20: APPENDIX — BACKUP (SE -> z -> power)
{
  const s = lightSlide(pres);
  kicker(s, "Appendix — backup, in case asked");
  slideTitle(s, "Why a 90/10 holdout still has enough power to detect the effect");
  pageNum(s, 20);

  s.addShape("roundRect", { x: 0.6, y: 2.05, w: 5.7, h: 4.7, rectRadius: 0.08, fill: { color: ICE_TINT }, line: { type: "none" } });
  s.addText("THE FORMULAS", { x: 0.9, y: 2.25, w: 5.1, h: 0.35, fontFace: FONT_BODY, fontSize: 12, bold: true, color: TERRACOTTA, charSpacing: 1.5, margin: 0 });
  s.addText([
    { text: "SE (pooled, for the test):  √[ p̄(1−p̄)(1/n₁ + 1/n₂) ]", options: { breakLine: true } },
    { text: "z = (p₁ − p₂) / SE", options: { breakLine: true } },
    { text: "Power ≈ Φ(|z| − z꜀ᵣᵢₜ), z꜀ᵣᵢₜ = 1.96 for a two-sided α=0.05", options: { breakLine: true } },
    { text: "Design effect (fixed total n, unequal split): 1 / [4·r·(1−r)], r = treated-arm share", options: { breakLine: true } },
  ], { x: 0.9, y: 2.65, w: 5.15, h: 2.1, fontFace: FONT_BODY, fontSize: 12, color: NAVY, lineSpacingMultiple: 1.35, margin: 0, paraSpaceAfter: 8 });
  s.addText("At r=0.5 the design effect is exactly 1 (no penalty). At r=0.9 (this project's actual split), "
    + "it's 1/(4·0.9·0.1) = 2.78× the variance a 50/50 split of the SAME total n would have had — worse, but "
    + "only ~1.67× the SE (√2.78), not a 10x disaster. It's the ABSOLUTE size of the smaller arm (~600 accounts "
    + "here), not its SHARE, that ultimately sets the precision floor.", {
    x: 0.9, y: 4.85, w: 5.15, h: 1.75, fontFace: FONT_BODY, fontSize: 11, italic: true, color: MUTED, margin: 0, lineSpacingMultiple: 1.22,
  });

  s.addShape("roundRect", { x: 6.55, y: 2.05, w: 6.05, h: 4.7, rectRadius: 0.08, fill: { color: NAVY }, line: { type: "none" } });
  s.addText("WORKED EXAMPLE — LV TIER (SMS), FIXED TOTAL n=6,000", { x: 6.9, y: 2.25, w: 5.4, h: 0.35, fontFace: FONT_BODY, fontSize: 10.8, bold: true, color: TERRACOTTA, charSpacing: 0.5, margin: 0 });
  const rows = [
    ["treated share r", "n treated", "n holdout", "SE", "z", "power"],
    ["0.50", "3,000", "3,000", "0.0115", "-5.07", "~1.00"],
    ["0.70", "4,200", "1,800", "0.0126", "-4.64", "~1.00"],
    ["0.80", "4,800", "1,200", "0.0144", "-4.05", "0.98"],
    ["0.90*", "5,400", "600", "0.0192", "-3.04", "0.86"],
    ["0.95", "5,700", "300", "0.0264", "-2.21", "0.60"],
  ];
  let ry = 2.68;
  const colX = [6.9, 8.15, 9.15, 10.15, 10.95, 11.65];
  rows.forEach((row, i) => {
    row.forEach((cell, ci) => {
      s.addText(cell, {
        x: colX[ci], y: ry, w: (colX[ci + 1] ?? 12.55) - colX[ci], h: 0.34,
        fontFace: FONT_BODY, fontSize: 10, bold: i === 0, color: i === 0 ? TERRACOTTA : (i === 4 ? TERRACOTTA : WHITE),
        align: ci === 0 ? "left" : "right", margin: 0, valign: "middle",
      });
    });
    ry += 0.36;
  });
  s.addText("* actual design. Holding total n and the OBSERVED effect fixed, power stays reasonable (~0.86) at "
    + "the actual 90/10 split — the point of running this table is to show that choice was checked, not assumed.", {
    x: 6.9, y: 4.95, w: 5.5, h: 1.6, fontFace: FONT_BODY, fontSize: 10.8, italic: true, color: ICE, margin: 0, lineSpacingMultiple: 1.25,
  });

  s.addNotes(
    "Only bring this slide up if asked to defend the 90/10 split, or asked to derive SE/z/power by hand. The HV "
    + "tier's own table (not shown) looks even more comfortable since its effect size is larger; LV/SMS is the "
    + "more conservative case worth having ready. This is the same SE→z→power chain used to originally size the "
    + "real project's A/B test allocation -- reused here to check the holdout fraction, not just to size a test "
    + "from scratch."
  );
}

pres.writeFile({ fileName: path.join(__dirname, "vanguard_dda_deck.pptx") }).then(() => {
  console.log("Deck written.");
});
