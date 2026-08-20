const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  BorderStyle, Table, TableRow, TableCell, WidthType, ShadingType
} = require('docx');

const slides = JSON.parse(fs.readFileSync('/tmp/slides_script.json', 'utf8'));

const PAGE = { size: { width: 12240, height: 15840 } }; // US Letter

function scriptParagraphs(scriptText) {
  return scriptText.split('\n\n').map(p => new Paragraph({
    spacing: { after: 160, line: 300 },
    children: [ new TextRun({ text: p, italics: true, size: 23, color: "1A1A1A" }) ],
  }));
}

const children = [];

// Title page
children.push(
  new Paragraph({ text: "DDA Retention Decision Engine", heading: HeadingLevel.TITLE, spacing: { after: 80 } }),
  new Paragraph({
    children: [ new TextRun({ text: "Presentation Speech Script", size: 30, color: "555555" }) ],
    spacing: { after: 40 },
  }),
  new Paragraph({
    children: [ new TextRun({ text: "19 core slides + 1 appendix backup · target ~19–20 minutes + Q&A · Vanguard, Data Analyst Senior Specialist / Data Scientist — Decision Analytics & Modeling", size: 20, color: "777777" }) ],
    spacing: { after: 300 },
  }),
);

// "Is the deck enough" guidance section
children.push(
  new Paragraph({ text: "Before You Present: Is Opening the Deck Enough?", heading: HeadingLevel.HEADING_1, spacing: { before: 200, after: 120 } }),
  new Paragraph({
    spacing: { after: 120, line: 300 },
    children: [ new TextRun({ text: "Screen-sharing the PPT itself is the right primary vehicle — the slides are deliberately sparse (one or two numbers, one line of framing), so the substance has to come from what you say, not what's on screen. That's exactly what this script is for: don't read the slide text out loud, narrate past it using the script below.", size: 22 }) ],
  }),
  new Paragraph({
    spacing: { after: 120, line: 300 },
    children: [ new TextRun({ text: "A few things worth having ready alongside it, in case the conversation goes deeper than the slides:", size: 22 }) ],
  }),
  ...[
    "Backup tabs open (but not shown unless asked): the GitHub repo, in case someone wants to see the actual code, not just the results; output/rdd_bandwidth_sensitivity.csv, output/did_summary.json, and output/dormant_summary.json for the full confidence intervals (slide 20, the appendix backup slide, is “ready if asked to go deeper” on the dormant holdout's statistical power specifically).",
    "The bilingual Q&A document (项目二-延伸-RDD-DiD-优化-QA.docx) as your own private crib sheet for follow-up questions — not something you show, something you've internalized.",
    "A PDF export of the deck as a fallback, in case the interviewer's system doesn't render .pptx cleanly, or in case you're not the one driving the screen share.",
    "Know the five “anchor numbers” cold, without looking at the slide: -8.3pp (RDD), -5.8pp (DiD), -10.8pp / -5.8pp (dormant RCT, HV cashback / LV SMS), +64.3% / +$167,927 (optimization/business impact), -30% relative (the real A/B test). If you can say these without reading them off the screen, the whole talk reads as fluent rather than recited.",
    "Practical logistics: test the screen share beforehand, mute notifications, and know how to jump directly to a specific slide number if asked to go back or skip ahead — interviewers often interrupt mid-flow. Slide 20 (appendix) is deliberately NOT part of the normal flow — only jump to it if asked to defend the 90/10 holdout split or derive SE→z→power by hand.",
  ].map(t => new Paragraph({
    numbering: undefined,
    bullet: { level: 0 },
    spacing: { after: 100, line: 280 },
    children: [ new TextRun({ text: t, size: 22 }) ],
  })),
  new Paragraph({
    spacing: { before: 100, after: 300, line: 300 },
    children: [ new TextRun({ text: "Pacing target: Title+Situation ~55s, Task/Framing ~75s (don't skip this one), Architecture ~50s, Predict ~40s, the six causal-inference slides (6–12) ~5.5 minutes combined, Optimize (13–14) ~1.5 minutes, Business Impact + Recommendations (15–16) ~1.5 minutes, Tying back + Limitations (17–18) ~1.5 minutes, Closing ~15 seconds — leaves comfortable room inside a 20-minute slot for the interviewer to interject. Slide 20 is backup only and isn't counted in the pacing target.", size: 21, italics: true, color: "555555" }) ],
  }),
);

// Per-slide sections
for (const s of slides) {
  children.push(
    new Paragraph({
      pageBreakBefore: s.num === 1,
      spacing: { before: 300, after: 40 },
      border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "999999", space: 4 } },
      children: [
        new TextRun({ text: `Slide ${s.num}`, bold: true, size: 26, color: "2C4870" }),
        new TextRun({ text: `  —  ${s.title}`, bold: true, size: 26 }),
      ],
    }),
    new Paragraph({
      spacing: { after: 140 },
      children: [ new TextRun({ text: `Target time: ${s.duration}`, size: 19, color: "888888", italics: true }) ],
    }),
    ...scriptParagraphs(s.script),
  );
}

const doc = new Document({
  sections: [{
    properties: { page: { size: PAGE.size, margin: { top: 1080, bottom: 1080, left: 1080, right: 1080 } } },
    children,
  }],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync('/root/vanguard_dda_project/deck/presentation_speech_script.docx', buf);
  console.log('written');
});
