# Build half, Stages 4 and 5: hand off, verify live, start

Read this when Stage 2 (or 3) finishes. Stage 4 runs in every mode; Stage 5 only in `full` or after a follow-up that ends in a started test. "SDK file", `platforms.md`, "6c", "Rules that apply throughout" as in Stage 2.

## Stage 4: Hand off

Send one short summary of what exists now, as plain structured text (it asks nothing), only the lines that apply to the mode:
- the A/B test in Noibu, linked to its console page (`scripts/console_links.py`)
- the preview link (the theme `previewUrl`, a CI preview or staging URL), what QA checked and what it could not (B rendering, mobile, console errors), the verdict and warnings — or that QA will run on production before Start (`full` with no preview)
- the PR link (in the provider's own word), and any older PR to close
- the patch file and the files changed (`preview`)
- the preview theme's name ("Noibu preview: …") and preview link (`theme`)
- the test's `consoleFollowUps`, as steps to do in the Noibu console before starting
- overlap risks with running tests, and anything that's their call

Then the gate for the mode:
- **`full`:** `AskUserQuestion` (header "Merge"): "Merge the pull request when you're ready, then tell me." — "I've merged it" ("Confirm it's live, then start the test") · "Hold, I want changes" ("Nothing is started"). Never merge yourself. On "I've merged it", Stage 5. (No pull request because nothing could push: the run stops here with the patch; say it can't reach the merge gate.)
- **`pr`, `theme`, `preview`:** the follow-up question from `references/run-modes.md` section 5. Nothing after it; wait. A continue answer resumes at the first stage not yet done, reusing the draft, branch, patch and preview theme (a `theme` run that continues to `full` has its QA done, so it goes 2d → the merge gate). "Stop here" ends the run with one line on how to resume.

## Stage 5: Verify live, then start

Runs only in `full` mode, or after a follow-up that ends in a started test. `scripts/ab_flow.py check-write full start-test --merged --live` must allow the start.

1. Confirm the PR is merged through the provider (`references/git-hosts.md`, "Merged?"). Then prove the code is live with the method from 6c: the Admin API checksum route through a matched read-only Shopify MCP; otherwise the served-asset check in Edge (`get_dom` of the page or the asset URL, looking for the flag key); failing that, ask the person to confirm (a human attestation, recorded as such). Poll every ~60 s for up to 10 minutes (longer if the pipeline is slow or needs a manual release — say what's pending). If it never lands, stop and tell them. **Never start a test whose code isn't live** (SDK file, "What the platform records").
2. If QA was deferred (no preview), run Stage 3 steps 2–4 now on production, with `references/qa-checklist.md`. Any FAIL → stop; don't start.
3. Start the test: `noibu_advance_ab_test` with `status: "RUNNING"` and the test's id (the merge confirmation and the live check are the gate; the tool's own approval still applies). Confirm with `noibu_list_ab_tests` that the status reads RUNNING. Never stop a test here (STOPPED is permanent).
4. Assignment check: Cowork cannot read the assignment `reason` in the page. After the first sessions arrive, `noibu_get_ab_test_results` shows sessions per variation (a DRAFT or just-started test may show none yet: say so, and that one visitor isn't proof B is reachable). Offer the person the SDK file's console line to check their own assignment.
5. Tell them what's next: the minimum runtime (from the results tool's estimate, never your own number), the lifecycle limits from the SDK file, and how to read results (ask "how is the <title> test doing?" — `querying-noibu-data`). For a Noibu preview theme, ask about deleting it (`references/shopify-theme-preview.md` section 3 rule 4); for other preview methods, say how the preview is cleaned up (CI previews usually expire on their own).
