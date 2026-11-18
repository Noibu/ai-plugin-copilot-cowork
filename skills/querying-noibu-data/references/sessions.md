# Sessions analytics

Read this when the user asks session-level questions: conversion rate, revenue, AOV, traffic sources, bounce rate, products viewed or purchased, search behaviour, discount usage, trends over time, or the conversion funnel.

## noibu_search_sessions

Session-level analytics. One row per session. `orderBy` is REQUIRED (inside `queryInput`). Use for:

- Traffic analysis: sessions by UTM source/medium/campaign, referring URL, landing/exit URL
- Conversion analysis: checkout completion rates, cart event counts, payment submissions
- Revenue: order values (subtotal, shipping, tax, discounts), cart values, discount code usage
- Product performance: which products were viewed, added to cart, removed, purchased (by SKU, title, type, vendor, variant)
- Collection and search behaviour: collection views, search queries, search counts
- Customer behaviour: bounce rate, session duration, page view count
- Journey reconstruction: `PAGE_VISIT_URLS` collection (time-ordered, duplicates preserved; use for "show the user's navigation path"). Different from `VISITED_URLS` (deduped).
- CTA / click analysis: `CLICKED_TEXT` collection (the actual button or link text users clicked; the best signal for CTA effectiveness, friction detection and rage-click patterns).
- Custom attributes: `CUSTOM_ATTRIBUTE_NAMES` / `CUSTOM_ATTRIBUTE_VALUES` / `CUSTOM_ATTRIBUTE_TUPLES` collections for customer-specific tags.
- Segmentation by: browser, OS, device type, country, region, UTM params, checkout status, discount usage, cart currency

## noibu_get_session_trends

The same data as `noibu_search_sessions`, bucketed over time. Use when the user asks about trends, changes, or "how has X changed over Y period". Resolution options: MINUTE, HOUR, DAY, WEEK. Pick by range: last 24 hours → HOUR, last 7 days → DAY, last 90 days → WEEK.

## Conversion and revenue analysis

For conversion analysis, use the concrete event fields:

- `CHECKOUT_COMPLETED` (boolean): did the session complete a purchase?
- `ADDED_TO_CART_COUNT`: how many add-to-cart events occurred
- `CHECKOUT_STARTED_COUNT`: how many times checkout was initiated
- `PAYMENT_INFO_SUBMITTED_COUNT`: how many payment submissions
- `CHECKOUT_COMPLETE_COUNT`: completed checkouts (a count, not a boolean)

For revenue:

- `CHECKOUT_COMPLETE_TOTAL_VALUE`: final order value (includes tax, discounts)
- `CHECKOUT_COMPLETE_SUBTOTAL_VALUE`: order value before shipping and tax
- `CHECKOUT_COMPLETE_SHIPPING_VALUE`, `CHECKOUT_COMPLETE_TAX_VALUE`, `CHECKOUT_COMPLETE_DISCOUNT_VALUE`: breakdowns
- Prefer the `CHECKOUT_COMPLETE_` fields over the `CHECKOUT_START_` fields for accurate totals
- `ADDED_TO_CART_TOTAL_VALUE`: total value of items added to cart
- `MAX_CART_VALUE`: peak cart value during the session

For computed metrics, use measures with the DIVIDE operator:

- Checkout rate = COUNT(`CHECKOUT_COMPLETED`=true) / COUNT(`SESSION_ID`)
- Average order value = SUM(`CHECKOUT_COMPLETE_TOTAL_VALUE`) / COUNT(`CHECKOUT_COMPLETED`=true)

Prefer MEDIAN over AVG for monetary values (robust to outliers).

## The conversion funnel

When the user asks how many sessions reached each step, or asks to see the funnel ("show me the checkout funnel", "funnel for the last 7 days against the previous 7"):

1. Fetch the per-step session counts with `noibu_search_sessions`.
2. Answer with one table: step, sessions, share of the first step, and drop from the step before.
3. When a comparison period was asked for, add its change per step. For the first step that is the change in its session count. For every later step it is the difference between the two periods' shares of the first step, in percentage points (pp), not a relative %.

Analytical funnel questions ("where do users drop off", "abandonment by step") are page-level; answer them from `noibu_get_page_visits` with `references/page-visits.md`.
