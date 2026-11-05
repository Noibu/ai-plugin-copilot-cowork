---
name: checkout-analysis
description: Analyze Noibu checkout performance, funnel drop-off, payment and delivery mix, abandonment, and technical issues with a report card and investigation, export and scheduling follow-ups.
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

- Lead with one or two measured conclusions as the prose summary before the card; the card doesn't repeat them.
- Overview: compact population/cart reach, percentage-led cart → checkout → payment → completion funnel: Added to cart shows its raw count and is the 100% baseline; later stages show their share of that SAME cart population (not previous stage), completion/device/value highlights, supported abandonment rows and populated payment/delivery bars.
- Show exact windows, timezone, denominators, currency and express-checkout/coverage limits. Each period uses its OWN measured positive cart baseline for bars and rates; derive signed pp deltas from those rates, not counts. Show exact counts must expand actual current/prior session counts for EVERY stage in full AND compact. Missing/zero bases or unmeasured stages are Not measured, never invented zero rates. Keep checkout completion separate: completed / started checkout. See [funnel contract](../querying-noibu-data/references/funnel-visualization.md). Avoid duplicating KPIs as highlights.
- Put abandonment tables at `placement: "overview"`; supporting data is expandable. Label bounded samples and never extrapolate sample cart values to all abandoned sessions.
- Classify abandonment as observed behavior, not proven motives. Check continued product/category browsing before generic no-action. Payment/delivery mix measured only on purchases cannot establish gateway failure rates.
- Each numbered opportunity needs its cohort, current/prior denominators, signed pp/relative delta and `fix` containing **Next check** plus verification. Do not pad findings or treat tiny order movements as major opportunities.
- Missing slices stay omitted. With healthy completions but missing intermediate events, headline cart-to-completion rather than invented drops. An empty window warrants another date/store choice.
- Estimates need a formula/baseline and are not guaranteed recovery. Lower discount use alone does not prove coupon failure.

## Follow-ups

- Keep the tested light layout: overview, numbered investigation cards, Evidence & coverage. The question after the card offers the card's priorities.
- Investigate reuses the selected evidence; technical findings use the [repository/CI handoff](../tech-diagnosis/references/github-handoff.md), not ordinary UX/operations analysis.
- Scheduling follows [connected delivery](../querying-noibu-data/references/scheduling-delivery.md), with fresh rolling comparisons; exports reuse evidence unless refresh is requested.
- Issue/status changes require an explicit request, exact issue and supported status. Analysis/rendering authorizes no writes.

## Output

Follow the [UX guidelines](references/ux-guidelines.md) for everything the user sees: a 2–3 sentence summary, then one card, then the next-step question offering the card's priorities. The card carries Noibu link buttons only. Download, save and schedule run only when the user asks and are never offered or mentioned. No dashboards. In a scheduled run, ask nothing.

- Build the card with this skill's [local display guide](references/card-quickstart.md): write the `noibu.presentation/1` report, then run the [runner](scripts/show_card.py), which uses the [builder](scripts/build_presentation.py), [console helper](scripts/console_links.py), [checker](scripts/cowork_card_check.py) and [comparison adapter](scripts/comparison_acquisition.py) in this folder. Never hand-write card JSON; at most one render_ui call per response. Build the next-step question from the runner's `priorityOptions`.
- Give every finding a `shortTitle` of 5 words or fewer (the question shows it) and a title of 60 characters or fewer.
- Load querying-noibu-data by name for query and action guidance. Current/prior comparisons follow the [local contract](references/comparison-acquisition.md).
- Scheduled email always confirms the exact recipient addresses in chat, even if supplied ([connected delivery](../querying-noibu-data/references/scheduling-delivery.md)).
- **Drill-down options** (one priority: added as the second option; no priorities: both): "Break down by device" · "Change the date range".
- **Scheduled runs (only when asked):** preset label "Weekly on Mondays", description "9 am · Summary · Teams"; last 7 days vs the previous 7.

## Browser prerequisite, only for a requested browser step

Use the local [Edge connection/readiness guide](references/browser-readiness.md). Never prompt for browser setup during ordinary analytics/report display or repeat it when the browser is usable; explain the blocked step and continue nonbrowser work.
