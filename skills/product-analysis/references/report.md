# Writing the report data

Read this after the four-step workflow has run, when the full analysis is ready to deliver. Write one JSON file in the working folder in the shape below, then follow the Output section of SKILL.md.

Supply values only. Leave a key out when its data isn't populated for this store. Use `null` only for a value that should have been measured and wasn't; never 0 in its place.

## Shape

```json
{
  "skill": "product-analysis",
  "store": {"name": "<domain name>", "id": "<domain UUID>"},
  "window": {"start": "<window start>", "end": "<window end>"},
  "currency": "<three-letter code>",
  "kpis": {
    "sessions": 0,
    "conversionRate": 0,
    "medianOrder": 0
  },
  "funnel": {
    "viewedProduct": 0,
    "addedToCart": 0,
    "completedOrder": 0
  },
  "tables": {
    "products": [{"name": "", "sessions": 0, "addToCartRate": 0, "conversionRate": 0}],
    "collections": [{"name": "", "sessions": 0, "conversionRate": 0, "revenuePerSession": 0}],
    "productTypes": [{"name": "", "sessions": 0, "conversionRate": 0, "revenuePerSession": 0}]
  },
  "priorities": [
    {"signal": "", "title": "", "shortTitle": "", "evidence": "", "affected": 0}
  ],
  "noPrioritiesReason": ""
}
```

- Timestamps carry their timezone, e.g. `2026-10-03T00:00:00Z`.
- A rate is a percentage: 2.4 means 2.4%. If the tool returns a fraction (0.024), multiply by 100 first.
- Funnel values are session counts, not shares.

## Where each value comes from

| Field | Source |
| --- | --- |
| `kpis.sessions` | Total sessions in the window |
| `kpis.conversionRate` | Site-wide conversion rate: total purchases ÷ total sessions |
| `kpis.medianOrder` | Median completed order value |
| `funnel.viewedProduct` | Sessions that viewed any product |
| `funnel.addedToCart` | Of those, sessions that added to cart |
| `funnel.completedOrder` | Of those, sessions that completed an order |
| `tables.products` | Top 5 of products by views, by sessions descending: sessions, add-to-cart rate, conversion rate |
| `tables.collections` | Top 5 of collections, by sessions descending: sessions, conversion rate, revenue per session |
| `tables.productTypes` | Top 5 of product types, by sessions descending: sessions, conversion rate, revenue per session |

- **The funnel is product-scoped, not site-wide.** Its first step is sessions that viewed any product. Never use all sessions as a funnel step.
- **Product types.** Leave `productTypes` out when every type's conversion rate is within 20% of the others.
- **Add-to-cart rate** for a product row is that product's own rate. Use `null` when it wasn't measured for that product.
- **Names.** A product, collection or type name goes in as the store shows it. Where near-duplicate product titles appear as separate rows, keep them separate and say so in the summary.
- **Revenue per session** is the session's whole cart credited to every product viewed, so it is not product revenue. Say so in the summary when the report leans on it.
- **Currency.** Use the store's order currency. If amounts span more than one currency, leave `medianOrder` and `revenuePerSession` out and give each currency's figure in the summary.

## Priorities

List every signal picked in Step 3 (2–4), ranked by sessions affected, descending. The card draws the first three; the next-step question offers all of them.

| Field | What to write |
| --- | --- |
| `signal` | One of: `Low add-to-cart rate`, `Cart abandonment`, `Low collection conversion`, `Underperforming product type`, `High bounce rate` |
| `title` | The product, collection or product type name |
| `shortTitle` | The signal and the name in 5 words or fewer ("Cable bracelet low add-to-cart") |
| `evidence` | One sentence: the key number and why it matters ("It adds to cart at 2.1% against 6.1% across the store on 5,200 product views") |
| `affected` | Sessions affected, from the list below |

**Sessions affected** is the sessions most directly impacted:

- Low add-to-cart rate → view sessions for that product
- Cart abandonment → add-to-cart sessions for that product
- Low collection conversion → sessions that viewed the collection
- Underperforming product type → sessions that viewed that type
- High bounce rate → view sessions for that product

Rules:

- A priority carries the name, one sentence and its sessions affected. No tables, extra metrics or bullets; all supporting evidence comes out when the user investigates.
- A low conversion rate is a priority only against a same-tier benchmark (`references/queries.md`, "Data limits").
- Text contains no ids, field names, tool names or formulas.

**No priorities.** When no signal stands out, send an empty `priorities` list and one sentence in `noPrioritiesReason` saying what the data shows and why nothing stands out, e.g. "Conversion and add-to-cart rates are consistent across top products and collections, with no outliers above the traffic thresholds for this store size."
