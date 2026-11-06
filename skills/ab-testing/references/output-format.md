# Output format: the "Recommended test" reports and the chat cards

The deliverable is ONE standalone report file per recommended test plus the in-chat cards, all built from a single `page.json` you write. Do NOT write the reports' content into the conversation. The chat gets the findings lead (one sentence per test), the findings card (or its Markdown fallback when the card is not confirmed rendered; quiet-mode rule 6), and later the per-test card a "Preview test N" reply asks for.

A report's job: let a busy merchant read what the test is, see why the data supports it, look at the variation next to the current site where a capture exists, and see exactly how it will be set up in Noibu. Every report opens with the run's intro (title, goal, data and capture lines, the previews note) and then carries its one test in this order: what to change → why → before and after (or the description and why there is no image) → the setup as Noibu will receive it → dev notes → how to create it (reply "Create A/B test N" in the Cowork chat). The run-level "Outside your goal" list and the footer caveats close every report. A report has no button and no script: creating and building happen in the chat (`references/findings-card.md`).

## How the reports are built

1. Write `page.json` in the run's working folder (fields below), next to the `walkthrough.json` the site read wrote.
2. `python <skill-dir>/scripts/build_page.py page.json <domain-short>` writes, next to `page.json`: one report per test (`<domain-short>-test-1.html`, ...), `candidates.json` (the handoff, derived from `page.json` + `walkthrough.json` and validated by `validate_candidates.py`; never hand-written), `findings-report.json` and `test-report-<rank>.json` (the card inputs). A validation error is a reason to fix `page.json`, never to edit the outputs.
3. Do not publish yet. A report reaches the person's files only when they reply "Preview test N" (or, in an unattended run where no one can reply, at the end of the run, every report in rank order).
4. At the end of the finder run, the findings lead (one sentence per test, `references/findings-card.md`), then the findings card from the local runner (or its Markdown fallback when the card is not confirmed rendered), then its next-step question (`references/findings-card.md`).

The build script owns the HTML, the styling and the honesty rules (images embedded only from real files, no script, no remote fonts), so every run produces the same reports; never hand-write a report or edit the generated HTML. If something needs to change for every run, change the script.

### Delivering a report file

On a "Preview test N" reply (or at the end of an unattended run), publish that test's `<domain-short>-test-<N>.html` from the working folder to the person's output files with the host's file tool (`CopyArtifact` with the **output** surface, source `working/…`, destination the same file name; never the user's skills surface). Check the result's copied count; on "source not visible yet", retry the same call after a few seconds. Never write into `output/` directly, never paste a URL or path in chat, never publish a test's file before its own reply. The report is self-contained (images embedded as data), so no `previews/` folder travels with it. Each file is its own deliverable; a second test's publish never overwrites the first.

## page.json fields

Top level:

| Field | Content |
| --- | --- |
| `domain`, `domainId` | the resolved domain name and UUID |
| `goal` | the goal as the user chose it ("Increase add to cart rate"), or "All goals" |
| `successMetricLabel` | the goal's metric label, or omit for "All goals" |
| `dataLine` | "Noibu, <window> (<N> days, about <sessions> sessions, <mobile share>)", plus one clause when it applies: the market the reports are written for, "checkout is tracked on <sibling domain>", or, on a split-checkout store, "checkout runs on <sibling host>; checkout goals are off for split-domain stores for now" |
| `captureLine` | "Live-site check <date>, read in Edge (desktop window)<, <country> storefront (<currency>)>", or "No live-site check: <why>" when no browser read the site |
| `caveats` | footer lines, each only when it applies: the localized-storefront or multi-market note, "mobile layout was not previewed; mobile claims are inferred" (whenever a test is mobile-only or rests on mobile evidence: Cowork has no phone-size capture), the baseline note, the thin-traffic note, the recent-data-not-arriving note (R1 false with sessions in the window), the instrumentation note (cart or checkout events not recorded, or the payment step not fully tracked), the blank-country exclusion, the third-party testing tool on the page, and the run notes quiet-mode rule 6 lists (whether Edge read the site or no browser did, the cart add and the removal of that one line, the "All goals" default, missing business context, a scheduled run without a live-site check); nothing else. No line about how many tests made the cut: killed candidates go in `run.killed` only |
| `tests` | the ranked tests, 3 to 6 (2 if only 2 survived; record the removed ones in `run.killed`, never in a footer line) |
| `outsideGoal` | at most 2 one-line candidates that survived validation but act on another metric; omit for "All goals" runs |
| `run` | not rendered; carried into `candidates.json`: `generatedAt` (ISO with timezone), `window` ({start, end, days, sessions, mobileShare, label}; start/end ISO timestamps with timezone, e.g. `2026-09-29T00:00:00Z`), `timezone` (optional IANA), `catalogue` (the metric catalogue read from the `noibu_create_ab_test` schema: {primary, secondary, pageScoped, maxSecondary, source}), `liveSiteCheck` (`performed`/`partial`/`not-performed`; derived from `browser` when absent), `readiness` ({receivingData, funnelInstrumented, paymentStepTracked, businessContext, thinTraffic, splitCheckout?: {checkoutDomain, checkoutDomainId}}), `market` ({multiMarket, written_for}), `browser` (`"edge"` when Edge read the site, `"none"` otherwise), `previewBrowsers` ({desktop: "edge"|"none", mobile: "none"|"narrow-window"}), `siblings`, `companyId`, `platform`, `testingTools`, `existingTests`, `killed` ([{idea, reason}] for every candidate validation removed) |

Per test:

