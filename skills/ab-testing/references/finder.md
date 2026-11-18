# Finding test opportunities

Read this when the user picks "Look for new A/B test opportunities" or "Create a specific A/B test". It runs from the goal question to a ranked list of tests. Open `references/queries.md` in the same message; this file says when each query is used.

The finder produces a short list of A/B test recommendations for an ecommerce store, aimed at the goal the merchant cares about. The bar for inclusion is high: every recommendation is supported by measured Noibu data and checked against what that data shows already exists on the store. Fewer, better-supported tests beat a long speculative list.

Why it works this way: analytics data alone produces recommendations that die on contact with the site (proposing a feature that already exists, calling a working feature broken, missing copy that contradicts policy). Nothing here can read the store's pages, so the finder checks each candidate against what Noibu recorded shoppers doing on the page, and says plainly what it could not confirm. The store's own code settles the rest when a test is built (`references/build.md`). Expect the check to eliminate 1 to 3 data-derived candidates; that is the finder working, not failing. A goal exists because "here are six things to test" makes the merchant do the prioritizing; "here are three tests that move add to cart rate" is a decision they can act on. A readiness check exists because a domain with no traffic, or without the events the goal's metric counts, cannot be tested.

**The finder writes nothing**, in Noibu or on the store. It reads Noibu data and nothing else. A draft test is created only when the user asks for one (`references/follow-ups.md`).

## Rules for the whole run

1. **Run in parallel.** Every tool call that does not depend on an earlier result goes in the same message as its siblings. The shape of a run: the goal question → readiness → Batch 1 → Batch 2 → synthesis → the tests file → the report.
2. **Two query batches, maximum.** The readiness reads are not a batch: they are four small reads that decide whether the battery runs at all. One extra follow-up query is allowed only when a batch result is uninterpretable without it. Do not explore.
3. **Noibu data is the only source.** No page of the store is opened or read. What the data can't show about a page is said to be unconfirmed, never assumed.
4. **No rendering tools.** Do not call `noibu_visualize_page_visits` or `noibu_show_session_replay`. Get scroll behaviour from QUANTILES(MAX_SCROLL_DEPTH_RATIO) and click behaviour from CLICKED_TEXT queries. Exception: the user explicitly asks for a heatmap or replay.
5. **No narration.** Do not summarize between tool calls, paste query results into the chat, or describe what you are about to do. Write one sentence only on a blocker, or when readiness stops the run.
6. **Every number comes from this run's queries or pages.**
7. On every `noibu_*` call, pass `skill: "ab-testing"` and a short `skillStep`. The `querying-noibu-data` skill carries the `orderBy` requirement, the row caps (sessions 100 rows, page visits 1,500 rows), the measure-uniqueness rule, domain resolution, and the rule to check sibling domains before reporting a zero. This file does not restate them.

## The metric catalogue (read from Noibu every run)

Noibu adds and retires A/B metrics from time to time, so the skill never works from a fixed list. The catalogue is read from the `noibu_create_ab_test` tool's schema at the start of the run:

- **Primary metrics** = the enum of `successMetric.metric`.
- **Secondary metrics** = the enum of `secondaryMetrics[].metric`, and how many are allowed = that array's `maxItems`.
- **Page-scoped metrics** = the metrics the schema's `pageUrl` / `pageGroup` descriptions name (today PAGE_VIEW_TO_URL_RATE): only these take a page URL or page group, and they need exactly one of the two.
- **Not in the console (excluded):** a few codes the tool accepts have no matching option on the console's create screen, so a draft made with one could not be shown or edited there. Drop them from both lists before anything else reads the catalogue: never a goal, never a success or secondary metric. Today: **REVENUE_PER_SESSION**. A person who asks to improve an excluded metric is told in one clause that Noibu can't run a test on it yet and offered the nearest goal (for revenue per session: Increase checkout completes, with Average order value as a secondary metric).
- **Bounce rate (dormant until the tool offers it):** the console has "Bounce rate on page" (lower is better), but the tool does not expose it yet. It switches on the first run a primary enum value contains `BOUNCE` (for example BOUNCE_RATE_ON_PAGE): that code is the bounce metric, used as spelled. Until then nothing about bounce rate appears anywhere. If the schema does not list it as page-scoped, treat it as domain-wide: no pages question, no `pageUrl`/`pageGroup`.

Hold the catalogue for the whole run; every goal offered, every success and secondary metric written, and every `createInput` comes from it and nothing else. A metric code is written exactly as the enum spells it. If the schema cannot be read, use the last-known catalogue in `references/tests-file.md`, and say in the summary that the metric list could not be confirmed against Noibu.

