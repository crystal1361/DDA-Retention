const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
} = require("docx");
const fs = require("fs");
const path = require("path");

const NAVY = "1E2761";
const TERRACOTTA = "C1613C";
const GRAY = "5B6B8C";

function h1(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_1, spacing: { before: 200, after: 160 } });
}
function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2, spacing: { before: 320, after: 140 },
    children: [new TextRun({ text, bold: true, color: NAVY })],
  });
}
function label(text, color = TERRACOTTA) {
  return new Paragraph({
    spacing: { before: 160, after: 60 },
    // keepLines: true stops Word/LibreOffice from inserting a page break
    // in the MIDDLE of a wrapped heading line (which is what happened to
    // the longer Q14 heading before this was added -- the paragraph's
    // first wrapped line landed at the bottom of one page and its second
    // wrapped line started the next, splitting a Chinese word across the
    // page boundary). Harmless for every other (short, single-line) label
    // in this doc since a one-line paragraph has nothing to keep together.
    keepLines: true,
    children: [new TextRun({ text, bold: true, color, size: 21 })],
  });
}
function body(text) {
  return new Paragraph({ spacing: { after: 120 }, children: [new TextRun({ text, size: 21 })] });
}
function italicNote(text) {
  return new Paragraph({
    spacing: { after: 160 },
    children: [new TextRun({ text, italics: true, color: GRAY, size: 20 })],
  });
}
function bullet(text) {
  return new Paragraph({ text, bullet: { level: 0 }, spacing: { after: 60 } });
}
function qaBlock(qNum, qTitle, enText, cnText) {
  return [
    label(`Q${qNum}. ${qTitle}`, NAVY),
    label("English:"),
    body(enText),
    label("中文:"),
    body(cnText),
  ];
}
function hr() {
  return new Paragraph({
    spacing: { before: 100, after: 200 },
    border: { bottom: { color: "CADCFC", space: 4, style: BorderStyle.SINGLE, size: 6 } },
    children: [new TextRun({ text: "" })],
  });
}

const children = [];

// ---------------------------------------------------------------------- TITLE
children.push(
  new Paragraph({
    heading: HeadingLevel.TITLE,
    spacing: { after: 80 },
    children: [new TextRun({ text: "项目二 · 延伸材料", color: NAVY })],
  }),
  new Paragraph({
    spacing: { after: 240 },
    children: [new TextRun({
      text: "DDA 挽留决策引擎：RDD + 2组DiD + 分层随机化holdout RCT + 预算优化 + 业务影响量化（Vanguard 技术展示 / Technical Demo）",
      italics: true, color: GRAY, size: 22,
    })],
  }),
);

// ---------------------------------------------------------------------- POSITIONING
children.push(h2("定位说明 / Positioning"));
children.push(body(
  "This is a purpose-built technical demonstration, grounded in the same real DDA retention business problem I "
  + "worked on (see 项目二DDA存款流失挽留.docx) — the four churn modes, the trigger design, and the 30% relative "
  + "churn reduction from the real A/B test are all real. It is NOT presented as a literal retrofit of that "
  + "project's original design: every causal design here (RDD, DiD, the tier-stratified randomized-holdout RCT), "
  + "the ILP optimization, and the business-impact translation were built from scratch on synthetic data with a "
  + "known injected ground truth, with each trigger's analysis plan fixed BEFORE computing any effect — the same "
  + "discipline as pre-registration, not a result mined out of data already on hand. The goal is narrow and "
  + "explicit: demonstrate the causal-inference-under-non-randomization, optimization, and business-translation "
  + "skillset this Vanguard role calls for. Say this plainly if asked — it is honest framing, not a trick."
));
children.push(body(
  "这是一个专门为展示技能而设计的技术项目，扎根于我真实做过的DDA挽留业务问题（原始项目见《项目二DDA存款流失挽留.docx》）"
  + "——四种流失模式、触发式干预设计，以及真实A/B test测出的30%相对流失下降，都是真实的。但它不是对原项目设计的直接"
  + "复刻：这里的每一个因果设计（RDD、DiD、分层随机化holdout RCT）、ILP优化，以及业务影响翻译，都是用合成数据（内嵌"
  + "已知真实效应）从头搭建的，而且每个触发规则的分析方案都是在算出任何效应之前就先定好的——和预注册（pre-registration）"
  + "同样的纪律，不是从已有数据里现挖出来的结果。目的很单一、很明确：展示这个Vanguard岗位要求的、在无法随机化场景下"
  + "做因果推断、加上优化和业务转化的能力。被问到时就坦诚这样说——这是诚实的框定，不是套路。"
));

// ---------------------------------------------------------------------- STAR
children.push(h2("STAR — 更新版 Extended"));

children.push(label("Situation（English）"));
children.push(body("Same real business problem: no early-warning system for DDA churn, and blanket, undifferentiated retention outreach. The real A/B test validated a 30% relative churn reduction — but validation leaned on that outcome test alone, with no quasi-experimental analysis, no formal optimization behind the value cutoff, and no quantified business case beyond the headline percentage."));
children.push(label("Situation（中文）"));
children.push(body("同一个真实业务问题：DDA流失没有预警系统，挽留动作也是无差别的。真实A/B test验证了30%的相对流失下降——但验证只靠这一个结果检验，背后没有准实验分析，价值cutoff也没有正式优化支撑，除了这一个百分比之外也没有量化的业务案例。"));

