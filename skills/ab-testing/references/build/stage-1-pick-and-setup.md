# Build half, Stage 1 and 1b: find or pick the test, detect the environment, choose the run mode

Read this from SKILL.md right after Stage 0, before card 4a. "6a"–"6e" and "Stage 1 step N" elsewhere in this skill mean the steps below. `references/platform-restrictions.md` is the restrictions check these steps cite.

## Entering with the test already picked

A reply on the implement card ("Automate the implementation 2"), or a typed request naming a test by rank or title from this chat's recommendations ("build test 2", "automate the Quick add on collection cards test"), is the decision to build that test. It may also say "It's already in Noibu as A/B test 1234". Treat it as already picked; asking them to choose again would read as the reply not landing. Stage 1 changes to:

1. Load that run's `candidates.json` from the finder's working folder in this chat (next to the `<domain-short>-test-<rank>.html` reports). Accept it under step 2's rules (schema, domain). The tests a finder run produces live only in the chat that ran it: never fetch a `candidates.json` from a published report, OneDrive, an earlier conversation or a pasted link. If this chat has no finder run for that domain, say in one line that the tests from that report aren't available in this chat and that "Look for new opportunities" here will produce a fresh set, then ask card 4a.
2. Find the test by `title` (exact, then case-insensitive), falling back to `rank`. If neither matches, say which tests the run has and ask which one with one `AskUserQuestion` (the only question on this path).
3. Run step 3's de-duplication for that one test (RUNNING or STOPPED with its title → stop and say so; a DRAFT is adopted in 2a); step 6d then finds any open PR on the same idea, which the new PR supersedes.
4. Skip cards 4a and 4b and go to step 6, then Stage 1b. Stage 0 still runs first.

Everything after Stage 1 is unchanged, including Stage 1b: the reply says *which* test to build, not how much to automate. A request that merely mentions a report without naming a test, or names one but asks to reconsider or compare, is the normal path: ask card 4a.

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

     Before running anything, check the change against `references/platform-restrictions.md` using Stage 0's `siteType`; a change that fails gets that section's answer. Then run the finder with that change stated as the test to build, so it checks it against the data and the live site, previews it and writes one test to `page.json` and `candidates.json` (`origin: "user-requested"` when it found no measured gap: title = the change; hypothesis says it was requested directly; metric = the user's goal, ask if none). The finder ends as it always does, with the findings lead and the findings card showing that one test, but its next-step question is the **build question** (`references/findings-card.md`): "Build this test (Recommended)" · "Preview test 1" · "Create A/B test 1" · "Describe a different change". "Build this test" continues from step 3 with it as the pick, no card 4b; the other replies are answered as "When a reply wakes this chat" says, and "Describe a different change" asks the prompt above again. A test with no measured evidence says so on its card and in the Stage 4 summary.
   - **A typed answer:** a described change is "Create a specific test"; a named test is that test; "something new" or another goal is "Look for new opportunities".
   - **No answer:** don't pick. One short message listing the options, then wait.
6. **Detect the environment, check split checkout, then ask the setup questions.** Run 6a to 6d silently (nothing in chat) and record an **environment profile**: provider and account, repository, default branch, write path, platform, Noibu theme tools available / not, Shopify MCP matched read-only / off, preview method, proof-of-live method. Read `platforms.md` here.

   **6a. Platform, then the theme preview gate.**
   1. **Identify the platform** as `platforms.md` says (code tree first, else `siteType`, else the site read's platform, else business context).
   2. **Shopify Online Store theme?** Signals in order: `candidates.json` `storefront.shopifyOnlineStoreTheme` / `platform`; `siteType` Shopify/Shopify Plus plus a theme signal; business context. Headless (Hydrogen, a custom front end) has no theme to preview. Unclear and needed → ask in the 6e question.
   3. **Theme gate** (`references/shopify-theme-preview.md` section 1): **open** when the store is a Shopify Online Store theme AND the Noibu theme tools (`noibu_start_theme_change`, `noibu_edit_theme_file`, `noibu_write_theme_file`, `noibu_preview_theme_change`, `noibu_list_store_themes`) are in the tool list AND Stage 0 returned the domain's `numId`. Checking is reading the tool list, no call. A Shopify MCP connector (`get-shop-info`, `graphql_query`) is optional and read-only: if present, one `get-shop-info` confirms the shop matches the Noibu domain; it unlocks the Admin API checksum proof of live, never a write.
   4. **Check the picked test is actionable and safe on that platform** (`references/platform-restrictions.md`). A test that fails stops here, before any draft, branch or preview exists.

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
