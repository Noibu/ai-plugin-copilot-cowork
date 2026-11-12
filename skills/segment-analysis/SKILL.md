---
name: segment-analysis
description: "Analyze segment and traffic performance using Noibu data. Use when you want to know which channels, devices, or countries convert best, how mobile compares to desktop, where your traffic is coming from, which segments are underperforming, or where to find your best and worst converting customer segments."
---

# Segment analysis

Compares how devices, countries and channels convert, from Noibu session data. A full analysis ends in one report card with conversion by device, the top countries and channels, and three priorities ranked by sessions affected.

## When to use it

Use it for which channels, devices or countries convert best or worst, how mobile compares to desktop, and where traffic comes from.

Don't use it for:

- Where shoppers drop off inside checkout: `checkout-analysis`.
- Product or collection performance: `product-analysis`.
- The root cause and fix of one error or slow page: `tech-diagnosis`.
- A quick read on the whole store's last 24 hours: `store-pulse`.

## Guardrails

- If Noibu tools aren't available, ask the user in one line to finish the Connect prompt, then stop. No partial numbers.
- Reading data never permits a write. Never report a write as done without the tool's result.
- If a file this skill needs is missing, say which in one line and stop.
- **Bot filter first.** No segment becomes a priority before it has passed the bot filter in `references/queries.md`.
- **An empty store.** If total sessions in the window are zero or a handful, say plainly that the store has no traffic in this window and offer a wider range.
- **Work quietly.** Don't narrate resolving the store, reading files or confirming field names.
- On every `noibu_*` call, pass `skill: "segment-analysis"` and a short `skillStep`.

## Before you start

Run once: `ls scripts/card.py references/queries.md references/report.md references/follow-ups.md`

Then, before any query:

- **Resolve the store.** Use the domain the user gave (name or UUID). If they gave none and the account has one domain, use it. Otherwise ask which store in one clickable question listing up to five of their domains. Ask nothing else.
- **Confirm every field name by its role before using it.** The `querying-noibu-data` skill maps the role names used here to the real Noibu tools and columns. If it isn't available, read tool and field names from the live Noibu tool schema.
- **Window:** the last 30 days unless the user names another.

## Workflow

Pick the route from the request.

**Quick answer**: one focused question ("which channel converts best?", "how does mobile compare to desktop?", "which countries are underperforming?").

1. Open `references/queries.md`, run only the one or two queries the question needs, and answer directly.
2. Offer the full analysis in one clickable question with two options: "Yes: survey device, country and channel, then dig into anomalies" and "No thanks".

**Full analysis**: a broad request, a bare invocation, or yes to that offer.

1. Run the workflow: `references/queries.md`.
2. Write the report data: `references/report.md`.
3. Deliver the report: the Output section below.

**After a report**: the user picks a priority, or types a request to investigate, download or schedule. Open `references/follow-ups.md`.

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
- With fewer than two priorities, add: "Mobile against desktop", "Which countries underperform", "Which channel converts best", "Where traffic comes from".
- Schedule preset: Weekly on Mondays · 9 am · last 30 days.
