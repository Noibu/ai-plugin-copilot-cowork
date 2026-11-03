# Run modes: the test summary, the "What would you like to automate?" question and the follow-up questions

Read this at Stage 1b (a test has just been picked) and again whenever a partial mode finishes (Stage 4). It holds the four run modes, which options each environment gets, the inline test summary, the questions, and resuming. `scripts/ab_flow.py` encodes the mode table, the options, the follow-ups and the writes each mode may make.

Contents:
1. The four run modes
2. Which options appear
3. The test summary and the automation question (Stage 1b)
4. Reading the answer and resuming (incl. "When the pick needs a connection")
5. The follow-up questions (end of a partial mode)
6. Without `AskUserQuestion`

## 1. The four run modes

A mode is how much of the work the person asks Cowork to automate before it stops and hands control back. Every mode starts the same way (Noibu draft → implementation snippet → variation code, Stage 2a–2c); they differ in what happens after the code exists.

| Mode | Label | Runs | Stops at | Creates |
|---|---|---|---|---|
| `full` | Launch an end-to-end test | 2 → 3 → 4 → 5 | The merge gate (the user merges), then Start | Draft, branch, PR, preview, running test |
| `pr` | Prepare a pull request | 2 (incl. 2d) | Right after the PR is open; follow-up question | Draft, branch, PR |
| `theme` | Preview on a Shopify theme | 2a–2c → 3 | After QA on the unpublished preview theme; follow-up question | Draft, Noibu preview theme ("Noibu preview: …"), patch file |
| `preview` | Just show me the code | 2a–2c, 2e | After the diff is shown; follow-up question | Draft, a patch file |

The question speaks the merchant's language: labels and descriptions never name a provider, connector, branch, repository, preview method or tool. Where a provider has its own word for a pull request (GitLab's merge request), still say "pull request" here and switch once the run talks about a specific one.

Why the draft is created in every mode: the flag key and variation keys come from the draft, and the code can't be exact without them. A draft is invisible to shoppers and costs nothing. The question doesn't mention it: usually the person created it with "Create A/B test N" before this, and the summary above links it.

Why `preview` is always last: it is the smallest step, and the options read from "most automated" to "just show me the code".

In `full` mode the two gates still hold: the user merges; the test starts only once the code is proven live.

## 2. Which options appear

From the environment profile (Stage 1 step 6). Order fixed: `full`, `pr`, `theme`, `preview`; drop what doesn't apply, never reorder.

| Option | Shown when |
|---|---|
| `full` | Always |
| `pr` | Always |
| `theme` | The store runs on a Shopify Online Store theme (6a, or `candidates.json` `platform`/`storefront`), whether or not the Noibu theme tools are available |
| `preview` | Always |

The pull-request options appear even when no provider was found, and the theme option even when the theme tools are missing: the gap is handled when the person picks it (section 4), which is more useful than silently missing the option they wanted.

Notes:
- Existing work (Stage 1 step 3): a DRAFT is adopted in every mode; an open PR on the same idea is linked on the summary's "Open pull request" line and in the hand-off, never in the question.
- `full` with no preview method (6c rung 4): QA runs on production after merge, before Start; say so at the merge gate, not here.

## 3. The test summary and the automation question (Stage 1b)

Two parts in one message: the summary as plain chat text, then the question.

### The test summary (inline text)

It asks nothing, so it is ordinary structured chat text: it renders at once and keeps its links clickable. Every value comes from the picked test's `candidates.json` entry, the environment profile and the Noibu draft; never type a number from memory.

```markdown
| | [Test title] |
|---|---|
| **Store** | [domain] |
| **Change** | [One sentence: what changes for variation B, from devNotes.] |
| **Why** | [One sentence from `why`, at most 2 numbers from evidence[].numbers.] |
| **Where** | [surface / surfaceTemplate, e.g. Collection pages] |
| **Targeting** | [setup.targeting, e.g. Mobile, all countries] |
| **Success metric** | [success metric label] |
| **Volume** | [metricVolume] |
| **Overlap** | [overlap] (only when present) |
| **Fix first** | [fixFirst] (only when present) |
| **A/B test in Noibu** | [Draft <id>, linked to https://console.noibu.com/<domainId>/ab-tests/<id> \| Not created yet] |
| **Open pull request** | [#n, linked to its URL, on the same idea] (only when step 6d found one) |
```

