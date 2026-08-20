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
      text: "DDA 挽留决策引擎重建：RDD + 客户价值分层 DiD + DoubleML + 预算优化 + 业务影响量化（Vanguard 技术展示 / Technical Demo）",
      italics: true, color: GRAY, size: 22,
    })],
  }),
);

// ---------------------------------------------------------------------- POSITIONING
children.push(h2("定位说明 / Positioning"));
children.push(body(
  "This is a technical demonstration built on top of the real DDA retention project (see 项目二DDA存款流失挽留.docx). "
  + "The STAR narrative, the four churn modes, the trigger design, and the 30% relative churn reduction from the real "
  + "A/B test are all real. Everything involving RDD, value-tier DiD, DoubleML, formal optimization, and the "
  + "business-impact translation was built afterward, on synthetic data with a known injected ground truth, "
  + "specifically to demonstrate the quasi-experimental causal inference, optimization, and business-translation "
  + "skills this Vanguard role calls for. Say this plainly if asked — it is honest framing, not a trick, and it "
  + "mirrors exactly how the real project's own Q7 answer already owns the gap."
));
children.push(body(
  "这是在真实DDA挽留项目基础上做的技术展示（原始项目见《项目二DDA存款流失挽留.docx》）。STAR叙事本身、四种流失模式、"
  + "触发式干预设计，以及真实A/B test测出的30%相对流失下降，都是真实的。所有涉及RDD、客户价值分层DiD、DoubleML、"
  + "正式优化，以及业务影响量化的部分，都是之后用合成数据（内嵌已知真实效应）额外做的，专门用来展示这个Vanguard岗位"
  + "要求的准实验因果推断、优化和业务转化能力。被问到时就坦诚这样说——这是诚实的框定，不是套路，和原项目Q7里已经"
  + "承认的gap是同一个逻辑的延续。"
));

// ---------------------------------------------------------------------- STAR
children.push(h2("STAR — 更新版 Extended"));

children.push(label("Situation（English）"));
children.push(body("Same as the real project: no early-warning system for DDA churn, and blanket, undifferentiated retention outreach. The real A/B test validated a 30% relative churn reduction — but validation leaned on that outcome test alone, with no quasi-experimental analysis, no formal optimization behind the value cutoff, and no quantified business case beyond the headline percentage."));
children.push(label("Situation（中文）"));
children.push(body("和真实项目一样：DDA流失没有预警系统，挽留动作也是无差别的。真实A/B test验证了30%的相对流失下降——但验证只靠这一个结果检验，背后没有准实验分析，价值分层cutoff也没有正式优化支撑，除了这一个百分比之外也没有量化的业务案例。"));

children.push(label("Task（English）"));
children.push(body("On my own time, rebuild the analytical engine with the additional rigor this role specifically asks for: causal inference in situations where randomization isn't feasible (three different situations, three different designs), a formal optimization layer, and a translation of all of it into a quantified, confidence-tiered business recommendation — using synthetic data so I could validate methodology against a known ground truth."));
children.push(label("Task（中文）"));
children.push(body("利用业余时间重建这个分析引擎，补上这个岗位特别要求的严谨性：在三种不同、都无法随机化的场景下分别做因果推断，加上正式的优化层，并把这一切转化成一份量化的、按置信度分层的业务建议——用合成数据是为了能对照已知真实效应验证方法论本身对不对。"));

children.push(label("Action（English）"));
[
  "RDD on the 30%-withdrawal RM-outreach trigger (a deterministic, non-randomized rule) — McCrary-style manipulation check, rdrobust local-linear estimate with bias-corrected robust inference, bandwidth sensitivity sweep.",
  "Value-tier staggered DiD on the $100 DD-stop offer rollout — accounts are staggered into the offer by customer-value tier (balance, tenure, product count → a dollar-denominated account_value score) because RM capacity, not geography, is the actual rollout constraint. Parallel pre-trends check on the common pre-period window; naive static TWFE vs. a clean-control (stacked) estimator using only not-yet-treated tiers as controls; event-study plot showing a 3-month effect ramp.",
  "DoubleML (interactive regression model, XGBoost nuisance functions, cross-fitted, ATT-targeted) on the dormant-reactivation play, the one trigger with no RDD- or DiD-exploitable structure at all — because the flagging rule is itself a confound, both a naive comparison and a logistic-regression adjustment get the WRONG SIGN, and only the ML-adjusted estimate recovers the correct direction.",
  "Multiple-choice knapsack ILP (PuLP/CBC) replacing the informal 'top 50% by value' cutoff — maximizes net expected value protected subject to a budget constraint and a separate RM-capacity constraint, fed by all three causally-estimated effect sizes above (each carrying its own honestly-labeled confidence tier).",
  "A business-impact layer translating the optimizer's output into a per-10,000-scored-accounts dollar figure with an explicit scaling instruction (deliberately not a fabricated enterprise-wide total), a sensitivity check proving the one assumed rate in the value formula isn't load-bearing, and four prioritized, confidence-tiered recommendations.",
  "Every estimator graded against the true effect injected into the simulation, before ever trusting the method conceptually.",
].forEach(t => children.push(bullet(t)));
children.push(label("Action（中文）"));
[
  "对30%取款触发RM联系（一个确定性、非随机的规则）做RDD——McCrary式操纵检验、rdrobust局部线性估计+偏差修正稳健推断、bandwidth敏感性扫描。",
  "对$100停DD offer的上线做客户价值分层的分批DiD——账户按客户价值分层（余额、tenure、产品数量→一个美元化的account_value分数）被分批纳入这个offer，因为真正限制上线节奏的是RM产能而不是地区。在共同前置窗口做平行趋势检验，对比naive静态TWFE和只用尚未上线分层做对照组的clean-control（堆叠）估计量，event-study图显示3个月的效应爬坡。",
  "对dormant再激活这个动作做DoubleML（交互式回归模型，XGBoost作为nuisance函数，交叉拟合，以ATT为目标）——这是三个触发中唯一没有RDD或DiD可用结构的一个，因为打标规则本身就是混杂因素，naive对比和logistic回归调整都得出了错误的符号方向，只有ML调整后的估计恢复了正确方向。",
  "用PuLP/CBC实现的多选择背包整数规划，替代原来非正式的'前50%价值'规则——在预算约束和RM产能约束下最大化净预期保护价值，输入是上面三个因果估计出的效应大小（每个都带着自己诚实标注的置信度）。",
  "一个业务影响层，把优化器的输出转化为每万个评分账户的美元数字，并给出明确的放大说明（刻意不编造一个全行总数），同时用敏感性检验证明价值公式里唯一的假设比例不是决定性的，最后给出四条按优先级和置信度分层的行动建议。",
  "每个估计量在真正信任其方法论之前，都先对照模拟中注入的真实效应做了打分验证。",
].forEach(t => children.push(bullet(t)));

