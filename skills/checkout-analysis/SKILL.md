---
name: checkout-analysis
description: "Analyze checkout performance and health using Noibu data. Use when you want to know where shoppers drop off in the checkout funnel, what payment or delivery methods customers are using, why completion rates are low, what priority errors are hurting checkout, or how cart and order values benchmark."
---

# Checkout analysis

Finds where shoppers drop off in checkout and what changed, from Noibu session, order-value and error data. A full analysis ends in one report card with up to three priorities, ranked by sessions affected.

## When to use it

Use it for the checkout funnel, completion rates, abandonment, payment and delivery methods, checkout errors, and cart and order values.

Don't use it for:

- Product or collection performance: `product-analysis`.
- Channel, device or country comparisons across the whole store: `segment-analysis`.
- The root cause and fix of one error or slow page: `tech-diagnosis`.
- A quick read on the whole store's last 24 hours: `store-pulse`.

## Guardrails

- If Noibu tools aren't available, ask the user in one line to finish the Connect prompt, then stop. No partial numbers.
- Reading data never permits a write. Never report a write as done without the tool's result.
- If a file this skill needs is missing, say which in one line and stop.
- **Analyze what's present, never flag what's missing.** Which fields are populated varies by platform and account. An empty or null result is normal: skip that slice silently and build from the data that is there. No zero rows, no "no data" placeholder, and never a finding, priority or caveat about missing data, tracking or coverage.
- **Trust cart to completion when the steps between aren't instrumented.** If checkout-started or payment-submitted counts are near zero while completions are healthy, those events aren't tracked for this store. Don't treat the apparent drops as real: use cart to completion as the headline rate and lean on device, country and discount splits for the drop story.
- **An empty store is the one exception.** If total sessions in the window are zero or a handful, say plainly that the store has essentially no traffic in this window and offer a wider range or another store.
- **Work quietly.** Don't narrate resolving the store, reading files, or choosing tools, queries or fields. Narrate only what the data shows.
- On every `noibu_*` call, pass `skill: "checkout-analysis"` and a short `skillStep`.

## Before you start

Run once: `ls scripts/card.py references/queries.md references/report.md references/follow-ups.md`

Then, before any query:

- **Resolve the store, and keep the company id returned with it.** Use the domain the user gave (name or UUID). If they gave none and the account has one domain, use it. Otherwise ask which store in one clickable question listing up to five of their domains. Ask nothing else; take the default window and proceed. Priority errors and data-connection checks need the company id as well as the domain UUID.
- **Confirm every field name by its role before using it.** The `querying-noibu-data` skill maps the role names used here ("session query tool", "funnel depth field") to the real Noibu tools and columns and documents query limits. If it isn't available, read tool and field names from the live Noibu tool schema. Don't stop or guess.
- **Window:** the default in `querying-noibu-data`; if none, the last 30 days. The comparison is the equal-length window immediately before.

## Workflow

Pick the route from the request.

**Quick answer**: one focused question ("where do people drop off?", "what payment methods are used?", "errors on my checkout pages?").

1. Open `references/queries.md` and run only the one or two queries the question needs: funnel is Q1, why people abandon is Q1b, payment methods is Q3, errors is Q5.
2. Answer in a few sentences, with a small table if it helps.
3. Offer the full analysis. On yes, run it.

**Full analysis**: a broad request, a bare invocation, or yes to that offer.

1. Broad overview, current and previous window: `references/queries.md`, Step 1. Start by telling the user what you're doing in one line.
2. Rates and their change against the previous window: `references/queries.md`, Step 2.
3. Pick up to three regressions: `references/queries.md`, Step 3.
4. Run only the follow-up queries those call for: `references/queries.md`, Step 4.
5. Write the report data: `references/report.md`.
6. Deliver the report: the Output section below.

**After a report**: the user picks a priority, or types a request to investigate, ignore an issue, download or schedule. Open `references/follow-ups.md`.

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
- With fewer than two priorities, add: "Where shoppers leave checkout", "Mobile against desktop checkout", "Payment and delivery methods", "Checkout errors".
- Schedule preset: Weekly on Mondays · 9 am · last 30 days against the previous 30.
