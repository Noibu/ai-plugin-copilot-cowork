---
name: checkout-analysis
description: Analyze Noibu checkout performance, funnel drop-off, payment and delivery mix, abandonment, and technical issues with an interactive investigation board, dashboard, export, and scheduling actions.
---

# Checkout performance

- Read [shared query guidance](../querying-noibu-data/SKILL.md). Open [runtime/actions](../querying-noibu-data/references/runtime.md) only for a connection problem or a save, export, schedule, ticket or browser action. Use skill `checkout-analysis`; resolve the store and saved business context.
- Default to the last 30 days versus the immediately preceding equal window; honor requested dates.
- Focused questions use only relevant [queries](references/queries.md). For a full review:
  - Fetch Q1–Q7, Q1b when row-level fields exist, and prior counterparts **in one parallel batch** (all independent); only follow-ups wait for results.
  - Use distinct sessions reaching at least each stage. Express checkout may skip intermediate events.
  - Compare each segment with its own prior window. Candidate regressions are ≥3 pp absolute or ≥10% relative with sufficient traffic; rank up to three supported findings.
  - Run targeted follow-ups. Route merchant technical causes to tech-diagnosis; give UX/operations findings a concrete next check and verification plan.

## Report

Use the packaged [report display](references/card-quickstart.md); focused answers may remain prose.

- Put one or two measured conclusions inside the report card; successful in-chat reports are CARD ONLY, without preamble or post-card recap.
- Overview: compact population/cart reach, percentage-led cart → checkout → payment → completion funnel: Added to cart shows its raw count and is the 100% baseline; later stages show their share of that SAME cart population (not previous stage), completion/device/value highlights, supported abandonment rows and populated payment/delivery bars.
- Show exact windows, timezone, denominators, currency and express-checkout/coverage limits. Each period uses its OWN measured positive cart baseline for bars and rates; derive signed pp deltas from those rates, not counts. Show exact counts must expand actual current/prior session counts for EVERY stage in full AND compact. Missing/zero bases or unmeasured stages are Not measured, never invented zero rates. Keep checkout completion separate: completed / started checkout. See [funnel contract](../querying-noibu-data/references/funnel-visualization.md). Avoid duplicating KPIs as highlights.
- Put abandonment tables at `placement: "overview"`; supporting data is expandable. Label bounded samples and never extrapolate sample cart values to all abandoned sessions.
- Classify abandonment as observed behavior, not proven motives. Check continued product/category browsing before generic no-action. Payment/delivery mix measured only on purchases cannot establish gateway failure rates.
- Each numbered opportunity needs its cohort, current/prior denominators, signed pp/relative delta and `fix` containing **Next check** plus verification. Do not pad findings or treat tiny order movements as major opportunities.
- Missing slices stay omitted. With healthy completions but missing intermediate events, headline cart-to-completion rather than invented drops. An empty window warrants another date/store choice.
- Estimates need a formula/baseline and are not guaranteed recovery. Lower discount use alone does not prove coupon failure.

## Follow-ups

- Preserve the tested light dashboard, the saved-dashboard action (see the runtime guide) beneath dashboard content, investigation cards, and separate final save/download/scheduling controls.
- Investigate reuses the selected evidence; technical findings use the [repository/CI handoff](../tech-diagnosis/references/github-handoff.md), not ordinary UX/operations analysis.
- Saved dashboards follow [saved dashboard](../querying-noibu-data/references/saved-dashboard.md), including the mandatory refresh cadence/time/timezone/notification question (manual or decline is allowed).
- Scheduling follows [connected delivery](../querying-noibu-data/references/scheduling-delivery.md), with fresh rolling comparisons; exports reuse evidence unless refresh is requested.
- Issue/status changes require an explicit request, exact issue and supported status. Analysis/rendering authorizes no writes.

## In-chat report completion

Successful in-chat reports are CARD ONLY. Put every unique conclusion, priority, window, comparison scope, limitation and next-action hint inside the card before display; stop after the card, with no summary/recap prose before or after it. This does not suppress errors, unavailable-renderer fallbacks, prerequisite questions or separate user-requested action confirmations. Never claim a failed display succeeded. Follow shared card-quickstart.md; at most one render_ui call per response.

Scheduled Email always requires chat confirmation of the exact final recipient email list EVEN IF addresses were supplied; no schedule/send before that gate. Never infer the signed-in user from Email selected. See shared scheduling-delivery.md. Any private app save/build must ask refresh cadence, local time/IANA timezone and notification (manual/decline allowed), verify a same-app unattended DATA writer, and only then create/update a confirmed refresh schedule; no reminder substitute or unverified refresh-success claim.

## Browser prerequisite, only for a requested browser step

Use the local [Edge connection/readiness guide](references/browser-readiness.md). Never prompt for browser setup during ordinary analytics/report display or repeat it when the browser is usable; explain the blocked step and continue nonbrowser work.

## Local report completion contract (21.1.13)

Use this skill’s [local display guide](references/card-quickstart.md), [runner](scripts/show_card.py), [builder](scripts/build_presentation.py), [console helper](scripts/console_links.py), [exact checker](scripts/cowork_card_check.py) and [comparison adapter](scripts/comparison_acquisition.py). This own-skill display route has no sibling filesystem dependency. Load querying-noibu-data by name for query/action guidance at its actual returned location; do not assume that loading markdown materializes its scripts. Comparison acquisition and actual current/prior metric rows follow the [local contract](references/comparison-acquisition.md). A host render acknowledgement is terminal CARD ONLY with no client-visibility gate; unknown delivery never means failed or permits whole-report replay.
