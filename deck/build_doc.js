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
      text: "DDA 挽留决策引擎重建：RDD + 分批 DiD + 预算优化（Vanguard 技术展示 / Technical Demo）",
      italics: true, color: GRAY, size: 22,
    })],
  }),
);

// ---------------------------------------------------------------------- POSITIONING
children.push(h2("定位说明 / Positioning"));
children.push(body(
  "This is a technical demonstration built on top of the real DDA retention project (see 项目二DDA存款流失挽留.docx). "
  + "The STAR narrative, the four churn modes, the trigger design, and the 30% relative churn reduction from the real "
  + "A/B test are all real. Everything involving RDD, staggered DiD, and formal optimization was built afterward, on "
  + "synthetic data with a known injected ground truth, specifically to demonstrate the quasi-experimental causal "
  + "inference and optimization skills this Vanguard role calls for. Say this plainly if asked — it is honest framing, "
  + "not a trick, and it mirrors exactly how the real project's own Q7 answer already owns the gap."
));
children.push(body(
  "这是在真实DDA挽留项目基础上做的技术展示（原始项目见《项目二DDA存款流失挽留.docx》）。STAR叙事本身、四种流失模式、"
  + "触发式干预设计，以及真实A/B test测出的30%相对流失下降，都是真实的。所有涉及RDD、分批DiD、正式优化的部分，都是"
  + "之后用合成数据（内嵌已知真实效应）额外做的，专门用来展示这个Vanguard岗位要求的准实验因果推断和优化能力。被问到时"
  + "就坦诚这样说——这是诚实的框定，不是套路，和原项目Q7里已经承认的gap是同一个逻辑的延续。"
));

// ---------------------------------------------------------------------- STAR
children.push(h2("STAR — 更新版 Extended"));

children.push(label("Situation（English）"));
children.push(body("Same as the real project: no early-warning system for DDA churn, and blanket, undifferentiated retention outreach. The real A/B test validated a 30% relative churn reduction — but validation leaned on that outcome test alone, with no quasi-experimental analysis and no formal optimization behind the value_score cutoff."));
children.push(label("Situation（中文）"));
children.push(body("和真实项目一样：DDA流失没有预警系统，挽留动作也是无差别的。真实A/B test验证了30%的相对流失下降——但验证只靠这一个结果检验，背后没有准实验分析，value_score cutoff也没有正式优化支撑。"));

children.push(label("Task（English）"));
children.push(body("On my own time, rebuild the analytical engine with the additional rigor this role specifically asks for: causal inference in situations where randomization isn't feasible, and a formal optimization layer, using synthetic data so I could validate methodology against a known ground truth."));
children.push(label("Task（中文）"));
children.push(body("利用业余时间重建这个分析引擎，补上这个岗位特别要求的严谨性：在无法随机化的场景下做因果推断，加上正式的优化层，用合成数据是为了能对照已知真实效应验证方法论本身对不对。"));

children.push(label("Action（English）"));
[
  "RDD on the 30%-withdrawal RM-outreach trigger (a deterministic, non-randomized rule) — McCrary-style manipulation check, rdrobust local-linear estimate with bias-corrected robust inference, bandwidth sensitivity sweep.",
  "Staggered-adoption DiD on the region-by-region $100 DD-stop offer rollout — parallel pre-trends check on the common pre-period window, naive static TWFE vs. a Callaway-Sant'Anna-style estimator using only never-treated regions as controls, event-study plot showing a 3-month effect ramp.",
  "Multiple-choice knapsack ILP (PuLP/CBC) replacing the informal 'top 50% by value_score' cutoff — maximizes net expected value protected subject to a budget constraint and a separate RM-capacity constraint, with each account getting at most one intervention.",
  "Every estimator graded against the true effect injected into the simulation, before ever trusting the method conceptually.",
].forEach(t => children.push(bullet(t)));
children.push(label("Action（中文）"));
[
  "对30%取款触发RM联系（一个确定性、非随机的规则）做RDD——McCrary式操纵检验、rdrobust局部线性估计+偏差修正稳健推断、bandwidth敏感性扫描。",
  "对按地区分批上线的$100停DD offer做分批DiD——在共同前置窗口做平行趋势检验，对比naive静态TWFE和只用从未上线地区做对照组的Callaway-Sant'Anna式估计量，event-study图显示3个月的效应爬坡。",
  "用PuLP/CBC实现的多选择背包整数规划，替代原来非正式的'前50% value_score'规则——在预算约束和RM产能约束下最大化净预期保护价值，每个账户最多分配一种干预。",
  "每个估计量在真正信任其方法论之前，都先对照模拟中注入的真实效应做了打分验证。",
].forEach(t => children.push(bullet(t)));

