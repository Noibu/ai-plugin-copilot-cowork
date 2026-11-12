# The snapshot

Read this on every run. It holds the two query sets every snapshot needs, then the report data to write from them.

The snapshot is computed once and delivered: run the queries below, then write the numbers into the report data. The window is always the last 24 hours, compared to the 24 hours before. A scheduled run uses the window its prompt names, compared to the window of the same length immediately before.

Data source: Noibu only. Every metric here is computed from Noibu's session-level data; no commerce-platform connection is needed.

## Headline numbers

Five numbers, in this order: Sessions → Engagement → Conversion → AOV → RPS. All five are higher-is-better.

| Metric | Format | Comparison |
|---|---|---|
| Sessions | Integer | change against the previous period |
| Engagement | Percentage | difference between the two rates |
| Conversion | Percentage | difference between the two rates |
| AOV | Currency | change against the previous period |
| RPS | Currency | change against the previous period |

One call per period (current and previous), or one call with `compareToPrevious: true` if the response shape supports it cleanly. Both periods share the same measure shape:

```json
{
  "domainId": "<domain UUID>",
  "input": {
    "periodOptions": {
      "dateTimeRange": { "startTime": "<period_start>", "endTime": "<period_end>" }
    },
    "queryInput": {
      "measures": [
        { "aggregate": { "measureAlias": "sessions", "measureFunc": "COUNT", "target": { "field": "SESSION_ID" } } },
        { "predefined": { "measure": "BOUNCE_RATE", "measureAlias": "bounce_rate" } },
        { "predefined": { "measure": "CONVERSION_RATE", "measureAlias": "cvr" } },
        { "predefined": { "measure": "REVENUE_PER_SESSION", "measureAlias": "rps" } },
        { "aggregate": { "measureAlias": "aov", "measureFunc": "AVG", "target": { "field": "CHECKOUT_COMPLETE_TOTAL_VALUE" } } }
      ],
      "orderBy": { "measureAlias": "sessions", "direction": "DESCENDING" }
    }
  }
}
```

Compute `engagement = 1 - bounce_rate`.

**Empty state.** If a measure returns null or zero across a window with non-zero sessions, that value is not measured. If sessions itself is zero, every value is not measured and the summary says there was no traffic in this window.

## Purchase funnel

Five steps:

| Step | Definition | Source |
|---|---|---|
| 1 | Enter store | All sessions |
| 2 | View product | Sessions with `PRODUCT_VIEW_COUNT > 0` |
| 3 | Add to cart | Sessions with `CONVERSION_FUNNEL_DEPTH ≥ 1` |
| 4 | Start checkout | Sessions with `CONVERSION_FUNNEL_DEPTH ≥ 2` |
| 5 | Checkout complete | Sessions with `CONVERSION_FUNNEL_DEPTH = 4` |

The Add to cart step uses funnel depth, not the explicit add-to-cart event count. This is intentional: it keeps the funnel monotonic when sessions reach the cart stage through express-checkout flows.

Two queries per period (current and previous), in parallel.

**Query 1: funnel depth distribution.** Group sessions by `CONVERSION_FUNNEL_DEPTH`:

```json
{
  "queryInput": {
    "measures": [
      { "aggregate": { "measureAlias": "sessions", "measureFunc": "COUNT", "target": { "field": "SESSION_ID" } } }
    ],
    "groupBy": { "fieldSegments": ["CONVERSION_FUNNEL_DEPTH"] }
  }
}
```

Returns one row per depth bucket (null, 1, 2, 3, 4). Compute cumulative reach:

- Step 3 (Add to cart) = sum of rows where depth ≥ 1
- Step 4 (Start checkout) = sum of rows where depth ≥ 2
- Step 5 (Checkout complete) = row where depth = 4
- Step 1 (Enter store) = sum of all rows

**Query 2: product-view sessions.** Depth doesn't track product views as a step. Separate query:

```json
{
  "queryInput": {
    "measures": [
      {
        "aggregate": {
          "measureAlias": "pv_sessions",
          "measureFunc": "COUNT",
          "target": { "field": "SESSION_ID" },
          "filters": [{ "fieldName": "PRODUCT_VIEW_COUNT", "operator": "GREATER_THAN", "comparisonValues": ["0"] }]
        }
      }
    ]
  }
}
```

For each step, the share reaching it is `step_count / step_1_count × 100`, and its change is the current share minus the previous share.

**Data anomaly.** If a step's count is above zero while an earlier step's count is zero, that step is not measured.

## What the terms mean

Answer in prose when the user asks. None of this goes in the report data.

- **Engagement**: share of sessions that scrolled or clicked, derived from Noibu's bounce signal (engaged = not bounced).
- **AOV**: average order value, total revenue divided by orders.
- **RPS**: revenue per session, total revenue divided by sessions.
- **Add to cart** (funnel step): sessions that reached the cart stage by any means, including express-checkout flows (Apple Pay, Shop Pay, Buy Now) that skip the standard add-to-cart event.

## Report data

Write one JSON file in the working folder in this shape, then follow the Output section of SKILL.md. Supply values only.

```json
{
  "skill": "store-pulse",
  "store": {"name": "<domain name>", "id": "<domain UUID>"},
  "window": {"start": "<current window start>", "end": "<current window end>"},
  "currency": "<three-letter code>",
  "kpis": {
    "sessions": {"current": 0, "prior": 0},
    "engagement": {"current": 0, "prior": 0},
    "conversion": {"current": 0, "prior": 0},
    "aov": {"current": 0, "prior": 0},
    "rps": {"current": 0, "prior": 0}
  },
  "funnel": {
    "enterStore": {"current": 0, "prior": 0},
    "viewProduct": {"current": 0, "prior": 0},
    "addToCart": {"current": 0, "prior": 0},
    "startCheckout": {"current": 0, "prior": 0},
    "checkoutComplete": {"current": 0, "prior": 0}
  },
  "priorities": [
    {"title": "", "shortTitle": "", "evidence": ""}
  ],
  "noPrioritiesReason": ""
}
```

- Timestamps carry their timezone, e.g. `2026-11-01T21:00:00Z`.
- `prior` is the same measure for the previous period.
- **A rate is a percentage:** 0.25 means 0.25%. If the tool returns a fraction (0.0025), multiply by 100 first.
- Funnel values are session counts, not shares.
- A value that is not measured is `null`, never 0.
- `currency` is the store's order currency. If orders span more than one currency, set `aov` and `rps` to `null` and give each currency's figure in the summary.

### The summary

Plain prose, no bullets, no headings. Lead with the most notable thing: a drop, a surprise, a trend. Mix wins and concerns. Specific numbers, not an exhaustive list.

### Priorities

The priorities are the threads worth pulling on: up to 3 signals from the numbers just pulled (a drop, a surprise, a trend, an outlier), in the same order the summary mentions them. Fewer is fine.

| Field | What to write |
| --- | --- |
| `title` | The metric and the move ("Conversion fell on more traffic") |
| `shortTitle` | The same thread in 5 words or fewer ("Conversion fell") |
| `evidence` | One sentence with the number and its comparison ("Conversion was 0.25% against 0.29% in the previous 24 hours") |

Leave `affected` out; the snapshot doesn't rank by sessions affected. Text contains no ids, field names, tool names or formulas.

When nothing stands out, send an empty `priorities` list and one sentence in `noPrioritiesReason`, e.g. "No notable movement against the previous 24 hours."
