---
name: querying-noibu-data
description: Shared Noibu tool routing, domain resolution, query semantics, telemetry metadata and data interpretation for every Noibu workflow in Microsoft 365 Copilot, plus Noibu setup. Use with any request about Noibu data, sessions, conversion, page visits, errors or console.noibu.com links, and for "set up Noibu", "connect Noibu", "is Noibu working" or "which stores can I see".
---

# Noibu query guide

- Use [runtime/actions](references/runtime.md) for connection, browser, output and external-action behavior.
- Discover the exposed tool by its unqualified `noibu_…` name; never hardcode an installation prefix. Current tool schemas are authoritative.
- On supported calls include a specific `rationale`, active topical `skill`, short `skillStep` and `skillVersion: "1.1.0"`.
- Full reports use [report display](references/card-quickstart.md); focused answers may remain prose. For any scheduling request read [connected delivery](references/scheduling-delivery.md).

## Speed rules (Cowork)

- **Read only what the step needs.** A full report needs this file, the topical SKILL.md, its `references/queries.md` and [card-quickstart.md](references/card-quickstart.md). Open [runtime.md](references/runtime.md), [presentation-contract.md](references/presentation-contract.md), [adaptive-card-board.md](references/adaptive-card-board.md) or the data references (sessions, page visits, errors) only when a step below sends you there or a call fails. Never re-read a file already read in this conversation.
- **Batch independent calls.** Issue every independent Noibu call for a step in one turn, as parallel tool calls: both comparison windows, and every aggregate that doesn't need another's result. Store resolution and business context run in the same batch as the first queries when the store UUID is already known.
- **Skip setup on analysis requests.** When a store is named or was already resolved in this conversation, don't call `noibu_get_current_user` or list stores first. Go straight to `noibu_get_domain` and the queries. Run the setup steps below only for setup requests or when a store can't be resolved.
- **Never hand-write card JSON.** Write the small `report.json` and run the card script ([card-quickstart.md](references/card-quickstart.md)). This replaces thousands of output tokens with one tool call.

## First run and setup

Use this when the user asks to set up or check Noibu, or when no Noibu tool has run yet in the conversation (for agents that have no separate `noibu-setup` skill).

