---
name: ab-testing
description: "Find, build and launch A/B tests on a Noibu-monitored store: ranked test ideas from 30 days of Noibu data and the live site, a Noibu draft, flag-gated variation code, a pull request or Shopify preview theme, automated QA, and a started test after your merge. Use for \"what should we A/B test\", CRO or experiment ideas, building a specific test, implementing a test found earlier in this chat, replies such as \"Preview test 2\", \"Create A/B test 2\" or \"Automate the implementation 2\", or taking a Noibu draft test live. Replaces the former ab-test-opportunity-finder skill. Requires the Noibu connector. Do NOT use to read an existing test's results or verdict (querying-noibu-data) or for general store health (store-pulse)."
---

# Noibu A/B test (find, pick, build, run) — Microsoft 365 Copilot Cowork

Takes a Noibu-monitored store from "what should we test?" as far as the user wants: a code preview, a pull request, a Shopify preview theme, or a running experiment. Six stages, three human gates:

0. Resolve the store domain to its Noibu UUID (one call; nothing else runs before the first question)
1. Find opportunities → **user picks one** (the choose-a-test question is the first thing the user sees; "Look for new opportunities" runs the finder half of this skill, and "Implement an existing test" asks which of the tests already found in this chat); then, once a test is picked, detect the environment (repository provider, commerce platform, how code reaches production) and ask setup questions only when needed
1b. Summarize the picked test inline and **the user picks what to automate** (the run mode)
2. Draft the test in Noibu, write the variation code (with Noibu's implementation code in it), open a pull request
3. Build or locate a preview and run automated QA
4. Hand off: **the user confirms they merged the pull request** (full mode), or picks the next step (partial modes)
5. Verify the code is live, then start the test

Never merge, publish, deploy or start a test before its gate. The only writes before the merge gate are a Noibu **draft** test, a branch + pull request, an **unpublished** Noibu preview theme, and a patch file — and a partial mode creates only the subset its option promised (`scripts/ab_flow.py check-write` encodes this). The finder half writes nothing in Noibu at all: its report files and its cart round trip (one item added, then only that line removed) are its only side effects.

"Pull request" (PR) means the provider's equivalent: GitHub or Azure DevOps pull request, GitLab merge request. Questions and cards always say "pull request" and never name a provider; once the run is talking about a specific one (the hand-off summary, the merge gate), use the provider's own word.

**How Cowork differs from the Claude design (read once):** [references/cowork-host-map.md](references/cowork-host-map.md) maps every Claude tool, widget and button of the original design to its Cowork equivalent. In short: every pick-one-thing card is one `AskUserQuestion`; the findings, per-test report and implement cards are Adaptive Cards rendered by this skill's local runner, each followed by one next-step `AskUserQuestion`; a test's full report is a standalone HTML file published to the user's output files; the browser is the user's local Microsoft Edge (`browser_actions`), which reads pages but cannot run page scripts, resize to a phone or download files.

**Legacy name:** this skill replaces `ab-test-opportunity-finder` (21.1.x). A request, schedule, report action or handoff naming that skill or workflow id is handled here unchanged; legacy `noibu.ab-candidates/2` files still validate.

**Call metadata:** on every `noibu_*` call pass `skill: "ab-testing"` and a short `skillStep`. Load the `querying-noibu-data` skill by name before the first `noibu_*` call (orderBy rule, row caps, measure uniqueness, domain resolution, sibling-domain check).

## When NOT to Use

- Reading an existing test's results, verdict or configuration ("how is the sticky bar test doing?") — `querying-noibu-data` (`noibu_get_ab_test_results`, `noibu_list_ab_tests`).
- Starting, stopping or editing a test outside this skill's build flow — answer through `querying-noibu-data`'s A/B guidance; stopping is permanent and needs the person's explicit request.
- Fixing a bug, error or slow page — `tech-diagnosis` (a defect inside a test's surface becomes a "Fix first" line here, never a test).
- Store health, checkout, product or segment reporting — `store-pulse`, `checkout-analysis`, `product-analysis`, `segment-analysis`.
- Accessibility findings — `accessibility-audit`. Saving brand or business facts — `build-business-context`.

## Setup: the browser, and what to do when it is missing or blocked

The live-site read, the before look, the cart round trip and QA need a browser on the storefront. Cowork has one: the user's local **Microsoft Edge**, through `browser_actions` (`create_tab`, `navigate_to`, `get_dom`, `get_screenshot`, `click`/`dom_click`, `type`/`dom_type`, `scroll`, `wait`, `list_tabs`, `request_browser_interaction`, `request_user_form_fill`). It reads the DOM and takes screenshots that come back to you (not assumed to be saved as files). It **cannot** run page JavaScript, inject CSS, emulate a phone or resize the window, download files, or open internal browser pages. [references/finder/browser.md](references/finder/browser.md) has the details; the walkthrough scripts of the Claude design are replaced by DOM reads parsed with `scripts/dom_facts.py` plus a per-surface look.

Check the tool list first, on every invocation, before the re-invocation question and before Stage 0: is `browser_actions` present (loaded or deferred)? Looking costs nothing; do not open a tab yet.

- **Present:** the first browser step (Block 2's readiness message) opens the run's tab with `create_tab` on the store URL. If it fails because no local browser is connected, follow [references/browser-readiness.md](references/browser-readiness.md) **only then**, in one short message: which step is blocked and the user-controlled path (Edge installed, Cowork open in Edge, same work account, organization browsing enabled, first-run consent through the host's own interface). Never invent control names or setup links; never ask for passwords, cookies, tokens or codes. Continue every non-browser step meanwhile.
- **Absent, or the person declines:** no browser. The finder continues on Noibu data alone (the no-browser path in `references/finder/phases.md`, `site-validation.md` and `preview.md`: text-only previews, structural claims marked inferred, a footer line naming what was not checked), and the build half's QA is deferred to production or to the person's own check as `references/build/stage-3-qa.md` allows.

**Switching mid-run.** A bot-verification page ("unusual activity", a slider or puzzle), a login wall, a blank page, a tab that no longer answers (`tab-not-found`), or the person declining site access is never bypassed and never ends the run. Tell the person in one short message what happened on which page and offer, with one `AskUserQuestion`: "I'll pass it in the browser" (`request_browser_interaction` with `reason_type` `captcha` or `security_verification`, the person completes it in the take-control UI, then the run continues there) · "Continue without the site" (Recommended when unattended). A `tab-not-found` follows the tool's own rule: one `create_tab` retry, then say the tab could not be reopened. Record the cause in `walkthrough.json`'s `meta.couldNotComplete`; the surface not read gets no "already exists" check and its candidates carry that caveat.

**What stays true in every case.** A surface no browser read gets no "already exists" check, so its candidates are proposed with that caveat; every mobile claim is marked inferred (no phone-size capture exists in Cowork); a preview slot with no image carries a one-clause `previewNote` naming the real cause; a footer line says whether Edge read the site or no browser did, so a merchant knows how much weight the live-site findings carry.

**Scheduled run** (a task created by "Scheduling a recurring run" below): it runs unattended and the local browser may not be connected. The schedule records the person's choice: **"Noibu data only"** (every output says "No live-site check (scheduled run)" in the card header, on every report and as `liveSiteCheck: "not-performed"` in `candidates.json`) or **"Require the live-site check"** (when `browser_actions` is absent or the first `create_tab` fails, report that plainly in one line and stop; do not fall back to data alone, because a scheduled page without a site read looks like a full read to whoever opens it later). A required check that answered at the start and fails mid-run is recorded in the report like any mid-run failure.

**Any other unattended run** (a chat where the person has stopped replying): apply the same ladder without asking; say which rung the run ended on in the report caveats.

## Where to start when the skill is invoked

Once the Setup check is done, every invocation starts at Stage 0 unless this chat already has a run of it in progress. "In progress" means an earlier invocation in this same conversation got past Stage 0 and has not reached its end (the closing line of a partial mode's follow-up question, a started test, or a run the user told you to stop). A new chat, or a chat where the only earlier invocation was the one that just opened, has no run in progress: start at Stage 0, with nothing carried over from anything you may remember about this domain.

When a run is in progress and the skill is invoked again, the person means either "that went wrong, start again" or "carry on". Ask with one `AskUserQuestion` right after the Setup check and before anything else, not even the Stage 0 lookup:

- **Question (header "Restart?"):** "You've started this again for <domain>. Should I start over or continue where we left off?" When the new request names a different domain, say both: "…for <new domain>, while a run for <old domain> is in progress…".
- **"Start over (Recommended)"** — "Begin again from the domain lookup and the first question. Anything in progress is dropped." Recommend "Continue" instead only when the run is past Stage 2 (a draft, branch, PR or preview theme already exists), since starting over would leave those behind.
- **"Continue where we left off"** — "Pick up at <the last gate or step reached>." Name the step in plain words ("the goal question", "the run-mode question", "the pull request on GitHub").

**Start over** means a clean run: delete every pending or in-progress task of the earlier run (completed ones stay), forget the domain UUID, the picked test, the goal, the environment profile and the run mode, close any browser tab the earlier run opened, then run Stage 0 and ask card 4a. A finder run that already finished in this chat keeps its working folder, so its tests still appear under "Implement an existing test"; only the interrupted work is dropped. Nothing the earlier run created in Noibu, on the repository or in the theme library is deleted (de-duplication in Stage 1 step 3 and step 6d picks them up). **Continue** means resume at the last gate or step with everything kept; when the new request names a different domain, point that out in one line and still continue the old run.

No answer: do not pick for them. Send one short message asking them to reply "start over" or "continue", and wait.

This question is for a bare re-invocation only. A request in the "already picked" shape (below) is a decision, not a restart.

## The task list (the progress bar the user watches)

When `TaskCreate`/`TaskUpdate` are available, the task list is the progress bar; when they are not, skip it silently. Every task reads as a plain-language line about what is being done for *them*: never "Stage 0", "Stage 1b", "step 6", "finder", "environment profile", "candidates.json" or any other internal term, and no numbering. Mark each in progress when its work starts and done when it ends; don't narrate updates.

| When | Task (adapt the wording) |
|---|---|
| At the start | "Choose what to test on <domain>" |
| At the start | "Check your store and code setup" |
| At the start | "Choose what to automate" |
| Stage 2, always | "Draft the test in Noibu and write the variation code" (in `pr` and `full` add "Open a pull request"; in `preview` and `theme`, "Prepare the code preview") |
| Stage 3, in `full` and `theme` | "Preview the change and run QA" |
| Stage 4, always | `full`: "Hand off for your review and merge"; partial modes: "Show what was built and offer the next step" |
| Stage 5, in `full` | "Confirm the code is live and start the test" |

The finder's own tasks are "Analyze 30 days of Noibu data", "Check the live store" and "Prepare your ranked test ideas". A task whose work is skipped is deleted, not left pending.

## The two halves and where their text lives

- **The finder half** (`references/finder/`) finds the test opportunities: readiness checks, two batches of Noibu queries, a DOM read of the live site, synthesis, previews, one standalone "Recommended test" report file per test plus `candidates.json`, and one in-chat Adaptive Card: the **findings card** (one block per test under "Test N": "What to change" over the title and the change, "Why this test" over the measured problem), followed by the next-step question (Preview test N · Create A/B test 1). Nothing is published to the user's files until a "Preview test N" reply. Once a draft exists, the **implement card** offers "Automate the implementation N". `references/findings-card.md` has both cards and their replies. The finder runs when the user picks "Look for new opportunities" or "Create a specific test" on the first question, and never otherwise. Its four files are read together, in one message, when that route starts: `run-rules.md`, `browser.md`, `goal-and-readiness.md`, `phases.md`. Its other references (`noibu-query-battery.md`, `site-validation.md`, `preview.md`, `output-format.md`, `create-drafts.md`, `findings-card.md`) and `scripts/` are read and used when those files say.
- **The build half** (this file's Stages 0 to 1b, then `references/build/`): environment detection, the questions, the run-mode question, then draft → code → PR → QA → merge gate → start.

## Entering with the test already picked

A reply on the implement card ("Automate the implementation 2"), or a typed request naming a test by rank or title from this chat's recommendations ("build test 2", "automate the Quick add on collection cards test"), is the decision to build that test. It may also say "It's already in Noibu as A/B test 1234". Treat it as already picked; asking them to choose again would read as the reply not landing. Stage 1 changes to:

1. Load that run's `candidates.json` from the finder's working folder in this chat (next to the `<domain-short>-test-<rank>.html` reports). Accept it under step 2's rules (schema, domain). The tests a finder run produces live only in the chat that ran it: never fetch a `candidates.json` from a published report, OneDrive, an earlier conversation or a pasted link. If this chat has no finder run for that domain, say in one line that the tests from that report aren't available in this chat and that "Look for new opportunities" here will produce a fresh set, then ask card 4a.
2. Find the test by `title` (exact, then case-insensitive), falling back to `rank`. If neither matches, say which tests the run has and ask which one with one `AskUserQuestion` (the only question on this path).
3. Run step 3's de-duplication for that one test (RUNNING or STOPPED with its title → stop and say so; a DRAFT is adopted in 2a); step 6d then finds any open PR on the same idea, which the new PR supersedes.
4. Skip cards 4a and 4b and go to step 6, then Stage 1b. Stage 0 still runs first.

Everything after Stage 1 is unchanged, including Stage 1b: the reply says *which* test to build, not how much to automate. A request that merely mentions a report without naming a test, or names one but asks to reconsider or compare, is the normal path: ask card 4a.

## When a reply wakes this chat

Cowork cards can't send button clicks, so each findings, per-test and implement card is followed by one next-step question (`references/findings-card.md`). A choice or typed reply such as "Preview test 2" arrives as the person's own message: it is their decision, so act on it directly, without re-asking, re-ranking or re-validating. `candidates.json` in this chat's working folder is the source; the runner's `abReplyMap` (rank → title → createInputHash) binds the reply to what the card showed.

- **"Preview test N"** (also "Learn why and preview variation N", "open the report for test N"): render that test's report card from `test-report-<N>.json` (one `render_ui` through `scripts/show_card.py`, as `references/findings-card.md` "Answering a reply" says) and, in the same response, publish `<domain-short>-test-<N>.html` to the user's output files (`references/output-format.md`, "Delivering a report file"). Other tests' files stay unpublished until their own reply. Then the per-test card's next-step question, and nothing after it. Only a failure gets one line saying what failed. Never paste a URL or file path in chat.
- **"Create A/B test N"**: `references/findings-card.md` "Answering a reply": validate the candidate and hash, de-duplicate with `noibu_list_ab_tests`, call `noibu_create_ab_test` with the test's `createInput` unchanged to create only a DRAFT, then render the implement card and its next-step question. The reply is the authorization; native approval prompts still apply. Nothing after the question.
- **"Automate the implementation N"**: the "already picked" entry above, continuing from Stage 1's de-duplication; Stage 2a adopts the draft.

A second "Automate" reply for a test already being built gets one line pointing at the build already running, not a second build. A second "Create" reply for a test already drafted shows its implement card again (`existing`).

## Shared references (read, never restate)

- **SDK** — `references/shared/noibu-feature-flag-sdk.md`: flag keys and variation values, reading the assignment (incl. the `variant` vs `variation` gotcha), what the platform records, lifecycle, the gating helper, customer-theme conventions.
- **Platforms** — `references/shared/platforms.md`: identifying the platform, where each surface lives, how to see a change before it ships, how to prove code is live.
- **Platform restrictions and blast radius** — this file, below.
- **Hand-off** — `references/handoffs/candidates.md`: `candidates.json` (`noibu.ab-candidates/3`).

Read `platforms.md` in Stage 1 step 6 and `noibu-feature-flag-sdk.md` before Stage 2b. If one is missing from this skill's folder, stop and say the shared A/B references are missing; don't work from memory. If a shared file contradicts what you observe, follow its own instruction for that case and report the discrepancy; never patch around it here.

## The build half's references (read only when the condition holds)

| File | Read when |
|---|---|
| `references/shopify-theme-preview.md` | Stage 1 step 6a finds a Shopify Online Store theme store. Covers the Noibu theme tools gate, building the preview, Shopify MCP read-only checks, and preview-theme housekeeping. |
| `references/git-hosts.md` | Stage 1 step 6b: provider discovery, repository resolution, PR operations per connected provider, PR templates, CI preview config, the patch hand-off. |
| `references/split-checkout.md` | The picked test touches checkout (Stage 1 step 6). |
| `references/choice-cards.md` | Any pick-one-thing question: card 4a, card 4b, the goal and pages questions, the setup, connector and stop questions. The `AskUserQuestion` mapping for every Claude card. |
| `references/run-modes.md` | A test has just been picked (Stage 1b), and again when a partial mode ends (Stage 4). |
| `references/build/stage-2-draft-code-pr.md` | The run mode is known. |
| `references/build/stage-3-qa.md` | A mode that includes Stage 3 reaches it (`full`, `theme`, or a follow-up "QA it, then merge and start"). Also governs the browser in Stage 5. |
| `references/build/stage-4-5-handoff-and-start.md` | Stage 2 (or 3) is done. |
| `references/qa-checklist.md` | Stage 3, or QA deferred to production (Stage 5). |

## Stage 0: Resolve the store domain

One call, nothing else: `noibu_get_domain` (fallback `noibu_list_domains`); keep its UUID, `numId` (the theme tools need it), `siteType` and `companyId` for every call that follows. The finder's Block 2 reuses this result. No other lookup runs before card 4a: provider, repository, theme tools and preview method are detected in Stage 1 step 6, after a test is picked.

## Stage 1: Find opportunities and let the user pick

**Tests live in the chat that found them.** A finder run's output (`candidates.json` next to the `<domain-short>-test-<rank>.html` reports in this chat's working folder) is the only place this skill reads tests from. Earlier chats, OneDrive copies, published report files and pasted links are never loaded: a test proposed weeks ago was ranked against data and a site that have moved on.

**The choose-a-test question (card 4a) is the first thing the user sees in every run.** The pick-an-existing-test question (card 4b) appears only after "Implement an existing test". Steps 1 to 3 gather and clean tests for 4b, so they run only then. Environment detection and setup questions come in step 6, after the pick.

1. **Collect the tests this chat already has** (only on the way to card 4b): one `candidates.json` per finder run in this chat's working folders. A pasted link gets one line saying that report's tests aren't available here and a fresh run will produce a new set; no fetch.
   - **Pass the goal through.** When the finder runs and the request already says what to improve ("lift add to cart rate"), state that goal in the finder's terms so it skips its goal question. When the request names no goal, let the finder ask.
   - **After the finder, the findings card is the next step.** The finder ends with its findings card and its next-step question, then waits. Do not ask card 4b after it. Answer whichever reply comes (see "When a reply wakes this chat").
2. **Load `candidates.json`** for each run. Accept it only if `schema` is `noibu.ab-candidates/3` (or a legacy `/2`) and `domainId` matches; `scripts/validate_candidates.py` decides. No age check. If a run's `goal` differs from the request's goal, leave its tests off 4b unless that empties it (then show them with their goal named). A missing or failing file: say so in one line only if 4b ends up empty.
3. **De-duplicate before card 4b**, starting from the file:
   - `killed`: never re-offer those ideas.
   - `existingTests` is the finder's snapshot; refresh it with one `noibu_list_ab_tests` (all statuses). A test whose title matches a candidate's `createInput.title`: RUNNING or STOPPED → drop or flag it; DRAFT → keep it (2a adopts it).
   - Note running tests on the same page or element (overlap risk), alongside each test's `overlap` line.
4. **Ask the questions** ([references/choice-cards.md](references/choice-cards.md) has the exact `AskUserQuestion` payloads).

   **4a. Choose a test** (every run except the "already picked" entry). Header "A/B test", question "What would you like to do for <domain>?", up to three options in this order:

   | # | Label | Description |
   |---|---|---|
   | 1 | Look for new opportunities | "Analyze the last 30 days of data and the live site for fresh, ranked test ideas." + "for <goal>" when the request named one, else "I'll ask which goal first." |
   | 2 | Create a specific test | "Describe the change you want to test and I'll build it." When the request already describes a change, add "(Recommended)" to the label and quote the change. |
   | 3 | Implement an existing test | "Pick from the tests found earlier in this chat for <domain>." |

   Option 3 appears only when this chat holds a finder run for this domain (a glance at the working folder, not a lookup); otherwise options 1 and 2 only, and nothing is said about the missing third. No test titles and no setup questions on this question.

   **4b. Pick an existing test.** Only after "Implement an existing test" (steps 1 to 3 first); never after a finder run. Header "Test", question "Which test should I implement?", one option per surviving test by `rank` (newest run first on ties), labels and descriptions from `scripts/ab_flow.py test-options` (distinct labels of five words or fewer, the full title as the description). `AskUserQuestion` takes at most five options: show the top five; when more survive, name the rest in the question text ("…or type the name of another, e.g. <title 6>"); a typed name still matches. No "(Recommended)", source page, metric or "Draft #id" tag. **No tests left:** say why in one line, then ask 4a's other two options.
5. Do not continue until the user picks.
   - **A test (4b):** match the answer with `scripts/ab_flow.py match-test` (full title, then a unique label, then rank). Zero or several matches (the same title in two runs, a partial word) are re-asked with only those candidates; never take the first. From here, that entry is the source for everything it carries; never retype a field the file has.
   - **"Implement an existing test":** steps 1 to 3, then 4b.
   - **"Look for new opportunities":** run the finder: in one message read the four `references/finder/` files plus `noibu-query-battery.md`, `site-validation.md` and `choice-cards.md`; in the next, Block 1 (`run-rules.md` rule 1); then follow the finder files from Block 2 to Phase 5 through the reports and the findings card. Stop there and wait for a reply. If the finder stopped at readiness, its one sentence stands; when it named a sibling domain and the user takes that up, start again from Stage 0 with it. If the finder failed or returned no tests, say so in one line and ask 4a again.
   - **"Create a specific test":** if the change isn't described yet, send exactly this and wait:

     > What would you like to test on <domain>? Tell me the change, which page it's on, and (if you know) what it should improve — e.g. add to cart rate, checkout starts, checkout completes, or product page views.

     Before running anything, check the change against "Platform restrictions and blast radius" using Stage 0's `siteType`; a change that fails gets that section's answer. Then run the finder with that change stated as the test to build, so it checks it against the data and the live site, previews it and writes one test to `candidates.json`; continue from step 3 with it as the pick, no card 4b. If the finder can't produce it, build `createInput` from the description (title = the change; hypothesis says it was requested directly with no measured gap; metric = the user's goal, ask if none; `origin: "user-requested"`), and say in the Stage 4 summary that it had no measured evidence.
   - **A typed answer:** a described change is "Create a specific test"; a named test is that test; "something new" or another goal is "Look for new opportunities".
   - **No answer:** don't pick. One short message listing the options, then wait.
6. **Detect the environment, check split checkout, then ask the setup questions.** Run 6a to 6d silently (nothing in chat) and record an **environment profile**: provider and account, repository, default branch, write path, platform, Noibu theme tools available / not, Shopify MCP matched read-only / off, preview method, proof-of-live method. Read `platforms.md` here.

   **6a. Platform, then the theme preview gate.**
   1. **Identify the platform** as `platforms.md` says (code tree first, else `siteType`, else the site read's platform, else business context).
   2. **Shopify Online Store theme?** Signals in order: `candidates.json` `storefront.shopifyOnlineStoreTheme` / `platform`; `siteType` Shopify/Shopify Plus plus a theme signal; business context. Headless (Hydrogen, a custom front end) has no theme to preview. Unclear and needed → ask in the 6e question.
   3. **Theme gate** (`references/shopify-theme-preview.md` section 1): **open** when the store is a Shopify Online Store theme AND the Noibu theme tools (`noibu_start_theme_change`, `noibu_edit_theme_file`, `noibu_write_theme_file`, `noibu_preview_theme_change`, `noibu_list_store_themes`) are in the tool list AND Stage 0 returned the domain's `numId`. Checking is reading the tool list, no call. A Shopify MCP connector (`get-shop-info`, `graphql_query`) is optional and read-only: if present, one `get-shop-info` confirms the shop matches the Noibu domain; it unlocks the Admin API checksum proof of live, never a write.
   4. **Check the picked test is actionable and safe on that platform** ("Platform restrictions and blast radius"). A test that fails stops here, before any draft, branch or preview exists.

   **6b. Repository provider, repository and write path** (`references/git-hosts.md`).
   1. **Discover providers** with the plugin's provider rule (`querying-noibu-data/scripts/action_policy.py` `repository_provider_plan`, explained in `tech-diagnosis/references/github-handoff.md`): look for connected GitHub and Azure DevOps tools (and GitLab or Bitbucket only when a connector for them is actually in the tool list); verify authentication with one read per provider (`get_me`; `core_list_projects`); deduplicate tool surfaces of the same account, not distinct accounts. Zero eligible → recorded as missing (asked only if the user picks a pull-request mode); one → reuse it with a read-only scope check; several → ask which in 6e. Capabilities are separate: repository read, pull request, pipeline.
   2. **Find the repository**, in order: a repository URL the user gave; a "Variation code: <PR link>" line in the picked test's Noibu draft or a sibling test's hypothesis (from step 3's `noibu_list_ab_tests`); existing work step 3 found; then search the provider for the store's name/domain and for code mentioning `NoibuFeatureFlag` (earlier A/B PRs naming flag keys are the strongest signal). Confirm access with one read. Ask only if all of that fails (6e).
   3. **Write path**, first that works: (1) the connected provider's tools (branch, file write, pull request — see `git-hosts.md`); (2) nothing can push: build a patch (`references/build/stage-2-draft-code-pr.md` 2e) against the real repository files and hand it over with the PR body ready to paste. Cowork has no git CLI with the user's credentials; never ask the user to paste a token.

   **6c. Preview method and proof of live.**
   - **Preview**, first that applies: (1) theme gate open → an unpublished Noibu preview theme (`references/shopify-theme-preview.md`); (2) the repository's CI posts a per-PR preview deployment — decide from the CI config files (`git-hosts.md`), don't guess; (3) the platform's "how to see a change before it ships" from `platforms.md` (usually a staging URL the merchant provides — ask in 6e); (4) none possible: QA on production after merge and before Start (the flag returns the control for everyone until the test starts); say so plainly at the merge gate.
   - **Proof of live:** `platforms.md`'s method for the platform. The Admin API checksum route only through a matched Shopify MCP with theme read access (read-only `graphql_query`); otherwise the served-asset check in Edge (`get_dom` of the page or asset, looking for the flag key), and failing that a human attestation.

   **6d. De-duplicate on the repository and check split checkout.**
   - List branches and open PRs for A/B work on the picked idea (`ab-` names, its flag key, the element). A new PR says which one it supersedes; 2a adopts an open one on the same test.
   - If the test touches checkout (a checkout success metric or a `checkout` `surfaceTemplate`), follow `references/split-checkout.md` before creating anything.

   **6e. The setup questions.** Only what 6a to 6c left unresolved goes to the user, in one `AskUserQuestion` call (several questions in one call: provider account, repository, staging URL, "Is <store> built on Shopify?"), with the test named so the user sees why ("To build “<title>”, where does <domain>'s code live?"). Nothing unresolved → no question; go straight to Stage 1b.

## Stage 1b: Summarize the test and let the user pick what to automate

The user has said *which* test; this stage asks *how much* of the rest to automate, before anything more is created. Read `references/run-modes.md` and follow it. In short:

1. **Build the option list** (`scripts/ab_flow.py modes`): `full`, `pr` and `preview` always; `theme` whenever the store runs on a Shopify Online Store theme, theme tools or not. Order never changes. Labels and descriptions are fixed and generic: never a provider, repository, branch, connector or preview method.
2. **Summarize the test inline, as chat text** (`run-modes.md` section 3): one two-column table with the title, what changes and why (at most two evidence numbers), where / targeting / success metric / volume, overlap and fix-first when present, and the "A/B test in Noibu" line linking the test in the console. Every value from the picked test's `candidates.json` entry.
3. **Then the automation question:** one `AskUserQuestion` (header "Automate", question "What would you like to automate?", the mode labels and descriptions). Output nothing after it and wait. Don't start Stage 2 speculatively.
4. **Match the answer to a mode** (`run-modes.md` section 4) and check it against the profile. A pull-request mode with no eligible provider asks where the code is hosted and how to connect it; the theme preview without the Noibu theme tools says what is missing (`run-modes.md`, "When the pick needs a connection"). Then record the mode, add its tasks and continue. A reply that edits the test is applied first and the summary and question shown again; a reply naming another test goes back to Stage 1 step 5.
5. **Unattended:** never `full`, and no connection prompt. `pr` when a PR can be opened, else `preview`; say so at the top of the report.

Which stages each mode runs: `full` 2 → 3 → 4 (merge gate) → 5; `pr` 2 → 4 (follow-up); `theme` 2a–2c → 3 → 4 (follow-up); `preview` 2a–2c, 2e → 4 (follow-up). The follow-up question after a partial mode offers the longer modes, reusing everything already made, so choosing less now never costs the option of more later.

## Stages 2 to 5

Once the mode is recorded, read `references/build/stage-2-draft-code-pr.md` and run Stage 2; then `references/build/stage-3-qa.md` when the mode includes Stage 3; then `references/build/stage-4-5-handoff-and-start.md`. Read each when its stage begins, not all at once.

## Platform restrictions and blast radius

Two questions are asked of every test, at every point where one is proposed or built:

1. **Can this merchant action it?** Hosted platforms lock some surfaces; Shopify's checkout is the best-known case. A test the merchant can't build is noise in the report and a dead end in the build half, however strong its evidence.
2. **Can it be built without risk to the rest of the site?** A variation is production code that ships to *every* visitor and is switched on for B by a flag. Code that is wrong for one product, page or visitor the moment the theme goes live breaks the store, not just the test. Example: swapping a product's image by hardcoding its URL into the product template changes the image on every product page once the theme is published.

It is applied at the four points under "Where it is applied"; `references/finder/phases.md` Phase 3 and `references/build/stage-2-draft-code-pr.md` Stage 2c point back here.

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

## Scheduling a recurring run

Triggered when the person asks for the finder on a cadence ("run this every Monday", "look for new tests each month"). What gets scheduled is the finder half only: "Look for new opportunities" with the goal fixed, ending at the report files and the findings card. A scheduled run never creates drafts, branches, pull requests or preview themes and never starts a test, even when asked to build; building needs the human gates of a live conversation. Follow `querying-noibu-data/references/scheduling-delivery.md`:

1. **Settle cadence, goal and the live-site check** with one `AskUserQuestion` call holding only what the request left unsaid: cadence (weekly / every two weeks / monthly, day and time in the person's own timezone); goal in the finder's terms (`references/finder/goal-and-readiness.md`; "All goals" is valid; offer this chat's earlier goal as the default); and the live-site check ("Noibu data only" — Recommended, because a scheduled run usually has no local browser — or "Require the live-site check", which stops a run that cannot reach Edge). No digest, automation or connector questions. If the person wants results delivered by email or Teams, the shared delivery rules apply in full, including chat confirmation of the exact final email recipient list EVEN IF addresses were supplied, before anything is scheduled.
2. **Create the schedule with `SetupScheduledPrompt`** (execution mode `separate`, `required_tools` naming the Noibu tools the run reads, plus the browser tool when the check is required; no write permissions requested). Name it "A/B test ideas for <domain>". Description (fill the brackets; no tool names, paths or scheduling words):

   > Look for new A/B test opportunities for [domain] as an unattended run for the goal [goal], with no questions. Live-site check: [Noibu data only — label every output "No live-site check (scheduled run)" | required — if the local browser is not reachable, say so in one line and stop]. Run the Noibu analysis and the site read end to end, build every test's report file and finish with the findings card and no closing message, so whoever opens this run can preview or create a draft from it. Do not create any Noibu test, branch, pull request or preview theme, and do not start or change any test.
3. **Confirm in one or two sentences** what the tool returned: cadence as stored, goal, domain, the live-site-check choice, and (for a required check) that the person's Edge must be open and connected at each run. Never claim delivery works until a run proves it.

Changing an existing schedule goes through `GetScheduledPrompts` / `EditScheduledPrompt`; check for a matching one (including paused) before creating a second.

## Local display contract

This skill renders its cards with its own local copies of the plugin's canonical display bundle: [local display guide](references/card-quickstart.md), [runner](scripts/show_card.py), [builder](scripts/build_presentation.py), [console helper](scripts/console_links.py), [exact checker](scripts/cowork_card_check.py), [comparison adapter](scripts/comparison_acquisition.py), [candidate validator](scripts/validate_candidates.py), plus [report builder](scripts/build_page.py), [DOM reader](scripts/dom_facts.py) and [gate contract](scripts/ab_flow.py). The display route has no sibling filesystem dependency. One `render_ui` per response, through the runner; after a host acknowledgement (`CARD_THEN_NEXT_STEP`, `allow_text_fallback: false`) comes only the card's next-step question ([UX guidelines](references/ux-guidelines.md)); `status: unknown` is not failure and never permits a replay or second render; an honest short fallback only after an explicit failure; a denial or refusal is respected, never routed around.

## Guardrails

- **Never merge, publish, deploy, start or stop** anything before its gate: the person merges the pull request; a test is started (`noibu_advance_ab_test` RUNNING) only after their merge confirmation AND a verified live check; a test is never stopped by this skill (STOPPED is permanent); a preview theme is never published.
- **Pre-merge writes are only** a Noibu DRAFT, a branch + pull request, an unpublished Noibu preview theme and a patch file, and each run mode makes only the subset it promised (`scripts/ab_flow.py check-write`). The finder writes nothing in Noibu or on the repository; a scheduled run never creates drafts, branches, pull requests or preview themes.
- **Deletes are destructive and always asked:** delete or discard a preview theme only after the person's go-ahead for that exact theme in this run; never delete a Noibu test, a branch or a pull request.
- **Storefront conduct:** add one item and remove only that line; never check out, pay, create an account, enter personal data or sign in on the person's behalf; never bypass a verification page; leave the person's consent choices alone unless a banner blocks the read (then decline, never Accept).
- **Secrets and authorization:** never ask for tokens, passwords or codes in chat; a reply on a card is the person's request, and native approval prompts still apply — a denial means nothing was written.
- **Honesty:** every number comes from this run; mobile claims without a phone-size view are inferred; a description is never presented as a screenshot; a capture or a pull request is never claimed unless a tool result shows it.

## Rules that apply throughout

- Platform- and provider-specific steps run only when step 6 detected that platform/provider. Never assume Shopify or GitHub.
- **Connection prompts only when the user has picked the thing they unlock.** Detection is reading the tool list plus one read call, silently. A missing or failing connection is raised in exactly two places, both in `references/run-modes.md` ("When the pick needs a connection"): after the user picks a pull-request mode with no eligible provider (including authentication failing partway through Stage 2d), and after they pick the Shopify theme preview without the Noibu theme tools (or the theme tools failing on authentication mid-run). Cowork has no connector-suggestion cards: say in one line which connection in Cowork would unlock it and ask whether to connect it now or continue without; never write re-authorization steps or ask for a token. Anywhere else, a missing connection is one clause of a message the run was already sending.
- The Noibu theme tools run only when the theme gate is open (6a); never on a non-Shopify store.
- Theme writes go only into the open Noibu theme change this run started (edits never touch the live theme; previews are unpublished copies named "Noibu preview: …"). Never publish a theme; publishing is the merchant's decision in Shopify admin. Never call a Shopify mutation.
- Never delete or discard a preview theme without the user's go-ahead for that exact theme in this run.
- Work from `candidates.json` for everything it carries (cards, create arguments, evidence, selectors, surfaces); never re-derive or retype it, and never restate its schema here.
- Don't copy SDK or platform facts into this skill, the PR body or code comments beyond what the task needs; cite the shared files.
- Never create a Noibu draft, branch or PR for a checkout-metric or checkout-page test on a split-checkout store.
- **Only recommend or build what the merchant can ship, built so it can't break the store** (in the finder's synthesis, the "Create a specific test" route, Stage 1 step 6a and Stage 2c).
- Every number comes from this run's queries or pages.
- Link every Noibu issue mentioned to its console URL (`querying-noibu-data/references/console-urls.md`; `scripts/console_links.py` validates).
- **`console.noibu.com` in the browser only when the person is already signed in there.** Edge is the person's own browser: if a console page shows a login screen, never sign in for them; ask them to sign in themselves (`request_user_form_fill` with `reason_type` `login`) or to paste the content, and prefer the `noibu_*` tools for the same data. Console links in cards come from `console_links.py`, never from browsing.
- Be explicit about what was verified and what wasn't (not tested on a real phone; mobile layout inferred; QA ran on production because no preview existed; B was shown on a preview theme, not by a real assignment).
- Do only what the chosen mode promised. A `preview` run pushes nothing; a `pr` run builds no preview theme and starts nothing; a `theme` run opens no PR. More happens only when the user picks it on a follow-up question.
- **No line after a question.** Every rendered card (findings, per-test report, implement) is followed by its next-step question; after any `AskUserQuestion`, output nothing, then wait. A typed reply is accepted without being invited.
- **Cards only where something is shown; questions only where something is asked.** A summary that asks nothing (the Stage 1b test summary, the Stage 4 hand-off) is plain structured chat text with real links.
- **After a "Preview test N" reply:** the per-test card, then its next-step question; say anything else only when the render or the file publish failed.
- **Don't narrate.** No "I'm now checking…", "Let me look up…", "Next I'll…", no summaries between tool calls, no description of what a card or task list already shows. The chat carries only the gates (the choose-a-test questions, the setup question, the run-mode question, a connection question when a pick needs one, the merge gate or follow-up question), a blocker, the end, and the one-line "what you'll see" message before each page of visible QA. While the finder runs, its quiet-mode rules (`references/finder/run-rules.md`) apply.
- **No closing message after the finder.** The end of a finder run is one message: one or two sentences naming the top test, the findings card, then its next-step question (quiet-mode rule 6). What is worth telling the person goes on every report as `caveats` footer lines; a switched goal also gets one plain sentence before the findings card.
- **After the findings card, only the next-step question.** Write no other text: not a summary of the tests, not a bullet per test with numbers, not why a test has no screenshot, not overlap between tests, not a data caveat, not what the run did on the store ("I added an item to the cart and removed it"). Each of those is on the card or belongs in the report's `caveats`. When a host message afterwards says the previous response had no visible output, do not answer with a recap; ask the next-step question again instead. The same applies to a follow-up finder run in the same chat.

  Bad (never send this after the card): "I found two desktop tests for checkout starts; they're on the card above. • Bag drawer stays open (ranked first): about 13,900 US desktop sessions… Run one of the two, not both. To check the drawer, I added the same item to the bag and then removed it…" Good: one or two sentences naming the top test, the findings card, the next-step question, and nothing after it.
- **No recap anywhere else either.** Don't summarize what a card, report, task list or pull request already shows, don't explain the question, don't list what was checked or done. Text in the chat is for a question the person must answer, a blocker, the Stage 1b test summary, the merge gate, and Stage 4's hand-off summary (`references/build/stage-4-5-handoff-and-start.md`), which carries the links and ids the person needs (draft, branch, pull request, preview); keep it to those lines.
