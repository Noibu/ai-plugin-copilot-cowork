# Platform restrictions and blast radius

Read this at the four points under "Where it is applied": the finder's synthesis (`references/finder/phases.md` Phase 3), the "Create a specific test" check, Stage 1 step 6a (`references/build/stage-1-pick-and-setup.md`) and Stage 2c (`references/build/stage-2-draft-code-pr.md`).

Two questions are asked of every test, at every point where one is proposed or built:

1. **Can this merchant action it?** Hosted platforms lock some surfaces; Shopify's checkout is the best-known case. A test the merchant can't build is noise in the report and a dead end in the build half, however strong its evidence.
2. **Can it be built without risk to the rest of the site?** A variation is production code that ships to *every* visitor and is switched on for B by a flag. Code that is wrong for one product, page or visitor the moment the theme goes live breaks the store, not just the test. Example: swapping a product's image by hardcoding its URL into the product template changes the image on every product page once the theme is published.

It is applied at the four points under "Where it is applied"; `references/finder/phases.md` Phase 3, `references/build/stage-1-pick-and-setup.md` step 6a and `references/build/stage-2-draft-code-pr.md` Stage 2c point back here.

### Which platform

Take the platform in this order: the code tree when a repository is connected, then `noibu_get_domain`'s `siteType`, then the site read's `platform`, then business context. `siteType` values map: `Shopify` and `Shopify Plus` → Shopify (a Hydrogen/Remix tree means headless: storefront rules follow the repo, checkout rules stay Shopify's); `Big Commerce` → BigCommerce (Stencil, or Catalyst when the tree is a Next.js app); `Salesforce Commerce Cloud` → SFCC (SFRA/SiteGenesis cartridges or PWA Kit); `Magento 2` → Magento (Luma, Hyvä or PWA Studio); `Oracle Commerce Cloud` → OCC (Design Studio widgets); `Custom`, `Unknown` or missing → the next source, and if nothing settles it, the "Custom / unknown" column.

### What the merchant can change

"Actionable" means the merchant's own developer can ship a flag-gated variation there with the platform as it stands. The Noibu flag SDK runs as page JavaScript, so a surface that accepts no merchant JavaScript cannot host a variation.

| Surface | Shopify / Shopify Plus | BigCommerce | SFCC | Magento 2 | OCC | Custom / unknown |
| --- | --- | --- | --- | --- | --- | --- |
| Home, collection, search results, PDP, header, announcement bar, footer, cart page and drawer | Yes (theme) | Yes (Stencil or Catalyst) | Yes | Yes | Yes (widgets) | Yes when a repo is found; otherwise ask where the code lives |
| Checkout steps and thank-you / order status page | **No** on any plan: no theme code or custom scripts run there. Plus can add checkout UI extensions in fixed slots, but they run sandboxed without page JavaScript, so the flag can't gate them: not buildable by this skill | Only when the repo holds a custom checkout (a `checkout-js` fork or Checkout SDK build). Default one-page checkout: additive copy outside form fields via Script Manager at most; never fields, steps, validation or payment | Yes | Yes, higher risk: QA before merge is required | Yes | Only when the repo contains the checkout |
| Card/payment fields, express-wallet buttons themselves | **No** anywhere (payment-provider iframes). Their container on a storefront page (position, order, nearby copy) is fine | | | | | |
| Prices, discounts, shipping rates, payment-method availability | **No** as a front-end test anywhere: platform config or server logic (Shopify Functions and discounts, BigCommerce/SFCC promotions, Magento cart rules) that a page flag can't switch per visitor. A displayed price, discount or rate that differs from what is charged is never acceptable | | | | | |
| Third-party app content (reviews, search/merchandising, upsell, chat widgets) | Container only (move, show, hide, spacing); the app's own markup and copy change in the app | Same | Same | Same | Same | Same |

Checkout as a *metric* is not checkout as a *surface*: on Shopify a cart or PDP change can still use a checkout success metric when readiness shows the counters are recorded and the store isn't split-checkout. Only a change that *sits on* a checkout or thank-you page is ruled out.

### Blast-radius rules (every platform)

A merged variation is live code on every page that renders the file it lives in. These rules keep the control identical for everyone not in B and keep B confined to the element and pages the test names. They govern the finder's `devNotes` and the code in Stage 2c.

1. **Everything visible is behind the flag.** B's markup, CSS and JS run only when the assignment is B. No ungated styles or "harmless" global tweaks. When the flag can't be read (SDK blocked, error, timeout), the visitor gets the control.
2. **Data-driven, never hardcoded in shared templates.** Product, collection and cart templates render for every product: never write one product's image, title, price, copy, URL, handle, SKU or ID into them. Read the value from the platform's data (Shopify product object and metafields, BigCommerce custom fields, SFCC or Magento product attributes) or a merchant-managed setting. When a test applies to a subset of products, scope it explicitly in the gating condition (tag, collection, metafield, ID list held in a setting) and name the subset in `devNotes` and the PR; every other product renders exactly as today.
3. **Scope every selector and style** under a variation attribute set by the gating helper (e.g. `[data-nb-<flagkey>="b"] .product-card__cta`), never on bare shared classes or by editing a shared stylesheet's existing rules. Before editing a shared component (header, product card, cart line), check where else it renders.
4. **Leave shared logic alone:** add-to-cart and cart-update requests, form actions, variant selection, price, tax, shipping, inventory, redirects into checkout, analytics calls. A test that needs one of these is not a front-end test.
5. **Decide the variation in the browser** unless the cache varies on it. Full-page caches (Magento Varnish/FPC, SFCC `<iscache>`, CDN caching on headless fronts) would store a server-rendered B and serve it to everyone.
6. **Prefer additive files:** B in a new snippet, section, component or module included behind the gate. Layout files (`theme.liquid`, `base.html`, `htmlHead` hooks, `default.xml`) change only to load the gating helper.
7. **Fail closed:** wrap B in try/catch; a missing element means no-op (control). Hide-until-ready only on the tested element, with a short timeout back to control; never hide the page or a section.
8. **No claims the store can't back:** no invented urgency, stock counts, reviews, badges or policy promises; copy matches the policy pages the site read recorded.

### Where it is applied, and what happens to a test that fails

- **Finder synthesis** (`references/finder/phases.md` Phase 3, right after split checkout): check every survivor against the two tables for this store's platform. Kill one the merchant can't action (record it in `killed` with a plain reason, e.g. "not actionable on Shopify: checkout pages accept no custom code"), unless the same mechanism can move to a surface they control and still serve the goal (a reassurance line moved from the shipping step to the cart): then reframe it there and say so in `why`. A candidate whose only realistic build breaks a blast-radius rule is reframed to a safe build or killed ("unsafe: would change every product page"). Every survivor's `devNotes` ends with one sentence on how the merchant ships it and what the merged code touches besides the tested element ("Ships as a new snippet in the collection grid section behind the flag; touches product cards on collection pages only; no product-specific values in the template").
- **"Create a specific test" route:** before the finder runs, check the described change. If it fails, say in two short sentences why it can't ship as described and the nearest version that can, then one `AskUserQuestion` (header "Change"): "Build the nearest version (Recommended)" · "Describe a different change" · "Stop here". Never build the original as described.
- **Stage 1 step 6a, after the platform is identified:** re-check the picked test (the platform may differ from the finder's guess; hand-described tests were never checked). A failing test stops before any draft, branch or preview exists: one plain explanation, then one `AskUserQuestion` offering the nearest safe version, up to three other passing tests from this chat's `candidates.json` (more are named in the question text) and "Stop here for now" (at most five options; `ab_flow.cap_options` keeps "Stop here for now" last). Unattended: stop and leave the explanation as the report.
- **Stage 2c, before committing:** write every line under the blast-radius rules, then review the diff file by file: which templates and pages render each changed file; confirm every visible change is inside the gate; search the diff for literals that only make sense for one product or page in a shared file (handles, IDs, SKUs, CDN image paths, prices, one product's title or copy) and refactor them into data or an explicit scoped condition. If it can't be made safe, stop before committing and handle it as the 6a re-check does. Add a short "Blast radius" section to the PR body (and to the `preview`-mode summary): files changed, where each renders, and that control visitors see no change.