- If Noibu tools aren't available yet, the user is most likely still connecting: the host shows a Connect/sign-in prompt on first use and the turn can start before sign-in finishes. Say Noibu isn't connected yet, ask them to finish the prompt and then ask again or say *continue*, and stop. Follow the runtime guide's steps if tools are still missing after they've connected; never lead with "configuration is missing or failing", and never ask for pasted tokens or loop on retries.
- Call `noibu_get_current_user` to confirm access (show only what's needed), then list authorized stores with `noibu_list_domains`, `pagination: {limit: 50, offset: 0}`, continuing as needed. Use a sole store or ask which one. An empty list may mean missing company/domain access in Noibu, not a broken connection.
- Resolve the chosen store as below and load its saved business context.
- Say briefly which optional capabilities this product offers, from the [runtime guide](references/runtime.md), marking each as available, not available or not checked from what this session actually exposes.
- Setup runs no analytics, scans, drafts or schedules; offer the relevant workflow next.

## Resolve the store

- Use a supplied UUID directly. For a name, call `noibu_get_domain` as supplied; do not substitute stores.
- On a miss, offer permitted suggestions or `noibu_list_domains` with `pagination: {limit: 50, offset: 0}`. Continue pagination; ask when multiple stores remain ambiguous.
- Retain UUID `id`, integer `numId`, company, platform and currency. Most analytics use UUID; business-context writes/accessibility jobs use integer numId.
- Fetch `noibu_get_business_context` before substantial analysis; null is normal.
- Before declaring data absent, inspect relevant sibling domains scoped to the resolved company. Storefront/checkout data do not automatically stitch. `noibu_get_company` expects company name, not numeric ID.

## Route queries

- Sessions, conversion, revenue, devices/countries/channels/products: `noibu_search_sessions` and [sessions](references/sessions.md).
- Row-level examples/checkout sub-steps: `noibu_session_lookup`; inspect its select/pagination schema, not aggregate substitutes.
- Page traffic, interactions, URLs and p75 vitals: `noibu_get_page_visits` and [page visits](references/page-visits.md). Use QUANTILE_75, not averages.
- Trends: available session/page/error trend tools with their live period/resolution schema.
- Exact-URL navigation: page visits; category-pattern sequences: [journeys/replay](references/journeys-and-replay.md). Replays only when requested.
- Errors or technical follow-ups: [errors](references/errors.md); ordinary business analysis starts with sessions/pages.
- Existing experiment configuration/verdicts: [A/B tests](references/ab-tests.md); roster and computed verdict are different tools.
- Report/action destinations: [verified Noibu links](references/console-urls.md). Successful draft writes need **Open draft in Noibu** from returned/verified IDs; preserve links in saved/exported/scheduled reports.
- Funnels: retrieve measured stage counts, then [funnel presentation](references/funnel-visualization.md).
- Accessibility: load accessibility-audit and its execution guide. Use approved browser axe or completed exports; limited review keeps automated counts unknown. No automatic remote scan job.

## Query contract

Example aggregate envelope; adapt to the exposed schema:

```json
{
  "domainId": "<resolved UUID>",
  "rationale": "<user intent>",
  "skill": "<active skill>",
  "skillStep": "<step>",
  "skillVersion": "1.1.0",
  "input": {
    "periodOptions": {
      "dateTimeRange": {"startTime": "<ISO timestamp>", "endTime": "<ISO timestamp>"}
    },
    "queryInput": {
      "measures": [
        {"aggregate": {"measureFunc": "COUNT", "target": {"field": "SESSION_ID"}, "measureAlias": "sessions"}}
      ],
      "orderBy": {"measureAlias": "sessions", "direction": "DESCENDING"},
      "limit": 1
    }
  }
}
```

- Bounded aggregates require `queryInput.orderBy`. A target-field/aggregation pair is unique; aliases do not permit duplicate measures.
- Caps: session aggregates 100 rows, page visits 1,500, row lookup 1,000. Respect hasMore/cursors; top-N/sample results are not population totals.
- Filters wrap fieldFilter/collectionFilter; scalar grouping uses groupBy.fieldSegments, collections groupBy.arrayJoin.
- Boolean filters use IS_ANY_OF with string values ["true"]/["false"], not IS.
- Row lookup selects field/timeField targets, e.g. MAX_CART_VALUE/SESSION_START_TIME, and orders by returned selectAlias.
- Normalize finite numeric strings; null/empty is not zero. LCP/FCP/TTFB/INP use milliseconds, CLS no unit. Convert timing displays deliberately.
- Anchor current/prior windows once; state exact dates/timezone. Default analytics 30 days; Store Pulse rolling 24 hours.
- Distinct sessions differ from event sums. Stage reach sums depth ≥ N; express checkout may skip intermediate events.
- Use measured CART_CURRENCY, not assumed domain currency. Never combine/rank currencies without verified conversion.
- AOV = completed-order revenue ÷ completed orders; median value differs. Product-associated whole carts are not product revenue.
- HAS_DISCOUNT is observed after a code is applied at checkout; comparisons have survivorship bias.
- Missing coverage is not measured zero or proof of a defect.

## Attribution and evidence

- URL/LANDING_URL/EXIT_URL strip parameters; page-visit REFERRING_URL preserves them. For gclid/gad_, search/order parameters, query REFERRING_URL CONTAINS parameter and UNIQ(SESSION_ID); label a lower bound. Bounces/stripped cross-origin referrers remain unmeasured; session landing referrers are not equivalent.
- Separate measured facts, correlation and causal hypotheses. ARL/revLost are directional projections, only for requested money impact; avoid recovery guarantees/double-counting.
- Retrieval does not authorize context/status/draft/lifecycle/job writes or messages. Resolve exact user-requested objects and use supported approvals; read state before retrying ambiguous writes. Tool failures do not authorize outbound feedback.
- Heatmaps/replays require actual supported MCP UI; numeric evidence/returned links remain useful if rendering fails. Never fabricate a heatmap or claim unverified rendering.

## In-chat report completion

Successful in-chat reports are CARD ONLY. Put every unique conclusion, priority, window, comparison scope, limitation and next-action hint inside the card before display; stop after the card, with no summary/recap prose before or after it. This does not suppress errors, unavailable-renderer fallbacks, prerequisite questions or separate user-requested action confirmations. Never claim a failed display succeeded. Follow shared card-quickstart.md; at most one render_ui call per response.

## Browser prerequisite, only for a requested browser step

Use the local [Edge connection/readiness guide](references/browser-readiness.md). Never prompt for browser setup during ordinary analytics/report display or repeat it when the browser is usable; explain the blocked step and continue nonbrowser work.

## Local report completion contract (21.1.13)

Use this skill’s [local display guide](references/card-quickstart.md), [runner](scripts/show_card.py), [builder](scripts/build_presentation.py), [console helper](scripts/console_links.py), [exact checker](scripts/cowork_card_check.py) and [comparison adapter](scripts/comparison_acquisition.py). This own-skill display route has no sibling filesystem dependency. Load querying-noibu-data by name for query/action guidance at its actual returned location; do not assume that loading markdown materializes its scripts. Comparison acquisition and actual current/prior metric rows follow the [local contract](references/comparison-acquisition.md). A host render acknowledgement is terminal CARD ONLY with no client-visibility gate; unknown delivery never means failed or permits whole-report replay.
