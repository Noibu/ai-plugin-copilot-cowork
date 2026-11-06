---
name: ab-testing
description: "Find, build and launch A/B tests on a Noibu-monitored store: ranked test ideas from 30 days of Noibu data and the live site, a Noibu draft, flag-gated variation code, a pull request or Shopify preview theme, automated QA, and a started test after your merge. Use for \"what should we A/B test\", CRO or experiment ideas, building a specific test, implementing a test found earlier in this chat, replies such as \"Preview test 2\", \"Create A/B test 2\" or \"Automate the implementation 2\", or taking a Noibu draft test live. Replaces the former ab-test-opportunity-finder skill. Requires the Noibu connector. Do NOT use to read an existing test's results or verdict (querying-noibu-data) or for general store health (store-pulse)."
---

# Noibu A/B test (find, pick, build, run) — Microsoft 365 Copilot Cowork

Takes a Noibu-monitored store from "what should we test?" as far as the user wants: a code preview, a pull request, a Shopify preview theme, or a running experiment. Six stages, three human gates:

0. Resolve the store domain to its Noibu UUID (one call; nothing else runs before the first question)
1. Find opportunities → **user picks one** (the choose-a-test question is the first thing the user sees); then, once a test is picked, detect the environment and ask setup questions only when needed
1b. Summarize the picked test inline and **the user picks what to automate** (the run mode)
2. Draft the test in Noibu, write the variation code, open a pull request
3. Build or locate a preview and run automated QA
4. Hand off: **the user confirms they merged the pull request** (full mode), or picks the next step (partial modes)
5. Verify the code is live, then start the test

Never merge, publish, deploy or start a test before its gate. The only writes before the merge gate are a Noibu **draft** test, a branch + pull request, an **unpublished** Noibu preview theme, and a patch file; a partial mode creates only the subset its option promised (`scripts/ab_flow.py check-write`). The finder half writes nothing in Noibu: its report files and its cart round trip (one item added, then only that line removed) are its only side effects.

"Pull request" (PR) means the provider's equivalent (GitHub or Azure DevOps pull request, GitLab merge request). Questions and cards always say "pull request"; once the run is talking about a specific one, use the provider's own word.

**How Cowork differs from the Claude design:** `references/cowork-host-map.md`. In short: every pick-one-thing card is one `AskUserQuestion`; the findings, per-test and implement cards are Adaptive Cards rendered by this skill's local runner, each followed by one next-step `AskUserQuestion`; a test's full report is a standalone HTML file published to the user's output files; the browser is the user's local Microsoft Edge (`browser_actions`), which reads pages but cannot run page scripts, resize to a phone or download files.

**Legacy name:** this skill replaces `ab-test-opportunity-finder` (21.1.x); requests, schedules and handoffs naming it are handled here unchanged, and legacy `noibu.ab-candidates/2` files still validate.

**Call metadata:** on every `noibu_*` call pass `skill: "ab-testing"` and a short `skillStep`. Load the `querying-noibu-data` skill by name before the first `noibu_*` call.

## When NOT to Use

