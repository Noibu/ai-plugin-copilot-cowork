---
name: ab-testing
description: "Find, build and launch A/B tests on a Noibu-monitored store: ranked test ideas from 30 days of Noibu data, flag-gated variation code, a pull request or a Shopify theme preview, a guided check, and a started test. Use for \"what should we A/B test\", CRO or experiment ideas, building a specific test, implementing a test already found, or taking a Noibu draft test live. Requires the Noibu connection."
---

# A/B testing (find, pick, build, run)

Takes a Noibu-monitored store from "what should we test?" as far as the user wants: a list of ranked test ideas, a draft test in Noibu, the variation code, a pull request or a Shopify theme preview, or a running experiment.

Everything is done through Noibu's tools and data. Nothing here opens the store's pages or runs code in them; where a page has to be looked at, a person looks, with the link and the checklist this skill gives them.

It has two halves, joined at the point where a test is picked:

- **The finder** finds the test opportunities from Noibu data alone: readiness checks, two batches of queries, a check of each idea against what the data shows is already on the store, synthesis, and one report card listing the tests.
- **The build** takes one picked test through a check of the store's code, a Noibu draft, the variation code, a pull request or theme preview, a check the user does, a merge or publish the user makes, proof from data that the code is live, and the start.

## When to use it

Use it for "what should we A/B test", conversion or experiment ideas, building a specific test, implementing a test already found in this conversation, or taking a Noibu draft test live.

Don't use it for:

- Reading the results of a test that is running or stopped: `querying-noibu-data`.
- Where shoppers drop off in checkout, or which products, channels or devices underperform: `checkout-analysis`, `product-analysis`, `segment-analysis`.
- The root cause and fix of an error or slow page: `tech-diagnosis`.

## Guardrails

- If Noibu tools aren't available, ask the user in one line to finish the Connect prompt, then stop. No partial numbers.
- Reading data never permits a write. Never report a write as done without the tool's result.
- If a file this skill needs is missing, say which in one line and stop.
- **Three gates, never skipped.** The user picks the test. The user picks what to automate. The user merges the pull request or publishes the theme. Never merge, publish, deploy or start a test before its gate.
- **The finder writes nothing in Noibu.** A draft is created only when the user asks for one, or by the build once a test and a mode are picked.
- **Do only what the chosen mode promised.** More happens only when the user picks it.
- **Only recommend or build what the merchant can ship, built so it can't break the store** (`references/platforms.md`). A recommendation the merchant can't action wastes their time, and a variation is production code that goes live for every visitor.
- **Never create a draft, branch or pull request for a checkout-metric or checkout-page test on a split-checkout store.**
- **Never start a test whose code isn't live.** Proof comes from Noibu data or the user's own confirmation, never from an assumption.
- **Theme changes go to a copy.** Never discard a theme change or delete a preview theme without the user's go-ahead for that exact one.
- **Tests live in the conversation that found them.** The `candidates.json` in this conversation's working folder is the only place tests are read from. A test proposed in another conversation was ranked against data and a site that have since moved on; a fresh run beats offering it again.
- **Every number comes from this run's queries or pages.**
- **Say what the data can't show.** The finder never saw the page. A claim about what a page contains comes from click data, a click label, the business context or the store's code, or it is marked unconfirmed.
- **Never sign in to the Noibu console for the user**, and never build a console link from anything but ids a Noibu tool returned.
- **Be explicit about what was verified and what wasn't.**
- **Don't narrate.** No "I'm now checking…", no summaries between tool calls, no description of what a question already shows. The chat carries the gates, a blocker, the report, a test's summary before the automation question, the links and checklist for the user's check, and the hand-off.
- **Nothing after a question.** After any clickable question, write nothing and wait. With no answer, don't pick for the user: send one short line listing the options, and wait.
- Platform- and host-specific steps run only when that platform or host was detected. Never assume Shopify or GitHub.
- On every `noibu_*` call, pass `skill: "ab-testing"` and a short `skillStep`.

