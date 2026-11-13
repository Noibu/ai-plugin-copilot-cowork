# The tests file and the report data

Read this when synthesis is done and the tests are about to be written, and again whenever a later step needs a field's rules. A finder run writes two files in the working folder, and publishes one report page per test to the Cowork output folder:

- **`candidates.json`**: the full record of the run's tests. Every later step works from it: a test's report page, its detail, the draft, the code, QA, the PDF. Nothing in it is typed twice.
- **The report pages**: one page per test with its full record, built from `candidates.json` by `scripts/report.py`. The user opens a page from its link in the chat.
- **The report data**: the few fields the report card shows, taken from `candidates.json`.

Tests live in the conversation that found them. Later steps read only the `candidates.json` in this conversation's working folder, never one from another conversation.

## `candidates.json`

```json
{
  "schema": "noibu.ab-candidates/1",
  "generatedAt": "2026-10-03T14:20:00Z",
  "domain": "www.example-store.ca",
  "domainId": "00000000-0000-4000-8000-000000000000",
  "goal": "Increase add to cart rate",
  "successMetricLabel": "Add to cart rate",
  "dataLine": "Noibu, Sep 3 to Oct 3, 2026 (30 days, about 483,000 sessions, 78% on mobile)",
  "platform": "shopify",
  "surfaces": {"home": "/", "collection": "/collections/plush", "product": "/products/silver-star-plush-toy"},
  "companyId": 2420,
  "siblings": [],
  "window": {"start": "2026-09-03", "end": "2026-10-03", "days": 30, "sessions": 482560, "mobileShare": 0.78},
  "market": {"multiMarket": false, "written_for": "CA"},
  "readiness": {"receivingData": true, "funnelInstrumented": true, "paymentStepTracked": false, "businessContext": false, "thinTraffic": false},
  "existingTests": [],
  "caveats": ["..."],
  "tests": [
    {
      "rank": 1,
      "title": "Quick add on collection cards",
      "surface": "/collections/plush and every other collection page",
      "surfaceTemplate": "collection",
      "variationName": "Add to cart button on cards",
      "what": "...", "why": "...",
      "successMetric": {"metric": "ADD_TO_CART_RATE"},
      "metricVolume": "About 6,500 add-to-cart shoppers a week in this targeting. Noibu shows the days to a verdict at setup.",
      "evidence": [
        {"claim": "Collection pages reach 29% of sessions", "numbers": {"collectionGroupSessions": 141000, "allSessions": 482560}, "source": "batch1#8, R2", "correlational": false}
      ],
      "siteFacts": [{"clickedOnSurface": ["Filter", "Sort by", "Load more"]}, {"clickLabels": [{"name": "Product card", "selector": "div.product-summary"}]}],
      "unconfirmed": ["Collection cards have no add-to-cart control"],
      "variations": [
        {"name": "Original", "isControl": true, "trafficSplit": 50},
        {"name": "Add to cart button on cards", "isControl": false, "trafficSplit": 50,
         "devNotes": "Collection grid: add an Add to cart control ...",
         "selectors": {"productCard": {"selector": "div.product-summary"}}}
      ],
      "setup": {"title": "...", "hypothesis": "...", "successMetric": "Add to cart rate (about 5.8%)", "secondaryMetrics": "...", "targeting": "Everyone (skip this section)", "variations": "..."},
      "createInput": {"title": "...", "hypothesis": "...", "successMetric": {"metric": "ADD_TO_CART_RATE"}, "variations": [{"name": "Original", "isControl": true, "trafficSplit": 50}, {"name": "Add to cart button on cards", "isControl": false, "trafficSplit": 50}]},
      "consoleFollowUps": [],
      "overlap": null,
      "fixFirst": "Mobile CLS on /collections/plush is 0.31 at p75 ..."
    }
  ],
  "outsideGoal": ["one line", "one line"],
  "killed": [{"idea": "Promo code field in the cart", "reason": "already present: shoppers clicked \"Apply\" on /cart 1,240 times in the window"}]
}
```

### Run-level fields