children.push(label("Task（English）"));
children.push(body("Build, from scratch, the analytical engine this role specifically asks for: causal inference in three genuinely different non-randomized situations (a deterministic threshold, a single-date rollout, and a trigger with no natural design at all), a formal optimization layer, and a translation of all of it into a quantified business recommendation — with every analysis plan fixed before looking at outcomes, and every method graded against a known ground truth before I'd trust it."));
children.push(label("Task（中文）"));
children.push(body("从零搭建这个岗位特别要求的分析引擎：在三种真正不同、都无法随机化的场景下做因果推断（一个确定性阈值、一个单一时点上线、以及一个完全没有自然设计结构的触发规则），加上正式的优化层，并把这一切转化成一份量化的业务建议——每个分析方案都在看到结果之前就先定好，每个方法在被信任之前都先对照已知真值打分验证。"));

children.push(label("Action（English）"));
[
  "Sharp RDD on the 30%-withdrawal RM-outreach trigger, HV accounts only (the ROI-based value split used throughout — see Q4) — McCrary-style manipulation check, rdrobust local-linear estimate with bias-corrected robust inference, bandwidth sensitivity sweep.",
  "A plain 2-group DiD on the $100 DD-stop offer: it launches for the whole HV group on one calendar month; LV never gets it in-window. One treated group, one adoption date — by construction there's no already-treated cohort to contaminate the comparison, so no staggered-adoption correction is needed. Parallel pre-trends F-test on the pre-launch window; a 2x2 differencing estimate cross-checked against a fixed-effects regression; event-study plot showing a 3-month effect ramp.",
  "A tier-stratified randomized-holdout RCT on the dormant-reactivation play, the one trigger with no exploitable threshold or rollout date at all: HV accounts get a cashback offer (90% treated, 10% randomized holdout), LV accounts get an SMS reminder (same 90/10 split) — two independent two-proportion z-tests, one per tier, plus a randomization-balance ('Table 1') check on both arms before trusting the comparison.",
  "Multiple-choice knapsack ILP (PuLP/CBC) replacing the informal 'top 50% by value' cutoff — maximizes net expected value protected subject to a budget constraint, an RM-capacity constraint, and a one-intervention-per-account constraint, with tier-eligibility built in (cashback: HV only; SMS: LV only) — fed by all four causally-estimated, now uniformly high-confidence effect sizes above.",
  "A business-impact layer translating the optimizer's output into a per-10,000-scored-accounts dollar figure with an explicit scaling instruction (deliberately not a fabricated enterprise-wide total), a sensitivity check proving the one assumed rate in the value formula isn't load-bearing, and four prioritized, confidence-labeled recommendations.",
  "Every estimator graded against the true effect injected into the simulation, before ever trusting the method conceptually.",
].forEach(t => children.push(bullet(t)));
children.push(label("Action（中文）"));
[
  "对30%取款触发RM联系（只在HV高价值账户内，用的是贯穿全项目的ROI价值分层——见Q4）做sharp RDD——McCrary式操纵检验、rdrobust局部线性估计+偏差修正稳健推断、bandwidth敏感性扫描。",
  "对$100停DD offer做一个纯粹的2组DiD：offer在同一个日历月对整个HV组统一上线，LV组在观测窗口内始终不会拿到。只有一个处理组、一个上线时点——从设计上就不存在'已处理群组污染对照组'的问题，所以不需要额外做分批偏差修正。在上线前的窗口做平行趋势F检验，用2x2差分估计和固定效应回归互相校验，event-study图显示3个月的效应爬坡。",
  "对dormant再激活动作做一个分层随机化holdout RCT，这是三个触发中唯一完全没有可用阈值或上线时点结构的一个：HV账户拿到cashback offer（90%处理，10%随机holdout），LV账户拿到短信提醒（同样90/10分配）——两个独立的双比例z检验，每个价值层各一个，并且在信任对比结果之前先做了随机化平衡检验（'Table 1'）。",
  "用PuLP/CBC实现的多选择背包整数规划，替代原来非正式的'前50%价值'规则——在预算约束、RM产能约束、每账户最多一个干预的约束下最大化净预期保护价值，并内置分层资格限制（cashback仅限HV，短信仅限LV）——输入是上面四个因果估计出的、现在统一都是高置信度的效应大小。",
  "一个业务影响层，把优化器的输出转化为每万个评分账户的美元数字，并给出明确的放大说明（刻意不编造一个全行总数），同时用敏感性检验证明价值公式里唯一的假设比例不是决定性的，最后给出四条按优先级和置信度分层的行动建议。",
  "每个估计量在真正信任其方法论之前，都先对照模拟中注入的真实效应做了打分验证。",
].forEach(t => children.push(bullet(t)));

children.push(label("Result（English）"));
children.push(body("Real result stands: -30% relative churn from the actual A/B test. On top of that, the rebuild shows RDD recovering a -8.3pp effect (vs. a near-zero, misleading -0.2pp naive comparison) within about a point of the true simulated local effect; the 2x2 DiD estimator and its regression cross-check agreeing almost exactly at -5.8pp against a true simulated effect of -5.1pp; the dormant RCT correctly and precisely estimating both tier-specific effects (-10.8pp for HV cashback, -5.8pp for LV SMS, both within half a point of true, both with a clean randomization-balance check); and the optimization layer protecting ~49% more net value than the heuristic at equal budget and RM capacity — worth +$133,873 per 10,000 scored accounts, translated into four prioritized, uniformly high-confidence recommendations for the business."));
children.push(label("Result（中文）"));
children.push(body("真实结果依然成立：真实A/B test测出-30%相对流失。在此基础上，重建版本显示RDD恢复出-8.3pp的效应（相比接近于零、会误导人的-0.2pp naive对比），和模拟真实局部效应只差约1个百分点；2x2 DiD估计量和它的回归交叉验证几乎完全一致，都是-5.8pp，对照模拟真实效应-5.1pp；dormant RCT正确且精确地估计出两个价值层各自的效应（HV cashback -10.8pp，LV短信-5.8pp，都和真值相差不到半个百分点，且都通过了随机化平衡检验）；优化层在同样预算和RM产能下，比经验规则多保护约49%的净价值——按每万个评分账户折算价值+$133,873，最终转化成四条按优先级排列、置信度统一为高的业务建议。"));