Labels: a known code uses its label from `references/tests-file.md` ("Success metric"); a code that table does not list is new, so build its label from the enum value in plain words (AVERAGE_ORDER_VALUE → "Average order value") and, when the schema describes it, from that description. A code in that table that is not in the catalogue is retired: never offer or write it. A metric is "Increase" unless lower is better (bounce rate, or a new code whose schema description says decrease): those are "Reduce".

## The goal question

Ask what the user is trying to move before pulling any data, because the goal decides which gaps count as candidates, which success metric every test uses, and which site surfaces need a closer look. Goals are built from the catalogue's primary metrics:

- each non-page-scoped primary metric is one goal, "Increase <label>" (today: add to cart rate; checkout completes for CHECKOUT_CONVERSION_RATE). Every primary metric left after the exclusions is offered;
- a metric the catalogue lists only as secondary (today AVERAGE_ORDER_VALUE) is never a goal, because the create tool rejects it as a success metric. A person who asks to raise it is offered Increase checkout completes as the goal, with average order value as a secondary metric, and told so in one clause;
- the bounce metric, once the catalogue has one, is the goal "Reduce bounce rate";
- the page-scoped metric gives the page-view goals: "Increase checkout starts" (page group Checkout, or the checkout URL) and "Increase page views" (product pages, collection pages, or one specific page). Page group names come from the domain's own data (Batch 1 query #8);
- "Not sure / show me everything" = "All goals": rank across every catalogue primary metric.

Ask one clickable question, "What do you want these tests to improve?", with one option per goal, label only, and "Not sure / show me everything" last. A question takes up to five options: when there are more goals than that, offer the first four and "Not sure / show me everything", and name the others in the question text for the user to type.

Only two answers need a second question:

- **Increase page views:** ask "Which pages?": Product pages · Collection pages · A specific page. A "specific page" answer gets one plain-text follow-up for the URL.
- **Reduce bounce rate** (only once the bounce metric is live and page-scoped): ask "Which pages?": Homepage · Product pages · Collection pages · A specific page.

Any other goal, "not sure", or anything typed in place of a pick: no second question. A typed reply that names a metric in the catalogue is that goal; one that names nothing measurable is "All goals".

