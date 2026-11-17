# Building a picked test

Read this once a test is picked: the user asked to automate a test's implementation, picked one of this conversation's tests to implement, or described a specific change that the finder turned into one test. It runs from the checks before anything is created to a started test. Read each stage when it begins.

Never merge, deploy or start a test before its gate, and never publish a theme at all. A partial mode creates only what its option promised.

The picked test's entry in `candidates.json` is the source for everything it carries (`references/tests-file.md`). Never retype a field the file has.

## Two ways the code reaches the store

Nothing here can open the store's pages, run code in them, or look at a screen. Everything is done through tools and data, and a person does the looking.

| Path | When | How the code is written | How it is seen first | Who puts it live |
|---|---|---|---|---|
| **Repository** | A git host is connected and the store's repository can be read through it | A branch and a pull request | The pull request's preview deployment, or a staging URL | The user merges |
| **Theme** | The store is a Shopify theme store and no repository was found | The Shopify plugin copies the live theme into an unpublished preview theme and writes the change there | The preview theme's link | Nobody publishes the preview theme. To go live, the change needs a pull request on the store's repository, which the user merges |

**A preview theme is for looking only, on both paths.** This skill never publishes one and never asks the merchant to publish one. Once the user has checked the preview, the recommended next step is a pull request with the same change; the test starts only after that pull request is merged and its code is proven live. A Shopify theme store on the repository path gets the preview theme as an option too ("Preview test on Shopify theme"). With neither path, the run can create the draft and describe the change, but it can't write code against real files; say so and stop after the draft.

"Pull request" means the host's equivalent (GitLab's merge request). Questions always say "pull request" and never name a host.

## Before anything is created

### 1. De-duplicate

Call `noibu_list_ab_tests` for the domain (all statuses).

- A test whose title matches the picked test's `createInput.title` and is RUNNING or STOPPED: stop and say so.
- A DRAFT with that title: keep going; Stage 2a adopts it and never creates a second one.
- Note running tests that touch the same page or element, alongside the test's `overlap` line.
- `killed` ideas in the tests file are never offered again.

### 2. Detect the environment, silently

Record an **environment profile**: platform, whether it is a Shopify theme store, path, repository and default branch (repository path), how the change is seen first, how it is proven live.

**Platform.** Identify it as `references/platforms.md` says ("Which platform"). Then check the picked test is actionable and safe on that platform (`references/platforms.md`, "Where the rules are applied"). A test that fails stops here.

**Repository.** In order: a repository URL the user gave; a "Variation code: <pull request link>" line in the picked test's Noibu draft or in a sibling test's hypothesis; then, on each connected git host, a search for the store's name or domain and for code mentioning `NoibuFeatureFlag`. Earlier A/B pull requests that mention flag keys are the strongest signal. Confirm access with one read. Classify the host from the remote URL (`github.com` → GitHub; `gitlab.com` → GitLab; `bitbucket.org` → Bitbucket; `dev.azure.com` → Azure DevOps). Bitbucket connects through the Atlassian connection, and it counts only when the read shows Bitbucket access for the workspace that holds the repository.

**Shopify theme store.** Yes when the `siteType` from `noibu_get_domain` is `Shopify` or `Shopify Plus` and the store is not headless (no Hydrogen/Remix tree in the repository, no business context saying the storefront is headless). Any other `siteType`, or a missing one: no. This one fact decides whether "Preview test on Shopify theme" is offered; never infer it from the domain name or from anything else.

**Path.** A readable repository: the repository path. Otherwise, a Shopify theme store: the theme path. Otherwise neither.

**How the change is seen first.** Theme path: the preview theme's link. Repository path: the pull request's preview deployment when the repository's CI posts one (decide from `.github/workflows/`, `.gitlab-ci.yml`, `bitbucket-pipelines.yml`, `azure-pipelines.yml`, `vercel.json`, `netlify.toml` and the like; don't guess), else a staging URL the merchant provides (ask for it), else nothing before merge: the check happens on the live store after merge and before the start, which is safe because the flag returns the control for everyone until the test starts. Say that plainly at the merge gate.