children.push(label("Result（English）"));
children.push(body("Real result stands: -30% relative churn from the actual A/B test. On top of that, the rebuild shows RDD recovering a -10.7pp effect (vs. a misleading -1.5pp naive comparison) within 1.3pp of the true simulated effect; the value-tier DiD's clean-control estimate at -3.7pp landing closer to the true -4.7pp than naive TWFE's -3.5pp; DoubleML correctly recovering the sign of the dormant effect (-6.5pp) where naive (+11.2pp) and logistic (+0.8pp) both got it backwards; and the optimization layer protecting 63% more net value than the heuristic at equal budget and RM capacity — worth +$116,211 per 10,000 scored accounts, translated into four prioritized, confidence-tiered recommendations for the business."));
children.push(label("Result（中文）"));
children.push(body("真实结果依然成立：真实A/B test测出-30%相对流失。在此基础上，重建版本显示RDD恢复出-10.7pp的效应（相比会误导人的-1.5pp naive对比），和模拟真实效应只差1.3pp；客户价值分层DiD的clean-control估计-3.7pp比naive TWFE的-3.5pp更接近真实的-4.7pp；DoubleML正确恢复了dormant效应的符号方向（-6.5pp），而naive（+11.2pp）和logistic（+0.8pp）方向都是反的；优化层在同样预算和RM产能下，比经验规则多保护63%的净价值——按每万个评分账户折算价值+$116,211，最终转化成四条按优先级和置信度分层的业务建议。"));

children.push(hr());

// ---------------------------------------------------------------------- Q&A
children.push(h2("技术追问 Q&A"));

qaBlock(1, "This is synthetic data — isn't that a problem? / 这是合成数据，这样合适吗？",
  "No, if framed honestly. Real account-level data with a designed quasi-experiment isn't something I could ever bring out of the bank, and it's also not publicly available anywhere, for privacy reasons. Building the data-generating process myself let me inject a KNOWN ground-truth effect, so I could validate that RDD, DiD, and DoubleML actually recover it before I'd trust any of them on a real decision. I'm upfront that this is a demonstration layered on a real project, not a claim that I ran these methods at my employer.",
  "如果坦诚说明就没问题。真实账户级数据、还带着设计好的准实验结构，这种数据我不可能从银行带出来，出于隐私原因这类数据在任何地方也不会公开。自己搭建数据生成过程，让我能内嵌一个已知的真实效应，这样才能验证RDD、DiD、DoubleML真的能恢复出这个效应，再去真正信任这些方法。我会坦诚说明这是在真实项目基础上做的展示，不是声称我在雇主那边真的跑过这些方法。"
).forEach(p => children.push(p));

qaBlock(2, "Walk me through the RDD identifying assumption. / RDD的识别假设是什么？",
  "The core assumption is that nothing else changes discontinuously at the 30% withdrawal cutoff except the RM outreach itself. Since withdrawal size is a real economic behavior — not something a customer can precisely dial to land just above or below 30% — accounts just below and just above the cutoff should be comparable in every way except treatment. I test this directly with a McCrary-style density check: if customers were gaming the cutoff, the density of the running variable would show a jump right at 30%. It didn't (p=0.151).",
  "核心假设是：在30%取款这个断点上，除了RM联系本身，没有别的东西同时发生跳跃。因为取款金额是真实的经济行为——客户没法精确操控让自己刚好卡在30%上下——所以断点左右两边的账户除了是否被联系，其他方面应该是可比的。我直接用McCrary式密度检验来验证这一点：如果客户在操纵这个断点，running variable的密度会在30%处出现跳跃。检验结果没有跳跃（p=0.151）。"
).forEach(p => children.push(p));