children.push(label("Result（English）"));
children.push(body("Real result stands: -30% relative churn from the actual A/B test. On top of that, the rebuild shows RDD recovering a -10.7pp effect (vs. a misleading -1.5pp naive comparison) within 1.3pp of the true simulated effect; DiD's Callaway-Sant'Anna-style estimate at -7.7pp landing closer to the true -6.4pp than naive TWFE's -8.5pp; and the optimization layer protecting ~497% more net value than the heuristic at equal budget and RM capacity."));
children.push(label("Result（中文）"));
children.push(body("真实结果依然成立：真实A/B test测出-30%相对流失。在此基础上，重建版本显示RDD恢复出-10.7pp的效应（相比会误导人的-1.5pp naive对比），和模拟真实效应只差1.3pp；DiD的Callaway-Sant'Anna式估计-7.7pp比naive TWFE的-8.5pp更接近真实的-6.4pp；优化层在同样预算和RM产能下，比经验规则多保护约497%的净价值。"));

children.push(hr());

// ---------------------------------------------------------------------- Q&A
children.push(h2("技术追问 Q&A"));

qaBlock(1, "This is synthetic data — isn't that a problem? / 这是合成数据，这样合适吗？",
  "No, if framed honestly. Real account-level data with a designed quasi-experiment isn't something I could ever bring out of the bank, and it's also not publicly available anywhere, for privacy reasons. Building the data-generating process myself let me inject a KNOWN ground-truth effect, so I could validate that RDD and DiD actually recover it before I'd trust either method on a real decision. I'm upfront that this is a demonstration layered on a real project, not a claim that I ran RDD/DiD at my employer.",
  "如果坦诚说明就没问题。真实账户级数据、还带着设计好的准实验结构，这种数据我不可能从银行带出来，出于隐私原因这类数据在任何地方也不会公开。自己搭建数据生成过程，让我能内嵌一个已知的真实效应，这样才能验证RDD和DiD真的能恢复出这个效应，再去真正信任这两个方法。我会坦诚说明这是在真实项目基础上做的展示，不是声称我在雇主那边真的跑过RDD/DiD。"
).forEach(p => children.push(p));

qaBlock(2, "Walk me through the RDD identifying assumption. / RDD的识别假设是什么？",
  "The core assumption is that nothing else changes discontinuously at the 30% withdrawal cutoff except the RM outreach itself. Since withdrawal size is a real economic behavior — not something a customer can precisely dial to land just above or below 30% — accounts just below and just above the cutoff should be comparable in every way except treatment. I test this directly with a McCrary-style density check: if customers were gaming the cutoff, the density of the running variable would show a jump right at 30%. It didn't (p=0.151).",
  "核心假设是：在30%取款这个断点上，除了RM联系本身，没有别的东西同时发生跳跃。因为取款金额是真实的经济行为——客户没法精确操控让自己刚好卡在30%上下——所以断点左右两边的账户除了是否被联系，其他方面应该是可比的。我直接用McCrary式密度检验来验证这一点：如果客户在操纵这个断点，running variable的密度会在30%处出现跳跃。检验结果没有跳跃（p=0.151）。"
).forEach(p => children.push(p));

qaBlock(3, "How did you pick the bandwidth, and does the result depend on it? / bandwidth怎么选的，结果对它敏感吗？",
  "I used rdrobust's MSE-optimal bandwidth selector (Calonico-Cattaneo-Titiunik) rather than picking one by hand, and reported both the conventional and bias-corrected robust estimate — the robust one is what you should actually trust. I then swept bandwidths from 4 to 20 months as a sensitivity check: the estimate stayed stable between -9.4pp and -10.7pp across that whole range, so the result isn't an artifact of one bandwidth choice.",
  "我用的是rdrobust自带的MSE最优bandwidth选择方法（Calonico-Cattaneo-Titiunik），不是手工挑的，同时报告了conventional和偏差修正后的robust估计——真正该信的是robust那个。然后我把bandwidth从4扫到20个月做敏感性检验：整个区间内估计值都稳定在-9.4pp到-10.7pp之间，说明结果不是某一个bandwidth选择的巧合。"
).forEach(p => children.push(p));

