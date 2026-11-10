# After a report

Read this when the user picks a priority from the next-step question, or types a request about a report already in this conversation. Each section is one request. Act on the report the request refers to: the same store, window and evidence. If more than one recent report could be meant, ask which.

## Investigate a priority

Arrives as a picked option, or typed ("investigate the Facebook Ads drag").

- Reuse the evidence already gathered; query again only when new depth is needed, with the Step 3 queries in `references/queries.md`.
- Diagnose the root cause first, then route the action:
  - **UX, campaign, localization or tracking-gap causes**: one concrete action, who owns it, and the check that confirms it worked.
  - **Priority error or page-speed causes**: these belong to `tech-diagnosis`. Give one line per issue the user can act on: *Ask Cowork: "use tech-diagnosis to fix <the issue or page> on <store>"*. If `tech-diagnosis` isn't available, name the issue or page, give a one-line likely root cause and a concrete next step.
- **Answer in plain chat text:** the root cause in 1–2 sentences, then a table of evidence (8 rows at most), then the recommended action. Don't show the report again.

## Download as PDF

Only when the user asks ("download this", "export as PDF").

Use the figures from the report in this conversation. Don't call any Noibu tool and don't query again. If no analysis is in this conversation, ask the user to run the segment analysis first.

Write a clean document, in this order, and save it as a PDF in the Cowork output folder:

1. Title: the report, store and date range, e.g. "Segment analysis: example.com · May 17 – Jun 16, 2026".
2. "Overview": the key stats as one sentence; then four tables: devices, countries, best converting channels, most visited channels.
3. One section per priority: "<Signal type>: <segment name>" as the heading (e.g. "Campaign drag: Facebook Ads"), then a short paragraph with the key number and why it matters.

Keep each section on one page where possible. Reply with one line saying where the file is.

## Schedule

Only when the user asks ("schedule this", "send me this every week").

- If a scheduled prompt for this store's segment analysis already exists, change that one; don't add a second.
- If the request already names how often and when, ask nothing more about timing.
- Otherwise ask one clickable question, header "Schedule", with these options:
  1. "Weekly on Mondays (Recommended)": 9 am · last 30 days
  2. "Every 2 weeks on Mondays": 9 am
  3. "Monthly": 9 am on the 1st
  4. "Something else": the user names the day and time

Set it up as a Cowork scheduled prompt named `segment-analysis-<store>`, with this prompt: *Run the full segment analysis for <store>.* The Output section of SKILL.md says what a scheduled run delivers. Confirm in one sentence once the schedule exists.

**Sending the result elsewhere** happens only if the user names a destination: email, Slack or Notion.

- If that connection isn't set up, say in one plain line which connection unlocks it, and stop there.
- Email: confirm the exact recipient addresses in chat before creating the schedule, even if the user already gave them.
- Slack or Notion: ask for the channel or page if it wasn't given.
- Add to the scheduled prompt: *Then send a digest to <destination>.* The digest is:
  - A title: "Segment analysis: <store>, <date>".
  - The overview: site-wide conversion, then the top and bottom converting segment for each of device, country and channel.
  - The top 3 priorities only. Each one: its signal type, its one-sentence evidence, "~N sessions affected", and a line the reader can copy: *Ask Cowork: "investigate <priority title> for <store>"*.