qaBlock(3, "How did you pick the bandwidth, and does the result depend on it? / bandwidth怎么选的，结果对它敏感吗？",
  "I used rdrobust's MSE-optimal bandwidth selector (Calonico-Cattaneo-Titiunik) rather than picking one by hand, and reported both the conventional and bias-corrected robust estimate — the robust one is what you should actually trust. I then swept bandwidths from 4 to 20 months as a sensitivity check: the estimate stayed stable between -9.4pp and -10.7pp across that whole range, so the result isn't an artifact of one bandwidth choice.",
  "我用的是rdrobust自带的MSE最优bandwidth选择方法（Calonico-Cattaneo-Titiunik），不是手工挑的，同时报告了conventional和偏差修正后的robust估计——真正该信的是robust那个。然后我把bandwidth从4扫到20个月做敏感性检验：整个区间内估计值都稳定在-9.4pp到-10.7pp之间，说明结果不是某一个bandwidth选择的巧合。"
).forEach(p => children.push(p));

qaBlock(4, "Why DiD for the DD-stop offer, and why stagger by customer value tier instead of region? / 为什么用DiD做停DD offer，为什么按客户价值分层而不是按地区分批？",
  "The offer rolled out in phases rather than everywhere at once — a real quasi-experiment, not a designed RCT. I stagger it by customer-value tier specifically because that's the more realistic mechanism at a bank like Vanguard: RM and ops bandwidth is genuinely scarce, so a phased rollout to the highest-value tier first, then the next, is exactly how a program like this would actually go out the door — much more so than an arbitrary region-by-region sequence. It also sharpens the pedagogy: value tier is plausibly correlated with baseline churn risk AND with treatment timing, which is exactly the confound structure that makes naive TWFE biased under staggered adoption (the Goodman-Bacon 2021 decomposition) — so this design isn't just more realistic, it's a cleaner demonstration of why the bias-correction step matters.",
  "这个offer是分阶段上线的，不是同时全行上线——是一个真实的准实验，不是设计好的随机实验。我特意按客户价值分层来分批，而不是按地区，因为这更接近Vanguard这类机构的真实上线逻辑：RM和运营的产能是真正稀缺的资源，所以先给最高价值分层上线、再逐层往下，这是这类项目实际会怎么推的方式——比一个随意的按地区顺序更合理。这个设计在教学上也更清晰：客户价值分层很可能同时和基线流失风险、以及处理时点都相关，这正是分批上线下naive TWFE产生偏差的混杂结构（Goodman-Bacon 2021的分解揭示了这一点）——所以这个设计不只是更贴近现实，也更干净地展示了为什么需要做偏差修正。"
).forEach(p => children.push(p));

qaBlock(5, "What's the 'clean-control' DiD estimator you used, concretely — is it Callaway-Sant'Anna? / 你用的'clean-control' DiD估计量具体是怎么做的？是Callaway-Sant'Anna吗？",
  "No — and I say that upfront rather than waiting to be caught. For each adoption tier, I compute a clean 2x2 difference-in-differences using ONLY the not-yet-treated tiers as the control group at that point in time — not-yet-treated units can't be contaminated by treatment yet, unlike already-treated tiers. I aggregate those tier-level ATTs, weighted by post-period sample size, into an overall estimate. This captures the SAME core intuition as Callaway-Sant'Anna (never let an already-treated unit serve as a control) but is a simplified, manually-implemented clean-control comparison — it doesn't have CS's full doubly-robust estimation or multiplier-bootstrap inference. I chose to build and present the simpler version specifically because I can fully explain and defend every step of it; if a production use case needed the extra robustness, I'd reach for the `did` / `csdid` package rather than re-derive it by hand.",
  "不是——而且我会主动这么说，而不是等着被问倒。对每个上线分层，我在处理发生的那个时点，只用当时'尚未处理'的分层作为对照组，做一个干净的2x2 DiD——尚未处理的单位在那个时点还不可能被处理污染，这一点不同于已经处理过的分层。我把这些分层级别的ATT按post-period样本量加权，汇总成一个整体估计。这抓住了和Callaway-Sant'Anna同样的核心思路（绝不让已处理单位充当对照组），但是一个简化的、手工实现的clean-control比较——它没有CS完整的doubly-robust估计或multiplier-bootstrap推断。我特意选择做并展示这个更简单的版本，是因为我能完整解释和辩护它的每一步；如果生产场景真的需要那种额外的稳健性，我会直接用`did`/`csdid`这类现成package，而不是自己手工重新推导。"
).forEach(p => children.push(p));

qaBlock(6, "How did you validate the parallel-trends assumption? / 平行趋势假设怎么验证的？",
  "I restricted to the common calendar window BEFORE any tier had gone live, then ran an F-test on the tier × calendar-month interaction — a significant interaction would mean tiers were already trending differently before treatment, which would break DiD's core assumption. It came back insignificant (p=0.951). I deliberately used the common pre-period window rather than each tier's full 'not yet treated' history, because comparing tiers with very different amounts of pre-period data can itself create a spurious 'differential trend' finding.",
  "我限定在所有分层都还没上线之前的共同日历窗口内，对'分层×日历月'交互项做F检验——如果交互项显著，就说明处理之前各分层已经在走不同的趋势，DiD的核心假设就不成立。检验结果不显著（p=0.951）。我特意用共同前置窗口而不是每个分层各自完整的'尚未处理'历史，因为拿前置数据量差异很大的分层互相比较，本身就可能制造出虚假的'趋势不同'的结论。"
).forEach(p => children.push(p));