qaBlock(4, "Why DiD for the DD-stop offer, and what's special about staggered rollout? / 为什么用DiD做停DD offer，分批上线有什么特殊之处？",
  "The offer rolled out region-by-region at different times rather than everywhere at once — a real quasi-experiment, not a designed RCT. Staggered timing is exactly where the standard two-way-fixed-effects DiD regression can be biased: it implicitly uses already-treated cohorts as part of the comparison trend for later-treated cohorts (the Goodman-Bacon 2021 decomposition), and that bias shows up specifically when the effect isn't flat over time. Here the offer's effect genuinely ramps in over about 3 months, so I don't assume naive TWFE is safe — I check.",
  "这个offer是分地区、分批次上线的，不是同时全行上线——是一个真实的准实验，不是设计好的随机实验。分批上线正是标准双向固定效应（TWFE）DiD回归容易出偏差的场景：它会隐性地把已经上线的队列当作后上线队列的对照趋势的一部分（Goodman-Bacon 2021的分解揭示了这一点），这个偏差在效应不是随时间恒定时尤其明显。这里offer的效应确实是大约3个月才爬坡到位的，所以我不会假设naive TWFE没问题——我会去检验。"
).forEach(p => children.push(p));

qaBlock(5, "What's the Callaway-Sant'Anna-style estimator you used, concretely? / 你用的Callaway-Sant'Anna式估计量具体是怎么做的？",
  "For each adoption cohort, I compute a clean 2x2 difference-in-differences using ONLY the never-treated regions as the control group — never-treated regions can't be contaminated by treatment at any horizon, unlike other treated cohorts. I aggregate those cohort-level ATTs, weighted by post-period sample size, into an overall estimate. It's a simplified, manually-implemented version of the Callaway-Sant'Anna logic, not the full package — but the core fix (never let an already-treated unit serve as a control) is the same.",
  "对每个上线队列，我只用从未上线的地区作为对照组，做一个干净的2x2 DiD——从未上线的地区在任何时间跨度上都不会被处理污染，这一点不同于其他已上线的队列。我把这些队列级别的ATT按post-period样本量加权，汇总成一个整体估计。这是Callaway-Sant'Anna思路的简化版、手工实现，不是完整的package——但核心修正（绝不让已处理单位充当对照组）是一致的。"
).forEach(p => children.push(p));

qaBlock(6, "How did you validate the parallel-trends assumption? / 平行趋势假设怎么验证的？",
  "I restricted to the common calendar window BEFORE any cohort had gone live, then ran an F-test on the cohort × calendar-month interaction — a significant interaction would mean cohorts were already trending differently before treatment, which would break DiD's core assumption. It came back insignificant (p=0.765). I deliberately used the common pre-period window rather than each cohort's full 'not yet treated' history, because comparing cohorts with very different amounts of pre-period data can itself create a spurious 'differential trend' finding.",
  "我限定在所有队列都还没上线之前的共同日历窗口内，对'队列×日历月'交互项做F检验——如果交互项显著，就说明处理之前各队列已经在走不同的趋势，DiD的核心假设就不成立。检验结果不显著（p=0.765）。我特意用共同前置窗口而不是每个队列各自完整的'尚未处理'历史，因为拿前置数据量差异很大的队列互相比较，本身就可能制造出虚假的'趋势不同'的结论。"
).forEach(p => children.push(p));

qaBlock(7, "Walk me through the optimization formulation. Why an ILP, not just ranking? / 优化怎么建模的？为什么要用整数规划而不是简单排序？",
  "It's a multiple-choice knapsack: each account can receive at most one of three interventions, subject to a total budget constraint AND a separate RM-capacity constraint (RM time, not dollars, is the actual bottleneck for the withdrawal play). A simple ranking works if there's exactly one resource constraint, but with two constraints binding different intervention types simultaneously, a formal ILP (I used PuLP with the CBC solver) finds the truly optimal allocation rather than an ad hoc approximation. The objective maximizes net expected value: predicted probability of that churn mode times the causally-estimated effect size times dollars at risk, minus intervention cost.",
  "这是一个多选择背包问题：每个账户最多接受三种干预中的一种，同时受总预算约束和一个单独的RM产能约束（RM时间而不是钱，才是取款干预真正的瓶颈）。如果只有一个资源约束，简单排序就够了，但这里有两个约束同时作用在不同干预类型上，用正式的整数规划（我用PuLP+CBC solver）才能找到真正最优的分配，而不是一个凑合的近似。目标函数是最大化净预期价值：预测的流失模式概率×因果估计出的效应大小×风险敞口金额，再减去干预成本。"
).forEach(p => children.push(p));

