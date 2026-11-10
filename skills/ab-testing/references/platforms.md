# Platforms, what can be tested, and the flag SDK

Read this at three points: when the finder checks its candidates (synthesis rule 3), when a picked test's environment is detected, and before any variation code is written. It holds the platform rules, the blast-radius rules, where each platform's surfaces live, and the one statement of how Noibu's flag SDK is read. Other files cite it and restate nothing from it.

Two questions are asked of every test, at every point where one is proposed or built:

1. **Can this merchant action it?** Hosted platforms lock some surfaces; Shopify's checkout is the best-known case. A test the merchant can't build is noise, however strong its evidence.
2. **Can it be built without risk to the rest of the site?** A variation is production code that ships to *every* visitor and is switched on for B by a flag. Code that is wrong for one product, page or visitor the moment the deploy goes live breaks the store, not just the test. Example: swapping a product's image by hardcoding its URL into the product template changes the image on every product page.

## Which platform

Take the platform in this order: the code tree when a repository is connected (it is what the developer edits), then `noibu_get_domain`'s `siteType`, then business context. `siteType` values map like this: `Shopify` and `Shopify Plus` → Shopify (a Hydrogen/Remix tree means headless: storefront rules follow the repository, checkout rules stay Shopify's); `Big Commerce` → BigCommerce (Stencil, or Catalyst when the tree is a Next.js app); `Salesforce Commerce Cloud` → SFCC (SFRA/SiteGenesis cartridges or PWA Kit); `Magento 2` → Magento (Luma, Hyvä or PWA Studio); `Oracle Commerce Cloud` → OCC (Design Studio components); `Custom`, `Unknown` or missing → use the next source, and if nothing settles it, apply the "Custom / unknown" column below.

## What the merchant can change

"Actionable" means the merchant's own developer can ship a flag-gated variation there with the platform as it stands. The Noibu flag SDK runs as page JavaScript, so a surface that accepts no merchant JavaScript cannot host a variation.

| Surface | Shopify / Shopify Plus | BigCommerce | SFCC | Magento 2 | OCC | Custom / unknown |
| --- | --- | --- | --- | --- | --- | --- |
| Home, collection, search results, PDP, header, announcement bar, footer, cart page and drawer | Yes (theme) | Yes (Stencil or Catalyst) | Yes | Yes | Yes | Yes when a repository is found; otherwise ask where the code lives |
| Checkout steps and thank-you / order status page | **No** on any plan: no theme code or custom scripts run there. Plus can add checkout UI extensions in fixed slots, but they run sandboxed without page JavaScript, so the flag can't gate them: not buildable by this skill | Only when the repository holds a custom checkout (a `checkout-js` fork or Checkout SDK build). Default one-page checkout: additive copy outside form fields via Script Manager at most; never fields, steps, validation or payment | Yes | Yes, higher risk: QA before merge is required | Yes | Only when the repository contains the checkout |
| Card/payment fields, express-wallet buttons themselves | **No** anywhere (payment-provider iframes). Their container on a storefront page (position, order, nearby copy) is fine | | | | | |
| Prices, discounts, shipping rates, payment-method availability | **No** as a front-end test anywhere: platform config or server logic that a page flag can't switch per visitor. A displayed price, discount or rate that differs from what is charged is never acceptable | | | | | |
| Third-party app content (reviews, search/merchandising, upsell, chat) | Container only (move, show, hide, spacing); the app's own markup and copy change in the app | Same | Same | Same | Same | Same |

Checkout as a *metric* is not checkout as a *surface*: on Shopify a cart or PDP change can still use a checkout success metric when readiness shows the counters are recorded and the store isn't split-checkout. Only a change that *sits on* a checkout or thank-you page is ruled out.

## Blast-radius rules (every platform)

A merged variation is live code on every page that renders the file it lives in. These rules keep the control identical for everyone not in B and keep B confined to the element and pages the test names. They govern every test's `devNotes` and all variation code.