| Field | Content |
| --- | --- |
| `title` | the test's name: name the change, not the metric ("Quick add on collection cards") |
| `surface` | the URL path(s) the test lives on |
| `variationName` | B's short noun phrase ("Add to cart button on cards") |
| `what` | one or two plain sentences: the change a shopper would notice |
| `why` | one or two sentences: the measured problem, at most 3 numbers, plus what the live site showed; correlational evidence labeled in one clause. Also shown on the findings card under "Why this test", so it must stand alone and lead with the customer's own numbers |
| `before`, `after` | paths under `previews/` (relative to `page.json`) to real captured image files, or `null`. Cowork's `get_screenshot` returns the image to you and is not assumed to save a file: set these only when an image file really exists in the run folder (the build script embeds it only then, and otherwise falls back to the description with "the capture was not saved as an image file in this session") |
| `previewNote` | when there are no images: why, in one clause, naming only a cause a tool result showed (see `references/preview.md`) |
| `beforeAlt`, `afterAlt`, `beforeCaption`, `afterCaption` | what each image shows (optional; defaults exist) |
| `previewViewport` | `"desktop"` (default), `"mobile-inferred"` (a mobile test with no phone-size capture), or `"narrow-desktop-window"` (the person narrowed their own window; never called a phone) |
| `previewKind` | optional: `"capture"` (default with images), `"preview-theme"` (B shown on an unpublished Noibu preview theme in the build half), `"description"` (no image) |
| `validation` | optional `{status: verified|partial|unvalidated, notes}`; derived when absent (no browser → unvalidated; the surface read → verified; only the homepage read → partial). An unvalidated test carries no selectors or site facts |
| `origin` | optional: `"user-requested"` for the "Create a specific test" route when no measured gap exists (then `handoff.evidence` may be empty) |
| `setup` | the six fields as the create screen shows them (rules below): `title`, `hypothesis`, `successMetric` (label plus baseline in parentheses), `secondaryMetrics`, `targeting`, `variations` |
| `metricVolume` | one line: the measured weekly volume of the event the success metric counts, in this test's targeting, plus "Noibu shows the days to a verdict at setup" (battery, "Metric volume"); never a day count, sample size or lift |
| `overlap` | one line, only when it applies: a RUNNING or DRAFT Noibu test on the same surface (title and status), or a third-party testing tool the walkthrough found on the page; else omit |
| `devNotes` | 1 to 3 sentences per lettered variation: page, element or block, what changes; selectors welcome, code never |
| `fixFirst` | one line, only when a verified defect sits inside the test's surface; else omit |
| `createInput` | the exact `noibu_create_ab_test` arguments for this test, minus `domainId`, `rationale` and call metadata: see `references/create-drafts.md` for the mapping. The report and cards show `setup`; a "Create A/B test N" reply sends `createInput`; they must say the same thing (the build script refuses a title or hypothesis mismatch) |
| `handoff` | not rendered; carried into `candidates.json`: `evidence` (the figures behind `why`, as `[{claim, numbers, source, correlational}]`; `numbers` is an **object of named figures**, e.g. `{"desktopCartSessions": 41074, "desktopCartToCheckout": 0.26, "mobileCartToCheckout": 0.79}`, never a string or a list, so a downstream hypothesis quotes numbers, not prose; `source` names the query or page it came from), optional `surfaceTemplate` (home, collection, product, cart, checkout; inferred from `surface` when absent, and it picks which script's selectors in `walkthrough.json` the test inherits), optional extra `selectors` (a `find` result the scripts did not record), optional `consoleFollowUps` (a country condition to add in the console) |

## Voice

Write for a busy merchant scanning on a phone. Short sentences. Plain
words. One idea per sentence. Say "shoppers" not "sessions" where the
meaning survives. Never use em dashes: use colons, commas, periods, or
parentheses. No hype adjectives, no pitch framing. At most 3 numbers per
test in `why`; pick the ones that carry the argument. Every number must
come from this run's queries, pages, or documents. A baseline you measured
is "about X%" (the battery derives it from session funnel depth and the
product's own definition may differ, so the setup screen's figure wins);
one you did not measure is "baseline shown at setup".

## Field-by-field rules (the `setup` block and `createInput`)

### Title

Name the change, not the metric. About 30 to 45 characters so it scans in
the tests list, and it must still make sense months later. The backend
derives the test's flag key from it, and a title already used on the
domain is rejected, so never reuse one.

### Hypothesis

Match the shape of the field's own example ("Moving the add to cart button
higher on the PDP will increase add to cart rate."). One sentence:
mechanism → expected direction → the success metric.

### Success metric

Exactly one, and it must be the metric the variant acts on most directly,
not the most impressive one. When the user chose a goal, every test uses
that goal's metric: the goal was the brief, and a test whose most direct
metric is something else does not answer it (it can be one line in
`outsideGoal` instead).

The supported success metrics are this run's catalogue
(`references/finder/goal-and-readiness.md`, "The metric catalogue"); a
metric the catalogue offers only as secondary is never a success metric.
Write the label the way the setup screen shows it:

| Write this label | Use when the variant directly drives... |
| --- | --- |
| Add to cart rate | adding a product to the cart |
| Checkout conversion rate | completing a purchase |
| Viewed page: \<URL\> | reaching one specific page (a landing page, the checkout URL, a sale page) |
| Viewed page: page group \<name\> | reaching any page in a Noibu page group (product pages, collection pages, checkout, cart) |
| Bounce rate on page: \<URL\> | (only once the catalogue has a bounce metric) keeping shoppers who land on one page from leaving without a second page view. Lower is better: hypotheses say "will reduce bounce rate on …" |
| Bounce rate on page: page group \<name\> | (same) the same for every landing page in a page group (product pages, collection pages) |

So "more checkout starts" is `Viewed page: page group Checkout` (or the
checkout URL when the domain has no Checkout group), "more product page
views" is `Viewed page: page group Product`, and "more collection views" is
`Viewed page: page group Collection`. Use the page group names exactly as
the domain's data reports them (Batch 1 query #8 lists them); if the
domain has no page groups, fall back to the URL form with the path the
walkthrough recorded. Average order value ("Average order value") is a
secondary metric only while the catalogue lists it only as secondary.
Secondary metrics go up to the catalogue's `maxItems`, each from its
secondary list. Do not use metrics outside the catalogue (no revenue per session, which the console can't show; no bounce rate until the catalogue has it; no exit rate, scroll depth, email capture, or per-step
completion rates). If a test's natural KPI is unsupported, choose the nearest
supported metric and, at most, note in one clause what the test
consequently does not measure.

If checkout completion is not instrumented on the domain (Batch 1 check
#4), do not use Checkout conversion rate; use `Viewed page: page group
Checkout` (or the checkout URL) and say in one clause that the test
measures reaching checkout, not buying.

### Secondary metrics

Up to 3. They give directional context and never decide the winner, so pick
the ones that would catch a side effect of this specific variant (a cart
change that might depress order size: Average order value; a routing change
that might just shuffle traffic: Viewed page on the destination). "None" is
a fine value; do not pad.

### Targeting

Only write conditions the product can express: UTM campaign, UTM medium,
UTM source, UTM term, UTM content, device type (Mobile, which includes
tablets, or Desktop), and location (country, set in the console).
Conditions combine with "and". Example: "UTM medium is email and device
type is Mobile". If the evidence is not segment-specific, write "Everyone
(skip this section)": targeting narrows traffic, and less traffic means a
longer wait for a verdict, so recommend a condition only when the measured
gap lives in that segment. If a candidate's natural audience cannot be
expressed with these conditions (returning customers, cart value bands,
logged-in state), either widen it to everyone and note the dilution in one
clause, or drop the candidate; do not invent targeting the setup screen
does not offer. On a multi-market store, write the market as a location
condition to be added in the console after creation ("Location is United
Kingdom, set in the console"), and keep `createInput` free of it. (Custom attributes registered through the SDK can extend
targeting, but that is dev work, not a setup-screen option; if a test
genuinely needs one, say so in dev notes, not in Targeting.)

### Variations

Variation A is always "Original" and is the control; never rename it. Name
B (and C at most: more variants split traffic thinner and stretch the
verdict) with a short noun phrase describing the experience, because that
name is what the results page, the verdict banner, and the SDK's flag value
will carry ("Button above info box", not "Variant B"). Default to "split
equally"; recommend an uneven split only with a stated reason.

### Dev notes

Noibu owns the split, targeting, and metrics; the store's own code decides
what each variation renders, by reading the assignment from Noibu's SDK
(the pattern is documented in `references/shared/noibu-feature-flag-sdk.md`
for the skill that writes the code), so a developer is in the loop on every
test and the variation code must be live before the test starts. These
notes are the one to three sentences per lettered variation that tell that
developer what to build: the page, the element or block, and what changes.
Concrete enough to start from ("PDP: move the whole add-ons block after the
trust badges block in the product info column"), never actual code, and
never instructions for A (the control renders the current experience by
definition). The preview phase already found the right block to move; say
that block, not the inner element.

### Fix first

Omit when there is nothing verified to fix. When a verified defect (error,
broken element, copy contradicting policy, poor vitals) sits inside a
test's surface, one line: what to fix and why it would otherwise pollute
the test's result.

## Guardrails and results framing

Guardrails are fixed and automatic in the product: error rate, P95 LCP,
sample ratio mismatch. They warn; they never block. Do not present ordinary
metrics as "guardrails" and do not invent per-test guardrails. Results in
the product are Bayesian ("chance to win", verdict banners); do not explain
this on a report and do not fabricate expected lifts, run durations, or
power calculations. No confidence ratings, no sizing, no duration
estimates: the product computes "About N days to reach a verdict" from the
real traffic at setup. The one traffic figure a card carries is
`metricVolume`: the measured weekly count of the success metric's event,
which is a fact from this run's queries, not a projection.

## Ranking

Order by evidence strength × traffic exposure × plausible effect, not
novelty. Aim for 3 to 6 tests.