qaBlock(8, "Why is the dormant-mode effect just 'assumed'? Isn't that a hole in the story? / 为什么dormant模式的效应只是'假设'？这不是个漏洞吗？",
  "It's an honest gap, not a hole I'm hiding. Neither RDD nor DiD naturally applies to the dormant-reactivation play in this dataset, so I didn't force a causal estimate I couldn't defend — I flagged it explicitly in the optimizer's inputs as ASSUMED and called for a future A/B test before scaling spend against it. I'd rather show I know the difference between a validated number and an assumed one than paper over it with a fabricated design.",
  "这是一个诚实承认的gap，不是藏起来的漏洞。RDD和DiD在这个数据里都没法自然地套用到dormant再激活这个动作上，所以我没有硬凑一个自己都无法辩护的因果估计——我在优化器的输入里明确标注它是ASSUMED，并且建议在扩大这块投入之前先做A/B test。比起用一个编造的设计掩盖过去，我更愿意展示自己清楚知道哪个数字是验证过的、哪个只是假设。"
).forEach(p => children.push(p));

qaBlock(9, "How would this extend toward a real production deployment? / 真要落地生产环境，还需要做什么？",
  "Same gap I named in the original project's Q7: today's validation is outcomes-based (plus, here, grading against a known synthetic truth). A real deployment needs independent model-risk validation per SR 11-7 — documented intended use, assumptions, and limitations; a conceptual-soundness review by a separate validation team; an ongoing monitoring/drift plan; and a real experiment (not an assumption) behind the dormant play before scaling spend on it.",
  "和原项目Q7里点出的gap是同一个：今天的验证是基于结果的（这里还额外对照了已知的合成真值）。真正落地生产环境，需要按SR 11-7做独立模型风险验证——记录intended use、假设、局限；由独立验证团队做conceptual-soundness审查；定义持续监控/drift计划；在扩大dormant这块投入之前，用真实实验而不是假设去支撑它。"
).forEach(p => children.push(p));

qaBlock(10, "What would you do differently next time? / 下次你会怎么做得不一样？",
  "I'd design the dormant-mode experiment from day one instead of leaving it as a gap, and I'd build the panel data richer (full month-by-month account trajectories rather than event-level samples) so the same dataset could support all three causal questions together instead of three separate analytic samples — closer to how a real production data pipeline would be structured.",
  "我会从一开始就把dormant模式的实验设计好，而不是留成一个gap，也会把面板数据做得更完整（完整的逐月账户轨迹，而不是事件级抽样样本），这样同一份数据集就能同时支撑三个因果问题，而不是三个分开的分析样本——这样更接近真实生产数据管道该有的样子。"
).forEach(p => children.push(p));

children.push(hr());

// ---------------------------------------------------------------------- QUICK REFERENCE
children.push(h2("速记 Quick Reference"));

const rows = [
  ["RDD cutoff / running variable", "30% of balance withdrawn in a month"],
  ["RDD naive vs. robust estimate", "-1.5pp (biased) vs. -10.7pp [95% CI -14.8, -6.6], p<0.001"],
  ["RDD manipulation check", "McCrary-style, p = 0.151 (pass)"],
  ["RDD bandwidth sensitivity", "-9.4pp to -10.7pp across h = 4 to 20 (stable)"],
  ["DiD rollout cohorts", "Regions adopt at months 8 / 14 / 20; 2 regions never-treated in-window"],
  ["DiD parallel pre-trends check", "F-test on common pre-period, p = 0.765 (pass)"],
  ["DiD naive TWFE vs. CS-style", "-8.5pp vs. -7.7pp (true simulated effect: -6.4pp)"],
  ["DiD effect ramp", "~3 months to reach steady state"],
  ["Optimization result", "+497% net value protected vs. heuristic, equal budget & RM capacity"],
  ["Optimization RM capacity used", "400 / 400 contacts (fully allocated)"],
  ["Real project result (unchanged)", "-30% relative churn, randomized A/B test"],
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