children.push(hr());

// ---------------------------------------------------------------------- Q&A
children.push(h2("技术追问 Q&A"));

qaBlock(1, "This is synthetic data — isn't that a problem? / 这是合成数据，这样合适吗？",
  "No, if framed honestly. Real account-level data with a designed quasi-experiment isn't something I could ever bring out of the bank, and it's also not publicly available anywhere, for privacy reasons. Building the data-generating process myself let me inject a KNOWN ground-truth effect, so I could validate that RDD, DiD, and the randomized-holdout RCT actually recover it before I'd trust any of them on a real decision. I'm upfront that this is a purpose-built demonstration grounded in a real business problem, not a claim that I ran these exact methods at my employer.",
  "如果坦诚说明就没问题。真实账户级数据、还带着设计好的准实验结构，这种数据我不可能从银行带出来，出于隐私原因这类数据在任何地方也不会公开。自己搭建数据生成过程，让我能内嵌一个已知的真实效应，这样才能验证RDD、DiD、随机化holdout RCT真的能恢复出这个效应，再去真正信任这些方法。我会坦诚说明这是扎根于真实业务问题、专门为展示技能搭建的项目，不是声称我在雇主那边真的跑过这些具体方法。"
).forEach(p => children.push(p));

qaBlock(2, "Walk me through the RDD identifying assumption. / RDD的识别假设是什么？",
  "The core assumption is that nothing else changes discontinuously at the 30% withdrawal cutoff except the RM outreach itself. Since withdrawal size is a real economic behavior — not something a customer can precisely dial to land just above or below 30% — accounts just below and just above the cutoff should be comparable in every way except treatment. I test this directly with a McCrary-style density check: if customers were gaming the cutoff, the density of the running variable would show a jump right at 30%. It didn't (p=0.83). This estimate is scoped to HV accounts specifically — the same ROI-based value split used everywhere in this project (see Q4) — so it speaks to that population, not a claim about how RM outreach would perform on LV accounts.",
  "核心假设是：在30%取款这个断点上，除了RM联系本身，没有别的东西同时发生跳跃。因为取款金额是真实的经济行为——客户没法精确操控让自己刚好卡在30%上下——所以断点左右两边的账户除了是否被联系，其他方面应该是可比的。我直接用McCrary式密度检验来验证这一点：如果客户在操纵这个断点，running variable的密度会在30%处出现跳跃。检验结果没有跳跃（p=0.83）。这个估计的范围限定在HV高价值账户内——用的是贯穿全项目同一个基于ROI的价值分层（见Q4）——所以它说的是这个人群的效应，不是在断言RM联系对LV账户也会有同样效果。"
).forEach(p => children.push(p));

qaBlock(3, "How did you pick the bandwidth, and does the result depend on it? / bandwidth怎么选的，结果对它敏感吗？",
  "I used rdrobust's MSE-optimal bandwidth selector (Calonico-Cattaneo-Titiunik) rather than picking one by hand, and reported both the conventional and bias-corrected robust estimate — the robust one is what you should actually trust. I then swept bandwidths from 4 to 20 months as a sensitivity check: the estimate stayed in the high-single-digit-to-low-double-digit percentage-point range (roughly -6.8pp to -10.7pp) across that whole range, so the result isn't an artifact of one bandwidth choice.",
  "我用的是rdrobust自带的MSE最优bandwidth选择方法（Calonico-Cattaneo-Titiunik），不是手工挑的，同时报告了conventional和偏差修正后的robust估计——真正该信的是robust那个。然后我把bandwidth从4扫到20个月做敏感性检验：整个区间内估计值都稳定在个位数到十位数百分点之间（大约-6.8pp到-10.7pp），说明结果不是某一个bandwidth选择的巧合。"
).forEach(p => children.push(p));

qaBlock(4, "Why DiD for the DD-stop offer, and why a single HV/LV split instead of a staggered rollout? / 为什么用DiD做停DD offer，为什么是单一的HV/LV分层而不是分批上线？",
  "The offer launches for the whole high-value group on one calendar month, and the low-value group never gets it in-window — a deliberately simple, single-adoption-date design, not a multi-wave rollout. Two reasons for that choice. First, the split itself isn't invented for this method — it's the SAME 50/50 high-value/low-value split used by RDD and the dormant RCT (see the shared-split callout on the architecture slide), grounded in the real project's own ROI logic: funded outreach only pencils out above that value line. Second, with exactly one treated group and one launch date, this design sidesteps the staggered-adoption bias (Goodman-Bacon 2021) that a multi-wave, tier-by-tier rollout would introduce entirely, rather than needing a clean-control estimator to correct for it after the fact — a simpler design that doesn't need the correction beats a more complex one that does, when the underlying business rollout doesn't actually require staggering.",
  "这个offer在同一个日历月对整个高价值组统一上线，低价值组在观测窗口内始终拿不到——这是一个刻意做得很简单的单一上线时点设计，不是多批次的分阶段上线。这么选有两个原因。第一，这个分层本身不是为这个方法专门发明的——它和RDD、dormant RCT用的是同一个50/50高价值/低价值分层（见架构那张slide上'一个分层，处处复用'的说明），根植于真实项目自己的ROI逻辑：只有在这条价值线以上，有资金支持的外联才划算。第二，只有一个处理组、一个上线时点，这个设计从根子上就绕开了多批次、逐层上线会引入的分批偏差问题（Goodman-Bacon 2021），而不需要事后再用clean-control估计量去修正——如果业务上线本身并不真的需要分批，一个不需要修正的简单设计，比一个需要修正的复杂设计更好。"
).forEach(p => children.push(p));

