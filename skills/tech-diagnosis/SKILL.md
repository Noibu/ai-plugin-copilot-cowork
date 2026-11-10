---
name: tech-diagnosis
description: "Diagnose technical issues and Core Web Vital performance problems using Noibu data, and recommend a fix. Use when you want to know what's broken across the store, why an error is happening, what's causing errors, the root cause of poor page performance, how to fix a technical issue, why an error rate spiked, or where errors are concentrated."
---

# Tech diagnosis

Two modes:

- **Scan**: no specific issue is named. Scans for the highest-value errors and page-speed problems and delivers a prioritized report card.
- **Diagnosis**: a specific signal is named. Produces one self-contained finding: summary, cause, fix.

## When to use it

Use it for what's broken across the store, why an error happens, why a page is slow, how to fix a technical issue, and where errors concentrate.

Don't use it for:

- Where shoppers drop off in checkout: `checkout-analysis`.
- Product or collection performance: `product-analysis`.
- Channel, device or country conversion: `segment-analysis`.
- Accessibility violations: `accessibility-audit`.

## Guardrails

- If Noibu tools aren't available, ask the user in one line to finish the Connect prompt, then stop. No partial numbers.
- Reading data never permits a write. Never report a write as done without the tool's result.
- If a file this skill needs is missing, say which in one line and stop.
- **No client-side data joins.** Read each Noibu source on its own terms.
- **Don't overstate impact.** "Present in X sessions", not "blocking X users". No revenue projections or lost-revenue figures.
- **Plain language.** Translate Noibu labels; keep identifiers in code style.
- **No citation sections.**
- **Never narrate internals.** No tool names, query parameters, state values, filter logic or fallback decisions. Retries happen silently.
- **Page criticality is internal only.** Checkout > Cart > Product page > Collection > Home > Other. Never a labelled field.
- **Name third-party services specifically.** If the stack trace says Klaviyo, GTM or Shop Pay, use that name.
- **Root cause, never suppression.** A fix addresses why the error happens. Never wrap code in try/catch to silence an error or add null checks that hide the real issue.
- **Never merge anything.** A person reviews and approves every pull request.
- On every `noibu_*` call, pass `skill: "tech-diagnosis"` and a short `skillStep`.

## Before you start

Run once: `ls scripts/card.py references/scan.md references/platforms.md references/diagnosis.md references/follow-ups.md`

Then:

1. **Store.** A UUID: use it. A name: resolve it. Nothing: ask which store in one clickable question listing up to five of the user's domains. Note the store's **platform** (Shopify, Magento, WooCommerce, BigCommerce or other).
2. **Mode.** Pick it from the request:
   - **Scan**: no specific issue given. A domain name alone is a scan. "Run tech diagnosis", "what's broken", "scan for issues".
   - **Diagnosis**: a specific issue is named with the store: an error name, a metric and a page, a Noibu issue number, or a page URL.
   - **Share with vendor**, **ignore an issue**, **schedule**: the request says so. Go straight to `references/follow-ups.md`.
   - **Unclear**: ask "Are you looking for a scan of what's broken across the store, or do you have a specific issue in mind?"
3. **Window.** The last 30 days unless the user names another.

## Workflow

**Scan**

1. Send first, before any query: "Scanning <store> for the top technical errors and performance issues. This may take a moment."
2. Read the platform's frame paths: `references/platforms.md`.
3. Scan errors, scan page speed, and rank: `references/scan.md`.
4. Write the report data: `references/scan.md`, "Report data".
5. Deliver the report: the Output section below.

**Diagnosis**

1. Follow `references/diagnosis.md` from Step 1. Classify stack frames with `references/platforms.md`.
2. The first thing the user sees is the finding, never narration.
3. End with the closing question that file defines.

**After a scan or a diagnosis**: the user picks a priority, or asks to see the fix, draft a pull request, open a ticket, share findings, share with a vendor, ignore an issue, or schedule. Open `references/follow-ups.md`.

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
- With fewer than two priorities, add: "Diagnose a specific error", "Check speed on a specific page".
- Schedule preset: Weekly on Mondays · 9 am · errors from the last 7 days, page speed from the last 30.