1. **Everything visible is behind the flag.** B's markup, CSS and JS run only when the assignment is B. No ungated styles or "harmless" global tweaks. When the flag can't be read (SDK blocked, error, timeout), the visitor gets the control.
2. **Data-driven, never hardcoded in shared templates.** Product, collection and cart templates render for every product: never write one product's image, title, price, copy, URL, handle, SKU or ID into them. Read the value from the platform's data (Shopify product object and metafields, BigCommerce custom fields, SFCC or Magento product attributes) or a merchant-managed setting. When a test applies to a subset of products, scope it explicitly in the gating condition (tag, collection, metafield, ID list held in a setting) and name the subset in `devNotes` and the pull request; every other product renders exactly as today.
3. **Scope every selector and style** under a variation attribute set by the gating helper (e.g. `[data-nb-<flagkey>="b"] .product-card__cta`), never on bare shared classes or by editing a shared stylesheet's existing rules. Before editing a shared component (header, product card, cart line), check where else it renders.
4. **Leave shared logic alone:** add-to-cart and cart-update requests, form actions, variant selection, price, tax, shipping, inventory, redirects into checkout, analytics calls. A test that needs one of these is not a front-end test.
5. **Decide the variation in the browser** unless the cache varies on it. Full-page caches (Magento Varnish/FPC, SFCC `<iscache>`, CDN caching on headless fronts) would store a server-rendered B and serve it to everyone.
6. **Prefer additive files:** B in a new snippet, section, component or module included behind the gate. Layout files (`theme.liquid`, `base.html`, `htmlHead` hooks, `default.xml`) change only to load the gating helper.
7. **Fail closed:** wrap B in try/catch; a missing element means no-op (control). Hide-until-ready only on the tested element, with a short timeout back to control; never hide the page or a section.
8. **No claims the store can't back:** no invented urgency, stock counts, reviews, badges or policy promises; copy matches the store's stated policies.

## Where the rules are applied, and what happens to a test that fails

