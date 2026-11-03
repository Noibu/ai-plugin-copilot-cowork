# Variation previews (every test, before delivery)

Purpose: let the merchant *see* each recommended variation next to the current site before anyone builds it, as far as the host honestly allows. Noibu has no force-variant or preview tool, so a recommendation that can be looked at gets discussed and approved; one that has to be imagined stalls. Each test's report shows the current page and the variation, or the reason there is no image, between the evidence and the setup.

This phase runs for every surviving test, between synthesis and building the reports (`references/finder/phases.md`, Phase 4).

## What a preview is, honestly

In the Claude design a preview was the variation's visible change injected into the live page with a short script and captured as screenshots. Cowork's browser cannot run page scripts or inject CSS, so that kind of "after" image cannot be made here. What remains, in order of preference:

1. **A real unpublished preview theme** (Shopify Online Store theme stores only, build half only). When the person picks "Preview on a Shopify theme" or "Launch an end-to-end test", Stage 3 builds B into an unpublished copy of the live theme with the Noibu theme tools (`references/shopify-theme-preview.md`) and opens its preview URL in Edge. That is real rendered code, but it is a build-half write, so the finder never does it.
2. **The before look plus a clearly labelled description of B** (the finder's default). The before look is `get_screenshot` of the surface at the element the change is about (scroll there first with `dom_scroll`/`scroll`); it is your second look at the surface and the basis for an exact description. The variation is described in plain words — what moves where, what text appears, on which pages — from the recorded selectors, the Dev notes and the before look. It is never presented as a screenshot or as what ships.
3. **Text only**, when no browser was available or the surface could not be read: the description with a one-line note saying why there is no image.

Screenshot files: `get_screenshot` returns the image to you; this skill does not assume it is saved in the workspace. A report embeds before/after images only when real image files exist in the run folder (`page.json` `before`/`after` paths relative to it, e.g. captures the person supplied, or a host that does save them); `scripts/build_page.py` checks the files exist and are images, embeds them as data, and otherwise falls back to the description. Never claim a capture exists when it doesn't, never generate a "mockup" image and call it a screenshot.

## The before look (finder)

One step per surviving test, all in the Phase 4 message, on the run's tab:
- `navigate_to` the test's surface (the top URL the site read used, under the top market's prefix on a multi-market store).
- One call: `wait` 3, `dom_scroll`/`scroll` so the element the change is about sits in view (about 260 px from the top), `wait` 2, `get_screenshot`.
- A banner or popup covering the element: its decline or close control once (never Accept), then shoot again. A page whose content never appears (anti-flicker of a testing tool, an endless loader) gets one more try after a 10-second wait; then the variation is description-only with the note "the page did not finish loading in time".
- If the before look shows the variation already in place (the shipping line under the buy box, an add control on cards), the candidate slipped through validation: drop it from `page.json` and record it in `run.killed` (not in a footer line).
- Record what the shot shows in `walkthrough.json` `look` (one sentence per test: the element, its position, anything notable). Never "tidy up" the description beyond the Dev notes' change.

## Mobile

A mobile test (targeting Mobile, or whose evidence is mobile) cannot be previewed at phone size in Cowork: no viewport resize or phone emulation exists. Its `previewViewport` is `"mobile-inferred"`, its description says what B does on phones, and the reports' footer says the mobile layout was not previewed and mobile claims are inferred. Only when the person asks to see it, ask them in one line to narrow their own Edge window to phone width; shoot it and caption it "narrow desktop window, not a phone" (`previewViewport: "narrow-desktop-window"`). Desktop looks are of the person's own window; do not make mobile claims from them.

## Hand the previews to the reports

The previews are not a page of their own: they are fields of each test in `page.json` (`references/output-format.md`):
- `before` and `after`: paths under `previews/test-<n>/<letter>/` only when those image files exist; otherwise `null`.
- `previewViewport`: `"desktop"`, `"mobile-inferred"` or `"narrow-desktop-window"`; `previewKind`: `"capture"`, `"preview-theme"` (set by the build half after a preview theme exists) or `"description"`.
- `beforeAlt`, `afterAlt`, `beforeCaption`, `afterCaption`: what each image shows (only with images).
- `previewNote` when there is no pair: why, in one clause, naming only a cause a tool result showed: "this session could not change the page to show the variation" (the default in Cowork), "no browser was available", "the change is mobile-only and Cowork's browser cannot show a phone-size page", "the page did not finish loading in time", "the store showed a verification page". Never infer a cause from what is loaded on the page.

The report section still renders with the description in the image's place; the per-test card says the same in one line.

## Failure and conduct rules

- Never modify the live site. The finder changes nothing; a preview theme (build half) is an unpublished copy, never the live theme, and is never published.
- Never preview on a checkout page past the cart.
- Never log in, add to cart, or dismiss anything but consent banners and marketing popups during the before look.
- A preview is never an error message, and its absence never holds a report.
