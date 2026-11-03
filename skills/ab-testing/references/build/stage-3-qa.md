# Build half, Stage 3: preview and automated QA

Read this when a mode that includes Stage 3 starts it (`full`, `theme`, or a follow-up "QA, merge, then start" from `pr`). Its "Showing the browser during QA" section also governs Stage 5 steps 2 and 4. "SDK file", `platforms.md`, "6c" and "Rules that apply throughout" as in Stage 2.

In `theme` mode there is no PR: the preview is built from the Noibu theme change (`references/shopify-theme-preview.md` section 2).

1. **Get the preview** with the method from 6c.
   - **Theme gate open:** `references/shopify-theme-preview.md` sections 2–3 (room check, reuse question, the theme change, `noibu_preview_theme_change` → `previewUrl`).
   - **Gate closed:** say so once, in a single line inside the Stage 4 summary (not its own message): "Pre-merge QA used this skill's own checks; the Shopify theme preview needs a Shopify Online Store theme and Noibu's theme access." Then the next preview method: wait for the PR's preview deployment (poll its checks/comments through the provider every ~60 s for up to 10 minutes), or the staging URL; confirm the preview serves the flag key (`get_dom` on the preview page, look for it) before testing.
2. **Each arm.** The product has no force-variant tool (SDK file), and Cowork's browser cannot run page scripts, so B cannot be forced by adding the helper's class or calling `setContext` here. In order: (a) the repository's own QA override when the codebase already has one (a URL parameter or cookie switch the helper reads) — open the preview with it; (b) otherwise check A in full, and check that B's code is present and gated (the flag key and the B snippet in the DOM, inactive); B's rendering is then checked by the person or after Start: give them the one documented console line from the SDK file to force B in their own browser if they want to look, and record "B not rendered in automated QA" in the verdict. Never claim B was seen when it wasn't.
3. **Run the checklist** in `references/qa-checklist.md`.
4. **A/B checks:** A matches live; B renders and its main interaction works end to end (only when 2a/2b allowed a real render — otherwise "not checked"); unforced, the draft returns the control (A renders on the preview); the assignment `reason` cannot be read without page scripts — list it as checked after Start by `noibu_get_ab_test_results` (sessions per variation) instead.
5. If QA finds a defect, fix it (repository or theme change), push the fix to the existing PR branch (`ab_flow.py check-write <mode> branch-fix`; in the "QA, merge, then start" follow-up this is the only repository write) or re-preview, and re-run the affected checks. Repeat until there is no FAIL.
6. Post the verdict table as a PR comment (when a PR exists), naming the browser (Edge, desktop window) and whether the person could watch, and what was not checked. With no PR yet (`theme` mode), keep the table for the Stage 4 summary and the PR body if one is opened later. Remove the cart line you added (step 7 below).

If no preview was possible, say so, go to Stage 4, and run this QA in Stage 5 step 2.

### Showing the browser during QA

QA is the part the person most wants to see, so it happens in their own Edge window, at a pace they can follow.

1. **One browser, one size.** QA runs in the person's Edge at their window's size (desktop). There is no phone-size view: mobile QA is not possible in Cowork; say so in the summary, and offer — only if they want — that they narrow their own window to phone width for a "narrow desktop window" look, captioned as such. Any `console.noibu.com` page follows SKILL.md's signed-in-only rule.
2. **Open the page** (`create_tab` or `navigate_to` on the run's tab). The browser's own take-control and visibility belong to the host; nothing here hides or shows panels.
3. **Say what's about to happen.** One short message per page (not per step): the page and the two or three things they will see ("the bar appears at the bottom; I tap it to add to cart"). This message is part of QA, so the no-narration rule doesn't cover it.
4. **Show it as a shopper would**: real actions (`scroll`, `dom_click`, `type`) with a `wait` of 2–3 seconds between steps and a `get_screenshot` after each meaningful step.
5. **Click by node, not by coordinate**: take the target's node id from `get_dom` and use `dom_click`. If a coordinate click seems to hit the wrong thing, re-read the DOM before reporting a FAIL.
6. **Keep the evidence**: one screenshot per arm checked plus one for B's main interaction when it rendered. They come back to you, not as files: describe them in the verdict comment; attach images only if real files exist.
7. **Leave things clean but visible**: remove only the cart lines you added, close any modal you opened, leave the last page open. Say in the summary what they saw and what was not checked (console errors, network requests, the assignment `reason`, phone sizes).
