# Live-site read (two batches, DOM records, goal-scoped)

Purpose: confirm or kill every data-derived candidate before it reaches the output. For each candidate the read answers three things: (1) does the variant I want to test already exist? (2) is the problem actually a defect rather than a test? (3) what does this surface really contain, so the "Why this test" and Dev notes lines are accurate and the build half can find the code from recorded selectors?

The read is done by the main run and never owns a round trip of its own: **Batch A** (homepage and policies) goes in the Block 3 message next to the Batch 1 queries, and **Batch B** (the goal's surfaces, at the URLs Batch 1 named) in the Block 4 message next to the Batch 2 queries. Each page is opened once in the person's Edge (`references/finder/browser.md`) and read into a small JSON record; nothing is explored by scrolling, and the screenshot is your look, not a file.

The read runs in the person's desktop Edge window. Never make mobile-layout claims from it; use the scroll/click query data for those, marked inferred.

## Reading one page

1. `navigate_to` the URL (its own call; the homepage is already open from `create_tab`).
2. One call: `wait` 3 → `get_dom` → `get_screenshot`.
3. **Saved DOM file** (the result says "Full output saved to: <path>"): `python <skill-dir>/scripts/dom_facts.py <path> --surface <surface> --url <path on the store> --into <run folder>/walkthrough.json`. Its JSON is the record. When it reports `"formatRecognized": false`, the saved format was not HTML markup: keep its text heuristics and do the checklist below from the inline DOM and the screenshot.
4. **No saved file** (the DOM fit inline, or the host has no file storage): read the inline DOM and the screenshot against the checklist and write the record yourself under the same key, with any selector marked `"source": "inline-dom"`. A cut-off inline DOM (over 48 KB, no file) is noted in `meta.couldNotComplete` for that surface.
5. From the screenshot, add a `look` entry: what is above the fold, whether the element a candidate depends on is visible, any banner or popup covering content.

The parser never reads input values, never claims visibility, and never runs anything from the page. A missing element is `null` or `"absent"` — a parser miss as often as a missing feature.

## The surfaces (`dom_facts.py --surface …`) and the checklist

| Surface | Run on | Records (the checklist when there is no saved file) |
| --- | --- | --- |
| `home` | homepage | platform (Shopify theme signal, BigCommerce, Magento, SFCC, WooCommerce), storefront (country, currency, page language), `testingTools`, announcement bar text verbatim, hero heading, search present, footer policy links, cart URL, product and collection links (fallback product when #5 names no product page) |
| `policy` | each same-origin shipping / returns / FAQ page from the footer (Shopify: `/policies/shipping-policy`, `/policies/refund-policy` first; at most three) | `notFound`, and the sentences stating thresholds, fees, delivery times, return windows and conditions, verbatim; off-site help centers are listed, not read |
| `pdp` | the top product page | title, price, the add-to-cart control (text, disabled), in stock, variant selector, shipping/returns copy near the buy box verbatim (or `"absent"`), express pay, review/BNPL widgets, selectors + blocks for the form, CTA, price, title |
| `collection` | the top collection page | title, product cards (count, sample), **quick add on cards** (if it exists, any "add quick add" candidate dies), sort options, filters, product-count text, card selector + block |
| `cart` | the cart page with the one added item | line rows, free-shipping progress and shipping messages verbatim, promo field, checkout CTA, express pay, upsells, the remove control, selectors |
| `checkout_entry` | the first checkout step (**checkout-completes goal only, observation only**) | guest vs login gate, password field present, field count and labels (never values), express pay. Enters nothing |

## Which surfaces each goal reads

| Goal | Batch A | Batch B surfaces (URLs from Batch 1 #5) |
| --- | --- | --- |
| Add to cart rate | home, policy | top collection → `collection`; top product page → `pdp` |
| Product page views, Collection page views | home, policy | top collection → `collection` (add the top product page → `pdp` for a product-views goal when #5 shows product pages as exits) |
| Bounce rate on page (once live) | home, policy | the top landing page in the goal's group → `pdp` / `collection`; note what is above the fold on first load (popups, consent banner, hero, the first link to another page) from the screenshot. No cart path |
| Viewed page: \<URL\> | home, policy | that URL with the fitting surface (`pdp`, `collection`, else one targeted look for the element the goal is about) |
| Checkout starts | home, policy | top product page → `pdp` → cart round trip → `cart` |
| Checkout completes | home, policy | the checkout-starts path plus the checkout step → `checkout_entry`, then back to the cart to remove the line |
| All goals | home, policy | top collection → `collection`; top product page → `pdp` → cart round trip → `cart` |

The product page is the top `/products/` URL by visits in #5 (take mobile's when the device lists differ: it is most of the traffic); with none, the homepage record's first product link. The collection page is the top `/collections/` (or the platform's listing path) URL in #5, never the "shop all" link. The cart URL comes from the homepage record (`/cart` when absent).

## Cart round trip (cart and checkout goals, "all goals")

Edge is the person's own browser, so their cart may already hold items, and those are never touched.

1. **Before adding**, read the cart (`navigate_to` the cart URL, `get_dom`) and record its lines in `meta.cartBefore` (titles and quantities only).
2. On the product page, pick an in-stock option when the control is gated ("Select size") with `dom_click` on an available option, then `dom_click` the page's own add-to-cart control (node id from `get_dom`; `intention: other`, reason "Add one item to the cart to read the cart, then remove it"). `wait` 2, re-read: a drawer that opened is read as the `cart` surface.
3. `navigate_to` the cart URL; read it as `cart` (one more line than before, or one more unit of an existing line).
4. Checkout-completes goal only: `dom_click` the checkout control once, `wait` 4, read the first step as `checkout_entry` — observation only; enter nothing, click nothing else; if it shows only a login or nothing without data entry, say so and rely on the funnel numbers. Then `navigate_to` the cart URL.
5. **Remove only the added line**: `dom_click` that line's remove control (or reduce its quantity by exactly the one unit added). Never a "clear cart" action. Re-read and compare with `meta.cartBefore`; record `meta.cartState` as "restored to its earlier contents" or exactly what remains. A restore that could not be verified is said in the footer and in one plain chat line at the end of the finder run only if an item may remain in the person's cart (the one exception to "no closing message", because it changes their cart).

Adding and removing one item is the maximum state-changing action; it happens only for cart and checkout goals and "all goals", it is reverted in the same message, and it is disclosed in a footer line.

## Fix-up rule

Each surface may get ONE fix-up, no more, and all fix-ups go in one message. What is still missing after it goes on the reports as a caveat, and the screenshot look in Phase 4 is the last look.
- A page failed to load or timed out: one more `navigate_to` + read. A `tab-not-found` follows the browser tool's rule (one `create_tab`), then the run continues without that surface.
- A verification page, login wall or CAPTCHA: never bypassed — SKILL.md "Switching mid-run".
- The add-to-cart click did not register (the cart shows no new line) twice: stop, describe the cart from the empty-cart read and from click data, and say so in the reports.
- Every policy page `notFound`: one more same-origin footer link; an off-site help center only if the same-origin pages said nothing about shipping.
- The collection record recognized no cards, or the product record has no title or price: one targeted look (`dom_scroll` to the grid or buy box, `get_dom`, `get_screenshot`) and record what it shows. Never re-read the whole site.

## What to look at in the results (the validation itself)

- **Storefront served.** Stores localize by IP: Edge in Canada sees CAD
  prices, different thresholds, and different copy from the US traffic that
  dominates the data. Compare `read_home.storefront` (country, currency, `htmlLang`, the price the screenshot shows) with where most
  sessions come from (Batch 1 device baseline grouped by COUNTRY_CODE if in
  doubt); if they differ, say so in the page's data line, and never report
  a threshold mismatch between two surfaces as a defect until both were
  read in the same storefront.
- **Market served.** The URL Edge landed on (a locale prefix such as
  `/en-gb/`, `/fr-fr/`) and `hreflang` links in the homepage DOM say which
  market the browser was served on a locale-routed store. Compare them with the data's top market and decide
  whether a Phase 2 read under another prefix is needed (`references/finder/phases.md`,
  "Multi-market stores").
- **Other testing tools.** `read_home.testingTools` lists experimentation
  tools loaded on the page (Optimizely, VWO, Convert, AB Tasty,
  Kameleoon, Dynamic Yield, Intelligems, Shoplift, Visually and similar). An
  entry is not a defect and kills nothing; it goes on every card's overlap
  line and in the footer so the page can say the surface may already carry
  someone else's test.
- **Announcement bar vs policy.** The bar often states a shipping threshold;
  the policy page is the statement of intended behavior. Where they
  disagree, that is a "Fix first" defect, and the policy's number is the one
  used in variants. Where the policy is silent on a threshold the bar
  advertises, the bar is the best available statement and the silence is
  worth one clause.
- **What already exists.** Free-shipping progress in the drawer or cart,
  a promo field (even behind a toggle), express pay, quick add on cards,
  shipping copy near the buy box, an upsell block: each of these present
  kills the candidate that would "add" it. This is the #1 reason the read
  exists. The converse is not safe: `"absent"` or `null` can be a selector
  miss on an unfamiliar theme (or a static DOM missing what scripts render
  later), so a candidate that exists only because a field came back empty
  is confirmed by the screenshot look or the fix-up before it ships.
- **Defects.** A disabled or sold-out CTA on a top product, a cart that did
  not take the add, a policy page that 404s, consent banners with no
  decline control covering the fold, copy contradicting policy, a dead
  "shop all" page: defects, not tests.
- **Selectors and block containers** come back with every element
  `dom_facts.py` records (`selector`, `block`, `column`, `source:
  "static-dom"`). They are where the build half starts searching the code;
  they come from a static DOM, so the code wins when it disagrees (Stage
  2c). If a candidate touches an element no record covers, one targeted
  `get_dom` look in the fix-up step records it rather than a later visit.

## The record (`walkthrough.json`)

The JSON each surface produced **is** the record of that surface. In the preview message (Phase 4), make sure `walkthrough.json` in the working folder holds one key per surface record (`read_home`, `read_policy`, `read_pdp`, `read_collection`, `read_cart`, `read_checkout_entry`, plus any Phase 2 read under its own key) — `dom_facts.py --into` writes these — each value unedited, plus `look` entries from the screenshots and a `meta` key: `{"storeUrl", "surfaces": {"home": "/", "collection": "/collections/x", "product": "/products/y", "cart": "/cart"}, "fixUps": [...], "couldNotComplete": [...] or [], "cartBefore": [...], "cartState": "restored to its earlier contents" | "never added" | what remains}`. `scripts/build_page.py` reads it to put selectors and site facts into `candidates.json`. Do not summarize the records in prose anywhere: summarizing ("has free shipping messaging") loses the threshold and the selectors.

## Conduct

- Do not check out, create accounts, enter personal data, or interact with payment surfaces. The checkout-entry stop observes the first step and enters nothing. Adding one item and removing that one line is the maximum state-changing action; it must be reverted and disclosed.
- Leave the person's existing consent choices alone; when a banner blocks the read, use its decline or close control, never Accept.
- Avoid clicking elements that trigger browser-native dialogs or downloads (downloads are not supported anyway).
- Never sign in to anything on the person's behalf; `request_user_form_fill` lets them do it themselves when a step genuinely needs it (never for the finder's storefront read).
- If no browser is available, run what you can, mark every structural claim inferred-not-observed, and let a footer line suggest running again with Cowork open in Microsoft Edge.