- Reading an existing test's results, verdict or configuration — `querying-noibu-data`.
- Starting, stopping or editing a test outside this skill's build flow — `querying-noibu-data`'s A/B guidance; stopping is permanent and needs the person's explicit request.
- Fixing a bug, error or slow page — `tech-diagnosis` (a defect inside a test's surface becomes a "Fix first" line here, never a test).
- Store health, checkout, product or segment reporting — `store-pulse`, `checkout-analysis`, `product-analysis`, `segment-analysis`. Accessibility — `accessibility-audit`. Saving business facts — `build-business-context`.

## Setup, on every invocation (before anything else)

1. **Package check.** This skill cannot run without its reference files and scripts. In one `bash` call from the skill's folder, run `ls references/output-format.md references/noibu-query-battery.md references/site-validation.md references/preview.md references/findings-card.md references/run-modes.md references/finder/phases.md scripts/build_page.py scripts/validate_candidates.py scripts/show_card.py scripts/build_presentation.py scripts/dom_facts.py scripts/ab_flow.py`. If any is missing, stop and say so in one line ("The A/B testing skill package is incomplete: <files> are missing. Re-upload the plugin, then run this again."). Do not improvise the queries, reports, `candidates.json` or cards by hand: a hand-rolled run cannot be validated, previewed or acted on.
2. **Browser check.** Is `browser_actions` in the tool list (loaded or deferred)? Looking costs nothing; do not open a tab yet. Present: the first browser step opens the run's tab, and only a failed `create_tab` triggers `references/browser-readiness.md`. Absent, or the person declines: the finder continues on Noibu data alone and QA is deferred. A bot check, login wall, blank page or dead tab mid-run is never bypassed and never ends the run. Scheduled and unattended runs follow their recorded choice. All of this, including the mid-run question and the unattended ladder, is `references/browser-setup.md`: read it now.
3. **Restart or continue.** Every invocation starts at Stage 0 unless this chat already has a run in progress; then ask the "Restart?" question first. The rule, the question and what "start over" drops are `references/invocation.md`, which also holds the task-list wording (the progress bar the user watches; never internal terms). Read it now.

## The two halves and where their text lives

- **The finder half** (`references/finder/`): readiness checks, two batches of Noibu queries, a DOM read of the live site, synthesis, previews, one standalone "Recommended test" report file per test plus `candidates.json`, and the in-chat **findings card** followed by its next-step question. Nothing is published to the user's files until a "Preview test N" reply; once a draft exists the **implement card** offers "Automate the implementation N" (`references/findings-card.md`). It runs only when the user picks "Look for new opportunities" or "Create a specific test" on card 4a. Its four files are read together, in one message, when that route starts: `run-rules.md`, `browser.md`, `goal-and-readiness.md`, `phases.md`; its other references and `scripts/` are used when those files say.
- **The build half**: Stage 0 below, then `references/build/stage-1-pick-and-setup.md` (pick, environment, run mode), then `references/build/stage-2-draft-code-pr.md`, `stage-3-qa.md`, `stage-4-5-handoff-and-start.md`, each read when its stage begins.

## When a reply wakes this chat

Cowork cards can't send button clicks, so each findings, per-test and implement card is followed by one next-step question (`references/findings-card.md`). A choice or typed reply such as "Preview test 2" arrives as the person's own message: it is their decision, so act on it directly, without re-asking, re-ranking or re-validating. This chat's `candidates.json` is the source; the runner's `abReplyMap` binds the reply to what the card showed. Handlers, all in `references/findings-card.md` "Answering a reply":

- **"Preview test N"**: render `test-report-<N>.json` (one `render_ui` via `scripts/show_card.py`) and, in the same response, publish `<domain-short>-test-<N>.html` to the user's output files; then the per-test card's question. An unconfirmed render gets the test as Markdown instead; a failed publish gets one line. Never paste a URL or file path.
- **"Create A/B test N"**: validate candidate and hash, de-duplicate with `noibu_list_ab_tests`, `noibu_create_ab_test` with `createInput` unchanged (a DRAFT only), then the implement card and its question.
- **"Automate the implementation N"**, "build test 2", or a typed request naming a test from this chat: the test is already picked. `references/build/stage-1-pick-and-setup.md` "Entering with the test already picked": load this chat's `candidates.json`, find the test, de-duplicate, skip cards 4a/4b, go to step 6 and Stage 1b. Stage 0 still runs first.
- **"Build this test"** (after "Create a specific test"): Stage 1 from step 3 with that test as the pick. **"Describe a different change"**: ask the specific-test prompt again.

A second "Automate" for a test already being built gets one line pointing at the running build; a second "Create" for a drafted test shows its implement card again (`existing`).

## References (read, never restate)

| File | Read when |
|---|---|
| `references/platform-restrictions.md` | Any test is proposed or built: the finder's synthesis, the "Create a specific test" check, Stage 1 step 6a, Stage 2c. Can this merchant action it, and can it ship without risk to the rest of the site? A failing test is reframed or stopped there, never built as described. |
| `references/shared/platforms.md` | Stage 1 step 6. `references/shared/noibu-feature-flag-sdk.md` before Stage 2b. If either is missing, stop and say the shared A/B references are missing; never work from memory. |
| `references/choice-cards.md` | Any pick-one-thing question: the exact `AskUserQuestion` payloads. |
| `references/shopify-theme-preview.md` | Step 6a finds a Shopify Online Store theme store. |
| `references/git-hosts.md` | Step 6b: providers, repository, PR operations, CI preview config, the patch hand-off. |
| `references/split-checkout.md` | The picked test touches checkout (step 6). |
| `references/run-modes.md` | Stage 1b, and again when a partial mode ends. |
| `references/qa-checklist.md` | Stage 3, or QA deferred to production. |
| `references/scheduling.md` | The person asks for the finder on a cadence. Only the finder is scheduled; a scheduled run never creates or starts anything. |
| `references/handoffs/candidates.md` | Never during a run (`build_page.py` writes `candidates.json`). |

## Stage 0: Resolve the store domain

One call, nothing else: `noibu_get_domain` (fallback `noibu_list_domains`); keep its UUID, `numId`, `siteType` and `companyId` for every call that follows. No other lookup runs before card 4a: provider, repository, theme tools and preview method are detected in Stage 1 step 6, after a test is picked.

## Stage 1 and 1b: in brief (the full steps are `references/build/stage-1-pick-and-setup.md`; read it now)

**Tests live in the chat that found them**: only this chat's `candidates.json` is ever read; never a published report, OneDrive copy, earlier conversation or pasted link.

**Card 4a is the first thing the user sees in every run** (header "A/B test", "What would you like to do for <domain>?"): "Look for new opportunities" · "Create a specific test" · "Implement an existing test" (only when this chat holds a finder run for this domain). No titles, no setup questions on it.

- **Look for new opportunities** → the finder: read its four files plus `noibu-query-battery.md`, `site-validation.md`, `choice-cards.md` in one message, then follow them from Block 1 to the findings card. Stop there and wait for a reply; never ask card 4b after it.
- **Create a specific test** → the prompt in the stage file, the platform-restrictions check, then the finder with that change as the one test; its next-step question is the build question.
- **Implement an existing test** → steps 1 to 3 (collect, validate, de-duplicate), then card 4b.
- Then **step 6** (environment profile: platform and theme gate, provider and repository, preview and proof of live, repository de-duplication and split checkout, and the setup questions only for what is still unresolved) and **Stage 1b** (the inline test summary, then the run-mode question from `references/run-modes.md`; unattended never `full`).

## Stages 2 to 5

Once the mode is recorded, read `references/build/stage-2-draft-code-pr.md` and run Stage 2; then `stage-3-qa.md` when the mode includes Stage 3; then `stage-4-5-handoff-and-start.md`. Read each when its stage begins.

## Local display contract

Cards are rendered with this skill's own copies of the display bundle (`references/card-quickstart.md`; `scripts/show_card.py`, `build_presentation.py`, `console_links.py`, `cowork_card_check.py`, `validate_candidates.py`, `build_page.py`, `dom_facts.py`, `ab_flow.py`): no sibling filesystem dependency. One `render_ui` per response, through the runner; after a host acknowledgement comes only the card's next-step question (`references/ux-guidelines.md`); `status: unknown` is not failure and never permits a second render; the Markdown fallback only as `references/findings-card.md` says; a denial or refusal is respected, never routed around.

## Guardrails

- **Never merge, publish, deploy, start or stop** anything before its gate: the person merges the pull request; a test is started (`noibu_advance_ab_test` RUNNING) only after their merge confirmation AND a verified live check; a test is never stopped by this skill; a preview theme is never published.
- **Pre-merge writes are only** a Noibu DRAFT, a branch + pull request, an unpublished Noibu preview theme and a patch file, and each run mode makes only the subset it promised. The finder writes nothing in Noibu or on the repository; a scheduled run never creates drafts, branches, pull requests or preview themes.
- **Deletes are destructive and always asked:** delete or discard a preview theme only after the person's go-ahead for that exact theme in this run; never delete a Noibu test, a branch or a pull request.
- **Storefront conduct:** add one item and remove only that line; never check out, pay, create an account, enter personal data or sign in on the person's behalf; never bypass a verification page; leave consent choices alone unless a banner blocks the read (then decline, never Accept).
- **Secrets and authorization:** never ask for tokens, passwords or codes in chat; a reply on a card is the person's request, and native approval prompts still apply.
- **Honesty:** every number comes from this run; mobile claims without a phone-size view are inferred; a description is never presented as a screenshot; a capture or a pull request is never claimed unless a tool result shows it.

## Rules that apply throughout

- Platform- and provider-specific steps run only when step 6 detected that platform or provider. Never assume Shopify or GitHub.
- **Connection prompts only when the user has picked the thing they unlock** (`references/run-modes.md`, "When the pick needs a connection"): say in one line which connection would unlock it and ask whether to connect now or continue without; never re-authorization steps or a token.
- The Noibu theme tools run only when the theme gate is open (6a); theme writes go only into the open Noibu theme change this run started; never publish a theme or call a Shopify mutation.
- Work from `candidates.json` for everything it carries; never re-derive or retype it. Cite the shared SDK and platform files instead of copying them.
- Never create a draft, branch or PR for a checkout-metric or checkout-page test on a split-checkout store.
- Link every Noibu issue mentioned to its console URL (`scripts/console_links.py`). **`console.noibu.com` in the browser only when the person is already signed in there**: never sign in for them; prefer the `noibu_*` tools.
- Be explicit about what was verified and what wasn't. Do only what the chosen mode promised.
- **No line after a question.** Every rendered card is followed by its next-step question; after any `AskUserQuestion`, output nothing, then wait.
- **Cards only where something is shown; questions only where something is asked.** The Stage 1b summary and the Stage 4 hand-off are plain structured chat text with real links.
- **Don't narrate.** No "I'm now checking…", no summaries between tool calls, no description of what a card or task list already shows. The chat carries only the gates, a blocker, the end, and the one-line "what you'll see" before each page of visible QA. While the finder runs, its quiet-mode rules apply (`references/finder/run-rules.md`).
- **The end of a finder run is one message**: the findings lead (one sentence per test: title, change, key number; never dropped), the findings card, its Markdown fallback when the runner did not confirm `status: rendered`, then its next-step question, and nothing after it. Not a summary, a bullet per test, a caveat or what the run did on the store: those go on the report as `caveats`. A message that is only the question, with nothing about the tests, is a failed run from the person's point of view.
- **No recap anywhere else either.** Text in the chat is for a question, a blocker, the Stage 1b summary, the merge gate and the Stage 4 hand-off (`references/build/stage-4-5-handoff-and-start.md`); keep it to those lines.