**Existing work.** Repository path: list branches and open pull requests for A/B work on the picked test's idea (titles or branches with `ab-`, its flag key, the element). A new pull request says which one it supersedes. Shopify theme store: an earlier preview theme for this test is looked for only once a preview theme is being built ("The Shopify preview theme"). On the repository path, make no Shopify call before the user picks "Preview test on Shopify theme".

**Split checkout.** Only when the picked test touches checkout: its `createInput.successMetric` is a checkout metric (`CHECKOUT_CONVERSION_RATE`, or `PAGE_VIEW_TO_URL_RATE` on the Checkout page group or a checkout URL), or its `surfaceTemplate` is `checkout`.

1. Use `readiness.splitCheckout` from `candidates.json` when present. Otherwise list the company's domains (`noibu_list_domains` with the domain's `companyId`) and look for the store's own checkout host on another Noibu domain (`checkout.`, `secure.` or `pay.` on the same root domain), or business context saying checkout runs elsewhere.
2. Not split: carry on.
3. Split: stop before creating anything. Tell the user in plain words: this test measures checkout, and checkout on this store runs on `<checkout host>`, which Noibu tracks as a separate site; sessions don't carry across, so the test couldn't count checkouts per version correctly; support for split-domain stores is coming. Then ask one question: one option per remaining test in `tests[]` that doesn't touch checkout, plus "Stop here for now". In a scheduled run, stop and leave that message as the result.

**The setup question.** Only what detection left unresolved goes to the user, in one question (the repository, a staging URL), with the picked test named ("To build “<title>”, where does <domain>'s code live?"). Nothing unresolved: no question.

### 3. Check the store's code

The finder worked from data and could not see the page. This is where the test is checked against what the store actually renders, before a draft exists.

- **Theme path.** Read the live theme through the Shopify plugin ("The Shopify preview theme", steps 1–3). Nothing is written at this point. If the plugin isn't connected, that section's connect line is the reply; wait for it.
- **Repository path.** Use the host's connection to search the repository.

