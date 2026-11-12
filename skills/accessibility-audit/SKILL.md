---
name: accessibility-audit
description: "Audit a website for WCAG 2.1 AA accessibility violations using Noibu's page scanner and traffic data, and turn the findings into prioritized fixes. Use when you want to know what's inaccessible across the store, check WCAG or ADA compliance, find contrast or heading errors, audit for screen reader support, generate an accessibility report, or fix accessibility violations with pull requests or tickets."
---

# Accessibility audit

Starts Noibu's WCAG 2.1 AA scan on the store's ten busiest pages and gives the links to the results. When the user brings findings back into the conversation, it pools the repeats into unique fixes, ranks them by severity and traffic, and reports them.

The scan runs on Noibu's side, and its results open in the Noibu console. **This skill cannot read an audit's results.** It works on findings only once the user pastes or attaches them.

## When to use it

Use it to find what's inaccessible across the store, check WCAG or ADA compliance, find contrast or heading errors, check screen reader support, produce an accessibility report, or fix violations with pull requests or tickets.

Don't use it for errors, crashes or slow pages (`tech-diagnosis`), or for conversion and funnel questions (`checkout-analysis`, `product-analysis`, `segment-analysis`).

## Guardrails

- If Noibu tools aren't available, ask the user in one line to finish the Connect prompt, then stop.
- Reading data never permits a write. Never report a write as done without the tool's result.
- If a file this skill needs is missing, say which in one line and stop.
- **Never state a finding, a count or a severity the user did not provide.** After starting audits, there is nothing to report but the pages and their links.
- **Start an audit only when the user asks for one.** Each start is a new scan.
- **Never name the scanning tool** in anything the user sees.
- **Say what an automated audit is.** Every report of findings carries one sentence: automated checks find 30%–90% of issues on the scanned pages, and the result is informational, not legal advice or a compliance certification.
- **Pool before scoring or reporting anything.** The same selector and criterion is one finding (`references/findings.md`, "Pooling").
- **"Pageviews", never "visits".**
- **"GitHub Issue", never bare "Issue".** "Automated tickets" is the umbrella term for any ticket or GitHub Issue this skill creates.
- **"Severity"** is the scan's impact level (critical, serious, moderate, minor). **"Priority"** is the traffic-weighted ranking score; it decides order and is never shown as a number.
- **"Auto-draft PR"**, never "Auto-fix".
- **Every WCAG criterion links to its W3C Understanding page** in prose, PDFs, tickets and pull requests: `https://www.w3.org/WAI/WCAG21/Understanding/<slug>.html`.
- **Never merge anything.** A person does every merge, close and status change.
- **Link out; don't copy status.** Never reproduce a ticket's or GitHub Issue's live status in a report.
- On every `noibu_*` call, pass `skill: "accessibility-audit"` and a short `skillStep`.

## Before you start

Run once: `ls scripts/card.py references/audit.md references/findings.md references/fix-locations.md`

Then resolve the store. A UUID: use it. A name: `noibu_get_domain`. Neither: `noibu_list_domains`; use it if there is exactly one, else ask which in one clickable question listing up to five. Keep the domain's UUID, its integer `numId` and its name; the scan takes the `numId` and the result links take the UUID. Note the store's platform.

## Workflow

**Run an audit**: the user asks for an accessibility audit.

1. Pull the top 10 pages by 30-day pageviews and start one scan per page: `references/audit.md`.
2. Reply with the pages and their result links, as that file says. No card and no next-step question: there are no findings yet.

**Report on findings**: the user pastes or attaches findings from an audit.

1. Pool, score and sort them, and write the report data: `references/findings.md`.
2. Deliver the report: the Output section below.

**After a report**: the user picks a priority, or asks to download the report, draft pull requests or create tickets. Open `references/findings.md`, "After the report". Pull requests use `references/fix-locations.md`.

**Schedule**: the user asks to run the audit on a schedule. Open `references/audit.md`, "Schedule".

## Output

A full report is three separate steps, in this order:

1. **Summary.** 2–3 sentences. Lead with the biggest movement, with real numbers and their window. Don't repeat the card's numbers.
2. **Card.** Write the report data, then run `scripts/card.py` once; it builds and shows the card. Never write card JSON yourself. If it fails, say so in one sentence and give the same report as Markdown.
3. **Next step.** One clickable question with the header "Next step" and the options the script returned, exactly as given. Write nothing after it. If it is skipped, reply with the script's recovery line and stop.

Finding titles name the metric and the move in 60 characters or fewer. Each finding has one evidence sentence with its number and comparison.

A focused question gets prose with the number, its window and its base; a card only if it helps.

Download, save and schedule run only when the user asks. Never offer them.

In a scheduled run, ask nothing. Deliver the summary and the card, then one line per priority: *Ask Cowork: "investigate <priority title> for <store>"*.

- Run the card: copy `scripts/card.py` to `.aether/scripts/card.py`, then RunScript `card.py` with the arg `report` set to the path of the report data file.
- With fewer than two priorities, add: "See every finding", "Pages scanned and their violation counts".
- Schedule preset: Weekly on Mondays · 9 am · top 10 pages by 30-day pageviews.
