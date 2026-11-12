# Building a picked test

Read this once a test is picked: the user asked to automate a test's implementation, picked one of this conversation's tests to implement, or described a specific change that the finder turned into one test. It runs from the checks before anything is created to a started test. Read each stage when it begins.

Never merge, publish, deploy or start a test before its gate. A partial mode creates only what its option promised.

The picked test's entry in `candidates.json` is the source for everything it carries (`references/tests-file.md`). Never retype a field the file has.

## Two ways the code reaches the store

Nothing here can open the store's pages, run code in them, or look at a screen. Everything is done through tools and data, and a person does the looking.

| Path | When | How the code is written | How it is seen first | Who puts it live |
|---|---|---|---|---|
| **Repository** | A git host is connected and the store's repository can be read through it | A branch and a pull request | The pull request's preview deployment, or a staging URL | The user merges |
| **Theme** | The store runs on a Shopify Online Store theme and no repository was found | Noibu's theme tools edit a copy of the live theme | `noibu_preview_theme_change` builds an unpublished copy and returns its link | The merchant publishes it in Shopify admin |

A store whose theme is deployed from a repository uses the repository path, because a direct theme edit would be overwritten by the next deploy. With neither path, the run can create the draft and describe the change, but it can't write code against real files; say so and stop after the draft.

"Pull request" means the host's equivalent (GitLab's merge request). Questions always say "pull request" and never name a host.

## Before anything is created

### 1. De-duplicate

Call `noibu_list_ab_tests` for the domain (all statuses).

- A test whose title matches the picked test's `createInput.title` and is RUNNING or STOPPED: stop and say so.
- A DRAFT with that title: keep going; Stage 2a adopts it and never creates a second one.
- Note running tests that touch the same page or element, alongside the test's `overlap` line.
- `killed` ideas in the tests file are never offered again.

### 2. Detect the environment, silently

Record an **environment profile**: platform, path, repository and default branch (repository path), how the change is seen first, how it is proven live.

**Platform.** Identify it as `references/platforms.md` says ("Which platform"). Then check the picked test is actionable and safe on that platform (`references/platforms.md`, "Where the rules are applied"). A test that fails stops here.

**Repository.** In order: a repository URL the user gave; a "Variation code: <pull request link>" line in the picked test's Noibu draft or in a sibling test's hypothesis; then, on each connected git host, a search for the store's name or domain and for code mentioning `NoibuFeatureFlag`. Earlier A/B pull requests that mention flag keys are the strongest signal. Confirm access with one read. Classify the host from the remote URL (`github.com` → GitHub; `gitlab.com` → GitLab; `bitbucket.org` → Bitbucket; `dev.azure.com` → Azure DevOps). Bitbucket connects through the Atlassian connection, and it counts only when the read shows Bitbucket access for the workspace that holds the repository.

**Path.** A readable repository: the repository path. Otherwise, a Shopify Online Store theme (`siteType` Shopify or Shopify Plus, not headless): the theme path. Otherwise neither.

**How the change is seen first.** Theme path: the preview link. Repository path: the pull request's preview deployment when the repository's CI posts one (decide from `.github/workflows/`, `.gitlab-ci.yml`, `bitbucket-pipelines.yml`, `azure-pipelines.yml`, `vercel.json`, `netlify.toml` and the like; don't guess), else a staging URL the merchant provides (ask for it), else nothing before merge: the check happens on the live store after merge and before the start, which is safe because the flag returns the control for everyone until the test starts. Say that plainly at the merge gate.

**Existing work.** Repository path: list branches and open pull requests for A/B work on the picked test's idea (titles or branches with `ab-`, its flag key, the element). A new pull request says which one it supersedes. Theme path: an open theme change is found in step 3.

**Split checkout.** Only when the picked test touches checkout: its `createInput.successMetric` is a checkout metric (`CHECKOUT_CONVERSION_RATE`, or `PAGE_VIEW_TO_URL_RATE` on the Checkout page group or a checkout URL), or its `surfaceTemplate` is `checkout`.

1. Use `readiness.splitCheckout` from `candidates.json` when present. Otherwise list the company's domains (`noibu_list_domains` with the domain's `companyId`) and look for the store's own checkout host on another Noibu domain (`checkout.`, `secure.` or `pay.` on the same root domain), or business context saying checkout runs elsewhere.
2. Not split: carry on.
3. Split: stop before creating anything. Tell the user in plain words: this test measures checkout, and checkout on this store runs on `<checkout host>`, which Noibu tracks as a separate site; sessions don't carry across, so the test couldn't count checkouts per version correctly; support for split-domain stores is coming. Then ask one question: one option per remaining test in `tests[]` that doesn't touch checkout, plus "Stop here for now". In a scheduled run, stop and leave that message as the result.

