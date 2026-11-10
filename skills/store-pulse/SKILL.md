---
name: store-pulse
description: An instant, at-a-glance read on your store's health from the last 24 hours, with the option to schedule a recurring report. Use to check on how the overall store is doing, or to schedule a recurring summary.
---

# Store Pulse

A daily snapshot of the store. Every run leads with a fresh answer for the last 24 hours against the 24 hours before: a short summary, the five headline numbers, the purchase funnel, and up to three threads worth pulling on.

## When to use it

Use it for "how's my store doing", "check on example.com", a bare invocation, or a request to schedule a recurring store summary.

Don't use it for:

- Where shoppers drop off in checkout: `checkout-analysis`.
- Which products or collections underperform: `product-analysis`.
- Which channels, devices or countries convert best: `segment-analysis`.
- Why an error or slow page is happening: `tech-diagnosis`.

## Guardrails

- If Noibu tools aren't available, ask the user in one line to finish the Connect prompt, then stop. No partial numbers.
- Reading data never permits a write. Never report a write as done without the tool's result.
- If a file this skill needs is missing, say which in one line and stop.
- **Always fresh.** Every run queries the last 24 hours again. Never answer from an earlier snapshot.
- **Don't fake the math.** A measure that comes back null is not measured; it is never 0. If the window has no sessions, say there was no traffic in this window.
- **One schedule per store.** Different stores can each have their own.
- **Work quietly.** Don't narrate resolving the store, reading files or choosing tools. Narrate only what the data shows.
- On every `noibu_*` call, pass `skill: "store-pulse"` and a short `skillStep`.

## Before you start

Run once: `ls scripts/card.py references/snapshot.md references/blocks.md references/follow-ups.md`

Then resolve the store. Use it without asking if it is already clear from the conversation. Otherwise call `noibu_list_domains`: with one result, use it; with several and none named, ask which store in one clickable question listing up to five.

## Workflow

**Snapshot**: every invocation.

1. Run the headline and funnel queries for the last 24 hours and the 24 hours before: `references/snapshot.md`.
2. If the user asked for top products, channel performance or paid ad performance, run those too: `references/blocks.md`.
3. Write the report data: `references/snapshot.md`, "Report data".
4. Deliver the report: the Output section below.

**A focused question** about one of the snapshot's numbers ("what's my conversion today?", "how are my channels doing?"): run only the query it needs from `references/snapshot.md` or `references/blocks.md` and answer in prose.

**After a snapshot**: the user picks a thread, or types a request to schedule or download. Open `references/follow-ups.md`.

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
- With fewer than two priorities, add: "Where's the biggest revenue opportunity?", "What changed since yesterday?".
- Schedule preset: Weekly on Mondays · 9 am · the preceding 7 days.
