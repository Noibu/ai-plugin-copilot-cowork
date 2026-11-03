# Creating a Noibu draft from a recommendation ("Create A/B test N")

Purpose: turn a recommendation into a real DRAFT test in the customer's Noibu account when the person who decides asks for it. A draft serves no traffic and stays fully editable; starting it is a separate, explicit step after the variation code is deployed.

In the Claude design the button lived on the hosted report and called the viewer's own connector. Cowork reports are static files with no runtime, so the button became a reply: **"Create A/B test N"** on the findings card or the per-test card (or the report file's "reply Create A/B test N" line). `references/findings-card.md` ("Answering a reply") is the handler: validate the candidate and its createInput hash, de-duplicate with `noibu_list_ab_tests`, check the metric codes against the tool's current schema, then `noibu_create_ab_test` with the test's `createInput` unchanged, then the implement card. `scripts/ab_flow.py plan-create` gives the same decision deterministically.

What the run guarantees, so you know what to promise:
- The finder itself never calls `noibu_create_ab_test`: creating objects in a customer's account is the person's decision. A reply is that decision; native approval prompts still apply, and a denial creates nothing.
- One reply creates one draft. The setup is shown on the per-test card and the report; the existing-test check makes a duplicate impossible (a DRAFT with that title is reused as `existing`; RUNNING or STOPPED stops with one line).
- On success the implement card shows the derived flag key and the numeric id (a console link) and the one reminder that matters: deploy the variation code before starting the test. A duplicate-title rejection from the tool is answered like an existing draft (look it up in the roster). A timeout or "Noibu did not answer" means reconcile with the roster before retrying or claiming anything: the draft may exist.
- Never starts, updates, advances or deletes a test. Location (country) targeting is never set: the tool doesn't support it; the console follow-up says so.

## Mapping a setup block to `createInput`

The setup block is written in the create screen's vocabulary, so each
field maps directly. `domainId`, `rationale`, `skill` and `skillStep` are added at call time;
everything else goes in `createInput` exactly as the tool takes it.

Metric codes in `createInput` come from the run's catalogue
(`references/finder/goal-and-readiness.md`, "The metric catalogue"),
verbatim. A page URL or page group goes only on a page-scoped metric, and
exactly one of the two; the secondary list never exceeds the catalogue's
`maxItems`. A catalogue metric with no row below maps to
`{metric: "<CODE>"}`, plus `pageUrl`/`pageGroup` only when page-scoped.
Before writing `page.json`, check every `createInput` metric against the
catalogue; rewrite or drop a test whose metric isn't in it.

The metric rows below are the **last-known catalogue (October 2026)**:
primary ADD_TO_CART_RATE, CHECKOUT_CONVERSION_RATE, PAGE_VIEW_TO_URL_RATE;
secondary the same plus AVERAGE_ORDER_VALUE, up to 3. (The MCP also
offers REVENUE_PER_SESSION in both lists; it is in the console-exclusion
list in `goal-and-readiness.md`, so it is never used.) Use them as the
catalogue only when the schema could not be read, with the footer line
`goal-and-readiness.md` describes.

| Setup block field | `createInput` |
| --- | --- |
| Title | `title` (verbatim; the backend derives the flag key from it) |
| Hypothesis | `hypothesis` (verbatim) |
| Success metric: Add to cart rate | `successMetric: {metric: "ADD_TO_CART_RATE"}` |
| Success metric: Checkout conversion rate | `successMetric: {metric: "CHECKOUT_CONVERSION_RATE"}` |
| Success metric: Viewed page: \<URL\> | `successMetric: {metric: "PAGE_VIEW_TO_URL_RATE", pageUrl: "<URL>"}` (exact page URL) |
| Success metric: Viewed page: page group \<name\> | `successMetric: {metric: "PAGE_VIEW_TO_URL_RATE", pageGroup: "<name>"}` (name exactly as Batch 1 query #8 listed it) |
| Success metric: Bounce rate on page: \<URL\> | `successMetric: {metric: "<bounce code>", pageUrl: "<URL>"}`; the code is the catalogue's bounce enum value, verbatim. Only once the catalogue has one |
| Success metric: Bounce rate on page: page group \<name\> | `successMetric: {metric: "<bounce code>", pageGroup: "<name>"}` (page group name as Batch 1 query #8 listed it). If the schema doesn't list the bounce code as page-scoped, `{metric: "<bounce code>"}` only |
| Secondary metrics (up to 3) | `secondaryMetrics`: same mapping, plus Average order value → `{metric: "AVERAGE_ORDER_VALUE"}`; "None" → omit |
| Targeting: device type is Mobile / Desktop | `deviceTypes: ["mobile"]` / `["other"]` (no "desktop" value exists; "other" is what the console shows as Desktop) |
| Targeting: UTM \<parameter\> is \<value\> | `utmConditions: [{parameter: "utm_<parameter>", values: ["<value>"]}]`, one entry per condition (ANDed, matching the block's "and") |
| Targeting: location (country) | not supported by the tool: leave it out of `createInput` and say in `setup.targeting` that the country condition is added in the console after creation |
| Targeting: Everyone (skip this section) | omit `deviceTypes` and `utmConditions` |
| Variations: A: Original (control) · B: \<name\>, split equally | `variations: [{name: "Original", isControl: true, trafficSplit: 50}, {name: "<B name>", isControl: false, trafficSplit: 50}]` (three-way: 34/33/33); explicit percentages carry over as written |

The control is always the current experience: `isControl: true` goes on
"Original" and nowhere else. Splits must sum to 100. Variation names
become the flag values the SDK serves, verbatim, so keep the page's
names and the `createInput` names identical.


## What to say

Nothing in chat explains the reply hints. The implement card carries the reminder that variation code must be live before a test is started (shoppers bucketed into a variation whose code is not live see the control while being counted against it, and that data cannot be repaired).

## No implementation control on the report

The report file has no "build" control and nothing that reaches back into a chat: building a test is a chat action. Once a draft exists, the implement card's "Automate the implementation N" reply (or a typed "build test N") starts the build half in the conversation the person is already in. Tests are scoped to the chat that found them, so a report opened elsewhere can only point the reader back to that chat.