qaBlock(7, "How did you build the account-value formula, and how do you defend the specific 15% number? / 账户价值公式怎么建的，那个15%具体怎么辩护？",
  "This is a formula I redesigned specifically after getting negative interview feedback on an earlier arbitrary weighted index (product_count*3 + tenure_months*0.05 + balance_tier*2 — weights with no defensible origin). The current version is account_value = balance * (1 + 15% * product_count): a dollar-denominated estimate of the relationship's value, where each additional product is assumed to add roughly 15% incremental value on top of the base balance (cross-sell revenue, stickiness, lower attrition risk). Two things make this defensible where the old one wasn't: first, it's in DOLLARS, not an arbitrary index, so every term has a real-world unit and interpretation. Second — and this is the answer to 'why 15% and not something else' — I ran a sensitivity check: recomputing the ranking at 10% and 20% instead of 15% gives a Spearman rank correlation above 0.999, and over 98% of the accounts that land in the top value quartile under 15% stay there under 10% or 20%. So the specific number affects who's on the margin, but not the overall prioritization the business actually acts on — that's the concrete, provable answer, instead of asserting the number is 'right'.",
  "这是我在因为之前一个任意加权指数（product_count*3 + tenure_months*0.05 + balance_tier*2——权重没有可辩护的来源）被面试官差评之后，专门重新设计的公式。现在的版本是account_value = balance × (1 + 15% × product_count)：一个美元化的客户关系价值估计，假设每多开一个产品，大致在基础余额上再带来15%的增量价值（交叉销售收入、粘性、更低的流失风险）。这个版本比旧版更能站住脚，原因有两个：第一，它是美元单位，不是一个任意的指数，每一项都有真实世界的单位和含义。第二——这也是'为什么是15%不是别的数'的答案——我做了敏感性检验：把15%换成10%或20%重新计算排序，Spearman秩相关系数都在0.999以上，而且在15%假设下进入价值前25%分位的账户，换成10%或20%之后有超过98%依然留在前25%分位。所以这个具体数字会影响谁刚好卡在边界上，但不会影响业务实际会采取行动的整体优先级排序——这是一个具体的、可以证明的答案，而不是断言这个数字'就是对的'。"
).forEach(p => children.push(p));

qaBlock(8, "Walk me through the optimization formulation. Why an ILP, not just ranking? / 优化怎么建模的？为什么要用整数规划而不是简单排序？",
  "It's a multiple-choice knapsack: each account can receive at most one of three interventions, subject to a total budget constraint AND a separate RM-capacity constraint (RM time, not dollars, is the actual bottleneck for the withdrawal play). A simple ranking works if there's exactly one resource constraint, but with two constraints binding different intervention types simultaneously, a formal ILP (I used PuLP with the CBC solver) finds the truly optimal allocation rather than an ad hoc approximation. The objective maximizes net expected value: predicted probability of that churn mode times the causally-estimated effect size times account_value (dollars at risk), minus intervention cost. At equal budget and RM capacity, the optimizer protects 63% more net value than the heuristic — and notably, it doesn't spend to the last dollar or the last RM contact; it stops once an account's marginal expected value turns negative, which is a form of capital discipline the flat heuristic doesn't have.",
  "这是一个多选择背包问题：每个账户最多接受三种干预中的一种，同时受总预算约束和一个单独的RM产能约束（RM时间而不是钱，才是取款干预真正的瓶颈）。如果只有一个资源约束，简单排序就够了，但这里有两个约束同时作用在不同干预类型上，用正式的整数规划（我用PuLP+CBC solver）才能找到真正最优的分配，而不是一个凑合的近似。目标函数是最大化净预期价值：预测的流失模式概率×因果估计出的效应大小×account_value（风险敞口金额），再减去干预成本。在同样预算和RM产能下，优化器比经验规则多保护63%的净价值——而且值得注意的是，它不会把预算或RM名额用到最后一分钱/一个名额，一旦某个账户的边际预期价值转负就会停止分配，这是一种经验规则没有的资金纪律。"
).forEach(p => children.push(p));