qaBlock(5, "Isn't a plain 2x2 DiD too simple? When would you need something like Callaway-Sant'Anna? / 一个简单的2x2 DiD是不是太简单了？什么时候才需要Callaway-Sant'Anna这类方法？",
  "It's simple on purpose, and that's a feature here, not a shortcut: with exactly one treated group and one adoption date, the four-group-means differencing and a fixed-effects regression are two ways of computing the exact same number (they agree here to two decimal places), which is itself a useful sanity check to show working, and there's no staggered-timing structure for a more sophisticated estimator to correct for. I'd reach for Callaway-Sant'Anna, a clean-control/stacked estimator, or a DoubleML-based staggered-DiD tool specifically when the rollout has MULTIPLE adoption dates across groups AND the effect isn't constant over time — that combination is what creates Goodman-Bacon's negative-weighting bias. Neither condition holds in this design, so reaching for that machinery here would be over-engineering, not rigor.",
  "这里故意做得很简单，而且这在这个场景下是个优点，不是走捷径：只有一个处理组、一个上线时点，四组均值差分和固定效应回归算出来的其实是同一个数字（这里两种方法的结果精确到小数点后两位都一致），这本身就是一个很好的自证一致性的检验，而且这里也不存在分批时点结构需要更复杂的估计量去修正。我会在上线有多个时点、跨组不一样，而且效应又不是随时间恒定的时候，才去用Callaway-Sant'Anna、clean-control/stacked估计量，或者基于DoubleML的分批DiD工具——正是这两个条件同时满足，才会产生Goodman-Bacon说的负权重偏差。这个设计里这两个条件都不成立，所以在这里硬上那套机器不是严谨，是过度设计。"
).forEach(p => children.push(p));

qaBlock(6, "How did you validate the parallel-trends assumption? / 平行趋势假设怎么验证的？",
  "I restricted to the pre-launch window (before the offer goes live for HV accounts at all), then ran an F-test on the value-group × calendar-month interaction — a significant interaction would mean HV and LV were already trending differently before treatment, which would break DiD's core assumption. It came back insignificant (p=0.63). Note the assumption is about the TREND, not the LEVEL: HV and LV don't need to have the same churn rate pre-launch (they don't — HV churns less overall), they just need to be moving in the same direction month to month.",
  "我限定在offer对HV账户上线之前的窗口内，对'价值分层×日历月'交互项做F检验——如果交互项显著，就说明处理之前HV和LV已经在走不同的趋势，DiD的核心假设就不成立。检验结果不显著（p=0.63）。要注意这个假设针对的是趋势，不是水平：HV和LV在上线前不需要有一样的流失率（事实上也确实不一样——HV整体流失更低），只需要两者逐月的变化方向一致。"
).forEach(p => children.push(p));

qaBlock(7, "How did you build the account-value formula, and how do you defend the specific 15% number? / 账户价值公式怎么建的，那个15%具体怎么辩护？",
  "This is a formula I redesigned specifically after getting negative interview feedback on an earlier arbitrary weighted index (product_count*3 + tenure_months*0.05 + balance_tier*2 — weights with no defensible origin). The current version is account_value = balance * (1 + 15% * product_count): a dollar-denominated estimate of the relationship's value, where each additional product is assumed to add roughly 15% incremental value on top of the base balance (cross-sell revenue, stickiness, lower attrition risk). Two things make this defensible where the old one wasn't: first, it's in DOLLARS, not an arbitrary index, so every term has a real-world unit and interpretation. Second — and this is the answer to 'why 15% and not something else' — I ran a sensitivity check: recomputing the ranking at 10% and 20% instead of 15% gives a Spearman rank correlation above 0.999, and over 98% of the accounts that land in the top value quartile under 15% stay there under 10% or 20%. So the specific number affects who's on the margin, but not the overall prioritization the business actually acts on — that's the concrete, provable answer, instead of asserting the number is 'right'. This is also the exact formula behind the 50/50 high/low value split that RDD, DiD, and the dormant RCT all share.",
  "这是我在因为之前一个任意加权指数（product_count*3 + tenure_months*0.05 + balance_tier*2——权重没有可辩护的来源）被面试官差评之后，专门重新设计的公式。现在的版本是account_value = balance × (1 + 15% × product_count)：一个美元化的客户关系价值估计，假设每多开一个产品，大致在基础余额上再带来15%的增量价值（交叉销售收入、粘性、更低的流失风险）。这个版本比旧版更能站住脚，原因有两个：第一，它是美元单位，不是一个任意的指数，每一项都有真实世界的单位和含义。第二——这也是'为什么是15%不是别的数'的答案——我做了敏感性检验：把15%换成10%或20%重新计算排序，Spearman秩相关系数都在0.999以上，而且在15%假设下进入价值前25%分位的账户，换成10%或20%之后有超过98%依然留在前25%分位。所以这个具体数字会影响谁刚好卡在边界上，但不会影响业务实际会采取行动的整体优先级排序——这是一个具体的、可以证明的答案，而不是断言这个数字'就是对的'。这也正是RDD、DiD、dormant RCT三处共用的50/50高低价值分层背后的那个公式。"
).forEach(p => children.push(p));

