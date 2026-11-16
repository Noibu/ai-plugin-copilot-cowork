# After a report

Read this when the user picks a priority or the schedule option from the next-step question, or types a request about a report already in this conversation. Each section is one request. Act on the report the request refers to: the same store, window and evidence. If more than one recent report could be meant, ask which.

## Investigate a priority

Arrives as a picked option, or typed ("investigate the bracelet's low add-to-cart rate").

- **Don't re-run the breakdown that ranked the priority.** Reuse the evidence already gathered; query again only when new depth is needed.
- **Go one level deeper** for root cause, with the Step 4 queries in `references/queries.md`. One investigation may surface more than one cause.
- **Route the next step by cause type. Decide this after diagnosing.**
  - **UX, merchandising, funnel, operations or localization causes**: write the action inline: one concrete step, who owns it, and the check that confirms it worked.
  - **Priority error or page-speed causes**: these belong to `tech-diagnosis`. Give one line per issue the user can act on: *Ask Cowork: "use tech-diagnosis to fix <the issue or page> on <store>"*. If `tech-diagnosis` isn't available, name the issue or page, give a one-line likely root cause and a concrete next step.
- **Answer in plain chat text:** the root cause in 1–2 sentences, then a small table of supporting evidence (8 rows at most), then the recommended action or the `tech-diagnosis` line. Keep it tight. Don't show the report again.

## Download as PDF

Only when the user asks ("download this", "export as PDF").

Use the figures from the report in this conversation. Don't call any Noibu tool and don't query again. If no analysis is in this conversation, ask the user to run the product analysis first.

Write a clean document, in this order, and save it as a PDF in the Cowork output folder:

1. Title: the report, store and date range, e.g. "Product analysis: example.com · May 17 – Jun 16, 2026".
2. "Overview": the key stats as one sentence; then the funnel as a table of step, sessions and share of product viewers; then the top-5 tables for products, collections and product types.
3. One section per priority: "<Signal type>: <product or collection name>" as the heading (e.g. "Low add-to-cart rate: OEX Vertex Hub 1.1"), then a short paragraph with the key number and why it matters.

Keep each section on one page where possible. Reply with one line saying where the file is.

## Schedule

When the user picks the schedule option in the next-step question, or asks ("schedule this", "send me this every week").

- If a scheduled prompt for this store's product analysis already exists, change that one; don't add a second.
- If the request already names how often and when, ask nothing more about timing.
- Otherwise ask one clickable question, header "Schedule", with these options:
  1. "Weekly on Mondays (Recommended)": 9 am · last 30 days
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

Set it up as a Cowork scheduled prompt named `product-analysis-<store>`, with this prompt: *Run the full product analysis for <store>.* Apart from a send line, write nothing into the prompt about what the run delivers: the Output section of SKILL.md decides that when it runs. Confirm in one sentence once the schedule exists, saying when it runs and where each report is sent.

**The digest:**

- A title: "Product analysis: <store>, <date>".
- The overview: the funnel as one line ("Viewed product 38,100 → Added to cart 24% → Completed order 3.4%"), then the key stats.
- The top 3 priorities only. Each one: its signal type, its one-sentence evidence, "~N sessions affected", and a line the reader can copy: *Ask Cowork: "investigate <priority title> for <store>"*.

- **Email**: the title is the subject.
- **Teams**: the title in bold.
- **Notion**: a page named with the title; each priority as a heading and a paragraph.