qaBlock(9, "Why DoubleML for the dormant play, and why target ATT instead of ATE? / 为什么dormant这个动作用DoubleML？为什么目标是ATT而不是ATE？",
  "Neither RDD nor DiD naturally applies here — dormant accounts get flagged by a threshold/branching rule (long dormancy streak, or a shorter streak combined with low engagement) and treated together, with no cutoff to exploit and no phased rollout. That flagging rule is itself the confound: the accounts most likely to get flagged are also the ones most likely to churn anyway — a naive before/after or treated-vs-untreated comparison mixes up 'the offer worked' with 'we specifically targeted the accounts already heading for the door,' a pattern called confounding by indication. DoubleML (the interactive regression model, with XGBoost as the nuisance-function learner and cross-fitting to avoid overfitting bias) adjusts for this by flexibly modeling both the treatment-assignment mechanism and the outcome mechanism given observed covariates, using a Neyman-orthogonal score so the final effect estimate is robust to small errors in either nuisance model. I target ATT, not ATE, because the true injected effect is concentrated specifically among the flagged accounts — the population-average effect is small and hard to estimate precisely, while the effect ON THE ACCOUNTS THAT ACTUALLY GET TREATED is the number that matters for deciding whether to keep running this exact play on exactly this population.",
  "RDD和DiD在这里都用不上——dormant账户是被一个阈值/分支规则打标的（较长的休眠时长，或者较短的休眠时长叠加低活跃度），然后被一起处理，没有断点可用，也没有分批上线。这个打标规则本身就是混杂因素：最容易被打标的账户，本来也是最容易流失的账户——一个naive的前后对比或者处理vs未处理对比，会把'这个offer起作用了'和'我们本来就专门挑了已经在流失路上的账户'这两件事混在一起，这种模式叫做confounding by indication（因适应症混杂）。DoubleML（交互式回归模型，用XGBoost作为nuisance函数的学习器，并做交叉拟合避免过拟合偏差）通过灵活建模处理分配机制和结果机制（都基于可观测协变量）来调整这一点，用的是Neyman正交得分，这样最终的效应估计对两个nuisance模型中任何一个的小误差都是稳健的。我用ATT而不是ATE，是因为注入的真实效应恰恰集中在被打标的那部分账户里——全体平均效应很小、很难精确估计，而'在实际会被处理的这批账户上'的效应，才是决定要不要继续对这批人群跑这个动作的关键数字。"
).forEach(p => children.push(p));

qaBlock(10, "How do you know DoubleML is actually working here, rather than just being a fancier black box? / 你怎么知道DoubleML真的起作用了，而不只是一个更花哨的黑箱？",
  "Because I can show it against the two simpler baselines and a known ground truth, side by side. The naive difference comes out +11.2pp — the WRONG SIGN, implying the play increases bad outcomes, purely because of confounding by indication. A logistic-regression adjustment (linear, additive controls) barely moves it, +0.8pp — still the wrong sign, because the true confounding relationship is a threshold/branching rule that a linear-additive model can't represent, but a tree-based model can. Only DoubleML recovers the correct sign, -6.5pp (95% CI [-8.6, -4.5]), against a true injected ATT of -9.8pp — closer to the truth than either baseline, and in the right direction, which the other two aren't. That side-by-side comparison, not just DoubleML's estimate in isolation, is the actual evidence.",
  "因为我能把它和两个更简单的baseline以及已知真值放在一起对比。naive对比算出来是+11.2pp——符号方向是错的，意味着这个动作反而增加了坏结果，纯粹是因为confounding by indication。logistic回归调整（线性、加性控制变量）几乎没怎么改变结果，+0.8pp——符号方向依然是错的，因为真实的混杂关系是一个阈值/分支规则，线性加性模型没法表达，但树模型可以。只有DoubleML恢复了正确的符号方向，-6.5pp（95%置信区间[-8.6, -4.5]），对照注入的真实ATT -9.8pp——比另外两个baseline都更接近真值，而且方向是对的，另外两个都不是。这个并排对比本身，而不是孤立地看DoubleML的估计值，才是真正的证据。"
).forEach(p => children.push(p));

qaBlock(11, "Business impact: why report per-10,000-accounts instead of one big enterprise-wide dollar number? / 业务影响为什么按每万个账户折算，而不是给出一个全行的大数字？",
  "Because I don't know the real book size, and inventing one to produce a bigger, more impressive-sounding total would be exactly the kind of overclaiming I've been careful to avoid everywhere else in this project. This project's data is a sized demo (a 10,000-account scored test set), not the institution's actual book. So I report the incremental value — +$116,211, +63.2% — per 10,000 scored accounts, with an explicit instruction: multiply by (your real scored-account count / 10,000) to get your actual number. The mechanism behind the gain is what matters and what I'd actually defend: same budget, same RM capacity, better targeting — and that mechanism scales linearly with book size, unlike a one-time fixed-cost project, which is the honest and still-compelling way to make the business case without a number I can't stand behind.",
  "因为我不知道真实的账户规模，编一个数字出来让总数看起来更大、更唬人，恰恰是我在这个项目其他地方一直刻意避免的那种过度声称。这个项目的数据是一个按规模缩小的demo（一万个账户的评分测试集），不是机构真实的账本。所以我把增量价值——+$116,211，+63.2%——按每万个评分账户来报告，并明确说明：乘以（你真实的评分账户数/10,000）就能得到你的实际数字。真正重要、也是我真正能站住脚辩护的，是这个提升背后的机制：同样的预算、同样的RM产能，更好的targeting——而这个机制会随账本规模线性放大，不像一次性固定成本的项目，这是一个诚实、同时依然有说服力的方式去讲这个业务案例，而不是用一个我自己都无法完全站得住的数字。"
).forEach(p => children.push(p));

