---
name: store-pulse
description: Show a Noibu store-health snapshot with KPI tiles and a purchase funnel, with follow-ups to export or schedule a recurring report; optionally include products and traffic channels.
---

# Store Pulse

- Read [shared query guidance](../querying-noibu-data/SKILL.md). Open [runtime/actions](../querying-noibu-data/references/runtime.md) only for a connection problem or a save, export, schedule, ticket or browser action. Use skill `store-pulse`; resolve the store and saved context.
- Fetch fresh data for each invocation. Default to rolling last 24 hours versus preceding 24 hours, using one anchor; honor requested windows.
- Follow [snapshot queries](references/snapshot-queries.md). Send **all six window queries in one parallel batch**: core metrics, completed revenue and orders, and funnel depth, each for the current and prior window, plus `noibu_get_business_context` when not yet loaded. Compute after they return; don't query one at a time:
  - Fetch sessions, bounce/conversion, completed-order revenue and completed-order count for both windows; keep currencies separate.
  - Derive engagement = 1 − bounce, AOV = completed-order revenue ÷ completed orders, and RPS = completed-order revenue ÷ sessions. Undefined denominators remain unknown.
  - Build cumulative funnel depths from distinct sessions, not event sums; account for express checkout/missing intermediate events.
- Query products/channels/paid traffic only when requested, using [optional blocks](references/optional-blocks.md).

## Report and actions

- Lead with one or two measured conclusions as the prose summary, then the card from the packaged [report display](references/card-quickstart.md).
- Show light unfilled Sessions/Engagement/Conversion/AOV/RPS groups and a connected five-stage funnel with rates against total sessions, comparison context and exact counts.
- Rate deltas use pp; volume/value deltas use relative %, undefined when prior is zero. Explicit measured downward changes use orange; captions remain separate.
- Scheduling uses [shared connected delivery](../querying-noibu-data/references/scheduling-delivery.md). Store Pulse alone adds **Daily** to Weekly/Every 2 weeks/Monthly; weekly remains initially selected.
- Daily means every calendar day, including weekends, at confirmed local time/IANA timezone; no weekday/first-run/monthday fields. Recurrence does not change source windows: fetch fresh last 24 hours versus preceding 24 hours, or the confirmed alternative, on every run.

## Output

Follow the [UX guidelines](references/ux-guidelines.md) for everything the user sees: a 2–3 sentence summary, then one card, then the next-step question offering the card's priorities. The card carries Noibu link buttons only. Download, save and schedule run only when the user asks and are never offered or mentioned. No dashboards. In a scheduled run, ask nothing.

- Build the card with this skill's [local display guide](references/card-quickstart.md): write the `noibu.presentation/1` report, then run the [runner](scripts/show_card.py), which uses the [builder](scripts/build_presentation.py), [console helper](scripts/console_links.py), [checker](scripts/cowork_card_check.py) and [comparison adapter](scripts/comparison_acquisition.py) in this folder. Never hand-write card JSON; at most one render_ui call per response. Build the next-step question from the runner's `priorityOptions`.
- Give every finding a `shortTitle` of 5 words or fewer (the question shows it) and a title of 60 characters or fewer.
- Load querying-noibu-data by name for query and action guidance. Current/prior comparisons follow the [local contract](references/comparison-acquisition.md).
- Scheduled email always confirms the exact recipient addresses in chat, even if supplied ([connected delivery](../querying-noibu-data/references/scheduling-delivery.md)).
- **Drill-down options** (one priority: added as the second option; no priorities: both): "See the last 7 days" · "Break down by device".
- **Scheduled runs (only when asked):** preset label "Daily at 8 am", description "Summary · Teams · last 24 hours"; rolling last 24 hours vs the preceding 24 hours. Store Pulse is the only skill that offers Daily.

## Browser prerequisite, only for a requested browser step

Use the local [Edge connection/readiness guide](references/browser-readiness.md). Never prompt for browser setup during ordinary analytics/report display or repeat it when the browser is usable; explain the blocked step and continue nonbrowser work.
