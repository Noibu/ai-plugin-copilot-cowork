---
name: querying-noibu-data
description: >
    Required reference for calling `noibu_*` tools — field and measure semantics,
    query constraints (the `orderBy` requirement, row caps,
    unique-measure rule), the call-metadata argument convention (`rationale`,
    `skill`), and domain
    resolution. Also covers parsing of pasted `console.noibu.com` URLs.
    Loads alongside topical Noibu skills
    (e.g., `checkout-analysis`, `tech-diagnosis`), not instead of them — they
    own routing for their respective domains.
---

# Querying Noibu data

Noibu is an ecommerce analytics platform that tracks sessions, page visits and errors to help teams improve site performance and conversion. Its datasets are exposed as `noibu_*` tools. Use this guide to pick the right tool for the question, then open the matching reference for field-level detail.

## When to use it

Use it whenever a `noibu_*` tool is about to be called: to choose the tool, name fields and measures correctly, and respect the query limits. It also covers a pasted `console.noibu.com` link.

It loads alongside the topical skills (`checkout-analysis`, `product-analysis`, `segment-analysis`, `store-pulse`, `tech-diagnosis`), not in their place. They own the workflow for their subject; this owns how the tools are called.

## Guardrails

- If Noibu tools aren't available, ask the user in one line to finish the Connect prompt, then stop. No partial numbers.
- Reading data never permits a write. Never report a write as done without the tool's result.
- If a file this skill needs is missing, say which in one line and stop.
- **`orderBy` is required** on both query tools. It lives inside `queryInput`, alongside `measures`, `groupBy`, `filters` and `limit`. Without it, the row cap returns arbitrary rows and aggregates are silently wrong.
- **Never report "no data" early.** Don't tell the user a metric is zero, missing or "not tracked" until both checks below are done. Prefer "at least N, and here is why it undercounts" over "no data".
  1. **The signal may be in a URL parameter.** `URL`, `LANDING_URL` and `EXIT_URL` are stripped of their query string when stored, but `REFERRING_URL` is not. Ad clicks (`gclid`, `gad_`), on-site search terms (`search?q=`) and order IDs survive there. See "Recovering URL parameters" in `references/page-visits.md`.
  2. **The data may be on a sibling domain.** Call `noibu_get_company` to list the company's other domains. Storefront and checkout are frequently separate Noibu domains, and completed orders often exist only on the checkout domain, so a storefront-only query makes conversion look broken when it is not. Sessions do not stitch across domains.
- **Lead with analytics.** Errors, bugs and crashes are investigated only when the user explicitly asks. They are not the default answer to "what should I fix".
- **Never build a console link.** `references/console-urls.md` has the policy.

## Before you start

Run once: `ls references/sessions.md references/page-visits.md references/journeys-and-replay.md references/errors.md references/ab-tests.md references/console-urls.md`

**Resolve the domain.**

1. If the user gave a domain UUID, use it directly. Skip `noibu_get_domain` and `noibu_list_domains`.
2. If they gave a domain name, call `noibu_get_domain`. It looks up one domain by exact name. It accepts bare names or full URLs and tolerates `www.`, scheme, path, query, fragment and a trailing dot. Typos do not resolve: on a miss it errors with `NotFound` and gives up to 3 nearest permitted names in `errors[0].extensions.suggestions`. Show those to the user as given and let them pick; never substitute one silently.
3. If there is no match, no suggestions, or no name at all, call `noibu_list_domains` and let the user choose.

**Fill in the call metadata on every `noibu_*` call.**

- `rationale`: one sentence on why the tool is being called right now, phrased from the user's perspective. Noibu engineers cannot see the conversation; the rationale is the only signal of what people are trying to do, so make it specific to the question.
  - Good: `rationale: "User asked which checkout CTAs convert best on mobile, fetching clickmap for /checkout"`
  - Good: `rationale: "Following up on the cart-abandonment spike: pulling page visits to find where users drop off"`
  - Bad: `rationale: "calling tool"`, `rationale: "to get data"`
- `skill`: the name the topical skill states (e.g. `"checkout-analysis"`). If no topical skill is running, use `"querying-noibu-data"`.
- `skillStep`: a short label for the step this call serves (`"funnel"`, `"Q3"`, `"follow-up"`).

## Workflow

Three tools cover almost every analytics question. Prefer them in this order:

1. **`noibu_get_domain`**: resolve a domain name to its UUID.
2. **`noibu_search_sessions`**: session-level aggregates (conversion rate, revenue, cohorts, traffic sources, products). One row per session.
3. **`noibu_get_page_visits`**: page-level aggregates. One row per page visit.

Pick the route from the question, then open exactly one reference.