| Field | Content |
| --- | --- |
| `domain`, `domainId` | the resolved domain name and UUID |
| `goal` | the goal as the user chose it ("Increase add to cart rate"), or "All goals" |
| `successMetricLabel` | the goal's metric label; leave out for "All goals" |
| `dataLine` | "Noibu, <window> (<N> days, about <sessions> sessions, <mobile share>)", plus one clause when it applies: the market the tests are written for, "checkout is tracked on <sibling domain>", or, on a split-checkout store, "checkout runs on <sibling host>; checkout goals are off for split-domain stores for now" |
| `caveats` | short lines, each only when it applies: the localized-storefront or multi-market note (which market the tests are written for, and that per-market targeting is set in the console), the baseline note, the thin-traffic note, the instrumentation note (cart or checkout events not recorded, or the payment step not fully tracked), the blank-country exclusion, that the live store was not read and other testing tools on it could not be detected, the "All goals" default, missing business context. Nothing else, and no line about how many tests made the cut |
| `tests` | the ranked tests, 3 to 6 (2 if only 2 survived) |
| `outsideGoal` | at most 2 one-line candidates that survived validation but act on another metric; leave out for "All goals" |
| `window`, `readiness`, `market`, `siblings`, `companyId`, `platform`, `surfaces` | what the run measured, as the example shows. `surfaces` are the top pages by visits that the click data was read for. `readiness.splitCheckout` is present only on a split-checkout store |
| `existingTests` | the domain's tests from `noibu_list_ab_tests` |
| `killed` | `[{idea, reason}]` for every candidate validation removed, so nobody proposes it again |

### Per-test fields