qaBlock(8, "Walk me through the optimization formulation. Why an ILP, not just ranking? / 优化怎么建模的？为什么要用整数规划而不是简单排序？",
  "It's a multiple-choice knapsack: each account can receive at most one of four interventions (large-withdrawal RM contact, DD-stop offer, dormant cashback, dormant SMS), subject to a total budget constraint, a separate RM-capacity constraint (RM time, not dollars, is the actual bottleneck for the withdrawal play), and tier eligibility (an account is only ever a candidate for the intervention its value tier actually qualifies for). A simple ranking works if there's exactly one resource constraint; with two constraints binding different intervention types simultaneously plus tier eligibility, a formal ILP (I used PuLP with the CBC solver) finds the truly optimal allocation rather than an ad hoc approximation. The objective maximizes net expected value: predicted probability of that churn mode times the causally-estimated effect size times account_value (dollars at risk), minus intervention cost. At equal budget and RM capacity, the optimizer protects about 49% more net value than the heuristic — and notably, it doesn't spend to the last dollar or the last RM contact; it stops once an account's marginal expected value turns negative, a form of capital discipline the flat heuristic doesn't have. This approach fits a handful of discrete, mutually-exclusive interventions with known effect sizes and hard resource caps; it wouldn't fit a continuous decision (how much to offer, not just whether) or effect sizes too uncertain to plug into a point-estimate objective without a robustness check first.",
  "这是一个多选择背包问题：每个账户最多接受四种干预（取款RM联系、DD停用offer、dormant cashback、dormant短信）中的一种，同时受总预算约束、一个单独的RM产能约束（RM时间而不是钱，才是取款干预真正的瓶颈），以及分层资格限制（一个账户只会是它自己价值分层真正符合条件的那个干预的候选）。如果只有一个资源约束，简单排序就够了，但这里有两个约束同时作用在不同干预类型上，再加上分层资格限制，用正式的整数规划（我用PuLP+CBC solver）才能找到真正最优的分配，而不是一个凑合的近似。目标函数是最大化净预期价值：预测的流失模式概率×因果估计出的效应大小×account_value（风险敞口金额），再减去干预成本。在同样预算和RM产能下，优化器比经验规则多保护约49%的净价值——而且值得注意的是，它不会把预算或RM名额用到最后一分钱/一个名额，一旦某个账户的边际预期价值转负就会停止分配，这是一种经验规则没有的资金纪律。这个方法适合少数几个离散、互斥、效应大小已知、且有硬性资源上限的干预；不适合连续决策（给多少折扣，而不只是给不给），也不适合效应大小本身太不确定、还没经过稳健性检验就直接当点估计塞进目标函数的场景。"
).forEach(p => children.push(p));

qaBlock(9, "Why redesign the dormant play as a randomized holdout instead of the observational (DoubleML) approach, and why two separate arms? / 为什么把dormant这个动作改成随机化holdout而不是继续用观测性方法（DoubleML）？为什么分两个独立的臂？",
  "Neither RDD nor DiD naturally applies here — dormant accounts get flagged by a threshold/branching rule and treated together, with no cutoff to exploit and no phased rollout. An earlier version of this project handled that with DoubleML (selection-on-observables): it correctly recovered the sign where naive and logistic comparisons didn't, but its validity rested on an assumption — 'we captured every important confounder' — that can't be directly tested from the data, unlike RDD's no-manipulation check or DiD's pre-trends check. Rather than lean further into that weaker identification, I redesigned the rollout itself: a small (10%) randomized holdout within each value tier converts an untestable assumption into a directly testable one (a randomization-balance check), at a modest cost (10% of flagged accounts don't get the offer, temporarily, purely for measurement). The two tiers get genuinely different plays — HV gets a funded cashback offer, LV gets a near-free SMS reminder — so they're kept as two separate randomized comparisons rather than pooled: pooling would confound 'which offer is more effective' with 'which tier is inherently lower-risk,' since HV and LV differ on both dimensions by construction.",
  "RDD和DiD在这里都用不上——dormant账户是被一个阈值/分支规则打标的，然后被一起处理，没有断点可用，也没有分批上线。这个项目更早的版本用DoubleML（selection-on-observables）处理这个问题：它确实正确恢复了符号方向，而naive和logistic对比都没做到，但它的有效性依赖一个假设——'我们捕捉到了所有重要的混杂因素'——这个假设没法直接从数据里验证，不像RDD的操纵检验或DiD的前置趋势检验那样。与其在这个较弱的识别方式上继续深挖，我重新设计了上线方式本身：在每个价值层内留一个小比例（10%）的随机化holdout，把一个没法验证的假设变成一个可以直接验证的假设（随机化平衡检验），代价也不大（10%被打标的账户暂时拿不到offer，纯粹是为了测量）。两个价值层拿到的是真正不同的干预——HV拿到有资金支持的cashback offer，LV拿到几乎零成本的短信提醒——所以它们被作为两个独立的随机化对比保留，而不是合并在一起：合并会把'哪个offer更有效'和'哪个价值层本身风险更低'这两件事混在一起，因为HV和LV在这两个维度上本来就都不一样。"
).forEach(p => children.push(p));

qaBlock(10, "How do you know the randomization actually worked here, rather than just assuming it did? / 你怎么知道这里的随机化真的起作用了，而不是只是假设它起作用？",
  "By running the standard 'Table 1' check any RCT write-up would run: within each value tier, compare treated and holdout accounts on five observed covariates (engagement score, dormancy streak, product count, tenure, balance) BEFORE any offer went out, using a two-sample t-test per covariate. Across both tiers and all five covariates (10 tests total), zero came back significant at p<=0.05 — consistent with what you'd expect if randomization worked, roughly the ~0.5 false positives chance alone would predict at that alpha level, and no more. That's the direct evidence the two arms are comparable by construction, not just by assumption — the same standard of proof RDD's no-manipulation check and DiD's pre-trends check provide for their own designs.",
  "方法是跑一个任何RCT报告都会做的标准'Table 1'检验：在每个价值层内，用双样本t检验，在offer发出之前，对比处理组和holdout组在五个可观测协变量上的差异（活跃度分数、休眠时长、产品数量、tenure、余额）。两个价值层、五个协变量总共10个检验，没有一个在p≤0.05的水平上显著——这正符合随机化真的起作用时该有的样子，大约就是这个显著性水平下纯属偶然会出现的~0.5个假阳性，不多不少。这就是两组在设计上（而不只是假设上）真的可比的直接证据——和RDD的操纵检验、DiD的前置趋势检验为各自设计提供的是同一等级的证明。"
).forEach(p => children.push(p));