One two-column table; the header row is the test (first cell empty, title second); Store is the first row. One line per cell; escape a pipe as `\|`; drop "only when present" rows rather than leaving them empty. "A/B test in Noibu" always appears; the console link comes from `scripts/console_links.py` with the numeric id. No heading, intro sentence, source or date line, and nothing between the table and the question.

### The automation question

One `AskUserQuestion`: `header: "Automate"`, `question: "What would you like to automate? I'll draft the code, but nothing goes live without your approval."`, options from `ab_flow.py modes` in order:

| Label | Description |
|---|---|
| Launch an end-to-end test | Open a pull request on my code repository, check preview. Once merged, confirm it's live and start test. |
| Prepare a pull request | Open a pull request on my code repository. |
| Preview on a Shopify theme | Build an unpublished copy of my live theme with the change and check it. Shoppers never see it. |
| Just show me the code | Nothing is pushed or published, I show the code here. |

Wording as written, nothing appended (no provider, branch, repository, preview method, "supersedes PR #n" or connector note). After the call, output nothing and wait — not "The summary of draft <id> is above", not a pointer to either part.

## 4. Reading the answer and resuming

Match the selected label, or any paraphrase (`ab_flow.py match-mode`):
- "launch an end-to-end test", "end to end", "run it", "all the way", "merge and start" → `full`
- "prepare a pull request", "pull request only", "merge request only", "just the PR", "open a PR" → `pr`
- "preview on a Shopify theme", "theme preview", "preview theme" → `theme`
- "just show me the code", "preview the implementation", "show me the code", "just the diff" → `preview`
- "QA, merge, then start", "QA it, then after I merge, start the test" (the follow-up after `pr`) → `qa-merge-start`: the rest of `full` on the existing draft and pull request — preview theme, QA fixes pushed to the existing PR branch, the PR verdict comment, the merge gate, then Start only after the merge confirmation and the live check (`ab_flow.py check-write qa-merge-start …`); no new draft, branch or pull request

Then check the pick against the profile (below) before Stage 2. A reply that changes the test ("make it the whole card, not just the button") edits `createInput` / `devNotes`: apply it, say which fields changed, and show the summary and the question again. A reply naming a different test goes back to Stage 1 step 5.

Unattended: never `full`. `pr` when a PR can be opened, else `preview`; say which and why at the top of the report.

Record the mode and add its tasks (Stage 2 always; 3 for `full` and `theme`; 4 always; 5 for `full`).

### When the pick needs a connection

Two picks can land on a gap Stage 1 step 6 found but did not mention, and a connection can also drop partway through. This is the one place the skill asks the person to connect something, because now they have asked for what it unlocks. Cowork has no connector-suggestion card: say it in one plain line and ask.

**`full` or `pr` (or a follow-up "create the pull request") with no eligible provider** — the provider's tools are absent; present but the read failed on authentication; or a Stage 2d call (branch, file write, pull request) fails on authentication (401/403, "bad credentials", expired or revoked token, "re-authenticate"). In the mid-run case stop 2d without retrying, keep what was written, and run this flow before anything else about the failure.

