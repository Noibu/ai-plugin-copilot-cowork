# Top products, channel performance and paid ad performance

Read this when the user asks for one of these three blocks, alone or added to a snapshot, or when a scheduled run's prompt names them. Each block is one query set and one table.

Data source: Noibu only. Use the same window as the snapshot.

## Adding a block to the report data

Add a `tables` object to the report data from `references/snapshot.md`:

```json
"tables": {
  "channels": [{"channel": "", "sessions": 0, "engagement": 0, "conversion": 0, "rps": 0}],
  "paidPlatforms": [{"platform": "", "sessions": 0, "conversions": 0, "revenue": 0}],
  "topProducts": [{"name": "", "sessions": 0, "addToCartRate": 0}]
}
```

- Include only the blocks that were asked for.
- The card holds two tables. When all three are asked for, put two in `tables` and give the third in the summary: its top row and that row's numbers.
- Rates are percentages: 2.1 means 2.1%.
- Rows keep the order each block defines below.

## Top products

The 5 products with the most session traffic in the period, each with its add-to-cart rate.

| Column | Format | Notes |
|---|---|---|
| Product | Product title | |
| Sessions | Integer | Sessions that viewed the product page |
| Add to cart | Percentage | Add-to-cart sessions ÷ product-view sessions |

Product titles, view events and add-to-cart events come from Noibu's session data through the `VIEWED_PRODUCT_TITLES` and `ADDED_TO_CART_PRODUCT_TITLES` collections, so this works for any store Noibu monitors.

One query per period. Group by product title (`arrayJoin` on `VIEWED_PRODUCT_TITLES`), with two measures:

```json
{
  "queryInput": {
    "measures": [
      { "aggregate": { "measureAlias": "sessions", "measureFunc": "COUNT", "target": { "field": "SESSION_ID" } } },
      {
        "aggregate": {
          "measureAlias": "atc_sessions",
          "measureFunc": "COUNT",
          "target": { "field": "SESSION_ID" },
          "filters": [{ "fieldName": "ADDED_TO_CART_COUNT", "operator": "GREATER_THAN", "comparisonValues": ["0"] }]
        }
      }
    ],
    "groupBy": {
      "arrayJoin": { "arrayJoinCollection": "VIEWED_PRODUCT_TITLES" }
    },
    "orderBy": { "measureAlias": "sessions", "direction": "DESCENDING" },
    "limit": 5
  }
}
```

Compute `atcPct = atc_sessions / sessions * 100` per row.

**Site-wide add-to-cart rate.** The benchmark for each row is the site-wide rate over the same period:

`site_atc_pct = (sessions where ADDED_TO_CART_COUNT > 0) / (sessions where PRODUCT_VIEW_COUNT > 0) × 100`

The funnel queries already pull these counts. State the benchmark in the summary when a product sits well above or below it. Higher is better.

**Empty state.** If no product-view events were recorded in the window, leave the table out and say in the summary that there is no product data in this window and that product page tracking is worth checking.

## Channel performance

How each traffic channel is performing: sessions, engagement, conversion and revenue per session. Up to six rows, by sessions descending. All four metrics are higher-is-better.

| Column | Format | Notes |
|---|---|---|
| Channel | String | One of six buckets (mapping below) |
| Sessions | Integer | Channel volume |
| Engagement | Percentage | Compare against site-wide engagement |
| Conversion | Percentage | Compare against site-wide conversion |
| RPS | Currency | Compare against site-wide RPS |

**Channel mapping.** Noibu returns sessions grouped by `UTM_SOURCE` and `UTM_MEDIUM`. Bucket them into six rows after the query returns:

| Channel | Match rule |
|---|---|
| Direct | `utm_source` is empty/null |
| Paid | `utm_medium` ∈ (cpc, ppc, paid, paid_social, paidsocial) |
| Organic | `utm_medium` = organic OR referrer matches a search engine domain (google.com, bing.com, etc.) |
| Email | `utm_medium` = email OR `utm_source` matches known email tools (klaviyo, mailchimp, shopify_email, etc.) |
| Social | `utm_medium` = social OR `utm_source` matches social platforms (facebook, fb, instagram, ig, tiktok, twitter, etc.) |
| Referral | Anything else with a `utm_source` |