Then search the code (the live theme's files, or the repository search) for:

1. **The thing the variation would add or move.** If it is already there (an add-to-cart control in the card snippet, a shipping line by the buy box, a progress bar in the cart drawer), the test is dead: say what was found and in which file, record it in `killed`, and offer the other tests in this conversation's `candidates.json`.
2. **Each line in the test's `unconfirmed` list.** Settle each one from the code.
3. **The elements the variation touches.** Note the file and lines that render them. When the code disagrees with a selector in the tests file, the code wins.
4. **An existing Noibu gating helper** (`NoibuFeatureFlag`, `noibuFeatureFlagReady`), its conventions, and other tests' flag files.

If nothing renders the element where the test says it is, say so and ask whether to build it where the code does render it, or stop.

## The test summary and what to automate

The user has said *which* test; this asks *how much* of the rest to automate.

**The summary** is a chat message of its own, sent before the question: one two-column table, with nothing above or below it. It never goes inside the question. Every value comes from the picked test's `candidates.json` entry, the environment profile and the Noibu draft. Drop a row marked "only when present" when it has nothing to show. Keep every cell to one line.

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

**Then one clickable question** whose text is exactly "What would you like to automate?" and nothing else: no summary, no table, no note, no caveat. Anything the user needs to know before choosing is already in the summary table; a limit that only matters for one option (the store's theme count, a missing connection) is raised when that option is picked, not here. It has the options for the path, in this order. Labels and descriptions are fixed; they never name a git host, repository, branch or tool.

| Mode | Path | Label | Description |
|---|---|---|---|
| `full` | Both | Launch an end-to-end test | Open a pull request on my code repository, check preview. Once merged, confirm it's live and start test. |
| `pr` | Both | Prepare a pull request | Open a pull request on my code repository. |
| `preview` | Both | Just show me the code | Nothing is pushed or published, I show the code here. |
| `theme` | Both, Shopify theme store only | Preview test on Shopify theme | Build the test on an unpublished copy of my live Shopify theme and check it. Shoppers never see it. |

"Preview test on Shopify theme" is offered exactly when the environment profile says the store is a Shopify theme store, whether or not the Shopify plugin is connected yet: it is always the fourth option. On any other store it is never shown.

"Launch an end-to-end test" and "Prepare a pull request" are offered on the theme path as well, so a Shopify theme store always gets all four options: no repository was found, but the store may still have one, and a pull request is the only way this skill puts a test's code live. When either is picked there, find the repository before anything else ("When a pull request is wanted and none can be opened"); once one is readable, the run is on the repository path from then on, and "Check the store's code" is repeated against the repository.

| Mode | Runs | Stops at | Creates |
|---|---|---|---|
| `full` | Stage 2 → 3 → 4 → 5 | The merge gate (the user merges), then the start | Draft, pull request, running test |
| `pr` | Stage 2a–2d | Right after the pull request is open | Draft, branch, pull request |
| `theme` | Stage 2a–2c, 2f → 3 | After the preview has been checked | Draft, preview theme |
| `preview` | Stage 2a–2c, 2e | After the code is shown | Draft, a patch file |

Write nothing after the question. The draft is created in every mode, because the flag key and variation keys come from it and the code can't be exact without them; a draft is invisible to shoppers.

**Reading the reply.** "End to end", "run it", "all the way" → `full`. "Pull request only", "just the PR" → `pr`. "Theme preview", "preview theme", "preview it on Shopify" → `theme`. "Show me the code", "just the diff" → `preview`. A reply that changes the test is an edit to `createInput` and `devNotes`: apply it, say which fields changed, and show the summary and the question again. A reply that names another test goes back to picking.

**When a preview theme is wanted and the Shopify plugin isn't connected:** "The Shopify preview theme", step 1. Nothing is built until it is.

**When a pull request is wanted and none can be opened:** if no repository was found, ask for the repository's URL; if the host isn't known, ask where the code is hosted (GitHub, GitLab, Bitbucket, Azure DevOps). Say in one plain line which connection unlocks it (GitHub; Bitbucket through the Atlassian connection), or that there is no connection for GitLab or Azure DevOps, and that nothing was pushed. Once connected, detect the repository again and continue. Otherwise continue with "Preview test on Shopify theme" on a Shopify theme store, or with "Just show me the code". Ask once; don't raise a declined connection again in this run.

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

**When the code goes into a Shopify theme** (the theme path, and `theme` mode on the repository path):

- Write every changed file starting from the **live theme's** copy of it, read through the Shopify plugin ("The Shopify preview theme", step 3), never from the repository's copy: a repository is often ahead of or behind the live theme, and uploading its copy would add or roll back other work in the preview. On the repository path the repository still supplies the conventions and the helper found in "Check the store's code".
- Hold the result as full file contents in the working folder, one file per theme file, ready to upload. Prefer new files (a snippet, a section, an asset) included behind the gate.
- Check each one before it is uploaded: JavaScript parses, JSON parses, every Liquid tag opened is closed.
- Never touch `checkout.liquid` or anything under `checkout/`. Never edit `config/settings_data.json` for a merchant-managed value; describe the setting to change.
- In `preview` mode, read the files but upload nothing.

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

### 2f. Build the preview theme (`theme`, on either path)

Follow "The Shopify preview theme", steps 4–6: copy the live theme, upload the changed files to the copy, verify it, and take its preview link. The live theme stays untouched.


## The Shopify preview theme

How a test is built on an unpublished copy of the store's live Shopify theme. It is done through the Shopify plugin for Cowork, which gives access to the store's Shopify Admin API. Used by "Check the store's code" on the theme path (steps 1–3, read only) and by Stage 2f (steps 4–6).

Use the plugin's own GraphQL workflow on every call: look up the schema (`graphql_schema`), validate the query or mutation (`validate_graphql_codeblocks`), then execute it. Never write a query from memory without those two steps.

**The only store write this skill makes through Shopify is an unpublished preview theme.** Never write a file to the live theme, never publish a theme, never delete a theme, and never change products, orders, settings or anything else in the store.

1. **The plugin is connected, to this store.** If no Shopify tool is available in this session, reply with one plain line and wait: "To preview this test on a Shopify theme, install and connect the Shopify plugin in Cowork (Customize → Plugins → Shopify), then tell me it's connected." Nothing is built, and the Noibu draft and the code written so far are kept. Once the user says it is connected, check again and carry on from here; if the tools still aren't there, suggest a new chat (tools load at the start of a turn) and say `continue the <title> test` picks it up. Ask once; if the user declines, offer the question's other options and don't raise it again in this run.

   Then confirm the connected store is this one:

   ```graphql
   query { shop { name myshopifyDomain primaryDomain { host } } }
   ```

   The primary domain or the `myshopify.com` domain must match the Noibu domain (ignoring `www.`). If it doesn't, stop and say which store the plugin is connected to; never build a preview on another store.

2. **Find the live theme and count the themes.**

   ```graphql
   query { themes(first: 50) { nodes { id name role processing updatedAt } } }
   ```

   The theme with role `MAIN` is the live one. Note any theme named "Noibu A/B preview: <test title> …": it is an earlier preview of this test. Shopify allows 20 themes.

3. **Read the live theme's files.** List the filenames (page through `files(first: 250)`, filenames only), then read the ones the test touches, plus the files `references/platforms.md` names for the surface:

   ```graphql
   query($id: ID!, $f: [String!]) { theme(id: $id) { files(filenames: $f, first: 50) { nodes { filename checksumMd5 body { ... on OnlineStoreThemeFileBodyText { content } } } } } }
   ```

   The Admin API has no text search across a theme, so search by reading: the surface's section and its snippets first, then `layout/theme.liquid` and the assets it loads for an existing Noibu helper. Keep each file's `checksumMd5` as read.

4. **Create or reuse the preview theme.**
   - An earlier preview of this test exists and is unpublished: reuse it. Compare its files' `checksumMd5` with the live theme's; only the files this test changes may differ. If anything else differs, the live theme has moved on since: don't reuse it.
   - Otherwise, with room for another theme: `themeDuplicate` on the live theme, named `Noibu A/B preview: <test title> (<Mon D>)`. This copies the live code and the live settings. Wait until the new theme's `processing` is false.
   - At 20 themes with nothing to reuse: stop, list the unpublished "Noibu A/B preview: …" themes with their dates, and ask the user to delete one in Shopify admin (Online Store → Themes), then say so. Never delete one for them.

5. **Upload the changed files to the preview theme only.** Just before uploading, read each changed file's `checksumMd5` on the live theme again. If one moved since step 3, the live theme changed under the run: read that file again, redo its edit on the new copy, then upload.

   ```graphql
   mutation($themeId: ID!, $files: [OnlineStoreThemeFilesUpsertFileInput!]!) { themeFilesUpsert(themeId: $themeId, files: $files) { upsertedThemeFiles { filename } job { id done } userErrors { field message code filename } } }
   ```

   Pass each file whole: `body: { type: TEXT, value: <full file> }`. The `themeId` is the preview theme's, checked against the live theme's id before every call. Any `userErrors`: stop and show them; never report the preview as built.

6. **Verify, then give the link.** Read `checksumMd5` for every uploaded file on the preview theme and match it to the md5 of what was sent. Confirm that no other file differs from the live theme. The preview link is `https://<domain>/?preview_theme_id=<the preview theme's numeric id>`. A fix after checking is uploaded to the same preview theme and verified the same way; it needs no new theme.

The preview theme stays in the store's theme library, unpublished, until the merchant deletes it in Shopify admin. Never suggest publishing it: the way to put the test live is a pull request.

## Stage 3: checking the change

Runs in `full` and `theme`, and after a later "check it, then start the test". A person does the looking; the run gives them exactly what to open and what to look for.

**The links are the reply, unprompted.** As soon as the preview exists, end the turn with the message below. It is the last thing in the turn: no clickable question, no tool call and no text after it. Text written before a clickable question can end up folded into the work log where the user never sees it, and a question's own text doesn't show links, so the links are never put in a question, in a question's description, or in a message followed by a question. The user can't judge variation B without the links, and should never have to ask for them.

**The message is this template and nothing more.** The two link labels are fixed: always "Variation B" and "Variation A (Original)", in that order, never the variation's own name or key.

```markdown
[One sentence: where the preview was built and that shoppers can't see it.]

- **Variation B:** <full B link>
- **Variation A (Original):** <full control link>

[Only when the storefront is password-protected: one sentence saying the store password is needed first.]

Check both links on a phone and on a desktop: Variation B should show [the change, in a few words] with nothing else moved, and Variation A should look like your live store. Make sure add to cart still works on both.

Tell me whether it looks right or what you'd change. If it looks right, [the next step for this mode].
```

- The check paragraph is two or three sentences of prose. No bullet list, no per-page instructions, no restating of the dev notes. Name B's main interaction in place of "add to cart" only when the test changes a different one.
- The next step, by mode:
  - `full`: "you merge the pull request, then I'll confirm it's live and start the test."
  - `theme`: "I recommend a pull request next: I'll open one with this change, and start the test once it's merged and live."
- Nothing else goes in this message: no checklist, no notes about what wasn't compared or verified, no warnings, no draft details. Those belong in the Stage 4 hand-off.

1. **The links.** From the place the change is seen first (the preview link, the pull request's preview deployment, or the staging URL), build one link per arm on the test's surface page (the top page for that surface in the run-level `surfaces`):
   - Variation A (Original): the page as it is.
   - Variation B: the same page with `nff_<flag key>=<variation name>` added (or the codebase's own QA override). For a preview link that already has a query string, add it with `&`.
2. **Read the reply.** "Looks right", "looks good", "yes" → it looks right; carry on to Stage 4, where the next step named in the message is offered at its gate. Anything that names a problem → fix it in the same branch or preview theme, rebuild the preview, and end the turn with the same message again. Repeat until it looks right.
3. Record what the user confirmed. Be explicit about what was verified and by whom: the user looked at B through the QA link, not through a real assignment; nothing was checked on a real phone unless they said so.

With no place to see the change before merge, say so, go to Stage 4, and run this check in Stage 5 on the live store. In a scheduled run there is no one to look: skip this stage and say so.

## Stage 4: hand off

Send one short summary of what exists now, as plain text, with only the lines that apply:

- the A/B test in Noibu, linked to its console page
- the links for the control and for B, what the user confirmed, and any warnings; or that the check will happen on the live store before the start
- the pull request link, and any older pull request to close
- the preview theme's name and link (when one was built)
- the patch file and the files changed (`preview`)
- the test's `consoleFollowUps`, as steps to do in the Noibu console before starting
- overlap risks with running tests, and anything that is the user's call

Then the gate for the mode:

- **`full`:** one question to confirm the merge: "I've merged it" / "Hold, I want changes". Never merge yourself.
- **`pr`, `theme` and `preview`:** one question, "What would you like to automate next?". What already exists is reused, never recreated.

| After | Options |
|---|---|
| `preview` | "Launch an end-to-end test" · "Prepare a pull request" · "Preview test on Shopify theme" (Shopify theme store) · "Stop here" |
| `pr` | "Check it, then merge and start the test" (continues at Stage 3 with this pull request) · "Preview test on Shopify theme" (Shopify theme store) · "Stop here — I'll merge later" |
| `theme` | "Prepare a pull request (Recommended)" (opens one with the checked change) · "Launch an end-to-end test" (opens the pull request; the check is done, so it goes to the merge gate) · "Stop here" |

Each option's description says, in plain words, what it reuses and what it creates. On "Stop here", reply with one line saying how to pick it up later ("Say `continue the <title> test` and I'll pick up from the pull request."). When a preview theme was built, add that it stays in the store's themes, unpublished, and can be deleted in Shopify admin (Online Store → Themes) once it is no longer needed.

A pull request opened after a preview theme carries the same change the user checked, applied to the repository's copy of each file. If the repository's copy differs from the live theme's in the lines the change touches, say so in the pull request body.

## Stage 5: confirm it is live, then start

Runs only in `full`, or after the user chose an option that ends in a started test. **Never start a test whose code isn't live** (`references/platforms.md`, "What Noibu records").

1. **The code was shipped.** Confirm through the host's connection that the pull request is merged. A published preview theme is never the proof and never the route: if the user says they published the preview theme themselves, say the test still needs its pull request merged, and stop.
2. **The code is running on real pages.** Query `noibu_search_sessions` from the time of the merge to now, counting sessions that carry the helper's rendered attribute:

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

A request like "continue the Quick add test" resolves the domain, finds the draft by title in `noibu_list_ab_tests`, and finds the work: the branch or pull request by name, or the preview theme named "Noibu A/B preview: <title> …" in the store's themes ("The Shopify preview theme", step 2). Confirm the flag key in the code matches the draft, then continue from the first stage not yet done. Ask the "What would you like to automate next?" question for the mode that stopped; don't show the summary and the first question again.

A second request to build a test that is already being built gets one line pointing at the build under way, not a second build.
