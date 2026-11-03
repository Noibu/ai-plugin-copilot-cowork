---
name: store-pulse
description: Show a Noibu store-health snapshot with KPI cards, a purchase funnel, and actions to save a private dashboard, export, or schedule recurring reports; optionally include products and traffic channels.
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

- Put one or two measured conclusions inside the card, using the packaged [report display](references/card-quickstart.md).
- Show light unfilled Sessions/Engagement/Conversion/AOV/RPS groups and a connected five-stage funnel with rates against total sessions, comparison context and exact counts.
- Rate deltas use pp; volume/value deltas use relative %, undefined when prior is zero. Explicit measured downward changes use orange; captions remain separate.
- Place the saved-dashboard action (see the runtime guide) below all dashboard content, before supported investigation opportunities; keep save/download/scheduling in the final section.
- Saved dashboards use [saved dashboard](../querying-noibu-data/references/saved-dashboard.md): reuse the existing private app, preserve domain/window/optional blocks, verify totals and the saved snapshot by rereading it, and always ask refresh cadence/local time/IANA timezone/notification, with explicit manual/decline allowed. Do not require a spreadsheet or visitor connection for saved-data mode.
- **Schedule report** uses [shared connected delivery](../querying-noibu-data/references/scheduling-delivery.md). Store Pulse alone adds **Daily** to Weekly/Every 2 weeks/Monthly; weekly remains initially selected.
- Daily means every calendar day, including weekends, at confirmed local time/IANA timezone; no weekday/first-run/monthday fields. Recurrence does not change source windows: fetch fresh last 24 hours versus preceding 24 hours, or the confirmed alternative, on every run.

## In-chat report completion

Successful in-chat reports are CARD ONLY. Put every unique conclusion, priority, window, comparison scope, limitation and next-action hint inside the card before display; stop after the card, with no summary/recap prose before or after it. This does not suppress errors, unavailable-renderer fallbacks, prerequisite questions or separate user-requested action confirmations. Never claim a failed display succeeded. Follow shared card-quickstart.md; at most one render_ui call per response.

Scheduled Email always requires chat confirmation of the exact final recipient email list EVEN IF addresses were supplied; no schedule/send before that gate. Never infer the signed-in user from Email selected. See shared scheduling-delivery.md. Any private app save/build must ask refresh cadence, local time/IANA timezone and notification (manual/decline allowed), verify a same-app unattended DATA writer, and only then create/update a confirmed refresh schedule; no reminder substitute or unverified refresh-success claim.

## Browser prerequisite, only for a requested browser step

Use the local [Edge connection/readiness guide](references/browser-readiness.md). Never prompt for browser setup during ordinary analytics/report display or repeat it when the browser is usable; explain the blocked step and continue nonbrowser work.

## Local report completion contract (21.1.13)

Use this skill’s [local display guide](references/card-quickstart.md), [runner](scripts/show_card.py), [builder](scripts/build_presentation.py), [console helper](scripts/console_links.py), [exact checker](scripts/cowork_card_check.py) and [comparison adapter](scripts/comparison_acquisition.py). This own-skill display route has no sibling filesystem dependency. Load querying-noibu-data by name for query/action guidance at its actual returned location; do not assume that loading markdown materializes its scripts. Comparison acquisition and actual current/prior metric rows follow the [local contract](references/comparison-acquisition.md). A host render acknowledgement is terminal CARD ONLY with no client-visibility gate; unknown delivery never means failed or permits whole-report replay.