qaBlock(11, "Business impact: why report per-10,000-accounts instead of one big enterprise-wide dollar number? / 业务影响为什么按每万个账户折算，而不是给出一个全行的大数字？",
  "Because I don't know the real book size, and inventing one to produce a bigger, more impressive-sounding total would be exactly the kind of overclaiming I've been careful to avoid everywhere else in this project. This project's data is a sized demo (a 10,000-account scored test set), not the institution's actual book. So I report the incremental value — +$133,873, +49.4% — per 10,000 scored accounts, with an explicit instruction: multiply by (your real scored-account count / 10,000) to get your actual number. The mechanism behind the gain is what matters and what I'd actually defend: same budget, same RM capacity, better targeting — and that mechanism scales linearly with book size, unlike a one-time fixed-cost project, which is the honest and still-compelling way to make the business case without a number I can't stand behind.",
  "因为我不知道真实的账户规模，编一个数字出来让总数看起来更大、更唬人，恰恰是我在这个项目其他地方一直刻意避免的那种过度声称。这个项目的数据是一个按规模缩小的demo（一万个账户的评分测试集），不是机构真实的账本。所以我把增量价值——+$133,873，+49.4%——按每万个评分账户来报告，并明确说明：乘以（你真实的评分账户数/10,000）就能得到你的实际数字。真正重要、也是我真正能站住脚辩护的，是这个提升背后的机制：同样的预算、同样的RM产能，更好的targeting——而这个机制会随账本规模线性放大，不像一次性固定成本的项目，这是一个诚实、同时依然有说服力的方式去讲这个业务案例，而不是用一个我自己都无法完全站得住的数字。"
).forEach(p => children.push(p));

qaBlock(12, "How would this extend toward a real production deployment? / 真要落地生产环境，还需要做什么？",
  "Same gap I named in the original project's Q7: today's validation is design-based (plus, here, grading against a known synthetic truth). A real deployment needs independent model-risk validation per SR 11-7 — documented intended use, assumptions, and limitations; a conceptual-soundness review by a separate validation team; an ongoing monitoring/drift plan, including watching whether the dormant RCT's effect sizes hold up as the flagged population and take-up rates shift over time. I'd also flag external validity explicitly: every estimate here is scoped to the specific tier it was tested on (RDD and the DiD offer: HV only; cashback: HV only; SMS: LV only) — none of these should be assumed to transfer across tiers without testing there directly.",
  "和原项目Q7里点出的gap是同一个：今天的验证是基于设计的（这里还额外对照了已知的合成真值）。真正落地生产环境，需要按SR 11-7做独立模型风险验证——记录intended use、假设、局限；由独立验证团队做conceptual-soundness审查；定义持续监控/drift计划，包括随时间观察dormant RCT的效应大小在被打标人群和触达率变化之后是否依然成立。我还会主动提出外部有效性的问题：这里的每一个估计都限定在它被测试的那个具体价值层上（RDD和DiD offer：仅HV；cashback：仅HV；短信：仅LV）——都不应该在没有直接测试过的情况下，假设它能跨价值层照搬。"
).forEach(p => children.push(p));

qaBlock(13, "What would you do differently next time? / 下次你会怎么做得不一样？",
  "I already made the biggest change I'd have recommended in an earlier version of this project: the dormant play is no longer a selection-on-observables workaround, it's a genuine randomized holdout designed in from the start. What's left: I'd build the panel data richer (full month-by-month account trajectories rather than event-level samples) so the same dataset could support all the causal questions together instead of separate analytic samples — closer to how a real production data pipeline would be structured. I'd also layer causal-ML methods (e.g. causal forests / uplift modeling) on top of the now-randomized dormant data to estimate HETEROGENEOUS effects across accounts, not just the two tier-level averages — that's the natural next question once a clean average effect is in hand.",
  "这个项目更早的版本里我最想改的那件事，这次已经改了：dormant这个动作不再是一个selection-on-observables的变通方案，而是从一开始就设计好的真正随机化holdout。剩下还能改进的：我会把面板数据做得更完整（完整的逐月账户轨迹，而不是事件级抽样样本），这样同一份数据集就能同时支撑所有因果问题，而不是分开的分析样本——这样更接近真实生产数据管道该有的样子。我也会在现在已经随机化的dormant数据基础上叠加因果机器学习方法（比如causal forest/uplift建模），去估计跨账户的异质效应，而不只是两个价值层各自的平均效应——这是拿到一个干净的平均效应之后，很自然的下一个问题。"
).forEach(p => children.push(p));

