# After a report

Read this when the user picks a priority and an action, or the schedule option, from the next-step prompt, or types a request about a report already in this conversation. Each section is one request. Act on the report the request refers to: the same store, window and evidence. If more than one recent report could be meant, ask which.

## A priority is picked

Arrives from the next-step prompt as two answers, a priority and an action, or typed ("fix the mobile checkout drop", "open a ticket for the payment error").

- **The schedule option** was picked: go to "Schedule" below and ignore the action.
- **Investigate first**, a priority with no action, or a typed "investigate": "Investigate a priority" below.
- **Get the fix**, **Draft a pull request** or **Open a ticket**: the section of that name below. Each starts by finding the cause the way "Investigate a priority" does, without writing the investigation out.

An error priority is a Noibu issue, so its cause, fix, pull request and ticket belong to `tech-diagnosis`. Use that skill for the issue, with the same action (Get the fix, Draft a pull request or Open a ticket), and continue in this conversation; don't make the user ask again. If `tech-diagnosis` isn't available, handle it inline as "Investigate a priority" says.

## Investigate a priority

Arrives as Investigate first, or typed ("investigate the mobile checkout drop").

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

## Get the fix

Find the cause first, as in "Investigate a priority", without writing the breakdown out. Then, per cause:

- **Priority error or page-speed cause:** use `tech-diagnosis` for that issue or page with the action Get the fix.
- **UX, funnel, market, discount or operations cause:** write the finding's title as a `##` heading, the cause in one or two sentences under `### What's likely causing it` (a hypothesis unless the data proves it), then `### What to change`: the one concrete change, who owns it, and the check that confirms it worked.

End with one clickable question, header "Next step": "Draft a pull request" (only when a cause is in the store's code), "Open a ticket", "Investigate further". Write nothing after it.

## Draft a pull request

Find the cause first, as in "Investigate a priority", without writing it out.

- **Priority error or page-speed cause:** use `tech-diagnosis` for that issue or page with the action Draft a pull request. It handles GitHub, the repository and the case where GitHub isn't connected.
- **Any other cause:** the fix isn't a change to one file in the store's code. Say so in one line, then give the fix as in "Get the fix".

## Open a ticket

Find the cause first, as in "Investigate a priority", without writing it out.

- **Priority error or page-speed cause:** use `tech-diagnosis` for that issue or page with the action Open a ticket.
- **Any other cause:**
  1. Ask where the ticket should go: one clickable question, header "Destination", with four options: Linear, Jira, GitHub Issues, Notion.
  2. If the chosen destination isn't connected, say in one plain line which connection unlocks it, and stop.
  3. Ask for the details the destination needs (team, project or page), all in one message, before creating anything.
  4. Create one ticket. Title: the priority's title. Body in Markdown: Summary (the regression with its numbers and window) → Evidence (the breakdown, 8 rows at most) → Likely cause → What to change (the change, its owner and the check that confirms it worked). Labels, only if they already exist: `checkout-analysis`, `noibu`. Assignee: unset unless the user names one.
  5. Give the ticket link the tool returned. Never report a ticket as created without it.

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

When the user picks the schedule option in the next-step question, or asks ("schedule this", "send me this every week").

- If a scheduled prompt for this store's checkout analysis already exists, change that one; don't add a second.
- If the request already names how often and when, ask nothing more about timing.
- Otherwise ask one clickable question, header "Schedule", with these options:
  1. "Weekly on Mondays (Recommended)": 9 am · last 30 days against the previous 30
  2. "Every 2 weeks on Mondays": 9 am
  3. "Monthly": 9 am on the 1st
  4. "Something else": the user names the day and time

**Where to send it.** Once the timing is settled and before creating the schedule, ask one clickable question, header "Send to": "Where should each report be sent?" Skip it if the request already names where.

1. "Email": through Outlook
2. "Teams": a channel or chat
3. "Notion": a page
4. "Only in Cowork": nowhere else

More than one of the first three may be chosen. Every run shows its report in Cowork, whatever is picked.

For each destination picked:

- **Check its connector first**: Outlook for email, Teams, or Notion. If it isn't installed or connected, recommend it in one plain line ("To get this by email, install the Outlook connector in Cowork, then ask me to add email to this schedule"), leave that destination out, and carry on. The schedule is still created.
- **Email** goes through Outlook only. Confirm the exact recipient addresses in chat before creating the schedule, even if the user already gave them.
- **Teams**: ask which channel or chat if it wasn't given.
- **Notion**: ask which page if it wasn't given.
- Add to the scheduled prompt, once per destination: *Then send the digest to <destination>.*

A run that can't send still gives its report in Cowork; the Output section of SKILL.md says how.

Set it up as a Cowork scheduled prompt named `checkout-analysis-<store>`, with this prompt: *Run the full checkout analysis for <store>.* Apart from a send line, write nothing into the prompt about what the run delivers: the Output section of SKILL.md decides that when it runs. Confirm in one sentence once the schedule exists, saying when it runs and where each report is sent.

**The digest:**

- A heading: "Checkout analysis: <store>, <date>".
- The overview: the funnel as one line ("Added to cart 22,866 → Started checkout 42% → Payment 24% → Completed 23%"), then checkout completion, mobile and desktop conversion, checkout errors, median order and discounted share. Populated stats only.
- The priorities on the card, and no others. Each one: its title, its one-sentence evidence and "~N sessions affected".
- End with the script's scheduled lines exactly as given: "Dive deeper by asking Cowork:" and one request per priority on the card. Nothing else for the reader to copy, and no request under an individual priority.

- **Email**: the title is the subject.
- **Teams**: the title in bold.
- **Notion**: a page named with the title; each priority as a heading and a paragraph.
