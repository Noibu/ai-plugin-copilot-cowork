# Writing the report data

Read this after Steps 1–4 have run, when the full analysis is ready to deliver. Write one JSON file in the working folder in the shape below, then follow the Output section of SKILL.md.

Supply values only. Leave a key out when its data isn't populated for this store. Use `null` only for a value that should have been measured and wasn't; never 0 in its place.

## Shape

```json
{
  "skill": "checkout-analysis",
  "store": {"name": "<domain name>", "id": "<domain UUID>"},
  "window": {"start": "<current window start>", "end": "<current window end>"},
  "currency": "<three-letter code>",
  "kpis": {
    "sessions": 0,
    "addedToCartRate": 0,
    "checkoutCompletion": {"current": 0, "prior": 0},
    "mobileConversion": {"current": 0, "prior": 0},
    "desktopConversion": {"current": 0, "prior": 0},
    "checkoutErrors": 0,
    "medianOrder": 0,
    "discounted": 0,
    "itemsPerOrder": 0
  },
  "funnel": {
    "addedToCart": {"current": 0, "prior": 0},
    "startedCheckout": {"current": 0, "prior": 0},
    "paymentSubmitted": {"current": 0, "prior": 0},
    "completedOrder": {"current": 0, "prior": 0}
  },
  "tables": {
    "abandonment": [{"source": "<bucket name>", "sessions": 0, "cartValue": 0}],
    "paymentMethods": [{"method": "<name>", "orders": 0}],
    "deliveryMethods": [{"method": "<name>", "orders": 0}]
  },
  "priorities": [
    {"title": "", "shortTitle": "", "evidence": "", "affected": 0, "link": "<issue URL>"}
  ],
  "noPrioritiesReason": "",
  "links": ["<console URL>"]
}
```

- Timestamps carry their timezone, e.g. `2026-10-03T00:00:00Z`.
- A rate is a percentage: 54.2 means 54.2%.
- `prior` is the same measure for the previous window. Leave `prior` out when there is no previous window to compare.

## Where each value comes from

| Field | Source |
| --- | --- |
| `kpis.sessions` | Total sessions in the window (Q1, all depths) |
| `kpis.addedToCartRate` | depth-1+ ÷ total |
| `kpis.checkoutCompletion` | depth-4 ÷ depth-2+, current and previous |
| `kpis.mobileConversion`, `kpis.desktopConversion` | Q6 conversion rate per device, current and previous |
| `kpis.checkoutErrors` | Count of priority errors on checkout pages (Q5) |
| `kpis.medianOrder` | Median completed order value (Q2) |
| `kpis.discounted` | Discount rate among checkout-entering sessions, from the completion-time discount value (Q2) |
| `kpis.itemsPerOrder` | Median product quantity per order (Q2) |
| `funnel.addedToCart` | Sessions at depth-1+ |
| `funnel.startedCheckout` | Sessions at depth-2+ |
| `funnel.paymentSubmitted` | Sessions at depth-3+ |
| `funnel.completedOrder` | Sessions at depth-4 |
| `tables.abandonment` | Q1b buckets with a non-zero count, by session count descending, at most 5. `source` is the bucket name exactly as Q1b lists it; `cartValue` is the bucket's summed cart value |
| `tables.paymentMethods` | Q3 rows, by count descending; `orders` is the completed-checkout count |
| `tables.deliveryMethods` | Q4 rows, same |

- **Uninstrumented steps.** When the steps between cart and completion aren't instrumented, leave `startedCheckout` and `paymentSubmitted` out of `funnel` and leave `kpis.checkoutCompletion` out. State the cart-to-order rate (depth-4 ÷ depth-1+) in the summary.
- **Payment and delivery.** If Q3 or Q4 returned any rows, include that table. Leave a table out only when its query came back empty.
- **Order profile.** Include only the populated ones of `medianOrder`, `discounted` and `itemsPerOrder`.
- **Currency.** Use the store's order currency. If amounts span more than one currency, leave `medianOrder` and `cartValue` out and give each currency's figure in the summary. Never add or rank amounts across currencies.
- **Caveats.** A caveat that changes how a number should be read (a sale period inside the window, express checkout lifting completions above payment submissions) goes in the summary. Payment and delivery counts cover completed orders only; say so in the summary when the report leans on them.

## Priorities

Up to 3, ranked strictly by sessions affected, descending. Fewer is fine. Rank by sessions affected, not by how obvious the signal is.

| Field | What to write |
| --- | --- |
| `title` | The signal headline. For a change: name the metric and that it moved ("Checkout completion fell on mobile"), not the absolute level. For a qualified error: a plain-English description of the error |
| `shortTitle` | The same signal in 5 words or fewer ("Mobile checkout completion drop") |
| `evidence` | One sentence. For a change: the segment, the current value and the previous value with its window ("Mobile completion dropped to 1.4% from 1.9% against the previous 30 days"). For an error: occurrences, when it was last seen, and where it fires. No cause, no recommended action |
| `affected` | Sessions affected, from the table below |
| `link` | For a qualified error only: the issue URL the Noibu tool returned. Leave out otherwise |

**Sessions affected.** For a change it is the **incremental** sessions lost to the regression, `(previous rate − current rate) × current volume at that stage`, not the absolute volume at the step:

| Finding type | Sessions affected = |
| --- | --- |
| Funnel-step regression | (previous step rate − current) × sessions reaching the stage before |
| Device regression | (previous device conversion − current) × that device's sessions |
| Market regression | (previous market conversion − current) × that market's sessions |
| Payment-method regression | (previous method completion − current) × that method's submitted sessions |
| Cart-exit regression | extra add-to-cart sessions not reaching checkout against the previous window |
| Sub-step abandonment bucket regression (Q1b) | (previous bucket share − current) × current depth-2+ sessions |
| Qualified active error | session impact count from the errors tool |

Rules:

- **A change-based priority must be a regression against the previous window.** Never flag a metric for its absolute level or a gap against another segment or the site average. The only non-regression priority is a qualified active error (Q5).
- **Markets are relative.** A chronically low or 0% market that didn't change is not a priority.
- **No discount-value priority** unless the discount rate or discounted conversion regressed.
- Every priority names a specific funnel step, device, payment method, market or error. No dollar figures; sessions affected is the only impact measure.
- Never create a priority about missing data or coverage, and don't pad with weak signals.
- Text contains no ids, field names, tool names or formulas. Write a date as "Oct 27, 5:44 pm (UTC)".

**No priorities.** When no regression clears the threshold and no error qualifies, send an empty `priorities` list and say why in `noPrioritiesReason`, in one sentence:

- Nothing regressed: "No checkout regressions against the previous 30 days and no active fixable errors; checkout is holding steady."
- No previous window to compare: "No previous 30 days to compare against, so there are no change-based signals this run."

## Links

`links` takes up to two `console.noibu.com` URLs that a Noibu tool returned in this run, such as the issue URL of a qualified error. Never build a URL. No URL, no link.
