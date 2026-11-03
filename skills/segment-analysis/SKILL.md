---
name: segment-analysis
description: Compare devices, countries, channels, and campaigns using Noibu, identify conversion regressions, and provide an interactive report with investigation, dashboard, export, and scheduling actions.
---

# Segment conversion analysis

- Read [shared query guidance](../querying-noibu-data/SKILL.md). Open [runtime/actions](../querying-noibu-data/references/runtime.md) only for a connection problem or a save, export, schedule, ticket or browser action. Use skill `segment-analysis`; resolve the store and saved context. Default to 30 days.
- Focused questions need only relevant queries. For a full review, follow [queries](references/queries.md):
  - Fetch device, country and UTM source/medium aggregates plus a direct whole-domain baseline **in one parallel batch**.
  - Compare channels with peers of similar intent/objective; compare devices with their own history. Use equal halves with exact dates for within-window device ratios.
  - Assess traffic quality and sparse purchases; zero conversion or geography alone does not identify bots.
  - Select up to three supported signals and run campaign, landing-page or funnel follow-ups.

## Dashboard and opportunities

Use the packaged [report display](references/card-quickstart.md).

- Put one or two measured conclusions inside the report card; successful in-chat reports are CARD ONLY, without preamble or post-card recap.
- Overview: site-wide/mobile/desktop conversion, purchasing/session denominators, exact window/timezone and a few nonduplicative country/channel highlights. No mandatory funnel.
- Under Show more/Show less, use three `placement: "overview"` tables when supported: Countries, Best converting channels, Most visited channels. Include Sessions/CVR/Revenue per session with measured currency components kept separate.
- State each ranking's volume filter, population and top-N bounds. A capped result cannot establish a global winner. Retain five-row previews/all rows; history/campaign/landing tables use `supporting`.
- Use up to three visible `overviewNotes` for material attribution, reconciliation or currency caveats; retain detailed evidence too.
- Each top opportunity has a factual tag, specific cohort, actual traffic unit and concise evidence; `fix` holds expandable investigation/verification.
- Keep the saved-dashboard action (see the runtime guide) directly after dashboard content, then opportunities, then separate final save/download/schedule controls. Shared styling supplies light panels and orange measured declines.

## Interpretation

- A stable device gap is not a regression. A worsening ratio driven by faster desktop improvement or traffic mix does not prove mobile deteriorated.
- Separate country opportunity, channel intent and campaign objective; exposure is not proven blocked users or lost orders.
- Do not merge source/medium aliases or call all unattributed sessions Direct without evidence.
- Missing UTM share needs a complete unattributed aggregate and whole-domain denominator, not overlapping cohort sums. Missing tags do not prove a tracking defect.
- For absent paid-traffic UTM rows, use the shared guide's referrer-parameter recovery and label results a lower bound.
- Preserve low-volume uncertainty, count discrepancies and currency boundaries; do not invent signals to fill cards.

## Follow-ups

- Investigate retains the selected evidence. Route genuine technical findings to tech-diagnosis and its [repository/CI handoff](../tech-diagnosis/references/github-handoff.md), not ordinary marketing findings.
- Saved dashboards use [saved dashboard](../querying-noibu-data/references/saved-dashboard.md), including the mandatory refresh cadence/time/timezone/notification question (manual or decline is allowed).
- **Schedule Insights** uses [shared connected delivery](../querying-noibu-data/references/scheduling-delivery.md), fresh rolling scope and the confirmed equal-half/other baselines. Daily is not offered here.

## In-chat report completion

Successful in-chat reports are CARD ONLY. Put every unique conclusion, priority, window, comparison scope, limitation and next-action hint inside the card before display; stop after the card, with no summary/recap prose before or after it. This does not suppress errors, unavailable-renderer fallbacks, prerequisite questions or separate user-requested action confirmations. Never claim a failed display succeeded. Follow shared card-quickstart.md; at most one render_ui call per response.

Scheduled Email always requires chat confirmation of the exact final recipient email list EVEN IF addresses were supplied; no schedule/send before that gate. Never infer the signed-in user from Email selected. See shared scheduling-delivery.md. Any private app save/build must ask refresh cadence, local time/IANA timezone and notification (manual/decline allowed), verify a same-app unattended DATA writer, and only then create/update a confirmed refresh schedule; no reminder substitute or unverified refresh-success claim.

## Browser prerequisite, only for a requested browser step

Use the local [Edge connection/readiness guide](references/browser-readiness.md). Never prompt for browser setup during ordinary analytics/report display or repeat it when the browser is usable; explain the blocked step and continue nonbrowser work.

## Local report completion contract (21.1.13)

Use this skill’s [local display guide](references/card-quickstart.md), [runner](scripts/show_card.py), [builder](scripts/build_presentation.py), [console helper](scripts/console_links.py), [exact checker](scripts/cowork_card_check.py) and [comparison adapter](scripts/comparison_acquisition.py). This own-skill display route has no sibling filesystem dependency. Load querying-noibu-data by name for query/action guidance at its actual returned location; do not assume that loading markdown materializes its scripts. Comparison acquisition and actual current/prior metric rows follow the [local contract](references/comparison-acquisition.md). A host render acknowledgement is terminal CARD ONLY with no client-visibility gate; unknown delivery never means failed or permits whole-report replay.
