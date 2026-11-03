---
name: product-analysis
description: Analyze Noibu product and collection performance, add-to-cart opportunities, and purchase friction; present an interactive priority board with investigation, dashboard, export, and scheduling actions.
---

# Product and collection performance

- Read [shared query guidance](../querying-noibu-data/SKILL.md). Open [runtime/actions](../querying-noibu-data/references/runtime.md) only for a connection problem or a save, export, schedule, ticket or browser action. Use skill `product-analysis`; resolve the store and saved context. Default to 30 days.
- Focused questions use only necessary queries. For a full review, follow [queries](references/queries.md): products by views, product-page cart opportunities, collections and product types, **sent as one parallel batch**; compare suitable cohorts and run targeted follow-ups for supported signals.

## Dashboard and opportunities

Use the packaged [report display](references/card-quickstart.md), not a custom redesign.

- Put one or two measured conclusions inside the report card; successful in-chat reports are CARD ONLY, without preamble or post-card recap.
- Keep session count, session conversion and measured median completed cart value/currency in `overviewContext`.
- Prefer a complete product-viewer cohort funnel: viewed product → cart → purchase. Name a focused cohort in `funnelContext`; never derive a store-wide funnel from top-N products. Any-cart purchase after viewing is not purchase of that product.
- Declare viewers/cart/all-session denominators and use counts for geometry. Missing stages stay omitted.
- Use two primary `placement: "overview"` tables, normally products and collections by sessions; other tables use `supporting`. Retain Show more/Show less, five-row previews and all source rows/full names. Numeric session counts may use `barColumn`.
- Label URL-based collection cohorts when events are sparse; omit unmeasured ATC, prices and revenue/session.
- Show the strongest two or three opportunities, fewer if warranted. Use a factual tag, specific product/collection, actual traffic unit and concise evidence with material limitations.
- Put the investigation/verification plan in `fix`, under **Investigation & verification**. Additional real signals retain their IDs/count; do not invent fillers.
- Keep the saved-dashboard action (see the runtime guide) directly after dashboard content, then opportunities, then separate final save/download/schedule controls. Shared styling supplies light panels and orange measured declines.

## Interpretation

- Whole-cart values are not product revenue; distinguish AOV from median value.
- Compare price tiers only with measured prices/confirmed context, not title guesses. Without credible peers, use measured cart-opportunity scores and funnel behavior.
- Title variants/localized URLs may split a product; disclose suspected duplicates rather than silently merging.
- Low scroll does not prove a control was unseen; country differences do not establish shipping restrictions; errors correlated with low conversion do not prove causation.
- Exposure is not proven blocked users or recoverable sales. Preserve attribution/identity limitations.

## Follow-ups

- Reuse evidence for Investigate and exports. Route technical causes to tech-diagnosis and its [repository/CI handoff](../tech-diagnosis/references/github-handoff.md); normal analysis does not require a repository.
- Saved dashboards use [saved dashboard](../querying-noibu-data/references/saved-dashboard.md), including the mandatory refresh cadence/time/timezone/notification question (manual or decline is allowed).
- **Schedule Insights** uses [shared connected delivery](../querying-noibu-data/references/scheduling-delivery.md) with fresh product scope, rolling windows and comparison rules. Daily is not offered here.

## In-chat report completion

Successful in-chat reports are CARD ONLY. Put every unique conclusion, priority, window, comparison scope, limitation and next-action hint inside the card before display; stop after the card, with no summary/recap prose before or after it. This does not suppress errors, unavailable-renderer fallbacks, prerequisite questions or separate user-requested action confirmations. Never claim a failed display succeeded. Follow shared card-quickstart.md; at most one render_ui call per response.

Scheduled Email always requires chat confirmation of the exact final recipient email list EVEN IF addresses were supplied; no schedule/send before that gate. Never infer the signed-in user from Email selected. See shared scheduling-delivery.md. Any private app save/build must ask refresh cadence, local time/IANA timezone and notification (manual/decline allowed), verify a same-app unattended DATA writer, and only then create/update a confirmed refresh schedule; no reminder substitute or unverified refresh-success claim.

## Browser prerequisite, only for a requested browser step

Use the local [Edge connection/readiness guide](references/browser-readiness.md). Never prompt for browser setup during ordinary analytics/report display or repeat it when the browser is usable; explain the blocked step and continue nonbrowser work.

## Local report completion contract (21.1.13)

Use this skill’s [local display guide](references/card-quickstart.md), [runner](scripts/show_card.py), [builder](scripts/build_presentation.py), [console helper](scripts/console_links.py), [exact checker](scripts/cowork_card_check.py) and [comparison adapter](scripts/comparison_acquisition.py). This own-skill display route has no sibling filesystem dependency. Load querying-noibu-data by name for query/action guidance at its actual returned location; do not assume that loading markdown materializes its scripts. Comparison acquisition and actual current/prior metric rows follow the [local contract](references/comparison-acquisition.md). A host render acknowledgement is terminal CARD ONLY with no client-visibility gate; unknown delivery never means failed or permits whole-report replay.