| The question is about… | Tool | Open |
|---|---|---|
| Conversion rate, revenue by X, share of sessions that did Y, AOV, bounce, search, products, trends over time | `noibu_search_sessions` | `references/sessions.md` |
| Traffic source, channel or campaign ("how much traffic from Google Ads", "which channel converts best") | `noibu_search_sessions` grouped by `UTM_SOURCE` / `UTM_MEDIUM`. If the channel named has no UTM rows, don't report it absent: paid clicks usually carry `gclid` / `gad_`. Switch to `noibu_get_page_visits` | `references/sessions.md`, then `references/page-visits.md` |
| How many sessions reached cart, checkout or payment; the conversion funnel, shown or counted | `noibu_search_sessions` | `references/sessions.md` |
| Which pages are slow, broken or busiest; web vitals; time on page; landing and exit pages; one-hop "what page comes before or after /X"; clicks or scroll on a URL; a clickmap or scrollmap | `noibu_get_page_visits`, `noibu_visualize_page_visits` | `references/page-visits.md` |
| Page-category journey shapes across many sessions, or an explicit request to watch a session replay | `noibu_list_page_group_journeys`, `noibu_show_session_replay` | `references/journeys-and-replay.md` |
| Errors, bugs, crashes, "what's the priority": only when asked explicitly | Error tools | `references/errors.md` |
| Releases, deploys, theme updates, campaign launches, "what changed on <date>"; also as a before-and-after anchor for an error spike or conversion drop | `noibu_list_releases` | none |
| A/B tests and experiments | `noibu_list_ab_tests`, `noibu_get_ab_test_results` | `references/ab-tests.md` |
| A pasted `console.noibu.com` link | Depends on the link | `references/console-urls.md` |

**No URL in a click question** ("top CTAs", "what users click most"): `noibu_search_sessions` with `CLICKED_TEXT`. Scroll has no site-wide equivalent; stay on `noibu_get_page_visits`. If the scope is unclear, ask.

### Sessions or page visits

Use `noibu_search_sessions` when the question is about the session as a whole:

- "What's our checkout completion rate?" → `CHECKOUT_COMPLETED`, `SESSION_ID`
- "Which products are added to cart most?" → `ADDED_TO_CART_PRODUCT_TITLES` collection
- "Sessions by traffic source?" → `UTM_SOURCE`, `UTM_MEDIUM`
- "Average order value by country?" → `CHECKOUT_COMPLETE_TOTAL_VALUE`, `COUNTRY_CODE`
- "Which discount codes are used most?" → `CHECKOUT_COMPLETE_DISCOUNT_CODES_APPLIED` collection
- "What are people searching for?" → `SEARCH_QUERIES` collection
- "How many people bounce?" → `BOUNCED`
- "What CTAs are users clicking most across the site?" → `CLICKED_TEXT` collection, `GROUP_ARRAY_10`
- "What's the user's navigation path in this session?" → `PAGE_VISIT_URLS` collection, ordered

Use `noibu_get_page_visits` when the question is about individual pages, performance, UX, or what a cohort did:

- "Which pages get the most traffic?" → `URL`, COUNT of `PAGE_VISIT_ID`
- "Average time on product pages?" → `PAGE_VISIT_DURATION`, filtered or segmented by URL
- "Which landing pages lead to conversion?" → `IS_LANDING_PAGE=true`, `CHECKOUT_COMPLETED`, segmented by URL
- "Which pages are slow?" → **`QUANTILE_75`** of LCP / INP / CLS per URL
- "Where are users abandoning?" → `IS_EXIT_PAGE=true`, segmented by URL
- "What pages do bouncers see?" → `SESSION_BOUNCED=true`, segmented by URL
- "Cohort behaviour for sessions with UTM_SOURCE=x" → filtered by `SESSION_UTM_SOURCE`. Session context is carried on each page visit; no join is needed

Web vitals (LCP, CLS, INP, FCP, TTFB, FID) and `VISUAL_ERROR_COUNT` live on page visits. They are the primary lens for "slow", "broken feeling" and UX-quality questions. Do not route these to the error tools.

### Analytics before errors

Most users ask business questions about their site, not technical questions about errors.

- "What are my top opportunities?" → Start with session and page-visit analytics: conversion trends, cart abandonment, traffic source performance, page engagement, device and browser breakdowns. Errors are one kind of opportunity, not the only or primary kind.
- "Why is checkout broken?" → Could be analytics or technical. Start with analytics to understand the scope (all users or one segment? when did it start?). Then ask whether to dig into specific errors or keep exploring the data.
- "How is my site performing?" → Analytics first.
- "What errors are happening?" → Explicitly technical. Open `references/errors.md`.

Analytics tools find patterns and frame the problem; error tools explain root causes. When in doubt, ask the user which they want.

## Query constraints

- Row caps: `noibu_search_sessions` returns up to 100 rows; `noibu_get_page_visits` up to 1,500.
- Each measure must be unique by (fieldName, measureFunc).
- Time series resolutions are MINUTE, HOUR, DAY and WEEK. Pick by range: last 24 hours → HOUR, last 7 days → DAY, last 90 days → WEEK.
- `HAS_DISCOUNT` is only populated once a discount code is applied at checkout. Comparing `HAS_DISCOUNT=true` with `false` carries survivorship bias.

## Reporting a blocker

`noibu_send_feedback` records a structured entry for the Noibu team, tagged with the user's identity, so failures in real conversations can be investigated.

Use it when you don't know how to answer the question with the available tools, a Noibu tool returned an error you can't recover from, the tool descriptions seem ambiguous, wrong or incomplete, or you are going in circles.

Inputs: `category` (`confused` or `blocked`), `intent` (what you were trying to do and why, the tool or step you reached for, and where you got stuck), `message` (the issue itself), and optional `context` (what the user was trying to do). Always fill in `intent`. Calling this tool does not replace answering the user; still do your best to help them.