## Before you start

Run once: `ls scripts/card.py scripts/report.py references/finder.md references/queries.md references/tests-file.md references/platforms.md references/build.md references/follow-ups.md`

Then:

1. **Resolve the store**, one call: `noibu_get_domain` (fall back to `noibu_list_domains`). Keep its UUID, its `numId` and its `siteType` for everything that follows. Nothing else is looked up before the opening question: the repository, the platform's details and the preview method are detected after a test is picked, because the picked test often answers them.
2. **A run already in progress.** If this conversation already has a run of this skill past the opening question and not yet ended, and the skill is asked for again with no new instruction, ask once: "You've started this again for <domain>. Should I start over or continue where we left off?"
   - "Start over (Recommended)": begin again from the opening question; anything in progress is dropped. Recommend "Continue" in its place only when a draft, branch or pull request already exists.
   - "Continue where we left off": name the step in plain words ("the goal question", "the pull request").

## Workflow

**The opening question**, first in every run: "What would you like to do for <domain>?" Up to three options, in this order, with these labels:

| Label | Description |
|---|---|
| Look for new A/B test opportunities | "Analyze the last 30 days of data for fresh, ranked test ideas." Add "for <goal>" when the request named a goal; otherwise add "I'll ask which goal first." |
| Create a specific A/B test | "Describe the change you want to test and I'll build it." When the request already describes a change, add "(Recommended)" to the label and quote the change. |
| Implement an existing A/B test | "Pick from the tests found earlier in this conversation for <domain>." Only when this conversation holds a finder run for this store. |

Skip it when the request already names the route: a named test to build goes straight to the build; a described change is "Create a specific A/B test".

**Look for new A/B test opportunities**

1. Open `references/finder.md` and `references/queries.md` together, and follow `references/finder.md` from the goal question to synthesis. Pass on a goal the request already stated.
2. Write the tests file, build each test's report page and write the report data: `references/tests-file.md`.
3. Deliver the report: the Output section below. Then wait.

If readiness stopped the run, its one sentence is the answer. If the finder found nothing, say so in one line and ask the opening question again.

**Create a specific A/B test**

1. If the change isn't described yet, reply with exactly this and wait: "What would you like to test on <domain>? Tell me the change, which page it's on, and (if you know) what it should improve — e.g. add to cart rate, checkout starts, checkout completes, or product page views."
2. Check the change against `references/platforms.md` ("Where the rules are applied"). A change that fails gets that section's answer.
3. Run the finder with that change stated as the test to build, so it is checked against the data and written as one test in `candidates.json`. If the finder can't produce it, build `createInput` from the description: the title is the change, the hypothesis says it was requested directly with no measured gap behind it, and the metric is the goal the user named (ask if none).
4. Go straight to the build with that test: `references/build.md`.

**Implement an existing A/B test**

1. Take the tests from every `candidates.json` this conversation holds for this store. Drop any in `killed`, and any that `noibu_list_ab_tests` shows as RUNNING or STOPPED.
2. Ask "Which test should I implement?" with one option per test, by rank: the title and nothing else. A question takes five options; with more tests, say how many more there are and that a typed title works.
3. With none left, say why in one line and ask the opening question again with its other two options.
4. Build the picked test: `references/build.md`.

**After the tests are shown**: the user picks a test, or asks to open its report, create it in Noibu, automate it, download its report or schedule the finder. Open `references/follow-ups.md`.

**Checking a test that is running** ("check the quick add test"): `references/build.md`, "Checking a running test is healthy".

**Building a test**: `references/build.md`, read stage by stage. It cites `references/platforms.md` for the platform rules and the flag SDK.

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
- With fewer than two priorities, add: "Look for tests on a different goal", "Create a specific A/B test".
- Schedule preset: Weekly on Mondays · 9 am · last 30 days.