qaBlock(14, "You said if this went to production you'd add unit tests, a config file, data validation and logging, full seeding for reproducibility, and a service layer — did you actually build those? / 你说过如果要往生产走会加单元测试、配置文件、数据校验和日志、完全seed保证可复现、再包一层服务接口——这些你真做了吗？",
  "Yes — all six. config.py centralizes every constant (paths, SEED, model hyperparameters, budget, RM capacity, the value-split percentile, the 15% product-value-uplift rate) that used to be hardcoded separately in each script. validation.py adds fail-loud-and-early checks, and it caught a real bug while I was building it: treated_rm_contact was being derived from the UNROUNDED withdrawal_pct while the stored running variable was rounded to 2 decimals, so a handful of boundary rows could round to exactly the cutoff and disagree with their own treatment flag — not a sharp RDD anymore for those rows. I fixed it by rounding before deriving treatment. logging_setup.py adds structured console+file logging alongside — not replacing — each script's narrated print() output, since that narration is genuinely useful for a live walkthrough. For reproducibility, config.seed_everything() seeds both numpy's modern Generator API and its legacy global RandomState (which scikit-learn's shuffle=True paths draw from) in one call, and XGBoost is pinned to n_jobs=1 to remove multi-threaded floating-point nondeterminism. I verified this by running the full 8-script pipeline twice independently and diffing data/, output/, and figures/ byte-for-byte — zero differences. I added a pytest suite (50+ tests) covering the config formula, every validation check's pass/fail path including the boundary bug above, the data generators' invariants, the optimizer's ILP constraints and tier-eligibility logic, and the service endpoints — which also meant refactoring 06_optimization.py, which had NO __main__ guard at all (running the entire optimization as an import side effect), into an importable run_optimization() function. And I wrapped the batch outputs in a FastAPI service (health check, per-account score lookup, the recommendation list, and a synchronous /optimize endpoint that re-solves the ILP under a caller-supplied budget) — deliberately not a live-retraining service, since the heavy model-fitting stays a scheduled batch job and only the cheap ILP re-solve needs to be synchronous.",
  "全部六项都做了。config.py把之前散落在各脚本里的常量（路径、SEED、模型超参数、预算、RM产能、价值分层的分位点、15%的产品价值加成率）集中到一个地方。validation.py加了'尽早报错'的校验，而且在写它的过程中真的抓到一个bug：treated_rm_contact是从没有四舍五入的withdrawal_pct算出来的，但存盘的running variable四舍五入到了2位小数，导致极少数边界行四舍五入后正好落在cutoff上，和自己的treatment标记不一致——对这些行来说已经不是严格的sharp RDD了。修复方式是先四舍五入再判定treatment。logging_setup.py加了结构化的console+文件日志，但没有替换掉每个脚本本身的print()叙事——因为那些叙事在真人讲解时是有实际用处的。可复现性方面，config.seed_everything()一次调用就同时锁定numpy新版Generator API和scikit-learn的shuffle=True会用到的旧版全局RandomState，另外把XGBoost的n_jobs固定成1，去掉多线程浮点数求和带来的不确定性。我验证的方式是把完整的8步pipeline独立跑两次，对data/、output/、figures/三个目录做字节级diff——完全没有差异。我加了一套pytest测试（50+条），覆盖config公式、每条校验规则的通过/失败路径（包括上面那个边界bug）、数据生成器的不变量、优化器ILP的约束和分层资格逻辑、以及服务端点——这也顺带逼着我把06_optimization.py重构了一遍，它之前完全没有__main__保护，只要import这个文件就会把整个优化流程当副作用跑一遍，我把它拆成了一个可以被单独调用的run_optimization()函数。最后把批处理的输出包了一层FastAPI服务（健康检查、按账户查分数、建议列表、以及一个允许调用方传入不同预算实时重新求解ILP的/optimize端点）——刻意没做成'每次请求都重新训模型'的服务，因为重的模型训练留在定时批处理里，只有轻量的ILP重新求解需要做成同步的。"
).forEach(p => children.push(p));

qaBlock(15, "This time you actually built the prospective design (pre-registered plans, a real holdout) instead of retrofitting — what did that trade off, and what's still missing for a real launch? / 这次你确实做出了前瞻式设计（预注册方案、真正的holdout），而不是事后补causal inference——这付出了什么代价？真要上线还差什么？",
  "The trade-off is concrete and small, not hypothetical: the dormant RCT's 10% holdout means, for as long as the test runs, 10% of flagged accounts in each tier don't get the offer they'd otherwise be prioritized for — a real, bounded cost paid specifically to get a testable identification instead of an untestable one. For the other two triggers, no extra cost was needed at all: RDD and the DiD offer both already had a naturally-occurring quasi-experimental structure (a threshold, a single rollout date) to exploit, so no additional test was proposed for them — the discipline there was choosing the RIGHT comparison in advance, not adding a new experiment. What's still missing for a real launch: a formal power/sample-size calculation done BEFORE launch rather than checked after the fact (the backup slide's SE→z→power table is the after-the-fact version of that same check), a pre-registered primary metric and analysis code, and sign-off from risk/compliance on withholding a small slice of already-identified accounts, including monitoring the holdout for any disparate impact across protected groups.",
  "这个代价是具体的、很小的，不是假设性的：dormant RCT的10% holdout意味着，只要这个测试还在跑，每个价值层里就有10%被打标的账户拿不到本该优先给到他们的offer——这是一个真实的、有边界的代价，专门用来换取一个可以被验证、而不是没法被验证的识别方式。另外两个触发规则完全不需要额外付出这个代价：RDD和DiD offer本身就已经有一个天然存在的准实验结构（一个阈值、一个单一上线时点）可以利用，所以没有为它们额外提议任何测试——那里的纪律是提前选对该做哪个对比，而不是加一个新实验。真要上线还差什么：一个在上线之前、而不是事后才做的正式power/样本量计算（附录backup slide上的SE→z→power表格，其实就是这同一个检验的事后版本）、一份预先注册好的主要指标和分析代码，以及拿到风控/合规对'暂时不干预一小部分已识别账户'这件事的审批，包括监控这个holdout会不会在受保护群体上产生不成比例的影响。"
).forEach(p => children.push(p));