**The setup question.** Only what detection left unresolved goes to the user, in one question (the repository, a staging URL), with the picked test named ("To build “<title>”, where does <domain>'s code live?"). Nothing unresolved: no question.

### 3. Check the store's code

The finder worked from data and could not see the page. This is where the test is checked against what the store actually renders, before a draft exists.

- **Theme path.** Open a theme change with `noibu_start_theme_change` (the domain's `numId`, title "A/B test: <test title>"). It returns a `changeId` and every file path in the theme; edits go to a copy, never the live theme. One change can be open per store: if the error names one already open, ask one question: continue that change, discard it and start again (`noibu_discard_theme_change`), or stop. Never discard a change the user didn't open in this run without their go-ahead.
- **Repository path.** Use the host's connection to search the repository.

Then search the code (`noibu_search_theme_files` with a regular expression, or the repository search) for:

1. **The thing the variation would add or move.** If it is already there (an add-to-cart control in the card snippet, a shipping line by the buy box, a progress bar in the cart drawer), the test is dead: say what was found and in which file, record it in `killed`, discard the change if this run opened it, and offer the other tests in this conversation's `candidates.json`.
2. **Each line in the test's `unconfirmed` list.** Settle each one from the code.
3. **The elements the variation touches.** Note the file and lines that render them. When the code disagrees with a selector in the tests file, the code wins.
4. **An existing Noibu gating helper** (`NoibuFeatureFlag`, `noibuFeatureFlagReady`), its conventions, and other tests' flag files.

If nothing renders the element where the test says it is, say so and ask whether to build it where the code does render it, or stop.

## The test summary and what to automate

The user has said *which* test; this asks *how much* of the rest to automate.

**The summary** is one two-column table, with nothing above or below it. Every value comes from the picked test's `candidates.json` entry, the environment profile and the Noibu draft. Drop a row marked "only when present" when it has nothing to show. Keep every cell to one line.

```markdown
| | [Test title] |
|---|---|
| **Store** | [domain] |
| **Change** | [One sentence: what changes for variation B, from devNotes.] |
| **Why** | [One sentence, from `why`, with at most 2 numbers from evidence[].numbers.] |
| **Where** | [surface / surfaceTemplate, e.g. Collection pages] |
| **Targeting** | [targeting, e.g. Mobile, all countries] |
| **Success metric** | [success metric label] |
| **Volume** | [metricVolume] |
| **Overlap** | [overlap line] (only when present) |
| **Fix first** | [fixFirst] (only when present) |
| **A/B test in Noibu** | [[Draft <id>](https://console.noibu.com/<domainId>/ab-tests/<id>) \| Not created yet] |
| **Open pull request** | [[#n](url) on the same idea] (only when one was found) |
```

The console link is built only from the `domainId` and the test id a Noibu tool returned.

**Then one clickable question**, "What would you like to automate?", with the options for the path, in this order. Labels and descriptions are fixed; they never name a git host, repository, branch or tool.

| Mode | Path | Label | Description |
|---|---|---|---|
| `full` | Repository | Launch an end-to-end test | Open a pull request on my code repository, check preview. Once merged, confirm it's live and start test. |
| `full` | Theme | Launch an end-to-end test | Build an unpublished copy of my live theme with the change and check it. Once published, confirm it's live and start test. |
| `pr` | Repository | Prepare a pull request | Open a pull request on my code repository. |
| `theme` | Theme | Preview on a Shopify theme | Build an unpublished copy of my live theme with the change and check it. Shoppers never see it. |
| `preview` | Both | Just show me the code | Nothing is pushed or published, I show the code here. |

| Mode | Runs | Stops at | Creates |
|---|---|---|---|
| `full` | Stage 2 → 3 → 4 → 5 | The merge or publish gate (the user does it), then the start | Draft, pull request or preview theme, running test |
| `pr` | Stage 2a–2d | Right after the pull request is open | Draft, branch, pull request |
| `theme` | Stage 2a–2c, 2f → 3 | After the preview has been checked | Draft, theme change, preview theme |
| `preview` | Stage 2a–2c, 2e | After the code is shown | Draft, a patch file |

Write nothing after the question. The draft is created in every mode, because the flag key and variation keys come from it and the code can't be exact without them; a draft is invisible to shoppers.

**Reading the reply.** "End to end", "run it", "all the way" → `full`. "Pull request only", "just the PR" → `pr`. "Theme preview", "preview theme" → `theme`. "Show me the code", "just the diff" → `preview`. A reply that changes the test is an edit to `createInput` and `devNotes`: apply it, say which fields changed, and show the summary and the question again. A reply that names another test goes back to picking.

**When a pull request is wanted and none can be opened:** if the host isn't known, ask where the code is hosted (GitHub, GitLab, Bitbucket, Azure DevOps). Say in one plain line which connection unlocks it (GitHub; Bitbucket through the Atlassian connection), or that there is no connection for GitLab or Azure DevOps, and that nothing was pushed. Once connected, detect the repository again and continue. Otherwise continue on the theme path when the store allows it, or with "Just show me the code". Ask once; don't raise a declined connection again in this run.

**In a scheduled run:** never `full`. Take `pr` when a pull request can be opened, otherwise `preview`, and say which at the top of the result.

Do only what the chosen mode promised.

## Stage 2: draft the test and write the code

### 2a. Create the Noibu draft

- **Draft already in Noibu:** adopt it. Read its id, key and variation keys from `noibu_list_ab_tests` and check its config against the test's `createInput`. If they differ, show the differences and ask whether to keep the draft as it is or update it to match (`noibu_update_ab_test`, DRAFT only).
- **Otherwise** create it with `noibu_create_ab_test` (draft only), passing the test's `createInput` exactly as the file has it, plus `domainId` and `rationale`. Before the call, check every metric in it against the tool's current schema enums; if one is not accepted, stop and tell the user; never substitute.
- Record the **test id, flag key and variation keys**, and treat them as `references/platforms.md` ("Keys and values") says. List the test's `consoleFollowUps` for the hand-off.

### 2b. Get Noibu's implementation code

The test's page in the Noibu console has an **Implementation** panel with the snippet for this test. Ask the user once to open the test in the console and paste that panel's code. Compare its read of the assignment against `references/platforms.md`, "Reading the assignment", and apply that section's instruction.

If the user would rather not, use the documented gating helper from `references/platforms.md` and say in the hand-off that the test's own snippet was not compared.

### 2c. Write the variation code

- Start from the picked test's `surface`, `surfaceTemplate` and each variation's `devNotes`, and from the files and lines found in "Check the store's code".
- Build it as `references/platforms.md` says ("The gating helper" and "Conventions observed"): reuse the codebase's existing helper and conventions when present, otherwise the documented helper. The helper must report `ab_rendered_<flag key>` and honour the `nff_<flag key>` link, or the codebase's own equivalents; Stages 3 and 5 depend on both.
- Place it per `references/platforms.md` (where the surface lives, and where the helper loads for above-the-fold changes), deferring to what the codebase already does.
- Put Noibu's implementation snippet into the flag script as a comment, when the user provided it.
- Don't gate the variation by CSS breakpoint when targeting is set in Noibu ("mobile" includes tablets). Let the flag decide.
- Use the site's own components and design tokens so B looks native.
- Write and review it under the blast-radius rules (`references/platforms.md`, "Before variation code is committed or shown").

**On the theme path:**

- Read a file with `noibu_read_theme_file` before editing it (200 lines or 64 KiB a call; read on from where it stopped).
- Change part of a file with `noibu_edit_theme_file`: exact string replacement, each `oldString` copied from what the read returned and occurring exactly once. Add a new file with `noibu_write_theme_file`. Prefer new files (a snippet, a section, an asset) included behind the gate.
- Never touch `checkout.liquid` or anything under `checkout/`. Never edit `config/settings_data.json` for a merchant-managed value; describe the setting to change.
- In `preview` mode, read the files but write nothing to the change.

### 2d. Open the pull request (repository path: `full` and `pr`)

- Branch from the default branch: `agent/ab-<slug>`. Commit and open the pull request through the host's connection, using the repository's pull request template if it has one.
- Body: test id, flag key, variation keys, targeting, metrics; the evidence, quoted from the test's `evidence[]` (claim, numbers, source; correlational ones labelled); `fixFirst` when present; a control-against-B table; files changed and why; the "Blast radius" section; the links that show each arm (Stage 3); **launch order** (merge → confirm live → start); overlap with running tests; which older pull request it supersedes.
- Update the Noibu draft's hypothesis (`noibu_update_ab_test`) to reference the pull request link.
- If the connection drops on an authentication error, stop that call without retrying, keep what was written, and say in one line that reconnecting it lets the run pick up where it stopped.
- In `pr` mode, go straight to Stage 4.

### 2e. Show the code (`preview`)

- Save the change as a patch in the Cowork output folder, as `ab-<slug>.patch`.
- In the chat: a short table of files changed and why; the diff in a code block when it is under about 150 lines, otherwise the part that renders variation B plus a pointer to the patch; the "Blast radius" section; the links that would show each arm; the Noibu draft's console link with its flag key and variation keys; the `consoleFollowUps`; and one line saying nothing was pushed or published.
- Then Stage 4.

### 2f. Build the theme preview (theme path: `full` and `theme`)

Call `noibu_preview_theme_change`. It writes the change into an unpublished copy of the live theme and returns `previewUrl`. The live theme stays untouched.

- **`previewUrl` is null and `conflicts` lists files:** the live theme changed those files. They now hold the live copy: read them again, redo their edits, and preview again.
- **No room for another theme** (Shopify allows 20): call `noibu_list_store_themes`, show the themes named "Noibu preview: …" with their dates, and ask which to delete. Delete only with `noibu_delete_preview_theme`, only the one the user named, and only after they confirm; deleting cannot be undone. Never the live theme, never a theme Noibu did not build.
- Each preview replaces the change's last one, so a fix after checking needs no new theme.

## Stage 3: checking the change

Runs in `full` and `theme`, and after a later "check it, then start the test". A person does the looking; the run gives them exactly what to open and what to look for.

1. **The links.** From the place the change is seen first (the preview link, the pull request's preview deployment, or the staging URL), build one link per arm on the test's surface page (the top page for that surface in the run-level `surfaces`):
   - Control: the page as it is.
   - B: the same page with `nff_<flag key>=<variation name>` added (or the codebase's own QA override). For a preview link that already has a query string, add it with `&`.
2. **The checklist**, as a short list the user can tick through, on a phone and on a desktop:
   - B shows the change described in the dev notes, and nothing else on the page moved.
   - The control link looks exactly like the live store.
   - B's main interaction works end to end (the new button adds to cart; the moved block still opens).
   - Add to cart, the cart count and the cart page still work on both links.
   - Product options still change the price and image.
   - No error messages, broken images or sideways scrolling.
3. **Ask one question:** "Does variation B look right?": "It looks right" / "Something is off". On "Something is off", ask what, fix it in the same branch or theme change, rebuild the preview, and give the links again. Repeat until it looks right.
4. Record what the user confirmed. Be explicit about what was verified and by whom: the user looked at B through the QA link, not through a real assignment; nothing was checked on a real phone unless they said so.

With no place to see the change before merge, say so, go to Stage 4, and run this check in Stage 5 on the live store. In a scheduled run there is no one to look: skip this stage and say so.

## Stage 4: hand off

Send one short summary of what exists now, as plain text, with only the lines that apply:

- the A/B test in Noibu, linked to its console page
- the links for the control and for B, what the user confirmed, and any warnings; or that the check will happen on the live store before the start
- the pull request link, and any older pull request to close
- the preview theme's name and link (theme path)
- the patch file and the files changed (`preview`)
- the test's `consoleFollowUps`, as steps to do in the Noibu console before starting
- overlap risks with running tests, and anything that is the user's call

Then the gate for the mode:

- **`full`, repository path:** one question to confirm the merge: "I've merged it" / "Hold, I want changes". Never merge yourself.
- **`full`, theme path:** say how to publish (Shopify admin → Online Store → Themes → the theme named "Noibu preview: …" → Publish), and that publishing makes the code live while every shopper still sees the control. Then one question: "I've published it" / "Hold, I want changes". Never publish for them.
- **`pr`, `theme` and `preview`:** one question, "What would you like to automate next?". What already exists is reused, never recreated.

| After | Options |
|---|---|
| `preview` | "Launch an end-to-end test" · "Prepare a pull request" (repository path) or "Preview on a Shopify theme" (theme path) · "Stop here" |
| `pr` | "Check it, then merge and start the test" (continues at Stage 3 with this pull request) · "Stop here — I'll merge later" |
| `theme` | "Launch an end-to-end test" (the check is done, so it goes to the publish gate) · "Stop here" |

Each option's description says, in plain words, what it reuses and what it creates. On "Stop here", reply with one line saying how to pick it up later ("Say `continue the <title> test` and I'll pick up from the pull request."). On the theme path, add that the theme change stays open and that asking to discard it removes its preview theme; discard it (`noibu_discard_theme_change`) only when the user asks.

## Stage 5: confirm it is live, then start

Runs only in `full`, or after the user chose an option that ends in a started test. **Never start a test whose code isn't live** (`references/platforms.md`, "What Noibu records").

1. **The code was shipped.**
   - Repository path: confirm through the host's connection that the pull request is merged.
   - Theme path: call `noibu_list_store_themes`. The live theme, listed first, must be the preview this run built. If it isn't, the publish didn't happen: say so and stop.
2. **The code is running on real pages.** Query `noibu_search_sessions` from the time of the merge or publish to now, counting sessions that carry the helper's rendered attribute:

   ```json
   {"measures":[{"aggregate":{"measureFunc":"COUNT","target":{"field":"SESSION_ID"},"measureAlias":"sessions"}}],"filters":[{"collectionFilter":{"collection":"CUSTOM_ATTRIBUTE_NAMES","operator":"CONTAINS_ANY","comparisonValues":["ab_rendered_<flag key>"]}}],"orderBy":{"measureAlias":"sessions","direction":"DESCENDING"},"limit":1}
   ```

   A count above zero is the proof. Zero right after shipping is normal: sessions take time to arrive. Check again every few minutes for up to 15 minutes, telling the user what is pending. If it stays at zero, or the codebase's own helper doesn't report that attribute, ask the user to open the B link on the live store and confirm they see the change: "I see variation B on the live store" / "I don't". Without one of the two, stop; don't start.
3. **If the check was deferred** (nothing to look at before merge), run Stage 3 now with links on the live store. Anything off: stop; don't start.
4. **Start the test** with `noibu_advance_ab_test` (status RUNNING). Confirm from the tool's result that it is running; only then say it has started.
5. **Tell the user what's next:** the minimum runtime, the lifecycle limits from `references/platforms.md`, how to read results, and that asking "check the <title> test" in a day confirms shoppers are landing in both arms.

## Checking a running test is healthy

When the user asks to check a test this skill started ("check the quick add test"), from data only:

1. `noibu_get_ab_test_results` for the test: its verdict and its three health checks. A `sampleRatio` warning means traffic is not landing in the configured split.
2. **Assigned against rendered.** For each variation, count sessions assigned to it and sessions that rendered it, over the same window since the start, with the same query as Stage 5 and these filters:
   - assigned: `{"collectionFilter":{"collection":"CUSTOM_ATTRIBUTE_TUPLES","operator":"CONTAINS_TUPLE","comparisonValues":["<test key>","<variation key>"]}}`
   - rendered: `{"collectionFilter":{"collection":"CUSTOM_ATTRIBUTE_TUPLES","operator":"CONTAINS_TUPLE","comparisonValues":["ab_rendered_<flag key>","<variation name>"]}}`

   The two counts should be close for every arm. Sessions assigned to B that did not render B mean visitors are being counted in an arm they cannot see: say so plainly, with both numbers, and that the test's data is not reliable until the code is fixed.
3. Report in a few sentences: both arms are receiving sessions, or which one isn't; the health checks; whether a verdict exists yet. Never present "too early" as a tie.

## Picking a build up later

A request like "continue the Quick add test" resolves the domain, finds the draft by title in `noibu_list_ab_tests`, and finds the work: the branch or pull request by name, or the open theme change (starting a change for a store that has one open returns its `changeId`). Confirm the flag key in the code matches the draft, then continue from the first stage not yet done. Ask the "What would you like to automate next?" question for the mode that stopped; don't show the summary and the first question again.

A second request to build a test that is already being built gets one line pointing at the build under way, not a second build.