qaBlock(12, "How would this extend toward a real production deployment? / 真要落地生产环境，还需要做什么？",
  "Same gap I named in the original project's Q7: today's validation is outcomes-based (plus, here, grading against a known synthetic truth). A real deployment needs independent model-risk validation per SR 11-7 — documented intended use, assumptions, and limitations; a conceptual-soundness review by a separate validation team; an ongoing monitoring/drift plan. Specifically for the dormant play, I'd flag it for its own workstream: unlike RDD's no-manipulation check or DiD's pre-trends check, DoubleML's unconfoundedness assumption isn't directly testable from the data, so before scaling budget against that -6.5pp number, I'd want a genuine randomized pilot on a few hundred flagged accounts to actually validate it, not just estimate it more cleverly.",
  "和原项目Q7里点出的gap是同一个：今天的验证是基于结果的（这里还额外对照了已知的合成真值）。真正落地生产环境，需要按SR 11-7做独立模型风险验证——记录intended use、假设、局限；由独立验证团队做conceptual-soundness审查；定义持续监控/drift计划。specifically针对dormant这个动作，我会单独把它标出来作为一个独立的工作项：不同于RDD的操纵检验或DiD的前置趋势检验，DoubleML的unconfoundedness假设没法直接从数据里检验，所以在拿-6.5pp这个数字去扩大预算投入之前，我会想在几百个被打标的账户上做一次真正的随机化小规模试验，去真正验证它，而不只是更聪明地估计它。"
).forEach(p => children.push(p));

qaBlock(13, "What would you do differently next time? / 下次你会怎么做得不一样？",
  "I'd design the dormant-play experiment from day one instead of leaving it to a selection-on-observables workaround, and I'd build the panel data richer (full month-by-month account trajectories rather than event-level samples) so the same dataset could support all three causal questions together instead of three separate analytic samples — closer to how a real production data pipeline would be structured. I'd also reach for the full `csdid`/`did` package implementation of Callaway-Sant'Anna if the staggered-DiD result needed to hold up under heavier scrutiny than the simplified clean-control version I built by hand.",
  "我会从一开始就把dormant这个动作的实验设计好，而不是靠一个selection-on-observables的变通方法去补救，也会把面板数据做得更完整（完整的逐月账户轨迹，而不是事件级抽样样本），这样同一份数据集就能同时支撑三个因果问题，而不是三个分开的分析样本——这样更接近真实生产数据管道该有的样子。如果分批DiD的结果需要经受比我手工实现的简化clean-control版本更严格的审视，我也会直接用完整的`csdid`/`did` package实现Callaway-Sant'Anna。"
).forEach(p => children.push(p));

qaBlock(14, "You said if this went to production you'd add unit tests, a config file, data validation and logging, full seeding for reproducibility, and a service layer — did you actually build those? / 你说过如果要往生产走会加单元测试、配置文件、数据校验和日志、完全seed保证可复现、再包一层服务接口——这些你真做了吗？",
  "Yes — all six. config.py centralizes every constant (paths, SEED, model hyperparameters, budget, RM capacity, the 15% product-value-uplift rate) that used to be hardcoded separately in each script. validation.py adds fail-loud-and-early checks, and it caught a real bug while I was building it: treated_rm_contact was being derived from the UNROUNDED withdrawal_pct while the stored running variable was rounded to 2 decimals, so a handful of boundary rows (e.g. raw 29.996) could round to exactly the cutoff and disagree with their own treatment flag — not a sharp RDD anymore for those rows. I fixed it by rounding before deriving treatment. logging_setup.py adds structured console+file logging alongside — not replacing — each script's narrated print() output, since that narration is genuinely useful for a live walkthrough. For reproducibility, I found and fixed a subtler issue: numpy has two separate RNG systems, the modern Generator API (which I'd seeded) and a legacy global RandomState that scikit-learn's KFold and, transitively, DoubleML's cross-fitting fold-splitting draw from — which had never been seeded. That's what was actually causing the DoubleML estimate to drift slightly run to run, not 'DoubleML just has irreducible randomness.' config.seed_everything() now seeds both, and I pinned XGBoost to n_jobs=1 to remove multi-threaded floating-point nondeterminism too. I verified this by running the full 8-script pipeline twice independently and diffing data/, output/, and figures/ byte-for-byte — zero differences. I added a pytest suite (38+ tests) covering the config formula, every validation check's pass/fail path including the boundary bug above, the data generators' invariants, the optimizer's ILP constraints, and the service endpoints — which also meant refactoring 06_optimization.py, which had NO __main__ guard at all (running the entire optimization as an import side effect), into an importable run_optimization() function. And I wrapped the batch outputs in a FastAPI service (health check, per-account score lookup, the recommendation list, and a synchronous /optimize endpoint that re-solves the ILP under a caller-supplied budget) — deliberately not a live-retraining service, since the heavy model-fitting stays a scheduled batch job and only the cheap ILP re-solve needs to be synchronous.",
  "全部六项都做了。config.py把之前散落在各脚本里的常量（路径、SEED、模型超参数、预算、RM产能、15%的产品价值加成率）集中到一个地方。validation.py加了'尽早报错'的校验，而且在写它的过程中真的抓到一个bug：treated_rm_contact是从没有四舍五入的withdrawal_pct算出来的，但存盘的running variable四舍五入到了2位小数，导致极少数边界行（比如原始值29.996）四舍五入后正好落在cutoff上，和自己的treatment标记不一致——对这些行来说已经不是严格的sharp RDD了。修复方式是先四舍五入再判定treatment。logging_setup.py加了结构化的console+文件日志，但没有替换掉每个脚本本身的print()叙事——因为那些叙事在真人讲解时是有实际用处的。可复现性方面我发现并修复了一个更隐蔽的问题：numpy有两套随机数系统，我之前只seed了新的Generator API，而scikit-learn的KFold、以及DoubleML内部cross-fitting做fold划分时用的，是从来没被seed过的旧版全局RandomState——这才是DoubleML估计结果每次跑会有轻微漂移的真正原因，不是'DoubleML本身就有没法消除的随机性'。现在config.seed_everything()会同时锁定这两套系统，另外把XGBoost的n_jobs固定成1，去掉多线程浮点数求和带来的不确定性。我验证的方式是把完整的8步pipeline独立跑两次，对data/、output/、figures/三个目录做字节级diff——完全没有差异。我加了一套pytest测试（38+条），覆盖config公式、每条校验规则的通过/失败路径（包括上面那个边界bug）、数据生成器的不变量、优化器ILP的约束、以及服务端点——这也顺带逼着我把06_optimization.py重构了一遍，它之前完全没有__main__保护，只要import这个文件就会把整个优化流程当副作用跑一遍，我把它拆成了一个可以被单独调用的run_optimization()函数。最后把批处理的输出包了一层FastAPI服务（健康检查、按账户查分数、建议列表、以及一个允许调用方传入不同预算实时重新求解ILP的/optimize端点）——刻意没做成'每次请求都重新训模型'的服务，因为重的模型训练留在定时批处理里，只有轻量的ILP重新求解需要做成同步的。"
).forEach(p => children.push(p));