qaBlock(16, "Once the dormant play is randomized, do you still need RDD/DiD at all for the other two triggers? / dormant这个动作已经随机化了，另外两个触发规则还需要RDD/DiD吗？",
  "For dormant specifically — no, and that's exactly the point of the redesign: once it's genuinely randomized, a simple two-proportion z-test (what 07_dormant_rct.py actually runs) is a strictly better answer than an observational method, because it doesn't rest on any untestable identifying assumption. RDD and DiD still earn their place for the other two triggers, though, because those ARE NOT randomized and can't cheaply be made so the way dormant could: the withdrawal threshold is a real-time risk rule (delaying or withholding RM contact from a flagged large-withdrawal account carries more immediate risk than delaying a cashback offer to a dormant one), and the DD-stop offer's single launch date is already about as simple a rollout as this business process supports. In principle you COULD design randomization into either — e.g. a small delayed-contact holdout for the withdrawal trigger, or randomizing which accounts within the HV group get the offer a few weeks earlier versus later (a stepped-wedge design) — and if I were rebuilding this a third time, that's the direction I'd push next, for the same reason the dormant redesign was worth doing: it trades a small, bounded cost for a strictly cleaner answer.",
  "对dormant这个具体动作来说——不需要了，这正是这次重新设计的意义：一旦真的随机化了，一个简单的双比例z检验（07_dormant_rct.py里实际跑的东西）就是比观测性方法更好的答案，因为它不依赖任何没法验证的识别假设。但RDD和DiD对另外两个触发规则来说仍然有存在的必要，因为这两个规则本身不是随机的，也没法像dormant那样低成本地改成随机的：取款阈值是一个实时风险规则（对一个已经被标记为大额取款的账户延迟或不做RM联系，比对一个dormant账户延迟发cashback offer的即时风险要大得多），而DD停用offer的单一上线时点，已经是这类业务流程能支持的最简单上线方式了。原则上你确实可以往这两个规则里设计进随机化——比如给取款触发加一个小比例的延迟联系holdout，或者把HV组内谁先几周拿到offer、谁晚几周拿到随机化（stepped-wedge设计）——如果我第三次重做这个项目，这会是我接下来想推进的方向，原因和这次重做dormant一样：用一个小的、有边界的代价，换一个更干净的答案。"
).forEach(p => children.push(p));

children.push(hr());

// ---------------------------------------------------------------------- QUICK REFERENCE
children.push(h2("速记 Quick Reference"));

const rows = [
  ["Outcome window (all 4 datasets)", "60 days / ~2 months -- deliberately matched to the real project's actual 2-month A/B test window (see Q6 in the original project's Q&A), not an arbitrary 1-month label"],
  ["Shared HV/LV split", "Top/bottom 50% by account_value -- one ROI-based business split, reused by RDD's population, DiD's treated/control groups, and both dormant RCT arms"],
  ["RDD cutoff / running variable / population", "30% of balance withdrawn in a month; HV accounts only"],
  ["RDD naive vs. robust estimate", "-0.2pp (biased, near zero) vs. -8.3pp [95% CI -12.3, -4.3], p<0.001"],
  ["RDD manipulation check", "McCrary-style, p = 0.83 (pass) -- guards against ANY unexplained density bunching at 30%, not just intentional gaming"],
  ["RDD bandwidth sensitivity", "~-6.8pp to -10.7pp across h = 4 to 20 (stable order of magnitude)"],
  ["DiD design", "2-group, single adoption date: offer launches for all HV accounts on one calendar month; LV never gets it in-window"],
  ["DiD parallel pre-trends check", "F-test on pre-launch window, p = 0.63 (pass)"],
  ["DiD 2x2 vs. regression estimate", "-5.8pp vs. -5.8pp (agree almost exactly; true simulated effect: -5.1pp)"],
  ["DiD effect ramp", "~3 months to reach steady state"],
  ["Account-value formula", "account_value = balance × (1 + 15% × product_count); ranking robust to 10%/20% alt. rates (Spearman > 0.999, 98%+ top-quartile overlap)"],
  ["Dormant RCT design", "HV: 90% cashback offer / 10% randomized holdout. LV: 90% SMS reminder / 10% randomized holdout. Two independent two-proportion z-tests."],
  ["Dormant RCT results", "HV cashback: -10.8pp [95% CI -14.5, -7.1], p<0.001 (true -10.4pp). LV SMS: -5.8pp [95% CI -9.8, -1.9], p=0.002 (true -6.0pp)."],
  ["Dormant RCT balance check", "0 / 10 covariate-balance tests flagged at p<=0.05, across both tiers"],
  ["Optimization result", "+64.3% net value protected vs. heuristic, equal budget & RM capacity"],
  ["Optimization RM capacity used", "193 / 400 contacts (optimizer stops at negative marginal value, not at capacity)"],
  ["Business impact (headline)", "+$167,927 net value per 10,000 scored accounts (+64.3%) — scale by (your accounts / 10,000)"],
  ["Real project result (unchanged)", "-30% relative churn, randomized A/B test"],
  ["Production-readiness additions", "config.py, validation.py (caught a real sharp-RDD boundary bug), logging_setup.py, full RNG seeding, 50+ pytest tests, FastAPI service.py — two independent full pipeline runs diff byte-identical"],
  ["What's still missing for real launch", "Pre-launch power/sample-size sign-off, risk/compliance approval on the holdout, independent SR 11-7 model-risk validation, ongoing drift monitoring on the RCT effect sizes"],
];

const table = new Table({
  width: { size: 100, type: WidthType.PERCENTAGE },
  columnWidths: [4500, 5500],
  rows: rows.map(([k, v], i) => new TableRow({
    children: [
      new TableCell({
        width: { size: 4500, type: WidthType.DXA },
        shading: { type: ShadingType.CLEAR, fill: i % 2 === 0 ? "EEF3FC" : "FFFFFF" },
        children: [new Paragraph({ children: [new TextRun({ text: k, bold: true, size: 20 })] })],
      }),
      new TableCell({
        width: { size: 5500, type: WidthType.DXA },
        shading: { type: ShadingType.CLEAR, fill: i % 2 === 0 ? "EEF3FC" : "FFFFFF" },
        children: [new Paragraph({ children: [new TextRun({ text: v, size: 20 })] })],
      }),
    ],
  })),
});
children.push(table);

const doc = new Document({
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 } } },
    children,
  }],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(path.join(__dirname, "..", "output", "项目二-延伸-RDD-DiD-优化-QA.docx"), buf);
  console.log("Doc written.");
});
