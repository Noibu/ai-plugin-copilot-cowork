# Finder half: Phases 1 to 5 (data and site read, extra stops, synthesis, previews, build and deliver)

Block 2 (resolve, goal, readiness) is in `goal-and-readiness.md`; this file is everything after it.

### Phase 1 — Noibu data and the site read, interleaved

The site read is goal-scoped, not a fixed tour, and record-first, not exploration: each surface is opened once in Edge, its DOM is read into a small JSON record (`scripts/dom_facts.py` over the saved `get_dom` file, or the surface checklist in `references/site-validation.md` when no file was saved), and its screenshot is your look at what a shopper sees above the fold. Policy pages are read the same way. `references/site-validation.md` has the two batches, the surfaces each goal reads, and the fix-up rule; this section says where they go.

**Block 3, one message:** every Batch 1 query from the battery AND the site read's Batch A on the run's tab (opened in the readiness message): the homepage (already loaded by `create_tab`: `get_dom` + `get_screenshot`, then `dom_facts.py --surface home`), then each same-origin shipping / returns / FAQ page the homepage links (`navigate_to`, `get_dom`, `dom_facts.py --surface policy`; at most three). Nothing in Batch A depends on data.

**Block 4, one message:** Batch 2 (filters come from Batch 1), the Phase 3–5 reference reads, AND the site read's Batch B on the same tab, one page after another, whose URLs come from Batch 1: the top collection page by visits from #5 (`--surface collection`) and the top product page by visits from #5 (`--surface pdp`) for add-to-cart, page-view and "all goals" runs; the cart path (product page → the page's own add-to-cart control → cart → `--surface cart` → remove that one line, plus the first checkout step, observation only, for a checkout-completes goal) for cart and checkout goals and "all goals"; the named URL with the fitting surface for a specific-page goal. Read the data's top pages, not a fixed route: the store's "shop all" link and a random product are the wrong pages when the data says shoppers are on `/collections/x` and `/products/y`.

As Batch 1 and Batch 2 results land, keep a private list of candidate opportunities, each tagged with the numbers that support it and the success metric it acts on. Read the site records in the same pass: anything they show already exists (free-shipping progress, a promo field behind a toggle, express pay, quick add on cards, shipping copy by the buy box, an upsell block) is not a candidate. A `null` or `"absent"` is a parser miss as often as a missing feature (static DOM, unfamiliar theme): when a candidate's survival depends on one, the screenshot of that surface is the second look (Phase 4), and a candidate it contradicts is dropped. `testingTools` names any Optimizely, VWO, Convert, AB Tasty, Kameleoon, Dynamic Yield or similar script on the page: another tool may already run experiments on the same surfaces, so every test's overlap line says so (Phase 3) and the footer names the tool.

If "The browser" found no browser, there is no site read: proceed without validation, mark structural claims as inferred per the prerequisites, and a footer line carries the "run with Cowork open in Edge" suggestion. If a page fails to load, the fix-up rule in `references/site-validation.md` applies once per surface; what is still missing goes in the reports' caveats, never re-explored.

Mark "Analyze 30 days of Noibu data" and "Check the live store" complete in the message after Block 4 returns.

What makes a candidate worth carrying forward: a measured gap (segment A vs segment B, page vs template peers, cohort vs baseline) that is large, sits on meaningful volume, has a plausible mechanism a variant could act on, and acts on the goal's metric. Generic best practices without a measured gap do not qualify, and neither does a strong gap on a metric the user did not ask about (it can earn one line under "Outside your goal").

#### Battery shape

`references/noibu-query-battery.md` is already consolidated: the
readiness reads live in Block 2; Batch 1 is queries #2 to #8 (device
baseline and its country sibling; top pages and scroll reach are one
query; #8 lists the domain's page groups), Batch 2 is #9 (one click-text
query over the goal's surfaces), #10 (landing attribution, only when an
underperformer exists), and the optional queries the goal lens or a
candidate calls for. Every entry in the battery carries its exact
`queryInput`; copy it rather than composing the JSON. There is never a
third batch.

#### Multi-market stores (read with Batch 1)

A store on Shopify Markets or any locale-routed storefront serves several
countries, prices and copy from one domain. Two signals, either one
enough: the top URLs in Batch 1 #5 carry a locale prefix (`/en-gb/`,
`/fr-fr/`, `/de-de/`), or the country sibling of #2 shows two or more
countries each above about 10% of sessions with conversion rates that
differ severalfold. When a store is multi-market:

- Treat the prefix (or the country) as the market. The top market by
  sessions is the one the page is written for; say so in the data line
  and the caveat.
- Compare the market the walkthrough was served (`read_home.storefront`: `country`,
  `currency`, `htmlLang`, and the path prefix of the URL Edge landed on) with the top market. When they
  differ and a candidate depends on copy, price or layout, Phase 2
  re-reads the homepage and the PDP under the top market's prefix in one
  batch; otherwise note the difference and carry on.
