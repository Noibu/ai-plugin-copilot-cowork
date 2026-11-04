# The choice questions: every pick-one-thing moment as one `AskUserQuestion`

The Claude design drew each pick-one-thing moment as a widget card with label-only buttons (`cowork-host-map.md`). Cowork renders no clickable card buttons, so each moment is one `AskUserQuestion` call: a short `header` (12 characters or fewer), the question, and 2 to 5 options, each a label of five words or fewer with a one-line description. There is no catch-all option: the person can always type instead, and a typed answer is matched exactly like a choice. The design's intent is kept: one decision per question, labels that read the same every run, nothing between the question and the options, and **no line after the call** — the question is the message.

When `AskUserQuestion` is unavailable or fails, send the same question as one plain message listing the labels ("Reply with one: …") and wait. Never skip the question because the tool is missing, and never pick for the person. Unattended runs never reach these questions (the finder defaults to "All goals", and the build half never picks a test on its own).

Contents:
1. Card 4a — choose a test (SKILL.md Stage 1)
2. Card 4b — pick an existing test
3. The goal question (finder Block 2)
4. The pages question (page-views and bounce follow-up)
5. The run-mode and follow-up questions (pointer)
6. Other questions (re-invocation, setup, connection, split checkout, blast radius, browser block, schedule, preview themes, merge gate)
7. Reading the answer
8. Option overflow

## 1. Card 4a — choose a test

`header: "A/B test"`, `question: "What would you like to do for <domain>?"`, single select:

| Label | Description |
|---|---|
| Look for new opportunities | Analyze the last 30 days of data and the live site for fresh, ranked test ideas[ for <goal> \| . I'll ask which goal first.] |
| Create a specific test | Describe the change you want to test and I'll build it. When the request already describes a change, the label gets “(Recommended)” and the description quotes the change. |
| Implement an existing test | Pick from the tests found earlier in this chat for <domain>. (Only when this chat holds a finder run for this domain.) |

Claude's labels ("Look for new A/B test opportunities", "Create a specific A/B test", "Implement an existing A/B test") are still matched when typed.

## 2. Card 4b — pick an existing test

`header: "Test"`, `question: "Which test should I implement?"`. One option per surviving test (SKILL.md Stage 1 steps 1–3), by rank, newest run first on ties. Labels and descriptions come from `scripts/ab_flow.py test-options` (never hand-shortened): each label is the title cut to five words or fewer, keeping the word that tells two similar titles apart ("Sticky add to cart mobile" / "Sticky add to cart desktop"), else suffixed `#rank`, or `(run N)` for the same title from two runs; labels are always distinct; the description is the full title exactly as `candidates.json` spells it. No "(Recommended)", source page, metric or "Draft #id" tag: the Stage 1b summary shows the test in full before anything is created. At most five options; with more, the question text ends "…or type another test's name (for example “<title 6>”)." **No tests left:** no question; one line saying why, then ask card 4a with its other two options.

## 3. The goal question (finder Block 2)

`header: "Goal"`, `question: "What do you want these tests to improve?"`. Options from the metric catalogue (`references/finder/goal-and-readiness.md`), in this order: each non-page-scoped primary metric as "Increase <label>" (today "Increase add to cart rate", "Increase checkout completes"), then "Increase checkout starts", "Increase page views", "Reduce bounce rate" once the catalogue has a bounce metric, any newer primary metric, and always last "Show me everything" (description: "Not sure: rank ideas across every goal Noibu can measure"). Each description is one short clause saying what the goal measures. On a split-checkout store the two checkout options are left off.

At most five options: with today's catalogue that is exactly four goals plus "Show me everything". When the catalogue offers more goals than fit, keep the first four goals and "Show me everything", and name the others in the question text ("You can also type: reduce bounce rate"). Never drop "Show me everything".

## 4. The pages question

Only after "Increase page views" or "Reduce bounce rate" (when the bounce metric is page-scoped). `header: "Pages"`, `question: "Which pages?"`:
- Page views: "Product pages" · "Collection pages" · "A specific page".
- Bounce rate: "Homepage" · "Product pages" · "Collection pages" · "A specific page".
Page group names come from the domain's own data where they differ. "A specific page" without a URL gets one plain-text follow-up asking for the URL; a pasted URL is that page.

## 5. The run-mode and follow-up questions

Defined in `references/run-modes.md` sections 3 and 5 (labels, descriptions and order fixed; `scripts/ab_flow.py modes` and `follow_up` produce them).

## 6. Other questions

| Moment | header | Question | Options (label — description) |
|---|---|---|---|
| Re-invocation (SKILL.md) | Restart? | You've started this again for <domain>. Should I start over or continue where we left off? | Start over (Recommended) — Begin again from the domain lookup; anything in progress is dropped · Continue where we left off — Pick up at <step> |
| Setup (Stage 1 step 6e), one call with several questions | Repository / Provider / Staging / Platform | To build “<title>”, where does <domain>'s code live? · Which connected account should I use? · What is the staging URL? (options [] for free text) · Is <store> built on Shopify? | Shopify: Shopify theme · Headless Shopify · Another platform · Not sure |
| Connection needed (run-modes.md section 4) | Code host | To open a pull request for “<title>”, where is <domain>'s code hosted? | GitHub · Azure DevOps · GitLab · Bitbucket (others typed) |
| Connect now? | Connect | <one line on what connecting unlocks> | I've connected it — Re-check and continue · Continue without — Use the next path (patch file / another preview) |
| Split checkout (split-checkout.md) | Next test | Which test should I build instead? | Up to four passing tests (labels from `ab_flow.py test-options`, full title as description) + Stop here for now |
| Blast radius / not actionable (SKILL.md) | Change | <why it can't ship as described>. What next? | Build the nearest version (Recommended) · up to three passing tests (labels from `ab_flow.py test-options`) · Stop here for now |
| "Create a specific test" fails the check | Change | <two sentences> | Build the nearest version (Recommended) · Describe a different change · Stop here |
| Readiness: goal not instrumented | Goal | Add to cart and checkout events aren't recorded here. Switch to page-view goals or stop? | Switch to page views (Recommended) · Stop here |
| Split checkout found in readiness | Goal | Checkout runs on <host>, tracked separately. Which goal instead? | Increase add to cart rate (Recommended) · Increase page views · Stop here |
| Browser blocked mid-run (SKILL.md Setup) | Browser | <page> showed a verification check. How should I continue? | I'll pass it in the browser · Continue without the site |
| Schedule (SKILL.md) | Cadence / Goal / Site check | How often? · Which goal? · Should scheduled runs check the live site? | Weekly · Every two weeks · Monthly / goal labels / Noibu data only (Recommended) · Require the live-site check |
| Preview theme room / reuse / delete (`shopify-theme-preview.md`) | Theme room / Reuse / Delete | as that file says | as that file says, reasons in the descriptions |
| Merge gate (Stage 4, `full`) | Merge | Merge the pull request when you're ready, then tell me. | I've merged it — Confirm it's live, then start the test · Hold, I want changes — Nothing is started |
| Implement fallback (findings-card.md) | Build | Automate the implementation of “<title>”? | Automate the implementation (Recommended) · Not now |

## 7. Reading the answer

The selected label (or a typed reply) is the person's next message. Match it, or any paraphrase:
- Goal: a label or typed reply naming a catalogue metric is that goal; "everything", "all", "not sure" is "All goals". A typed reply describing a change ("test a sticky add to cart button") is the "Create a specific test" route with the change already described.
- Pages: "product", "collection", "homepage", or a URL / "specific page".
- Card 4b, split checkout and blast radius test picks: `scripts/ab_flow.py match-test` — the full title (case-insensitive), then a unique label, then the rank ("test 2", "#2", "the first one"). A reply that matches zero or several tests (two runs with the same title, a partial word) is re-asked with one `AskUserQuestion` listing only those candidates; never take the first match. A described change is "Create a specific test"; "something new" or another goal is "Look for new opportunities".
- No answer, skipped, or one that matches nothing: don't pick. Cowork won't show the question again, so send one short line listing the labels and "say **continue** to see this question again", then wait. On *continue* (or "options", "what now"), ask the same question again.

## 8. Option overflow

`scripts/ab_flow.py` `cap_options(options, 5, keep_last="Stop here for now")` keeps the order, keeps a fixed last option such as "Stop here", and returns what was left off so the question text can name it. Two options minimum; a single possible answer is asked as one plain line instead.