| Field | Content |
| --- | --- |
| `title` | the test's name: name the change, not the metric ("Quick add on collection cards") |
| `surface` | the URL path(s) the test lives on |
| `surfaceTemplate` | home, collection, product, cart or checkout |
| `variationName` | B's short noun phrase ("Add to cart button on cards") |
| `what` | one or two plain sentences: the change a shopper would notice |
| `why` | one or two sentences: the measured problem, at most 3 numbers; correlational evidence labelled in one clause. It is shown on the report card, so it must stand alone and lead with the customer's own numbers |
| `evidence` | the figures behind `why`, as `[{claim, numbers, source, correlational}]`, with the battery query each came from in `source`. A hypothesis or pull request quotes these, never the prose. `claim` is shown on the test's report page without `numbers` or `source`, so it states its own figures in plain words ("Collection pages reach 29% of sessions"), with no ids, field names or query names |
| `siteFacts` | what the data showed is on the surface: the labels shoppers clicked there (query #9) and the click labels configured for it, as returned, not a summary |
| `unconfirmed` | what the test assumes about its page that the data could not show, one short line each. The build checks these against the store's code before a draft is created. Leave out when there is nothing |
| `variations[].selectors` | CSS selectors from the domain's click labels for the elements the variation touches, as returned. Leave out when no label covers them; the build finds them in the store's code |
| `variations[].devNotes` | 1 to 3 sentences per lettered variation: page, element or block, what changes; selectors welcome, code never |
| `setup` | the six fields as the create screen shows them (rules below): `title`, `hypothesis`, `successMetric` (label plus baseline in parentheses), `secondaryMetrics`, `targeting`, `variations` |
| `metricVolume` | one line: the measured weekly volume of the event the success metric counts, in this test's targeting, plus "Noibu shows the days to a verdict at setup". Never a day count, sample size or lift |
| `createInput` | the exact `noibu_create_ab_test` arguments for this test, minus `domainId` and `rationale`. `setup` is what a person reads; `createInput` is what is sent; they must say the same thing |
| `consoleFollowUps` | what the create tool cannot set (a country condition to add in the console) |
| `overlap` | one line, when it applies: a RUNNING or DRAFT Noibu test on the same surface (title and status). `null` when checked and nothing applies |
| `fixFirst` | one line, when a verified defect sits inside the test's surface. `null` when checked and nothing applies |

Keys the run did not supply are absent, not `null`, except `overlap` and `fixFirst`, which are explicit nulls so a reader can tell "checked, nothing" from "not checked".

## Voice

Write for a busy merchant scanning on a phone. Short sentences. Plain words. One idea per sentence. Say "shoppers" not "sessions" where the meaning survives. Never use em dashes: use colons, commas, periods or parentheses. No hype adjectives, no pitch framing. At most 3 numbers per test in `why`; pick the ones that carry the argument. A baseline you measured is "about X%" (the battery derives it from session funnel depth and Noibu's own definition may differ, so the setup screen's figure wins); one you did not measure is "baseline shown at setup".

## The setup block and `createInput`

### Title

Name the change, not the metric. About 30 to 45 characters, and it must still make sense months later. Noibu derives the test's flag key from it, and a title already used on the domain is rejected, so never reuse one.

### Hypothesis

One sentence: mechanism → expected direction → the success metric. ("Moving the add to cart button higher on the PDP will increase add to cart rate.")

### Success metric

Exactly one, and it must be the metric the variant acts on most directly, not the most impressive one. When the user chose a goal, every test uses that goal's metric.

The supported success metrics are this run's catalogue (`references/finder.md`, "The metric catalogue"); a metric the catalogue offers only as secondary is never a success metric. Write the label the way the setup screen shows it:

| Write this label | Use when the variant directly drives... |
| --- | --- |
| Add to cart rate | adding a product to the cart |
| Checkout conversion rate | completing a purchase |
| Viewed page: \<URL\> | reaching one specific page (a landing page, the checkout URL, a sale page) |
| Viewed page: page group \<name\> | reaching any page in a Noibu page group (product pages, collection pages, checkout, cart) |
| Bounce rate on page: \<URL\> | (only once the catalogue has a bounce metric) keeping shoppers who land on one page from leaving without a second page view. Lower is better: hypotheses say "will reduce bounce rate on …" |
| Bounce rate on page: page group \<name\> | (same) the same for every landing page in a page group |

So "more checkout starts" is `Viewed page: page group Checkout` (or the checkout URL when the domain has no Checkout group), "more product page views" is `Viewed page: page group Product`, and "more collection views" is `Viewed page: page group Collection`. Use the page group names exactly as the domain's data reports them (Batch 1 query #8); if the domain has no page groups, fall back to the URL form with the path from Batch 1 query #5. Do not use metrics outside the catalogue (no revenue per session; no bounce rate until the catalogue has it; no exit rate, scroll depth, email capture or per-step completion rates). If a test's natural KPI is unsupported, choose the nearest supported metric and, at most, note in one clause what the test consequently does not measure.

If checkout completion is not instrumented on the domain (Batch 1 check #4), do not use Checkout conversion rate; use `Viewed page: page group Checkout` (or the checkout URL) and say in one clause that the test measures reaching checkout, not buying.

### Secondary metrics

Up to the catalogue's limit (3 today), each from its secondary list. They give directional context and never decide the winner, so pick the ones that would catch a side effect of this specific variant (a cart change that might depress order size: Average order value; a routing change that might just shuffle traffic: Viewed page on the destination). "None" is a fine value; do not pad.

### Targeting

Only write conditions Noibu can express: UTM campaign, UTM medium, UTM source, UTM term, UTM content, device type (Mobile, which includes tablets, or Desktop), and location (country, set in the console). Conditions combine with "and". If the evidence is not segment-specific, write "Everyone (skip this section)": targeting narrows traffic, and less traffic means a longer wait for a verdict, so recommend a condition only when the measured gap lives in that segment. If a candidate's natural audience cannot be expressed with these conditions (returning customers, cart value bands, logged-in state), either widen it to everyone and note the dilution in one clause, or drop the candidate. On a multi-market store, write the market as a location condition to be added in the console after creation ("Location is United Kingdom, set in the console"), and keep `createInput` free of it.

### Variations

Variation A is always "Original" and is the control; never rename it. Name B (and C at most) with a short noun phrase describing the experience, because that name is what the results page and the SDK's flag value will carry ("Button above info box", not "Variant B"). Default to "split equally"; recommend an uneven split only with a stated reason.

### Dev notes

Noibu owns the split, targeting and metrics; the store's own code decides what each variation renders, by reading the assignment from Noibu's SDK, so a developer is in the loop on every test and the variation code must be live before the test starts. Dev notes tell that developer what to build: the page, the element or block, and what changes. Concrete enough to start from ("PDP: move the whole add-ons block after the trust badges block in the product info column"), never actual code, and never instructions for A.

### Fix first

When a verified defect (error, broken element, copy contradicting policy, poor vitals) sits inside a test's surface, one line: what to fix and why it would otherwise pollute the test's result.

### Guardrails and results

Guardrails are fixed and automatic in Noibu: error rate, P95 LCP, sample ratio mismatch. They warn; they never block. Do not present ordinary metrics as guardrails or invent per-test guardrails. Do not fabricate expected lifts, run durations or power calculations: Noibu computes "About N days to reach a verdict" from real traffic at setup.

### Mapping `setup` to `createInput`

`domainId` and `rationale` are added when the tool is called; everything else goes in `createInput` exactly as the tool takes it. Metric codes come from the run's catalogue, as spelled. A page URL or page group goes only on a page-scoped metric, and exactly one of the two. A catalogue metric with no row below maps to `{metric: "<CODE>"}`, plus `pageUrl`/`pageGroup` only when page-scoped. Before writing the file, check every `createInput` metric against the catalogue; rewrite or drop a test whose metric isn't in it.

The metric rows below are the **last-known catalogue (October 2026)**: primary ADD_TO_CART_RATE, CHECKOUT_CONVERSION_RATE, PAGE_VIEW_TO_URL_RATE; secondary the same plus AVERAGE_ORDER_VALUE, up to 3. Use them as the catalogue only when the tool's schema could not be read.

| Setup block field | `createInput` |
| --- | --- |
| Title | `title` (as written) |
| Hypothesis | `hypothesis` (as written) |
| Success metric: Add to cart rate | `successMetric: {metric: "ADD_TO_CART_RATE"}` |
| Success metric: Checkout conversion rate | `successMetric: {metric: "CHECKOUT_CONVERSION_RATE"}` |
| Success metric: Viewed page: \<URL\> | `successMetric: {metric: "PAGE_VIEW_TO_URL_RATE", pageUrl: "<URL>"}` (exact page URL) |
| Success metric: Viewed page: page group \<name\> | `successMetric: {metric: "PAGE_VIEW_TO_URL_RATE", pageGroup: "<name>"}` |
| Success metric: Bounce rate on page: \<URL\> | `successMetric: {metric: "<bounce code>", pageUrl: "<URL>"}`; the code is the catalogue's bounce enum value. Only once the catalogue has one |
| Success metric: Bounce rate on page: page group \<name\> | `successMetric: {metric: "<bounce code>", pageGroup: "<name>"}`. If the schema doesn't list the bounce code as page-scoped, `{metric: "<bounce code>"}` only |
| Secondary metrics (up to 3) | `secondaryMetrics`: same mapping, plus Average order value → `{metric: "AVERAGE_ORDER_VALUE"}`; "None" → leave out |
| Targeting: device type is Mobile / Desktop | `deviceTypes: ["mobile"]` / `["other"]` (no "desktop" value exists; "other" is what the console shows as Desktop) |
| Targeting: UTM \<parameter\> is \<value\> | `utmConditions: [{parameter: "utm_<parameter>", values: ["<value>"]}]`, one entry per condition |
| Targeting: location (country) | not supported by the tool: leave it out of `createInput`, list it in `consoleFollowUps`, and say in `setup.targeting` that the country condition is added in the console after creation |
| Targeting: Everyone (skip this section) | leave out `deviceTypes` and `utmConditions` |
| Variations: A: Original (control) · B: \<name\>, split equally | `variations: [{name: "Original", isControl: true, trafficSplit: 50}, {name: "<B name>", isControl: false, trafficSplit: 50}]` (three-way: 34/33/33); explicit percentages carry over as written |

The control is always the current experience: `isControl: true` goes on "Original" and nowhere else. Splits must sum to 100. Variation names become the flag values the SDK serves, so keep the names in `setup` and in `createInput` identical.

## The report pages

Once `candidates.json` is written, build the pages: copy `scripts/report.py` to `.aether/scripts/report.py`, then RunScript `report.py` with the arg `candidates` set to the path of `candidates.json`. Pass nothing else.

- It writes one page per test, named `<domain without www>-test-<rank>.html`, into a `pages` folder beside `candidates.json`, and returns `pages`: each test's rank, title and file path, in rank order.
- A script can't write to the Cowork output folder. Once the script returns, publish each returned page to the Cowork output folder yourself, unchanged and under the same file name. The published files are the ones the summary links.
- The script writes every heading and label on a page. Never write a page's HTML yourself, and never edit a page after it is built. To change a page, correct `candidates.json` and run the script again.
- If it returns `error`, or can't be run at all, or a page can't be published, don't retry. Carry on without the pages, and in place of the "Full reports" line write one sentence saying the full report pages couldn't be built and why, using the reason the script or RunScript gave.

## The report data

Write a second JSON file in the working folder for the report card, from `candidates.json`:

```json
{
  "skill": "ab-testing",
  "store": {"name": "<domain>", "id": "<domainId>"},
  "window": {"start": "<window start>", "end": "<window end>"},
  "tests": [
    {"title": "", "shortTitle": "", "change": "", "why": ""}
  ],
  "noPrioritiesReason": ""
}
```

| Field | Source |
| --- | --- |
| `tests` | the tests in `rank` order, up to 5 |
| `title` | the test's `title` |
| `shortTitle` | the title in 5 words or fewer |
| `change` | the first sentence of `what` |
| `why` | the test's `why` |
| `noPrioritiesReason` | only when no test cleared the bar: one sentence saying why |

Timestamps carry their timezone. Then follow the Output section of SKILL.md.

**The summary** for this report says, in 2–3 sentences: the goal the tests serve, the strongest measured problem behind them, that the tests rest on Noibu data and the live store was not read, and any other caveat that changes how the tests should be read (traffic is thin; the goal was switched). It never recaps the tests.

**The "Full reports" line.** When the report pages were built, write one line as its own message after the card is shown and before the next-step question: "Full reports:" followed by a link to each test's page file, in rank order. It is part of the answer, not a note to yourself, and it is written on every run, scheduled or not. The linked files are how the user opens a test's full report, so link every page that was published and nothing else. The tests' records never go in the chat.
