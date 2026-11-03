# `candidates.json`: the handoff from the finder half to the build half

Written by `scripts/build_page.py` in Phase 5, next to the per-test
report files, validated by `scripts/validate_candidates.py` before it is
written, and never mentioned in chat. It is not published with the
reports (they are self-contained); the skill reads only this working copy. It
carries the same tests the reports show, in the shape the build half (drafting the
code, QA, and building and starting one test)
needs to act without re-running the analysis or re-reading the
site: the evidence with its numbers, the surfaces, the selectors and block
containers the site read recorded, the exact create arguments, the traffic
line and the overlap notes.

It is **derived, never authored**: the build script merges `page.json`
(each test's `title`, `why`, `setup`, `createInput`, `metricVolume`,
`overlap`, `fixFirst`, previews, plus the optional `handoff` and `run`
blocks `references/output-format.md` describes) with `walkthrough.json`
(the site read's records, keyed by surface name, plus `meta`; see
`references/site-validation.md`, "The record"). A test inherits the
`selectors` of the record for its surface (`surfaceTemplate` →
`read_home` / `read_collection` / `read_pdp` / `read_cart` /
`read_checkout_entry`, written by `scripts/dom_facts.py`) and a few
verbatim fields from that record as `siteFacts` — unless the test is
`unvalidated`, which carries neither. Nothing in it is new analysis, and nothing in it is typed
twice: if a field is wrong here, fix `page.json` or `walkthrough.json` and
rebuild.

Home: this schema lives here, in the skill's finder half, which writes
the file in Phase 5; the build half reads it from Stage 1 on. The file
is scoped to the chat that produced it: the build half reads only the
copy in this chat's working folder, never a copy from another chat,
OneDrive or a pasted link. The finder itself never reads this file during a run.

## Shape

```json
{
  "schema": "noibu.ab-candidates/3",
  "generatedAt": "2026-10-03T14:20:00Z",
  "domain": "www.example-store.ca",
  "domainId": "00000000-0000-4000-8000-000000000000",
  "reportFiles": {"1": "example-store-test-1.html"},
  "goal": "Increase add to cart rate",
  "successMetricLabel": "Add to cart rate",
  "dataLine": "Noibu, Sep 3 to Oct 3, 2026 (30 days, about 483,000 sessions, 78% on mobile)",
  "captureLine": "Live-site check Oct 3, read in Edge (desktop window), Canada storefront (CAD)",
  "platform": "shopify",
  "testingTools": ["Visually"],
  "storefront": {"shopifyOnlineStoreTheme": true, "country": "CA", "currency": "CAD", "htmlLang": "en"},
  "surfaces": {"home": "/", "collection": "/collections/plush", "product": "/products/silver-star-plush-toy"},
  "cartState": "never added",
  "couldNotComplete": [],
  "companyId": 2420,
  "browser": "edge",
  "liveSiteCheck": "performed",
  "previewBrowsers": {"desktop": "edge", "mobile": "none"},
  "catalogue": {"primary": ["ADD_TO_CART_RATE", "CHECKOUT_CONVERSION_RATE", "PAGE_VIEW_TO_URL_RATE"], "secondary": ["ADD_TO_CART_RATE", "CHECKOUT_CONVERSION_RATE", "PAGE_VIEW_TO_URL_RATE", "AVERAGE_ORDER_VALUE"], "pageScoped": ["PAGE_VIEW_TO_URL_RATE"], "maxSecondary": 3},
  "siblings": [],
  "window": {"start": "2026-09-03T00:00:00Z", "end": "2026-10-03T00:00:00Z", "days": 30, "sessions": 482560, "mobileShare": 0.78},
  "market": {"multiMarket": false, "written_for": "CA"},
  "readiness": {"receivingData": true, "funnelInstrumented": true, "paymentStepTracked": false, "businessContext": false, "thinTraffic": false},
  "existingTests": [],
  "caveats": ["..."],
  "tests": [
    {
      "rank": 1,
      "title": "Quick add on collection cards",
      "reportFile": "example-store-test-1.html",
      "surface": "/collections/plush and every other collection page",
      "surfaceTemplate": "collection",
      "what": "...", "why": "...", "hypothesis": "...",
      "successMetric": {"metric": "ADD_TO_CART_RATE"},
      "metricVolume": "About 6,500 add-to-cart shoppers a week in this targeting. Noibu shows the days to a verdict at setup.",
      "evidence": [
        {"claim": "Collection pages reach 29% of sessions", "numbers": {"collectionGroupSessions": 141000, "allSessions": 482560}, "source": "batch1#8, R2", "correlational": false}
      ],
      "validation": {"status": "verified", "notes": "The surface was read in the browser during this run."},
      "siteFacts": [{"cards": {"count": 18, "sample": ["/products/a", "/products/b"]}}, {"quickAdd": {"present": false, "label": null}}],
      "variations": [
        {"name": "Original", "isControl": true, "trafficSplit": 50},
        {"name": "Add to cart button on cards", "isControl": false, "trafficSplit": 50,
         "devNotes": "Collection grid: add an Add to cart control ...",
         "selectors": {"productCard": {"selector": "div.product-summary", "block": "div.results-grid__item", "column": "div.results-grid", "source": "static-dom"}},
         "preview": {"note": "this session could not change the page to show the variation", "kind": "description", "viewport": "desktop"}}
      ],
      "setup": {"title": "...", "hypothesis": "...", "successMetric": "Add to cart rate (about 5.8%)", "secondaryMetrics": "...", "targeting": "Everyone (skip this section)", "variations": "..."},
      "createInput": {"title": "...", "hypothesis": "...", "successMetric": {"metric": "ADD_TO_CART_RATE"}, "variations": [{"name": "Original", "isControl": true, "trafficSplit": 50}, {"name": "Add to cart button on cards", "isControl": false, "trafficSplit": 50}]},
      "consoleFollowUps": [],
      "overlap": "Visually is loaded on every page ...",
      "fixFirst": null
    }
  ],
  "outsideGoal": ["one line", "one line"],
  "killed": [{"idea": "Shipping reassurance beside the PDP buy box", "reason": "already present: the PDP shows a Free shipping block above the buy box; caught by the before look"}]
}
```

