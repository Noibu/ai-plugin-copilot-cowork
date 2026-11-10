# After a report

Read this when the user picks a priority from the next-step question, or types a request about a report already in this conversation. Each section is one request. Act on the report the request refers to: the same store, window and evidence. If more than one recent report could be meant, ask which.

## Investigate a priority

Arrives as a picked option, or typed ("investigate the mobile checkout drop").

- **Don't re-run the breakdown that ranked the priority.** Its Step 4 follow-up already ran; reuse that evidence and query again only for data that wasn't pulled.
- **Go one level deeper** for root cause: error detail on the affected page, example sessions from the affected bucket, or a deeper breakdown of the same segment. One investigation may surface more than one cause, of mixed type (a form issue plus two priority errors, or a slow page).
- **Route the next step by cause type. Decide this after diagnosing.**
  - **UX, funnel, market, discount or operations causes**: write the next step inline: one concrete step, who owns it, and the check that confirms it worked.
  - **Priority error or page-speed causes**: these belong to `tech-diagnosis`, which owns root cause to fix, platform guidance and tickets. Give one line per issue, each carrying its own issue number or page, so several causes become several requests the user can pick from:
    - Fixable error: *Ask Cowork: "use tech-diagnosis to fix issue #<number> on <store>"*
    - Vendor or third-party error: *Ask Cowork: "use tech-diagnosis to share issue #<number> on <store> with the vendor"*
    - Page speed: *Ask Cowork: "use tech-diagnosis to fix <LCP, INP or CLS> on <page URL> for <store>"*
    - If `tech-diagnosis` isn't available, handle the cause inline: name the issue or page, give a one-line likely root cause and a concrete next step. Don't mention adding another skill.
- **Offer to run the next step yourself when Noibu can answer it.** Before handing a step to a human team, check whether Noibu tools can answer it now: page-speed numbers (LCP, INP, CLS) for the affected URL, session replays or session detail for this bucket, a click map for the page, or a deeper breakdown of the same segment. When they can, end with a one-line offer naming the action ("Want me to pull LCP and INP for the checkout page on mobile?"). Don't offer this for steps that are genuinely external (the payment processor checking gateway logs, the theme team reviewing code).
- **Answer in chat with:** the why (the breakdown already gathered, 8 rows at most, plus any deeper root-cause finding), then per cause either the inline next step or the `tech-diagnosis` line, and where it applies the one-line offer. Keep it tight. Don't show the report again.

## Ignore an issue

Only when the user asks ("ignore issue #445"), and only for a Noibu issue with a status; funnel, device and market priorities have none.

Call `noibu_update_issue` to set that issue's status to ignored (confirm the exact status value from the tool schema). Confirm in one line only after the tool returns success, e.g. "Ignored #445; it won't surface on future runs." If `noibu_update_issue` isn't available, say so briefly.

## Download as PDF

Only when the user asks ("download this", "export as PDF").

- **Don't call any Noibu query tool and don't re-run the analysis.** Reuse the exact figures from the report in this conversation; re-querying would move the window, and the PDF would not match what the user saw.
- **If no analysis is in this conversation**, ask the user to run the checkout analysis first. Don't regenerate it silently.

Write a clean document, in this order, and save it as a PDF in the Cowork output folder:

1. Title: the report, store and date range, e.g. "Checkout analysis: example.com · May 11 – Jun 10, 2026".
2. Summary: one short paragraph (2–3 sentences) directly under the title, with no heading. Checkout health: the headline completion read, the single biggest leak, and the top priority to act on.
3. "Overview": the key stats as one sentence (checkout completion, biggest reliable drop, errors, median order, discount rate); then the funnel as a table of stage, sessions and share of cart, showing only instrumented stages; then the payment and delivery mix as tables, only if populated.
4. One section per priority: the priority's title as the heading, then a short paragraph with the key number, sessions affected, and why it matters.

Keep each section on one page where possible. Reply with one line saying where the file is.

## Schedule

Only when the user asks ("schedule this", "send me this every week").

- If a scheduled prompt for this store's checkout analysis already exists, change that one; don't add a second.
- If the request already names how often and when, ask nothing more about timing.
- Otherwise ask one clickable question, header "Schedule", with these options:
  1. "Weekly on Mondays (Recommended)": 9 am · last 30 days against the previous 30
  2. "Every 2 weeks on Mondays": 9 am
  3. "Monthly": 9 am on the 1st
  4. "Something else": the user names the day and time

Set it up as a Cowork scheduled prompt named `checkout-analysis-<store>`, with this prompt: *Run the full checkout analysis for <store>.* The Output section of SKILL.md says what a scheduled run delivers. Confirm in one sentence once the schedule exists.

**Sending the result elsewhere** happens only if the user names a destination: email, Slack or Notion.

- If that connection isn't set up, say in one plain line which connection unlocks it, and stop there.
- Email: confirm the exact recipient addresses in chat before creating the schedule, even if the user already gave them.
- Slack or Notion: ask for the channel or page if it wasn't given.
- Add to the scheduled prompt: *Then send a digest to <destination>.* The digest is:
  - A heading: "Checkout analysis: <store>, <date>".
  - The overview: the funnel as one line ("Added to cart 22,866 → Started checkout 42% → Payment 24% → Completed 23%"), then checkout completion, mobile and desktop conversion, checkout errors, median order and discounted share. Populated stats only.
  - Each priority: its title, its one-sentence evidence, "~N sessions affected", and a line the reader can copy: *Ask Cowork: "investigate <priority title> for <store>"*. One line per priority; never a single generic line at the end.
