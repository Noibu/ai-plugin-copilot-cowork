---
name: segment-analysis
description: Compare devices, countries, channels, and campaigns using Noibu, identify conversion regressions, and provide a report card with investigation, export and scheduling follow-ups.
---

# Segment conversion analysis

- Read [shared query guidance](../querying-noibu-data/SKILL.md). Open [runtime/actions](../querying-noibu-data/references/runtime.md) only for a connection problem or a save, export, schedule, ticket or browser action. Use skill `segment-analysis`; resolve the store and saved context. Default to 30 days.
- Focused questions need only relevant queries. For a full review, follow [queries](references/queries.md):
  - Fetch device, country and UTM source/medium aggregates plus a direct whole-domain baseline **in one parallel batch**.
  - Compare channels with peers of similar intent/objective; compare devices with their own history. Use equal halves with exact dates for within-window device ratios.
  - Assess traffic quality and sparse purchases; zero conversion or geography alone does not identify bots.
  - Select up to three supported signals and run campaign, landing-page or funnel follow-ups.

## Report and opportunities

Use the packaged [report display](references/card-quickstart.md).

- Lead with one or two measured conclusions as the prose summary before the card; the card doesn't repeat them.
- Overview: site-wide/mobile/desktop conversion, purchasing/session denominators, exact window/timezone and a few nonduplicative country/channel highlights. No mandatory funnel.
- Under Show more/Show less, use three `placement: "overview"` tables when supported: Countries, Best converting channels, Most visited channels. Include Sessions/CVR/Revenue per session with measured currency components kept separate.
- State each ranking's volume filter, population and top-N bounds. A capped result cannot establish a global winner. Retain five-row previews/all rows; history/campaign/landing tables use `supporting`.
- Use up to three visible `overviewNotes` for material attribution, reconciliation or currency caveats; retain detailed evidence too.
- Each top opportunity has a factual tag, specific cohort, actual traffic unit and concise evidence; `fix` holds expandable investigation/verification.
- Card order: overview, then opportunities, then Evidence & coverage. Next steps (Investigate, Download as PDF, Schedule this report) come from the question after the card. Shared styling supplies light panels and orange measured declines.

## Interpretation

- A stable device gap is not a regression. A worsening ratio driven by faster desktop improvement or traffic mix does not prove mobile deteriorated.
- Separate country opportunity, channel intent and campaign objective; exposure is not proven blocked users or lost orders.
- Do not merge source/medium aliases or call all unattributed sessions Direct without evidence.
- Missing UTM share needs a complete unattributed aggregate and whole-domain denominator, not overlapping cohort sums. Missing tags do not prove a tracking defect.
- For absent paid-traffic UTM rows, use the shared guide's referrer-parameter recovery and label results a lower bound.
- Preserve low-volume uncertainty, count discrepancies and currency boundaries; do not invent signals to fill cards.

## Follow-ups

- Investigate retains the selected evidence. Route genuine technical findings to tech-diagnosis and its [repository/CI handoff](../tech-diagnosis/references/github-handoff.md), not ordinary marketing findings.
- Scheduling uses [shared connected delivery](../querying-noibu-data/references/scheduling-delivery.md), fresh rolling scope and the confirmed equal-half/other baselines. Daily is not offered here.

## Output

Follow the [UX guidelines](references/ux-guidelines.md) for everything the user sees: a 2–3 sentence summary, then one card, then the next-step question. The card carries Noibu link buttons only; investigate, download and schedule are offered by the question. No dashboards. In a scheduled run, ask nothing.

- Build the card with this skill's [local display guide](references/card-quickstart.md): write the `noibu.presentation/1` report, then run the [runner](scripts/show_card.py), which uses the [builder](scripts/build_presentation.py), [console helper](scripts/console_links.py), [checker](scripts/cowork_card_check.py) and [comparison adapter](scripts/comparison_acquisition.py) in this folder. Never hand-write card JSON; at most one render_ui call per response.
- Load querying-noibu-data by name for query and action guidance. Current/prior comparisons follow the [local contract](references/comparison-acquisition.md).
- Scheduled email always confirms the exact recipient addresses in chat, even if supplied ([connected delivery](../querying-noibu-data/references/scheduling-delivery.md)).
- Scheduled runs: preset "Weekly · Mon 9 am · Summary"; last 7 days vs the previous 7. Daily is not offered.

## Browser prerequisite, only for a requested browser step

Use the local [Edge connection/readiness guide](references/browser-readiness.md). Never prompt for browser setup during ordinary analytics/report display or repeat it when the browser is usable; explain the blocked step and continue nonbrowser work.