qaBlock(15, "If you were designing this project from scratch, would you build it forward-looking (prospective, with randomization) instead of retrofitting causal inference onto historical data? / 如果重新设计这个项目，是提前设计好实验，还是通过看历史数据做因果推断？",
  "These aren't competing choices for the same time period — you can't retroactively insert randomization into something that already happened, and a 'forward-looking' design can only be demonstrated as a written plan, not as results. So the honest framing is sequential: what I built is the retrospective half, applied to triggers that were already running deterministically; what follows is how I'd redesign each one prospectively if I were starting today. For the withdrawal trigger, I'd keep the 30% rule operationally, but layer a small randomized holdout on top of it — e.g. 90% of flagged accounts get RM contact as normal, 10% get a randomly-assigned delayed-contact holdout (delayed, not withheld entirely, to limit the cost of intentionally not helping a flagged high-value account). That gives a clean two-group comparison instead of needing RDD, and as a bonus lets me test whether 30% is the right cutoff, not just whether the trigger works. For the DD-stop offer, I'd keep the tier-based prioritization (RM capacity really is scarce), but randomize which accounts within each wave get treated now versus a wave later — a stepped-wedge design, common in health-services research when a resource-constrained rollout still needs a randomized comparison; that removes the need to validate parallel pre-trends at all, since timing itself is randomized by design. For the dormant play, I'd randomize flagged accounts directly into treatment versus a true control at the point of flagging — exactly the randomized pilot Q8 above already recommends. Across all three, I'd nail down a power/sample-size calculation using the historical baseline rate before launch (the real project's actual A/B test needed ~20k per arm for 83% power against a 0.8% baseline churn — the same math applies here), a pre-registered primary metric, and sign-off from risk/compliance on withholding a small slice of already-identified at-risk, high-value accounts, including monitoring the holdout for any disparate impact across protected groups.",
  "这两者不是同一个时间段上的竞争选项——你没法把随机化倒着插进已经发生过的事情里，'面向未来的设计'也只能停留在一份方案层面去展示，没法拿出真实跑出来的结果。所以诚实的框架是先后关系：我现在做出来的这部分，是对已经在确定性运行的触发规则做的retrospective分析；接下来是如果今天重新开始，我会怎么把这三个触发规则分别改成提前设计好的。取款触发这边，我会保留30%这条业务规则不变，但在此基础上叠加一个小比例的随机holdout——比如90%被标记的账户正常走RM联系，10%随机分到一个延迟联系的holdout组（是延迟，不是完全不做，这样能把'故意不帮一个已识别的高价值风险账户'这个代价控制到最小）。这样能得到一个干净的两组对比，不需要再用RDD；而且顺便还能测出30%这个cutoff本身对不对，而不只是测'这条规则有没有用'。DD停用offer这边，我会保留按价值分层优先的顺序（RM产能确实稀缺），但把'这一波具体给哪些账户上线'这一步随机化——也就是stepped-wedge设计，在资源有限、没法一次性全量上线、但仍然想要随机对照的场景下，卫生服务研究领域很常用这套设计；这样彻底不需要再去验证平行趋势假设，因为处理时点本身就是设计好的随机分配。dormant play这边，我会在打标那一刻，直接把被标记的账户随机分成treatment和真正的control两组——这正是上面Q8已经建议的randomized pilot的具体落地方式。三个规则重新设计之前都要先定好：用历史基线流失率算好样本量/检验力（真实项目那次A/B test在基线churn 0.8%的情况下，每组需要约2万个账户才能有83%的power，这里同样的算法适用）、预先注册好主要指标，以及拿到风控/合规对'故意不干预一部分已识别的高风险高价值账户'这件事的审批，包括监控这个holdout会不会在受保护群体上产生不成比例的影响。"
).forEach(p => children.push(p));

