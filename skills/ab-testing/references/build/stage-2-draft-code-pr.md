# Build half, Stage 2: draft the test, write the code, open the PR

Read this once the run mode is known (Stage 1b). "SDK file" is `references/shared/noibu-feature-flag-sdk.md`; `platforms.md` is `references/shared/platforms.md`; "6a"–"6e", "Stage 1 step N" and "Rules that apply throughout" are sections of SKILL.md. Before any write, `scripts/ab_flow.py check-write <mode> <write>` must allow it.

Runs in every mode. 2a–2c always; 2d only in `full` and `pr` (or a follow-up "create the pull request"); 2e in `preview` (and wherever no push is possible). In `theme` and `preview` nothing is pushed to the repository.

### 2a. Create the Noibu draft
- **Draft already in Noibu** (Stage 1 step 3, e.g. after a "Create A/B test N" reply): adopt it, don't create a second one. Read its id, key and variation keys from `noibu_list_ab_tests` and check its config against the test's `createInput`. If they differ, show the differences and ask (`AskUserQuestion`, header "Draft") whether to keep the draft as it is or update it to match (`noibu_update_ab_test`, DRAFT only; report re-derived keys).
- **Otherwise** create it with `noibu_create_ab_test` (DRAFT only), passing the test's `createInput` exactly as the file has it, plus `domainId`, `rationale`, `skill: "ab-testing"`, `skillStep: "build-draft"`. First check every metric against the tool's current schema enums; one no longer accepted → stop and say which, never substitute. User-requested edits at the summary are applied to `createInput` only, and you say which fields changed. Without a handoff file (Stage 1 step 5 fallback): title = the change, hypothesis = the evidence with real numbers, the date window and the correlational caveat if any (or that it was requested directly with no measured gap), metrics and targeting from the summary, variation A the control (`isControl: true`), B named per the SDK file's naming rule.
- Record the **test id, flag key and variation keys** and treat them as the SDK file says. List the test's `consoleFollowUps` (e.g. a country condition the create tool can't set) for the Stage 4 summary.

### 2b. Get Noibu's implementation code
The Implementation panel on `https://console.noibu.com/<domainId>/ab-tests/<testId>` (link from `scripts/console_links.py`) holds Noibu's snippet. No `noibu_*` tool returns it. Open the page in Edge only to read it, and only when the person is already signed in there: if Edge shows a login screen, never sign in for them — ask once in one line to sign in themselves (`request_user_form_fill`, `reason_type: login`) or to paste the Implementation panel's code, and wait. If no browser is available, ask them to paste it. Compare its read of the assignment with the SDK file's "Reading the assignment" and apply that section's instruction.

### 2c. Write the variation code
- Start from the picked test's handoff fields: `surface` and `surfaceTemplate`, each variation's `devNotes` and `selectors` (recorded `selector`, `block`, `column`, from a static DOM), and `siteFacts`. Search the repository (provider search, or `noibu_search_theme_files` in a theme change) for those selectors to find the template, section or component that renders them. When the code disagrees with the recorded selectors, the code wins: the site read saw a static snapshot, the code is what ships. Say so in the PR body.
- Build it as the SDK file's "The gating helper" and "Conventions observed" say: reuse the repository's helper and conventions when present, otherwise the documented helper — and don't introduce the observed conventions unasked.
- Place it per `platforms.md`, deferring to what the repository already does.
- Paste Noibu's implementation snippet into the flag script as a comment for traceability.
- Don't gate the variation by CSS breakpoint when targeting is set in Noibu ("mobile" includes tablets). Let the flag decide.
- Use the site's own components and design tokens so B looks native.
- Write and review it under SKILL.md's "Platform restrictions and blast radius" (its Stage 2c bullet: the file-by-file diff review and the PR body's "Blast radius" section).
- Validate before committing, offline in the workspace: JSON files parse (`python -c "import json…"`); JS files pass `node --check` when Node is available in the workspace; Liquid/template syntax is reviewed by reading. The repository's own lint or build cannot run here: say so in the PR body.
- In `theme` mode (and in `full` when the preview method is the theme preview) the same edits go into the Noibu theme change (`references/shopify-theme-preview.md` section 2).

### 2d. Open the PR (`full` and `pr` modes, or a follow-up "create the pull request")
- Branch from the default branch: `agent/ab-<slug>` (reuse it when it already exists from this run). Write the changed files with the provider's tools (`references/git-hosts.md`, "Pull-request operations").
- Open the PR (draft when supported), using the repository's PR template if it has one.
- If a provider call fails on authentication, stop without retrying, keep what was written, and follow `references/run-modes.md`, "When the pick needs a connection". Don't write re-authorization steps into the chat.
- PR body: test id, flag key, variation keys, targeting, metrics; the evidence quoted from the test's `evidence[]` (claim, numbers, source; correlational ones labelled); what the preview showed (the before look, the preview theme link when one exists — never a claimed screenshot that doesn't exist); `fixFirst` when present; a control-vs-B table; files changed and why; how QA checks each arm; **launch order** (merge → confirm live → start); overlap with running tests; which older PR it supersedes; the "Blast radius" section.
- Update the Noibu draft's hypothesis (`noibu_update_ab_test`, DRAFT only) to reference the PR link.
- In `pr` mode go straight to Stage 4; QA happens only if the person continues from the follow-up question.

### 2e. Show the implementation (`preview` mode, and the no-push hand-off)
The point is that the person reads the code before anything leaves the conversation:
- Build the patch (`references/git-hosts.md`, "The patch hand-off") as `ab-<slug>.patch` and publish it to their output files.
- In the chat: a short table of files changed and why; the diff in a code block when it is under ~150 lines, otherwise the hunk that renders variation B plus a pointer to the patch file; how QA would check each arm; the Noibu draft's console link with its flag key and variation keys; the `consoleFollowUps`; the "Blast radius" section; and one line saying nothing was pushed or published.
- Then Stage 4.
