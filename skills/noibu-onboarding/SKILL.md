---
name: noibu-onboarding
description: "Guided onboarding for a new Noibu customer in Microsoft 365 Copilot Cowork, as an eight-step checklist: confirm the Noibu connection and the store, check the Shopify plugin (Shopify stores), schedule one recurring report, check the code host connection, set up release reporting to Noibu from the store's pipeline, save a business context, then verify everything and list what is left and who does it. Use for \"get me fully set up with Noibu\", \"onboard me\", \"I just installed the Noibu plugin, what now\", \"finish my Noibu setup\", \"set up release tracking\", or picking a half-done setup back up. For a quick check that Noibu is connected or which stores are visible, use noibu-setup."
---

# Noibu onboarding

Walks a new customer from "plugin installed" to "Cowork is connected to Noibu, the store and the code, a report is scheduled, and releases are reported to Noibu". It is a checklist of eight steps. Each step first checks what is already in place and only asks the user to act on what is missing, so running it again picks up where it stopped.

## When to use it

Use it for "get me fully set up with Noibu", "onboard me", "what's left in my Noibu setup", "set up release tracking", or to continue a setup left half done.

Don't use it for:

- A quick check that Noibu is connected, or which stores the account can see: `noibu-setup`.
- Any analysis of a store: `store-pulse`, `checkout-analysis`, `product-analysis`, `segment-analysis` or `tech-diagnosis`.
- Writing a business context from scratch: `build-business-context`. This skill saves an existing file and offers that skill at the end.
- Changing a schedule that already exists: the report's own skill.

## Guardrails

- If Noibu tools aren't available, ask the user in one line to finish the Connect prompt, then stop.
- **Interactive only.** On a scheduled or unattended run, say "Noibu onboarding needs you in the chat, so this run did nothing." and stop.
- **Three writes, each only after the user picks it in a question:** one scheduled prompt (step 4), one pull request on GitHub (step 6), and saving a business context file the user supplied (step 7). Never report a write as done without the tool's result.
- **Never merge a pull request, register or run a pipeline, or commit to a default branch.** Those are the user's or their developer's.
- **Shopify is read only here.** Shop information, access scopes and the theme list. No mutation, no theme edit, copy, commit or publish, and no product or setting change, even though the plugin has tools for them.
- **Never add a connection or change a security setting for the user.** Say which plugin unlocks the step and where it is connected (Customize → Plugins), then wait for the user.
- **Never ask for a token, password, cookie or sign-in code.** Sign-ins happen in the provider's own window.
- **Check before asking.** Every step starts by checking whether it is already done. Already done: say so in one line and move on.
- **One step at a time.** Never ask a later step's question early.
- **Cowork often hides text written before a clickable question, so progress goes where it is shown.**
  - A turn that ends in a question carries its progress inside the question's text: the step label ("Step 3 of 8 · Shopify."), then one short sentence for each step finished since the user's last message, then the question. Plain text only; the question box renders no formatting. Write nothing outside the question.
  - A turn that ends in plain text opens each step with a header line (`**Step 4 of 8 · One scheduled report**`) and gives each finished step one line of result.
  - Anything the user has to read in full ends its turn as plain text, with no question after it: the report list in step 4, a pull request link or a pipeline file in step 6, and the checklist in step 8. Where the setup goes on afterwards, the last line is "Say *continue* and I'll carry on."
- **Skippable from step 3 on** ("skip", "later", "not now"). Record the step as skipped.
- **Nothing is a dead end.** When a step can't be finished (no connection available, a missing permission, someone else has to act), record a to-do with who needs to do it and go to the next step. Step 8 lists every to-do.
- **Keep a ledger** in the conversation and never re-ask what it holds: company name, store name, store UUID, store `numId`, platform, Shopify shop, where theme changes go (Shopify plugin, Noibu, or nowhere yet), the scheduled report, code host, repository, branch, component, the pull request or hand-off, whether a release has reached Noibu, the business context state, skipped steps, and every to-do with its owner.
- **Every choice is one clickable question** with 2–5 options, except the report in step 4, which the user types. If it is skipped or the reply matches no option, don't pick for the user: send one line listing the options, and wait.
- **Report only what this session shows.** A connection counts as working only when its tool is present in this session and a read through it succeeds.
- **Nothing machine-shaped in what the user reads**: no ids, tool names or field names. The one exception is the contents of a pipeline file. Dates read like "Oct 27, 5:44 pm (UTC)".
- **Work quietly.** Don't narrate tool calls.
- If a file this skill needs is missing, say which in one line and stop.
- On every `noibu_*` call, pass `skill: "noibu-onboarding"` and a short `skillStep` (for example `"step2-store"`).

## Before you start

Run once: `ls references/store.md references/code.md references/finish.md`

On first use Cowork shows a **Connect** prompt that opens a Noibu sign-in window, and this turn can start before the sign-in finishes. If no `noibu_*` tool is available, reply with this line and stop:

"Noibu isn't connected yet. Finish connecting with the Connect prompt, then say *continue* and I'll start your setup."

If the user says they connected and a later message still has no `noibu_*` tool, suggest two things in order: start a new chat and say "continue my Noibu setup", because tools load at the start of a turn; then check that **Customize → Plugins → Noibu** shows **Connected**. Then stop.

Before step 1, say in two sentences what the setup covers (Noibu, the store, one scheduled report, the code, release reporting and the business context) and that any step from the third on can be skipped.

Resolve stores and call Noibu's tools the way `querying-noibu-data` describes; if it isn't available, read tool and field names from the live Noibu tool schema.

## Workflow

1. **Noibu connection.** Confirm the sign-in works. Open `references/store.md`.
2. **The store.** Find and confirm the store this setup is for, and check it is receiving data. `references/store.md`.
3. **Shopify** (Shopify stores only). Check the Shopify plugin is connected to this store and where theme changes can go. `references/store.md`.
4. **One scheduled report.** The user types which report, picks how often, and it is scheduled. `references/store.md`.
5. **Code host.** Find where the store's code lives and check the connection to it. Open `references/code.md`.
6. **Release reporting.** A pull request on GitHub, or a filled pipeline file for the developer on any other host. `references/code.md`.
7. **Business context.** Check Noibu for a saved one, or save the user's file. Open `references/finish.md`.
8. **Check everything.** Re-check each item live, then list what is left and who does it. `references/finish.md`.

## Output

Onboarding is a conversation, not a report: no card.

During the steps, the chat carries only each step's label, its one-line result and its question, placed as the Guardrails say.

After step 8, the reply is plain text: the checklist and the to-do list from `references/finish.md`, then the closing lines, which end by naming what the user can ask for next. No clickable question follows it.