- Rows with an empty COUNTRY_CODE that carry more than about 10% of
  sessions and convert near zero are not shoppers: exclude them from
  every baseline you cite and say so in one footer line.
- The create screen has no market or country field a skill can set
  (location targeting is added in the console after creation): write the
  per-market condition in `setup.targeting` as a console follow-up, per
  `references/create-drafts.md`, and never claim the test is scoped to a
  market until that is done.

### Phase 2 — Extra site stops (rare)

Block 4 already read the homepage, the policy pages and the goal's own surfaces, so most runs skip this phase. Run it only when a surviving candidate depends on a surface nobody read: the top market's storefront when it differs from the one served (above), search (empty state, the #1 query from the data; skip if search is not instrumented), a paid landing page, or a candidate-specific URL. One page per step on the run's tab (`navigate_to`, then `get_dom` + `get_screenshot`, then `dom_facts.py` or the checklist). The question per candidate is the same: does the proposed variant already exist? Is the "problem" actually a defect? What does the surface really contain? Record selectors and block containers for anything a variation would touch.

The site read is done in the person's desktop Edge window; never make mobile-layout claims from it — use the scroll/click query data for those, and mark every mobile claim inferred (Cowork has no phone-size view).

#### Browser efficiency rules

- **Records, not exploration.** Each page gets one `get_dom` + `get_screenshot`; the saved DOM goes through `dom_facts.py`, whose JSON is the record. Never scroll through a page to "read" it, and never paste a whole DOM into chat or into `page.json`. Use one targeted look (a `get_dom` after one `dom_scroll`) only for a single element the record does not cover.
- **One page at a time, in one message.** `navigate_to` and `create_tab` must be their own calls; the read of a page (wait, `get_dom`, `get_screenshot`) is one call. Write the pages of a batch one after another in the same message.
- **One fix-up per surface; never a second.** What is still missing goes on the reports as a caveat.
- **Navigate directly.** The cart URL and an in-stock product come from the homepage record (the product is the fallback when #5 names no product page); policy pages are the homepage's footer links (Shopify: `/policies/shipping-policy`, `/policies/refund-policy` first).
- **One tab for the whole run**: the run's tab. There is no close action; leave it on a store page at the end (never on a checkout step).

### Phase 3 — Synthesis

Apply the inclusion rules, in this order:

1. Kill any candidate whose variant already exists on the site, or whose
   evidence dissolved under validation. Do not include them in the document.
2. Reclassify: anything that is simply wrong (copy contradicting policy,
   verified errors, broken pages, poor web vitals) is a defect, not a test.
   Fold a defect into a recommendation only as a one-line "Fix first" note
   when it lives inside that test's surface.
3. On a split-checkout store (Block 2), kill every candidate whose
   success metric is a checkout metric or whose change sits on a checkout
   page, and list none of them under "Outside your goal": the checkout
   session is on another domain and the test could not measure it. Then
   check every survivor against SKILL.md's "Platform restrictions and
   blast radius" for this store's platform, as its "Finder synthesis"
   bullet says.
4. Hold to the goal. When a goal was chosen, every test in "The tests"
   uses the goal's success metric, because that is the question the user
   asked. A survivor that most directly moves a different metric goes
   under "Outside your goal" as one line (at most two such lines), or is
   dropped; do not stretch it to the goal's metric with a weaker
   mechanism. For "All goals", rank across every catalogue primary metric.
5. Check the instrumentation under each candidate. When the payment step
   is thin (Batch 1 #3 depth 3, or the #4 PAYMENT_INFO_SUBMITTED counter,
   under about a fifth of completed checkouts), any candidate whose
   evidence is a drop-off between checkout start and completion is built
   on a gap in the data, not on shopper behaviour: drop it, and put one
   footer line on the page saying the payment step is not fully tracked
   and that fixing the instrumentation comes first. Checkout conversion
   rate itself stays valid on such a domain (completes are counted); only
   step-level claims are not.
6. Rank the survivors by evidence strength × traffic exposure × plausible
   effect, not novelty. Aim for 3 to 6 recommendations; if only 2 survive,
   ship 2 and say why the bar was high.
7. Label correlational evidence as such (self-selected cohorts like search
   users or email traffic justify running a test, never assuming the gap
   transfers).
8. Express every survivor in the create-flow's own fields (the setup block
   in `references/output-format.md`), with every success and secondary
   metric taken from this run's catalogue. A candidate that cannot be
   expressed there — no catalogue success metric even by proxy, or an audience that
   targeting cannot select (anything beyond UTM fields, device type, and
   country) — gets widened,
   reframed, or killed at this step, never shipped with fields the setup
   screen does not have.
9. Write each test's traffic line (`metricVolume`): how many sessions a
   week, in the test's own targeting, reach the event its success metric
   counts (add to cart, checkout completion, or the page group or URL),
   from Batch 1 #3 and #8 divided by the weeks in the window, rounded to
   two significant figures, plus the fixed clause "Noibu shows the days
   to a verdict at setup". When a candidate would be defensible on two
   supported metrics, pick the one with more weekly events and say so in
   one clause. Never write a day count, a required sample size, or an
   expected lift: the product computes "About N days to reach a verdict"
   from real traffic once the draft exists, and a number of yours next to
   it would be the one the merchant remembers. The battery's "Metric
   volume" section has the arithmetic.
10. Write each test's overlap line when something applies: a RUNNING or
   DRAFT Noibu test on the same surface (`noibu_list_ab_tests`, one call
   in Block 4 when the domain's test list has not been read yet), or a
   third-party testing tool the walkthrough found. Omit the line when
   nothing applies.
11. Never fabricate numbers. Every figure in the output must come from a
   query, page, or document from this run. If a baseline was not measured,
   write "baseline shown at setup". Site facts come from the site records
   of Blocks 3 and 4 (and Phase 2) verbatim, never from memory of how
   stores usually work.

### Phase 4 — Previews and the second look (every surviving test)

Once synthesis has fixed the list, give every lettered variation of every test its preview before building the reports, following `references/preview.md`. In Cowork the browser cannot change the page, so the finder's preview is:

1. **The before look:** `navigate_to` the test's surface, scroll to the element the change is about (`dom_scroll` / `scroll`), `get_screenshot`. It is the second look at the surface: a variation it shows already in place is dropped and recorded in `run.killed`. Describe what the shot shows in `walkthrough.json` (`look` entries keyed by test).
2. **The variation:** a plain, specific description of what B looks like (`what` plus the variation name), written from the recorded selectors and the before look. It is labelled a description, never presented as a screenshot or as what ships.
3. **Images in the report only from real files.** `get_screenshot` returns the image to you; it is not assumed to be saved. Set `before`/`after` in `page.json` only when real image files exist in the run folder (for example the person supplied captures); otherwise leave them `null` with a `previewNote` naming the real cause ("this session could not change the page to show the variation", "the change is mobile-only and Cowork's browser cannot show a phone-size page", "no browser was available").
4. **Mobile tests** (targeting Mobile, or mobile evidence) have no phone-size look: `previewViewport: "mobile-inferred"` and the footer line that mobile was not previewed. Only when the person asked for it, a "narrow desktop window" look (they narrow their own window), captioned as such.

A real rendered B exists only in the build half: on a Shopify Online Store theme, the `theme` or `full` mode builds an unpublished Noibu preview theme (`references/shopify-theme-preview.md`); the finder never writes anything to get one. Previews need no answer from the person, so they run the same way attended and unattended. With no browser, skip straight to description-only previews. A preview is never an error message, and its absence never holds a report.

The preview message also writes `walkthrough.json` in the working folder: every site record from Blocks 3 and 4 (and Phase 2), unedited, under its surface key (`references/site-validation.md`, "The record"), plus `meta` and the `look` entries. The build script reads it to fill `candidates.json` with selectors and site facts, so nothing from the site read is retyped later. Never paraphrase the site read into prose ("has free shipping messaging"): that loses the threshold and the selectors.

### Phase 5 — Build and deliver

Write `page.json` exactly per `references/output-format.md` (every test's `setup` and `createInput` say the same thing; the mapping is in `references/create-drafts.md`), including its `run` block (window with timezone-aware timestamps, readiness, browser, catalogue, killed …) and each test's `handoff` block (the evidence numbers behind `why`, the surface template). Build with `python <skill-dir>/scripts/build_page.py page.json <domain-short>`: it writes one report per test, `candidates.json` (validated; a validation error means fix `page.json`), `findings-report.json` and the `test-report-<rank>.json` files. Do NOT publish any report yet: a report reaches the person's files only on its "Preview test N" reply (`references/findings-card.md`). Until then the built files stay in the run's working folder, which is also where the build half reads `candidates.json` from.

In ONE message, together with the final task updates, render the findings card with the local runner (`references/findings-card.md`; RunScript `show_card.py` with `report: findings-report.json` and `candidates: candidates.json`), after one or two sentences naming the top test (quiet-mode rule 6), then the findings card's next-step question (`references/findings-card.md`). Keep the runner's `abReplyMap`. Do not write the reports' content in the conversation beyond that, do not list files, and ask nothing else: the next-step question is the follow-up, taken by the person who decides. (After "Look for new opportunities" nothing else follows. After "Create a specific test", SKILL.md continues from Stage 1 step 3 with the one test as the pick.)

The finder never creates a test: a run that calls `noibu_create_ab_test` because the person seemed likely to want it is a failure. A draft is created only on a "Create A/B test N" reply (`references/findings-card.md`, "Answering a reply"), or by the build half's Stage 2a once the person has picked a test and a run mode. Editing, starting and deleting tests stay explicit later steps.

In an unattended or scheduled run nobody can reply "Preview test N", so every report file is published to the output files at the end of the run, in rank order (`references/output-format.md`, "Delivering a report file"), with no URL or path in chat; the findings card still renders, and its reply hints wait for whoever reads the conversation.
