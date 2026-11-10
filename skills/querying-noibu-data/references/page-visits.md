# Page visits analytics

Read this when the user asks page-level questions: per-page traffic, time on page, web vitals (LCP/CLS/INP/FCP/TTFB/FID), landing and exit pages, visual errors, scroll depth, click and scroll behaviour, cohort behaviour for a specific URL, or a value that lives in a URL parameter.

## noibu_get_page_visits

Page-level analytics. One row per page visit. `orderBy` is REQUIRED (inside `queryInput`). Use for:

- Per-page traffic: URL visit counts, per-page engagement, bounce by URL
- User interaction, **per-page only**: `CLICKED_SELECTOR_COUNT` (total clicks), `CLICKED_SELECTORS` (CSS selectors), `CLICKED_TEXT` (text users click; the best per-page CTA, rage-click and friction signal). Site-wide aggregation across sessions is `noibu_search_sessions` with `CLICKED_TEXT`, not this tool.
- Page timing: `PAGE_VISIT_DURATION`, `PAGE_VISIT_START_TIME`, `PAGE_VISIT_END_TIME`
- Performance and web vitals: `LCP`, `CLS`, `INP`, `FCP`, `TTFB`, `FID`
- Visual UX defects: `VISUAL_ERROR_COUNT`, `VISUAL_ERROR_SNIPPETS` collection
- Engagement depth: `MAX_SCROLL_DEPTH`, `MAX_PAGE_HEIGHT`, `VIEWPORT_HEIGHT`, `VIEWPORT_WIDTH`
- Navigation role: `IS_LANDING_PAGE`, `IS_EXIT_PAGE` (booleans per page visit)
- Page context: `PAGE_TITLE`, `LANGUAGE`, `REFERRING_URL`, `PREV_URL`, `PREV_PAGE_GROUPS` collection
- Page-level conversion: `CHECKOUT_COMPLETED` per page; which specific pages are visited by converting sessions
- Cohort analysis (every page-visit row carries its session's context, so no join is needed): `SESSION_BOUNCED`, `SESSION_CONVERSION_FUNNEL_DEPTH`, `SESSION_UTM_*`, `SESSION_ORDER_ID`, `SESSION_CUSTOMER_ID`, `SESSION_WS_PATH`
- Segmentation by: URL, `PAGE_TITLE`, `LANGUAGE`, browser, OS, device type, country, region, checkout status, `IS_LANDING_PAGE`, `IS_EXIT_PAGE`, `PREV_URL`, `SESSION_BOUNCED`, `SESSION_CONVERSION_FUNNEL_DEPTH`, `SESSION_UTM_*`

| The user says | Tool |
|---|---|
| "how many clicks on /url", "top clicked on /url", "which CTA on /url" | `noibu_get_page_visits` |
| "% scroll to … on /url", "avg scroll depth on /url", "reach footer on /url" | `noibu_get_page_visits` |
| "show the clickmap for /url" | `noibu_visualize_page_visits` (`visualization.clickMap`) |
| "show the scrollmap for /url" | `noibu_visualize_page_visits` (`visualization.scrollMap`) |

Pair the numbers and the visual when both help.

## Web vitals: aggregate at p75, not the mean

When the user asks "how is my LCP", "what's my INP" or "which pages are slow", lead with `QUANTILE_75` of the relevant field. The 75th percentile is the canonical Core Web Vitals statistic: Google's CrUX defines the good, needs-improvement and poor thresholds at p75, and the Noibu console ranks pages by p75. Do NOT use `AVG`; outliers distort it. Use `MEDIAN` only if the user explicitly asks for the median, or `QUANTILES` when they want the full distribution.

Web vitals and `VISUAL_ERROR_COUNT` live here, not in the error tools. "Slow pages", "broken feeling" and "UX quality" questions route to this tool.

## Clickmaps and scrollmaps: noibu_visualize_page_visits

When the user wants to **see** click or scroll behaviour ("show me the clickmap", "scrollmap overlay"), call `noibu_visualize_page_visits`. It shows heatmap overlays on a snapshot of the page, in the conversation. It is visual only; there are no numeric counts in what it returns. Pair it with `noibu_get_page_visits` if numbers help too.

Set `visualization` to exactly one:

- `{ clickMap: { metric?: "CLICKS" | "CHECKOUT_CONVERSION" | "REVENUE_PER_SESSION" } }`: a click heatmap. `metric` preselects the view (default `CLICKS`):
  - `CLICKS`: general "what users click"
  - `CHECKOUT_CONVERSION`: elements correlated with conversion
  - `REVENUE_PER_SESSION`: elements correlated with revenue
- `{ scrollMap: {} }`: a scroll-depth heatmap

**Prefer `noibu_visualize_page_visits` over any generic visual.** Do not fall back to hand-drawn SVG or HTML, chart libraries, text heatmaps or screenshots; those lose the page context, the heatmap fidelity and the selectable metric. The tool's own view is the visualization.

## Recovering URL parameters

`URL`, `LANDING_URL` and `EXIT_URL` have their query string and fragment stripped when stored. `REFERRING_URL` does **not**: it is stored absolute and as received, so it is the only field that still carries URL parameters.

To recover a parameter, filter page visits on `REFERRING_URL CONTAINS "<param>"`, counting `UNIQ(SESSION_ID)`.

**Always run this on `noibu_get_page_visits`, never `noibu_search_sessions`.** A session's `REFERRING_URL` is only its landing referrer, which browsers strip of query parameters across origins. The parameters survive on *internal* referrers (the ad landing page pointing at the next page), which exist only per page visit. Routing this to the sessions tool undercounts by roughly 20x (779 against 15,642 sessions on one real domain).

- **Paid-ad traffic**: `gclid` or `gad_`. Google Ads auto-tagging adds these even when UTM tags are absent, so a domain with no `utm_source=google` can still be measured.
- **On-site search terms**: the site's search path, e.g. `search?q=` or `search?term=`. Discover the pattern first by grouping referrers that contain `?`.
- **Order IDs** and similar identifiers that appear in a confirmation URL.

Caveat: `REFERRING_URL` is populated on landing visits too, but browsers strip the query string on cross-origin navigation, so in practice parameters only survive on same-origin (internal) referrers: a visit that follows an earlier visit on the site. A bounced single-page session has a referrer but no recoverable parameters. Treat any count derived this way as a floor, and say so. Some values are masked (e.g. `email=******`). Grouping by `REFERRING_URL` returns raw URLs, so normalise case, `&page=N` and percent-encoding before ranking.