1. **Ask where the code lives**, unless the provider is already certain (a repository URL, or a failing connector that names itself): `AskUserQuestion` header "Code host", "To open a pull request for “<title>”, where is <domain>'s code hosted?" — GitHub · Azure DevOps · GitLab · Bitbucket (another can be typed). No answer: one line asking them to name it, and wait.
2. **Say what would unlock it**, in one line plus one `AskUserQuestion` (header "Connect"): connecting that provider in Cowork lets the run open the pull request itself (for a dropped connection: "The GitHub connection dropped, so I couldn't open the pull request. Reconnect it in Cowork and I'll pick up where I stopped."); options "I've connected it" · "Continue without". Say in the same line when nothing was pushed. GitLab and Bitbucket are used only when a connector for them is actually in the tool list; otherwise say in one clause that this session has no connection for that host and go to step 3's "continue without" path. Never ask for a token or `owner/repo`, never write re-authorization steps.
3. **After the answer.** "I've connected it" (or the provider's tools now appear): re-run 6b (discovery + one read). If the repository is still unknown, find it as 6b says; one clear match is used; several are offered in one `AskUserQuestion` (up to four, another can be typed); none → asked in that same question. Continue in the picked mode, resuming from the failed call. "Continue without", a decline or nothing to connect: continue on the patch hand-off (Stage 2e), built against the real repository files; if the repository could not be read at all, say the patch can't be made against real paths yet rather than handing over placeholder paths. In `full` with no way to push, the run writes the code, hands over the patch and stops at the hand-off; it can't reach the merge gate, so say so in the same clause rather than silently downgrading.

**`theme` without the Noibu theme tools** (the store is a Shopify Online Store theme, but `noibu_start_theme_change` and its siblings are not in the tool list, or the domain has no `numId`), **or a theme tool failing on authentication mid-run** (any mode that uses them). Mid-run: stop that call without retrying, keep what was built, and say "The Noibu connection dropped, so I couldn't <build the preview theme / finish the QA>. Reconnect Noibu in Cowork and I'll pick up where I stopped." Not the same as a theme-tool refusal for the store (no theme access, plan without preview themes): that is `references/shopify-theme-preview.md` section 1's "gate closed" path.

1. One line: the preview theme is built through Noibu's Shopify theme access, which this session does not have (or dropped); `AskUserQuestion` "I've connected it" · "Continue without".
2. "I've connected it": re-check the tool list and `numId`. Gate open → continue in `theme` (or resume the failed call, re-listing the open theme change first). Still closed → say what is missing and fall through to the next preview method in 6c, or offer `preview` if there is none.
3. "Continue without": say in one clause that the theme preview needs that access, and ask the automation question again without the `theme` option. For a mid-run drop in another mode, don't ask again: continue with the next preview method for QA, or the served-asset check (then a human attestation) for proof of live, saying which in one clause.

Both flows ask once. If the person declines, don't offer it again in this run, including on the follow-up questions. Unattended: skip both flows, take the next rung, say so at the top of the report.

## 5. The follow-up questions (end of a partial mode)

A partial mode ends with a short summary (Stage 4) and then one `AskUserQuestion` (`header: "Next step"`, `question: "What would you like to automate next?"`). The options resume this same run: the draft, branch, patch and preview theme are reused, never recreated (`ab_flow.py follow_up`).

| After mode | Options (label — description) |
|---|---|
| `preview` | Launch an end-to-end test — Uses the code I already wrote; opens the pull request, QA, then your merge and the start · Prepare a pull request — Uses the code I already wrote; opens the pull request and stops · Preview on a Shopify theme — Builds an unpublished preview theme from this code and checks it · Stop here — Keep the draft and the patch |
| `pr` | QA, merge, then start — QA on a preview, then after you merge I confirm it's live and start the test · Preview on a Shopify theme — Builds an unpublished preview theme from the pull request's code · Stop here — I'll merge later |
| `theme` | Prepare a pull request — Opens the pull request from the code already written; the preview theme is kept · Launch an end-to-end test — Opens the pull request; QA is already done, so it goes to the merge gate · Stop here — Keep the draft and the preview theme |

Same filtering as section 2 (no theme option off Shopify themes) and same wording rule. A pick that needs a connection is handled as in section 4. The phrases "Continue: create the pull request from the code you wrote", "Continue: run it end to end from here", "Continue: preview it on a Shopify theme", "Continue: QA it, then after I merge, start the test" and "Stop here" are still matched when typed.

After the call, output nothing and wait. On "Stop here", reply with one line on how to resume later ("Say “continue the <title> test” and I'll pick up from the pull request.") and, when a preview theme exists, ask the deletion question (`shopify-theme-preview.md` section 4 rule 4) in that same reply.

**Resuming in a later chat.** "continue PR #12 on store.com" or "continue the Quick add test" re-runs Stage 0, finds the draft by title in `noibu_list_ab_tests` and the branch/PR by name through the provider, confirms the flag key in the code matches the draft, then continues from the first stage not yet done (an open PR → Stage 3; a merged one → Stage 5). Ask the follow-up question for the mode that stopped, not the Stage 1b summary. (The finder's tests themselves are never loaded from another chat; a resume works from the draft and the PR.)

## 6. Without `AskUserQuestion`

Send the same question as one plain message: the summary first (as above), then "What would you like to automate? Reply with one: Launch an end-to-end test · Prepare a pull request · Preview on a Shopify theme · Just show me the code" (theme only when it applies), and wait. The follow-up questions degrade the same way. Never skip the question.