qaBlock(16, "If you add a randomized holdout, do you still need RDD/DiD/DoubleML at all? / 如果加了随机化holdout，是不是就不需要RDD/DiD/DoubleML了？",
  "For the average causal effect of that specific trigger — yes, once it's genuinely randomized, a simple two-group comparison (the same two-proportion z-test the real A/B test used) is a strictly better answer than RDD/DiD/DoubleML, because it doesn't rest on any untestable identifying assumption. Those three methods exist specifically as substitutes for a missing randomization — once randomization is in place, they're not needed for that question. But that doesn't make causal inference as a discipline unnecessary — it shifts which tools matter. A clean RCT still leaves real problems: heterogeneous treatment effects (the optimizer needs to know if the effect is bigger for some account segments than others, not just the average — that still requires causal ML, e.g. causal forests / uplift modeling, applied to the randomized data); non-compliance (if RM capacity means not every 'treatment' account actually gets called, or a holdout account gets contacted anyway through a different channel, you need instrumental-variable-style intent-to-treat vs. treatment-on-treated analysis); and variance reduction (CUPED-style covariate adjustment using pre-period data, to reach significance with a smaller or shorter holdout). Mature experimentation-first companies still run large causal inference teams for exactly these reasons, even with A/B testing as their default culture.",
  "对于某个具体触发规则的平均因果效应而言——是的，一旦真的随机化了，一个最简单的两组对比（跟真实项目那次A/B test用的两比例z检验一样）就是比RDD/DiD/DoubleML更好的答案，因为它不依赖任何没法被直接验证的识别假设。这三个方法存在的意义，本来就是在没有随机化时的替代方案——随机化到位之后，对这个具体问题就不再需要它们了。但这不代表'因果推断'这整个学科就不需要了——只是需要的工具变了。一个干净的RCT仍然留下真实的问题：异质效应（优化器需要知道效应在不同客群里是不是不一样，不只是一个平均数——这仍然需要因果机器学习，比如causal forest/uplift建模，应用在随机化之后的数据上）；合规性问题（如果RM产能有限导致不是每个'treatment'账户真的被联系到，或者holdout账户被别的渠道意外联系了，就需要用工具变量法去区分intent-to-treat和treatment-on-treated）；以及方差缩减（用CUPED这类方法，靠前置期协变量调整，让更小或更短的holdout也能测出显著性）。即使是把A/B test当默认文化的成熟公司，也仍然会为了这几个原因，维持一支规模不小的因果推断团队。"
).forEach(p => children.push(p));

children.push(hr());

// ---------------------------------------------------------------------- QUICK REFERENCE
children.push(h2("速记 Quick Reference"));

const rows = [
  ["Outcome window (all 4 datasets)", "60 days / ~2 months -- deliberately matched to the real project's actual 2-month A/B test window (see Q6 in the original project's Q&A), not an arbitrary 1-month label"],
  ["RDD cutoff / running variable", "30% of balance withdrawn in a month"],
  ["RDD naive vs. robust estimate", "-1.5pp (biased) vs. -10.7pp [95% CI -14.8, -6.6], p<0.001"],
  ["RDD manipulation check", "McCrary-style, p = 0.151 (pass) -- guards against ANY unexplained density bunching at 30%, not just intentional gaming (customers don't know the internal threshold exists)"],
  ["RDD bandwidth sensitivity", "-9.4pp to -10.7pp across h = 4 to 20 (stable)"],
  ["DiD rollout structure", "By customer-value tier (RM capacity, not geography): top 25% at month 8, next 25% at month 14, next 25% at month 20, bottom 25% never in-window"],
  ["DiD parallel pre-trends check", "F-test on common pre-period, p = 0.951 (pass)"],
  ["DiD naive TWFE vs. clean-control", "-3.5pp vs. -3.7pp (true simulated effect: -4.7pp)"],
  ["DiD effect ramp", "~3 months to reach steady state"],
  ["Account-value formula", "account_value = balance × (1 + 15% × product_count); ranking robust to 10%/20% alt. rates (Spearman > 0.999, 98%+ top-quartile overlap)"],
  ["Dormant play: naive vs. logistic vs. DoubleML", "+11.2pp (wrong sign) vs. +0.8pp (wrong sign) vs. -6.5pp [95% CI -8.6, -4.5] (correct sign, true ATT: -9.8pp)"],
  ["Optimization result", "+63.2% net value protected vs. heuristic, equal budget & RM capacity"],
  ["Optimization RM capacity used", "297 / 400 contacts (optimizer stops at negative marginal value, not at capacity)"],
  ["Business impact (headline)", "+$116,211 net value per 10,000 scored accounts (+63.2%) — scale by (your accounts / 10,000)"],
  ["Real project result (unchanged)", "-30% relative churn, randomized A/B test"],
  ["Production-readiness additions", "config.py, validation.py (caught a real sharp-RDD boundary bug), logging_setup.py, full RNG seeding (fixed DoubleML's unseeded legacy-RandomState drift), 38+ pytest tests, FastAPI service.py — two independent full pipeline runs diff byte-identical"],
  ["Prospective redesign (Q15/Q16)", "Withdrawal trigger -> small randomized delayed-contact holdout; DD-offer rollout -> stepped-wedge (randomize timing within each value-tier wave); dormant play -> randomize at point of flagging. Once randomized, a simple two-group comparison replaces RDD/DiD/DoubleML for that trigger's ATE -- but causal ML (heterogeneous effects), IV (non-compliance), and CUPED (variance reduction) remain relevant on top of randomized data."],
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
