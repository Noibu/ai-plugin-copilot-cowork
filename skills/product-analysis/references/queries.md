# Product analysis: query workflow

The four-step workflow for a full analysis. A quick answer runs one or two of the Step 1 or Step 4 queries. Field names are role-based; confirm each by its role before using it.

## Data limits

These apply to every query and every finding.

- **Conversion is only comparable within the same price tier.** High-ticket products and collections always convert at lower rates than low-ticket items; this is expected, not a signal. Never flag low conversion as underperformance without a same-tier benchmark. Use product and collection names to infer price tier; when no same-tier benchmark exists, rely on `ATC_LIFT_OPPORTUNITY` and funnel depth. This applies at every level: product, collection and product type. Price data is not available in Noibu session data.
- **Revenue per product is unavailable.** Order value is the total cart for the session, so every product in that session is credited the full value. Never label it "product revenue". Use purchase session count as the primary volume metric and median cart value as secondary.
- **Product title variants.** The same base product may appear as several rows (e.g. "WOMENS CLASSIC TEE - WT0200005" and "WOMEN'S CLASSIC TEE - WT0200005"). Flag near-duplicates; don't silently merge them.
- **URL fragmentation.** Always use URL CONTAINS with a SKU code or slug fragment in page visit queries.
- **Null funnel depth = viewed only.** Always label it "Viewed only", not blank or missing.

## Step 1: Broad overview (fire all four in one turn)

| Query | Tool | Group by | Measures | Limit | Order |
|---|---|---|---|---|---|
| Products by views | Session search | Viewed product titles | Sessions, CVR, revenue/session | 20 | Sessions ↓ |
| Product ATC opportunities | Page visits | URL (filter: CONTAINS '/products/') | Page views, ATC_LIFT_OPPORTUNITY, add-to-cart rate | 10 | ATC_LIFT_OPPORTUNITY ↓ |
| Collections by conversion | Session search | Viewed collection titles | Sessions, CVR, revenue/session | 15 | Sessions ↓ |
| Product types by conversion | Session search | Viewed product types | Sessions, CVR, revenue/session | 10 | Sessions ↓ |

> **Product ATC opportunities:** `ATC_LIFT_OPPORTUNITY` is a pre-computed score combining traffic volume and add-to-cart rate gap; higher = more opportunity. Use this ranking directly to identify low add-to-cart product candidates.

> **Products by purchase is not in Step 1.** Only run it in Step 3 if the data suggests cart abandonment (a product with good add-to-cart rates but weak purchase completion).

## Step 2: Cross-reference in post-processing

- **ATC opportunity** = use the `ATC_LIFT_OPPORTUNITY` ranking directly. Cross-check the top URLs against products-by-views to confirm they are high-traffic products.
- **Collection CVR benchmark** = compare collections against others in the same price tier, not the site-wide average. Two game-focused collections are valid benchmarks for each other; a premium hardware collection is not a valid benchmark for an accessories collection. Only flag low CVR when a same-tier benchmark exists.
- **Viewed-only %** = sessions with no funnel progression ÷ total view sessions. Flag products where 80%+ are viewed-only, but check the site-wide average first; high viewed-only is normal for low-intent browsing.
- **Site-wide CVR benchmark** = total purchases ÷ total sessions. Use only as context, never to flag high-ticket products, collections or types as underperforming. Price data is not in Noibu session data; infer price tier from product and collection names.

## Step 3: Pick 2–4 signals to dig into

| If you see this… | Follow-up |
|---|---|
| High ATC_LIFT_OPPORTUNITY product in top-20 views | Page deep-dive: scroll depth, time on page, click engagement, errors |
| Product with good ATC rate but weak purchase completion suspected | Run "Products by purchase" now (session search, purchased product titles, sessions + median cart value, limit 20, sessions ↓), then the funnel depth breakdown for that product |
| Collection CVR well below a comparable benchmark collection | Country breakdown: near-zero CVR across LATAM/non-primary = localization/checkout gap |
| Collection CVR below others in same category | Product mix drill-down within that collection |
| Product type significantly over/under | Break down by product title within the type |
| High-purchase product absent from views top | Journey path analysis: likely reached through search or direct links |
| Collections with non-English names at very low CVR | Check checkout/shipping availability in those markets |

## Step 4: Deeper follow-up queries

Run only the follow-ups the signals call for. Apply traffic thresholds now:

- >500K sessions/month: threshold ~0.1–0.2% of total
- 50K–500K: ~0.3–0.5%
- <50K: very low or skip

**Product page deep-dive** (high ATC_LIFT_OPPORTUNITY)

- Use the page visits tool. Filter URLs CONTAINS the product's SKU code or slug fragment (limit 15).
- Measures: page views, ATC_LIFT_OPPORTUNITY, add-to-cart rate, median duration, median max scroll depth ratio, median clicked selector count, total visual error count. Order by ATC_LIFT_OPPORTUNITY ↓.
- Use URL CONTAINS (not exact URL): product pages appear under `/products/`, `/collections/[name]/products/`, `/es/products/`, etc.
- Scroll depth: <0.20 = users not reaching the add-to-cart button; 0.20–0.40 with low clicks = content/pricing concern; high errors on one URL variant = possible JS error blocking add to cart.
- Compare add-to-cart rate across URL variants. A rate that's low on one variant but normal on others points to a URL-specific issue (broken localised page, collection-scoped page with missing add-to-cart).

**Funnel depth breakdown** (strong ATC, weak purchase)

- Session search tool. Filter to sessions where the target product title was viewed. Group by the funnel depth field. Measure session count. Order ↓.
- Depth values: null = viewed only, 1 = added to cart, 2 = checkout started, 3 = payment submitted, 4 = completed.
- Lead with "Viewed only %" = null sessions ÷ total.
- Depth-4 outnumbering depth-2/3 is normal (Apple Pay and Shop Pay skip checkout pages; not a data error).

**Country breakdown** (collection CVR well below benchmark)

- Session search tool. Filter to sessions where the collection title was viewed. Group by country code (limit 20). Measure sessions, CVR, revenue/session. Order ↓.
- Near-zero CVR across several LATAM/non-English markets = ops/localization gap, not a merchandising problem.

**Product mix within a collection** (collection underperforms, country breakdown is clean)

- Session search tool. Filter to collection title viewed. Group by viewed product titles (array join, limit 25). Measure sessions, CVR. Order ↓.

**Journey paths** (high views, high bounce)

- User journey tool. Anchor on the product slug fragment, loose mode. Both directions, max depth 6.