## Field rules

- `tests[].createInput` is byte-identical to the report's `createInput` for
  the same test, so the build half can create the draft without
  re-mapping. `consoleFollowUps` lists what the create API cannot set
  (location targeting for a market, a country condition).
- `evidence[].numbers` carries the figures that appear in the card's
  `why`, with the battery query they came from in `source`. A downstream
  skill writing a hypothesis quotes these, never the prose. They come from
  `page.json`'s `handoff.evidence`; a test without one has `[]`.
- `variations[].selectors` are the site read's recorded `selector`,
  `block` and `column` values for the surface, verbatim from
  `walkthrough.json`, plus anything `handoff.selectors` adds (a `find`
  result). They are what lets a code step grep the theme and a QA step
  write its change-specific check without another browser visit.
- `siteFacts` are verbatim fields from the surface's script JSON (cards,
  quick add, shipping copy, express pay, widgets, and so on), not a
  summary; `walkthrough.json` itself is the full record when more is
  needed.
- `metricVolume` is the measured weekly volume behind the card's traffic
  line; no day counts or sample sizes, for the same reason the page has
  none.
- `readiness` records what Block 2 found so the build half does not
  re-check it, and `killed` records what validation removed so nobody
  re-proposes it. `cartState` says whether a cart add happened in the
  read ("never added" on goals that do not touch the cart).
  `readiness.splitCheckout` is present only on a store whose checkout runs
  on another Noibu domain and names that domain; such a run ships no
  checkout-metric or checkout-page test.
- `browser` says whether Edge read the site (`edge`) or no browser did
  (`none`); with `none`, `liveSiteCheck` is `not-performed` and every
  test is `unvalidated`. `previewBrowsers.mobile` is `none` (Cowork has no
  phone-size capture) or `narrow-window` when the person narrowed their own
  window. `preview.viewport` is `desktop`, `mobile-inferred` or
  `narrow-desktop-window`; `preview.kind` is `capture` (real image files
  existed and are embedded in the report), `preview-theme` or
  `description`. `before`/`after` paths are relative to the run folder and
  present only when those files existed.
- `reportFiles` maps rank → the report file name in the run folder.
- `catalogue` is the metric catalogue read from the `noibu_create_ab_test`
  schema at run time; the validator checks metric codes against it
  (REVENUE_PER_SESSION is always excluded) and uses the last-known
  catalogue when it is absent.
- Keys the run did not supply are absent rather than `null`, except
  `overlap` and `fixFirst`, which are explicit nulls so a reader can tell
  "checked, nothing" from "not checked".

## Validation and the createInput hash

`scripts/validate_candidates.py` accepts this `/3` file and the 21.1.x
`noibu.ab-candidates/2` file (legacy, accepted for older handoffs); it
rejects anything else, including the Claude design's `/1`. `/3` adds to
every `/2` rule: timezone-aware window timestamps; `title` ==
`setup.title` == `createInput.title`; `hypothesis` == `setup.hypothesis`
== `createInput.hypothesis`; handoff `variations` mirror
`createInput.variations` exactly; unvalidated tests carry no selectors or
site facts; evidence is non-empty unless `origin` is `user-requested`; no
checkout-metric or checkout-page test when `readiness.splitCheckout` is
present; at most two `outsideGoal` lines; a mobile capture viewport is
refused (Cowork has none). The **createInput hash** is SHA-256 of
`json.dumps(createInput, sort_keys=True, separators=(',', ':'),
ensure_ascii=False)` encoded as UTF-8 — the same for `/2` and `/3`. The
findings card's runner returns it per rank (`abReplyMap`), and a "Create
A/B test N" reply is checked against it before anything is created.