One query per period, grouped by `UTM_SOURCE` and `UTM_MEDIUM`:

```json
{
  "queryInput": {
    "measures": [
      { "aggregate": { "measureAlias": "sessions", "measureFunc": "COUNT", "target": { "field": "SESSION_ID" } } },
      { "predefined": { "measure": "BOUNCE_RATE", "measureAlias": "bounce_rate" } },
      { "predefined": { "measure": "CONVERSION_RATE", "measureAlias": "cvr" } },
      { "predefined": { "measure": "REVENUE_PER_SESSION", "measureAlias": "rps" } }
    ],
    "groupBy": { "fieldSegments": ["UTM_SOURCE", "UTM_MEDIUM"] },
    "orderBy": { "measureAlias": "sessions", "direction": "DESCENDING" },
    "limit": 50
  }
}
```

Aggregate rows that fall into the same bucket: sum sessions; weighted-average engagement, conversion and RPS by sessions.

**Site-wide reference.** The benchmark for each channel is the site-wide value of that metric for the same period, from the headline numbers. Name the channels that sit clearly above or below it in the summary.

**Empty state.** Leave out a channel with zero sessions. If every channel except Direct is empty, send the Direct row alone and say in the summary that there was no tagged traffic in this window.

**Direct** means sessions with no UTM source. It includes typed URLs, bookmarks, in-app browsers and links with stripped referrer data, so it may absorb some untagged paid or social traffic. Say so when the user asks, or when the report leans on the Direct number.

## Paid ad performance

Noibu's UTM-attributed traffic, conversions and revenue per paid ad platform: Google Ads, Facebook and Instagram. Sessions, conversions and revenue are all higher-is-better.

| Column | Format | Source |
|---|---|---|
| Platform | String | Platform name |
| Sessions | Integer | Noibu sessions tagged to the platform through UTM |
| Conversions | Integer | Noibu sessions where `CHECKOUT_COMPLETED = true` AND tagged to the platform |
| Revenue | Currency | Sum of `CHECKOUT_COMPLETE_TOTAL_VALUE` for those converted sessions |

**Always three rows**, one per platform, whether or not tagged traffic exists. A platform with no tagged traffic shows `0` / `0` / `0`; don't leave it out, because operators want to know when a paid channel isn't driving traffic.

One Noibu query per platform, filtered by that platform's UTM source patterns:

```json
{
  "queryInput": {
    "measures": [
      { "aggregate": { "measureAlias": "sessions", "measureFunc": "COUNT", "target": { "field": "SESSION_ID" } } },
      {
        "aggregate": {
          "measureAlias": "conversions",
          "measureFunc": "COUNT",
          "target": { "field": "SESSION_ID" },
          "filters": [{ "fieldName": "CHECKOUT_COMPLETED", "operator": "EQUALS", "comparisonValues": ["true"] }]
        }
      },
      {
        "aggregate": {
          "measureAlias": "revenue",
          "measureFunc": "SUM",
          "target": { "field": "CHECKOUT_COMPLETE_TOTAL_VALUE" }
        }
      }
    ],
    "filters": [
      { "fieldFilter": { "fieldName": "UTM_SOURCE", "operator": "IS_ANY_OF", "comparisonValues": ["<platform_utm_sources>"] } }
    ],
    "orderBy": { "measureAlias": "sessions", "direction": "DESCENDING" }
  }
}
```

Per-platform UTM source patterns:

- Google Ads: `["google", "googleads"]`
- Facebook: `["fb", "facebook", "meta"]`
- Instagram: `["ig", "instagram"]`

**Attribution.** These numbers come from Noibu's own attribution: last-touch through UTM, matched to actual orders. They diverge from each ad platform's native reporting because:

1. Ad platforms use post-impression and view-through attribution windows (sometimes 7+ days) that Noibu doesn't.
2. Ad platforms count modeled conversions, not just observed ones.
3. UTM tracking is imperfect (lost parameters, custom domains, and so on).

Whenever this table is in a report, say in one sentence of the summary that conversions are last-touch through UTM and will differ from each ad platform's own count.