**Skip the question when the request already states the goal**, as long as its metric is in the catalogue: "find tests to get more people into checkout" is the checkout-starts goal; "our add to cart rate is bad" is Add to cart rate; "make more money per visitor" or "raise basket size" is excluded (offer checkout completes, as above); "fewer people leaving the homepage" is Reduce bounce rate: Homepage, once live (before that, say in one clause that Noibu can't run a bounce-rate test yet and offer Increase page views: Product pages); "more traffic to our collection pages" is page views: Collection. "What should we test" with no metric is a reason to ask. In a scheduled run, default to "All goals" and say so in the summary.

The goal shapes three things: which battery results are decisive (the "Goal lens" table in `references/queries.md`; a new catalogue metric with no row there has no lens, so its candidates are ranked on evidence that acts on it directly and its traffic line says the volume is shown at setup), which pages' click data is read (query #9), and the rule in "Synthesis" that every test uses the goal's metric.

A checkout-completes goal on a domain whose completion counters are zero (Batch 1 check #4) cannot be measured: say so in the summary and write the tests against the checkout-starts metric (Viewed page: page group Checkout).

**Split-checkout stores.** Some stores run checkout on a separate host (`mainsite.com` and `checkout.mainsite.com`), which Noibu tracks as a separate domain. Sessions do not carry across domains, so a test's arm, set on the storefront, is not on the checkout session, and a checkout metric measured on the storefront domain undercounts or reads zero. For these stores checkout is switched off: no checkout goal, no checkout success metric (Checkout conversion rate, Viewed page: page group Checkout or a checkout URL), and no test whose change sits on a checkout page. Readiness detects the split.

## Readiness

Default window: the last 30 full days. Adjust only if the user asks or the domain is low-traffic.

After the goal is known, run the four readiness reads together (the exact calls are the "Readiness" section of `references/queries.md`): `noibu_check_data_connection`; one `noibu_search_sessions` over the window grouped by CONVERSION_FUNNEL_DEPTH; `noibu_list_domains` filtered to the domain's `companyId` (the sibling domains); `noibu_get_business_context`. Read them together and decide before anything else runs:

- **Not receiving data, or fewer than about 1,000 sessions in the window:** stop. One sentence: the domain has no traffic to analyze, and, when a sibling domain does carry sessions (a `www.` twin, a storefront next to a `checkout.` host), name it and offer to run against it.
- **Every session at funnel depth null** (no add-to-cart or checkout events in the window): add to cart rate and checkout conversion rate cannot be measured here. For a page-views goal or "All goals", continue with page-view metrics only. For an add-to-cart or checkout goal, ask once whether to switch to page-view goals (Product, Collection, Checkout page group, or a URL) or stop; in a scheduled run, continue with page-view goals. Either way the summary says that cart and checkout events are not instrumented and that fixing that comes before any cart or checkout test.
- **Thin traffic** (under about 15,000 sessions in 30 days): continue, widen the window to 90 days, and say in the summary that traffic is thin. Each test's traffic line does the rest; Noibu's days-to-verdict estimate at setup is the final word, so do not pre-empt it with a number.
- **Siblings with traffic:** when a sibling carries more sessions than the domain asked for, say so in the data line.
- **Split checkout:** a sibling whose host is the store's own checkout host (`checkout.`, `secure.` or `pay.` on the same root domain), or business context saying checkout runs on another domain, marks the store as split-checkout. Then, in this order:
  1. **Warn**, in one sentence: "Checkout on this store runs on <sibling host>, which Noibu tracks as a separate site, so checkout goals and checkout tests are switched off for this run; support for split-domain stores is coming."
  2. **Switch off checkout.** If the goal was Increase checkout starts or Increase checkout completes, or a specific page on the checkout host or the Checkout page group, ask once for another goal: Increase add to cart rate (Recommended) · Increase page views · Stop here. In a scheduled run, or with no answer: Increase add to cart rate, said in the summary. "All goals" continues across add to cart rate and page-view metrics only.
  3. **Record it:** the data line says "checkout runs on <sibling host>; checkout goals are off for split-domain stores for now", and the tests file's `readiness.splitCheckout` carries `{"checkoutDomain": "<sibling host>", "checkoutDomainId": "<its UUID>"}`, so the build does not check again.
- **Business context null:** nothing changes in the run; the summary points to `build-business-context` in one clause. When context exists, read its brand-voice section before writing any `what`, `why`, hypothesis or variation name, and use the business facts it states (shipping thresholds, promotions, audiences, policies) as facts about the store, attributed to the business context.

A run that passes readiness goes straight on.

## The data, and checking candidates against the store

**First message:** every Batch 1 query from `references/queries.md`, with `noibu_list_click_labels` and `noibu_list_ab_tests` for the domain.

**Second message:** Batch 2, whose filters come from Batch 1. Its click-text query (#9) covers the goal's surfaces: the top collection page and top product page by visits from #5, the homepage, and `/cart` for cart and checkout goals and "All goals"; the named URL for a specific-page goal. Use the data's top pages, not a fixed route: the store's "shop all" link and a random product are the wrong pages when the data says shoppers are on `/collections/x` and `/products/y`.

As results land, keep a private list of candidate opportunities, each tagged with the numbers that support it and the success metric it acts on.

**Does the variant already exist?** Proposing a feature the store already has is the most common way a recommendation fails. Check every candidate against these, in this order:

1. **Click text on the surface (#9).** What shoppers click on a page shows what is on it. A clicked label that names the feature means it exists: "Quick add" or "Add to cart" clicked on a collection URL; "Apply" or a discount-code control on `/cart`; "Shop Pay", "PayPal" or another express button; a shipping estimator; a "View cart" or progress control in a drawer. A candidate that would "add" something shoppers already click is dead.
2. **Click labels (`noibu_list_click_labels`).** The names the merchant gave to clickable elements, each with its page scope and CSS selector. A label for the feature on the candidate's page means it exists. A label for the element a variation would move or change gives the selector for its dev notes.
3. **Business context.** Shipping thresholds, promotions, policies and what the team says is already on the site.
4. **The domain's tests.** A RUNNING or DRAFT test with the same idea is overlap; a STOPPED one is one clause in `why` ("a similar test ran in <month>; check its result before repeating it").

The converse is not safe. No click on a feature is not proof it is absent: it may be there and unused, which is itself a finding. So a candidate that survives only because nothing showed the feature carries one clause in its dev notes naming what to confirm ("Not checked against the live store: confirm collection cards have no add-to-cart control before building"), and the build checks the store's code before a draft is created.

**What the data cannot show** is never stated as fact: the wording of the announcement bar, what sits above the fold, the shipping copy near the buy box, a consent banner, which third-party testing tools are loaded. A candidate that depends on one of these is written as a question the developer answers first, or dropped.

**What makes a candidate worth carrying forward:** a measured gap (segment A against segment B, page against template peers, cohort against baseline) that is large, sits on meaningful volume, has a plausible mechanism a variant could act on, and acts on the goal's metric. Generic best practices without a measured gap do not qualify, and neither does a strong gap on a metric the user did not ask about (it can earn one line under "outside your goal").

**Battery shape.** Batch 1 is queries #2 to #8 (device baseline and its country sibling; top pages and scroll reach are one query; #8 lists the domain's page groups). Batch 2 is #9 (one click-text query over the goal's surfaces), #10 (landing attribution, only when an underperformer exists), and the optional queries the goal lens or a candidate calls for. Every entry carries its exact `queryInput`; copy it, don't compose it. There is never a third batch.

### Multi-market stores (read with Batch 1)

A store on Shopify Markets or any locale-routed storefront serves several countries, prices and copy from one domain. Two signals, either one enough: the top URLs in Batch 1 #5 carry a locale prefix (`/en-gb/`, `/fr-fr/`, `/de-de/`), or the country sibling of #2 shows two or more countries each above about 10% of sessions with conversion rates that differ severalfold. When a store is multi-market:

- Treat the prefix (or the country) as the market. The top market by sessions is the one the tests are written for; say so in the data line and the summary. Use that market's URLs in query #9.
- Rows with an empty COUNTRY_CODE that carry more than about 10% of sessions and convert near zero are not shoppers: exclude them from every baseline cited and say so once.
- The create tool has no market or country field (location targeting is added in the console after creation): write the per-market condition in `setup.targeting` as a console follow-up, and never claim the test is scoped to a market until that is done.

## Synthesis

Apply the inclusion rules, in this order:

1. Kill any candidate whose variant the data shows already exists on the store, or whose evidence dissolved on a second look.
2. Reclassify: anything that is simply wrong (copy contradicting policy, verified errors, broken pages, poor web vitals) is a defect, not a test. Fold a defect into a recommendation only as a one-line "Fix first" note when it lives inside that test's surface.
3. On a split-checkout store, kill every candidate whose success metric is a checkout metric or whose change sits on a checkout page, and list none of them under "outside your goal". Then check every survivor against `references/platforms.md` ("What the merchant can change" and "Blast-radius rules") for this store's platform. Kill one the merchant can't action, recording it in `killed` with a plain reason ("not actionable on Shopify: checkout pages accept no custom code"), unless the same mechanism can move to a surface they control and still serve the goal (a reassurance line moved from the shipping step to the cart): then reframe it there and say so in `why`. A candidate whose only realistic build breaks a blast-radius rule is reframed to a safe build or killed ("unsafe: would change every product page").
4. Hold to the goal. When a goal was chosen, every test uses the goal's success metric, because that is the question the user asked. A survivor that most directly moves a different metric goes under "outside your goal" as one line (at most two such lines), or is dropped; do not stretch it to the goal's metric with a weaker mechanism. For "All goals", rank across every catalogue primary metric.
5. Check the instrumentation under each candidate. When the payment step is thin (Batch 1 #3 depth 3, or the #4 PAYMENT_INFO_SUBMITTED counter, under about a fifth of completed checkouts), any candidate whose evidence is a drop-off between checkout start and completion is built on a gap in the data, not on shopper behaviour: drop it, and say once that the payment step is not fully tracked and that fixing the instrumentation comes first. Checkout conversion rate itself stays valid on such a domain; only step-level claims are not.
6. Rank the survivors by evidence strength × traffic exposure × plausible effect, not novelty. Aim for 3 to 6 recommendations; if only 2 survive, ship 2.
7. Label correlational evidence as such (self-selected cohorts like search users or email traffic justify running a test, never assuming the gap transfers).
8. Express every survivor in the create tool's own fields (the setup block in `references/tests-file.md`), with every success and secondary metric taken from this run's catalogue. A candidate that cannot be expressed there (no catalogue success metric even by proxy, or an audience that targeting cannot select: anything beyond UTM fields, device type and country) gets widened, reframed or killed at this step.
9. Write each test's traffic line (`metricVolume`): how many sessions a week, in the test's own targeting, reach the event its success metric counts, from Batch 1 #3 and #8 divided by the weeks in the window, rounded to two significant figures, plus the fixed clause "Noibu shows the days to a verdict at setup". When a candidate would be defensible on two supported metrics, pick the one with more weekly events and say so in one clause. Never write a day count, a required sample size or an expected lift. `references/queries.md` ("Metric volume") has the arithmetic.
10. Write each test's overlap line when a RUNNING or DRAFT Noibu test sits on the same surface (`noibu_list_ab_tests`). Omit the line when nothing applies. Other testing tools on the store can't be detected from here; say so once in the caveats.
11. Never fabricate numbers. If a baseline was not measured, write "baseline shown at setup". Facts about the store come from this run's data or the business context, never from memory of how stores usually work.
12. Every survivor's `devNotes` names anything about its page that the data could not confirm, as the first thing for the developer to check. It ends with one sentence on how the merchant ships it and what the merged code touches besides the tested element ("Ships as a new snippet in the collection grid section behind the flag; touches product cards on collection pages only; no product-specific values in the template").

## Then

Write the tests file and the report data with `references/tests-file.md`, and deliver the report as the Output section of SKILL.md says.

If the run found no test that clears the bar, the report data carries an empty `tests` list and one sentence in `noPrioritiesReason`.

The finder never creates a test because the user seemed likely to want one. A draft is created only when the user asks (`references/follow-ups.md`). Editing, starting and deleting tests stay in the console.
