---
name: product-analysis
description: Analyze Noibu product and collection performance, add-to-cart opportunities, and purchase friction; present a priority report card with investigation, export and scheduling follow-ups.
---

# Product and collection performance

- Read [shared query guidance](../querying-noibu-data/SKILL.md). Open [runtime/actions](../querying-noibu-data/references/runtime.md) only for a connection problem or a save, export, schedule, ticket or browser action. Use skill `product-analysis`; resolve the store and saved context. Default to 30 days.
- Focused questions use only necessary queries. For a full review, follow [queries](references/queries.md): products by views, product-page cart opportunities, collections and product types, **sent as one parallel batch**; compare suitable cohorts and run targeted follow-ups for supported signals.

## Report and opportunities

Use the packaged [report display](references/card-quickstart.md), not a custom redesign.

- Lead with one or two measured conclusions as the prose summary before the card; the card doesn't repeat them.
- Keep session count, session conversion and measured median completed cart value/currency in `overviewContext`.
- Prefer a complete product-viewer cohort funnel: viewed product → cart → purchase. Name a focused cohort in `funnelContext`; never derive a store-wide funnel from top-N products. Any-cart purchase after viewing is not purchase of that product.
- Declare viewers/cart/all-session denominators and use counts for geometry. Missing stages stay omitted.
- Use two primary `placement: "overview"` tables, normally products and collections by sessions; other tables use `supporting`. Retain Show more/Show less, five-row previews and all source rows/full names. Numeric session counts may use `barColumn`.
- Label URL-based collection cohorts when events are sparse; omit unmeasured ATC, prices and revenue/session.
- Show the strongest two or three opportunities, fewer if warranted. Use a factual tag, specific product/collection, actual traffic unit and concise evidence with material limitations.
- Put the investigation/verification plan in `fix`, under **Investigation & verification**. Additional real signals retain their IDs/count; do not invent fillers.
- Card order: overview, then opportunities, then Evidence & coverage. The question after the card offers the card's priorities. Shared styling supplies light panels and orange measured declines.

## Interpretation

- Whole-cart values are not product revenue; distinguish AOV from median value.
- Compare price tiers only with measured prices/confirmed context, not title guesses. Without credible peers, use measured cart-opportunity scores and funnel behavior.
- Title variants/localized URLs may split a product; disclose suspected duplicates rather than silently merging.
- Low scroll does not prove a control was unseen; country differences do not establish shipping restrictions; errors correlated with low conversion do not prove causation.
- Exposure is not proven blocked users or recoverable sales. Preserve attribution/identity limitations.

## Follow-ups

- Reuse evidence for Investigate and exports. Route technical causes to tech-diagnosis and its [repository/CI handoff](../tech-diagnosis/references/github-handoff.md); normal analysis does not require a repository.
- Scheduling uses [shared connected delivery](../querying-noibu-data/references/scheduling-delivery.md) with fresh product scope, rolling windows and comparison rules. Daily is not offered here.

## Output

Follow the [UX guidelines](references/ux-guidelines.md) for everything the user sees: a 2–3 sentence summary, then one card, then the next-step question offering the card's priorities. The card carries Noibu link buttons only. Download, save and schedule run only when the user asks and are never offered or mentioned. No dashboards. In a scheduled run, ask nothing.

- Build the card with this skill's [local display guide](references/card-quickstart.md): write the `noibu.presentation/1` report, then run the [runner](scripts/show_card.py), which uses the [builder](scripts/build_presentation.py), [console helper](scripts/console_links.py), [checker](scripts/cowork_card_check.py) and [comparison adapter](scripts/comparison_acquisition.py) in this folder. Never hand-write card JSON; at most one render_ui call per response. Build the next-step question from the runner's `priorityOptions`.
- Give every finding a `shortTitle` of 5 words or fewer (the question shows it) and a title of 60 characters or fewer.
- Load querying-noibu-data by name for query and action guidance. Current/prior comparisons follow the [local contract](references/comparison-acquisition.md).
- Scheduled email always confirms the exact recipient addresses in chat, even if supplied ([connected delivery](../querying-noibu-data/references/scheduling-delivery.md)).
- **Drill-down options** (one priority: added as the second option; no priorities: both): "Break down by device" · "Change the date range".
- **Scheduled runs (only when asked):** preset label "Weekly on Mondays", description "9 am · Summary · Teams"; last 7 days vs the previous 7. Daily is not offered.

## Browser prerequisite, only for a requested browser step

Use the local [Edge connection/readiness guide](references/browser-readiness.md). Never prompt for browser setup during ordinary analytics/report display or repeat it when the browser is usable; explain the blocked step and continue nonbrowser work.