- **Finder synthesis:** `references/finder.md`, rule 3.
- **"Create a specific A/B test":** before the finder runs, check the described change. If it fails, say in two short sentences why it can't ship as described and the nearest version that can, then ask one question: build the nearest version (Recommended) · describe a different change · stop. Never build the original as described.
- **After a test is picked and the platform is identified:** check the picked test again (the platform may have turned out different from the finder's reading, and hand-described tests were never checked). A test that fails stops before any draft, branch or pull request exists: one plain explanation, then one question offering the nearest safe version, the other tests in this conversation's `candidates.json` that pass, and "Stop here for now". In a scheduled run: stop and leave the explanation as the result.
- **Before variation code is committed or shown:** write every line under the blast-radius rules, then review the diff file by file. For each changed file, list which templates and pages render it and confirm every visible change is inside the gate. Search the diff for literals that only make sense for one product or page in a shared file (handles, IDs, SKUs, CDN image paths, prices, one product's title or copy) and refactor them into data or an explicit scoped condition. If it can't be made safe, stop and handle it as the picked-test check does. Add a short "Blast radius" section to the pull request body (and to the code summary): files changed, where each renders, and that control visitors see no change.

## Where surfaces live, how to see a change, how to prove it is live

| Platform | Where the surfaces usually live | How to see a change before it ships | How to prove the code is live |
| --- | --- | --- | --- |
| Shopify (Online Store 2.0) | `sections/main-product.liquid` (PDP), `sections/main-cart-items.liquid` or a cart drawer snippet (cart), `sections/header.liquid` + `announcement-bar.liquid` (bar), `sections/main-collection-product-grid.liquid` (collection); CSS in `assets/`; JS in `assets/*.js`; sections placed via `templates/*.json` or section-group JSON | An unpublished copy of the live theme built by `noibu_preview_theme_change`, opened at the preview link it returns | `noibu_list_store_themes` shows the published preview as the live theme; then sessions carrying the `ab_rendered_<flagKey>` attribute |
| Shopify (Hydrogen / headless) | `app/routes/products.$handle.tsx`, `app/components/Cart*.tsx`, `app/components/Header.tsx` | The host's preview deployment (Oxygen or the hosting provider's per-branch URL) | The pull request is merged and deployed; then sessions carrying the `ab_rendered_<flagKey>` attribute |
| Salesforce Commerce Cloud | `cartridges/<app>/cartridge/templates/default/product/productDetails.isml`, `cart/cart.isml`, `components/header/*.isml`; client JS under `cartridge/client/default/js/` | A staging or development instance URL the merchant provides | The pull request is merged and deployed; then sessions carrying the `ab_rendered_<flagKey>` attribute |
| Magento 2 | `app/design/frontend/<Vendor>/<theme>/Magento_Catalog/templates/product/view/*.phtml`, `Magento_Checkout/templates/cart/*.phtml`, layout XML under `Magento_Theme/layout/` | A staging environment URL the merchant provides | The pull request is merged and deployed; then sessions carrying the `ab_rendered_<flagKey>` attribute |
| BigCommerce Stencil | `templates/pages/product.html`, `templates/components/products/*.html`, `templates/components/cart/*.html` | A theme preview the merchant's team provides | The pull request is merged and deployed; then sessions carrying the `ab_rendered_<flagKey>` attribute |
| WooCommerce | The child theme's `woocommerce/single-product/*.php`, `woocommerce/cart/*.php`, `header.php`; enqueued JS under the child theme's `assets/` | A staging site from the host | The pull request is merged and deployed; then sessions carrying the `ab_rendered_<flagKey>` attribute |
| Custom / other | Search the tree first for the recorded selectors and copy; ask the user for the file only if the search finds nothing | A staging or preview URL the merchant provides | Sessions carrying the `ab_rendered_<flagKey>` attribute; failing that, a person attests that the deploy is live, and the test is not started on an assumption |

**How the flag script loads.** On every platform the SDK pattern is the same; what differs is where the helper is enqueued so it runs before first paint for above-the-fold changes (Shopify: `layout/theme.liquid` head or the top of the theme's main script; SFCC: the `htmlHead` hook; Magento: a `requirejs-config.js` or layout XML head script; BigCommerce: `templates/layout/base.html`; WooCommerce: `wp_enqueue_script` with a head placement).

**Proof of life is the property that matters:** a test started before its code is live buckets visitors into a variation they cannot see. Nothing here can open the store and look, so proof comes from Noibu's own data: the gating helper below reports the arm each page rendered as the custom attribute `ab_rendered_<flagKey>`, on every visit, from the moment the code is live, whether or not the test has started. Sessions carrying that attribute are proof the code is live and running on real pages (`references/build.md`, Stage 5).

## The flag SDK

Sources: Noibu's developer documentation, and one customer implementation observed in the field (marked as such). Where this says "documented", the developer docs say it; where it says "observed", one store's code does it and it has to be confirmed against the test's own Implementation snippet in the Noibu console before it becomes a rule.

### Keys and values (documented)

- A test's **flag key** is derived by Noibu from the test title when the draft is created, and is domain-prefixed (observed shape: `<numId>-<slug>`, for example `2083-free-shipping-bar`). Read it back from `noibu_list_ab_tests` (`key`) or the create result; never type it from memory, never strip or add the prefix.
- Each **variation's flag value is its variation name** as entered at setup. Variation names are therefore identifiers: keep them URL- and class-safe when naming a new test ("button-above-info" beats "Button above info box"); when the test already exists, use its names as they are and sanitize only in the class name, documenting the mapping.
- Both exist only once the test exists as a draft. Before that, say "derived from the title at creation" and have the developer confirm against the draft.

### Reading the assignment (documented, with one observed gotcha)

- Client: `window.NoibuFeatureFlag.getClient()`.
- Readiness: `client.addHandler("PROVIDER_READY", cb)` when `window.NoibuFeatureFlag` already exists, else the `noibuFeatureFlagReady` window event (`event.detail.client` is the client). Race readiness against a timeout; the loser is the control. 1,000 ms is the documented helper's default; one observed implementation waits up to 10 s after `window.load` for stores whose SDK loads late.
- Simple read: `client.getStringValue(flagKey, controlName)`. Synchronous, never throws, returns the default before the SDK is ready.
- Detailed read: `client.getStringDetails(flagKey, controlName)` returns an object with the arm and a `reason` (`SPLIT` for a live assignment, `CACHED` for a repeat visitor, `FLAG_NOT_FOUND` for a draft or stopped test, plus `errorCode` on failure).
- **Observed gotcha, to confirm:** the console's Implementation panel has been seen to destructure `const { variation } = client.getStringDetails(...)`, while the SDK's details object carries the arm in `variant` (and `value`), e.g. `{ variant: 'show-reassurance', value: 'show-reassurance', reason: 'CACHED' }`. Copied as shown, every visitor falls through to the control with no error. Until the snippet and the SDK are confirmed to agree, code that uses the details object reads `details.variant || details.variation || details.value || CONTROL`, and QA verifies the read on a flag that is already running. If the snippet is confirmed wrong, that is a product bug to report, not a convention to keep.
- Assignment is deterministic per browser and consistent across sessions; visitors excluded by targeting always get the control and never enter the results.

### What Noibu records

- A session is tagged with its arm when the flag is **evaluated**, as a custom-attribute tuple: name = the test's `key`, value = the variation `key`. The regular analytics tools can slice by arm with a `CUSTOM_ATTRIBUTE_TUPLES` `CONTAINS_TUPLE` filter.
- Evaluation is not rendering. Code that evaluates the flag but does not render the variation (partial or late deploy, broken branch) counts visitors into an arm while they see the control, silently. A test started with no evaluation code deployed collects nothing. This is why variation code must be live before a test starts, and why QA verifies the arm actually renders.
- Recommended, not documented: report the arm the page **rendered** as a second custom attribute with a distinct name (for example `ab_rendered_<flagKey>`), so the assigned tuple and the rendered attribute can be compared when a challenger tracks the control suspiciously closely.

### Lifecycle facts that shape the code (documented)

- Variation code must be deployed before the test is started in Noibu.
- While RUNNING only the hypothesis and secondary metrics are editable; variations, split, targeting and the success metric are locked.
- STOPPED is final: the flag turns off and everyone sees the control. Noibu does not roll the winner in; the developer implements the winner directly and removes the flag read.
- Noibu has no force-variant or preview tool. The documented check is `client.getStringDetails(FLAG_KEY, CONTROL).reason === "SPLIT"`, and a scenario can be pinned with `NoibuFeatureFlag.setContext({ targetingKey: "qa-b" })` in separate private windows.

### The gating helper (documented pattern, one per codebase)

Reuse an existing Noibu gating helper when the codebase has one (search for `NoibuFeatureFlag`, `noibuFeatureFlagReady`, `noibu` in layout or theme files, script tags, a package dependency) and copy its pattern exactly. Otherwise add this once, adapted to the codebase's module style, and gate rendering on a root-element class, which diffs smallest and is reversible with one line:

```js
// Noibu A/B test gating. Test: "<Title>"  Flag key: <key or "derived from title at creation">
// Deploy before starting the test in Noibu. Remove the flag read when the test is stopped.
(function () {
  var FLAG_KEY = "<flag key>";
  var CONTROL = "<control variation name>";   // the default: current experience
  var VARIATIONS = ["<variation B name>"];    // every non-control variation name
  var TIMEOUT_MS = 1000;

  function arm(client) {
    if (!client) return CONTROL;
    var d = client.getStringDetails ? client.getStringDetails(FLAG_KEY, CONTROL) : null;
    return (d && (d.variant || d.variation || d.value)) || client.getStringValue(FLAG_KEY, CONTROL) || CONTROL;
  }
  function forced() {
    // QA only: ?nff_<flag key>=<variation name> shows that arm on this page view.
    try {
      var v = new URLSearchParams(window.location.search).get("nff_" + FLAG_KEY);
      return v && VARIATIONS.indexOf(v) > -1 ? v : null;
    } catch (e) { return null; }
  }
  function apply(client) {
    var qa = forced();
    var variation = qa || arm(client);
    if (variation !== CONTROL) {
      document.documentElement.classList.add("nb-test-" + variation);
    }
    if (!qa && window.NOIBUJS && NOIBUJS.addCustomAttribute) {
      try { NOIBUJS.addCustomAttribute("ab_rendered_" + FLAG_KEY, variation); } catch (e) {}
    }
  }
  function onReady(cb) {
    if (window.NoibuFeatureFlag) {
      var client = window.NoibuFeatureFlag.getClient();
      client.addHandler("PROVIDER_READY", function () { cb(client); });
    } else {
      window.addEventListener("noibuFeatureFlagReady", function (e) { cb(e.detail.client); }, { once: true });
    }
  }
  var done = false;
  function once(client) { if (!done) { done = true; apply(client); } }
  onReady(once);
  setTimeout(function () { once(window.NoibuFeatureFlag ? window.NoibuFeatureFlag.getClient() : null); }, TIMEOUT_MS);
})();
```

**Seeing an arm before the test runs.** A draft returns the control to everyone, and nothing outside the page can force an arm. So the helper honours one URL parameter, `nff_<flag key>=<variation name>`, which shows that arm for that page view only and is left out of the rendered attribute. It is how a person checks B on a preview. If the codebase already has its own QA override, use that one.

Make the rendering change depend on `html.nb-test-<variation name>`. For above-the-fold changes the helper must run early (head, or the top of the theme's main script) so the class lands before first paint; below-the-fold changes tolerate a swap after resolution. A CSS-only variation (`html.nb-test-<name> .product__cta { order: -1 }`) is the ideal shape for position, visibility and copy changes; markup changes only when the variation adds something not on the page today.

### Conventions observed in one customer theme (detect, then fall back)

These are not SDK facts. Look for them in an existing theme and mirror them when present; when absent, use the documented helper above and do not introduce them unasked:

- One flag script per test under `assets/noibu-flag-<slug>.js`, and a gate section per test under `sections/noibu-<slug>-ab.liquid` placed through the template or section-group JSON (subtractive gate: the variation markup is always rendered and hidden until the flag says B).
- A paint-time `localStorage` hint so returning visitors do not see a flash before the SDK resolves.
- `noibuFeatureFlagError` handling that falls back to the control.
- Never editing another test's flag file, or control-defining files such as `sections/header.liquid` and `layout/theme.liquid`, while tests run.

### Open question

Which read is canonical for new code, `getStringValue` or `getStringDetails`? This file recommends the details read with the defensive field order because it also yields `reason` for QA, and keeps the simple read as the fallback.
