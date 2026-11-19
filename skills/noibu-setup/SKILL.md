---
name: noibu-setup
description: "Sets a Noibu customer up in Microsoft 365 Copilot Cowork, as an eight-step checklist: confirm the Noibu connection and the store, check the Shopify plugin (Shopify stores), check the code host connection, set up release reporting to Noibu from the store's pipeline, save a business context, verify everything and list what is left and who does it, then schedule one recurring report. Use for \"set up Noibu\", \"connect Noibu\", \"get started with Noibu\", \"onboard me\", \"I just installed the Noibu plugin\", \"finish my Noibu setup\", \"set up release tracking\", \"is Noibu working\", \"which stores can I see\", a first Noibu request with no store and no task, or picking a half-done setup back up."
---

# Set up Noibu

Walks a new customer from "plugin installed" to "Cowork is connected to Noibu, the store and the code, a report is scheduled, and releases are reported to Noibu". It is a checklist of eight steps. Each step first checks what is already in place and only asks the user to act on what is missing, so running it again picks up where it stopped.

## When to use it

Use it for "set up Noibu", "connect Noibu", "onboard me", "what's left in my Noibu setup", "set up release tracking", a first Noibu request that names no store and no task, or to continue a setup left half done.

For "is Noibu working" or "which stores can I see", do steps 1 and 2 only, answer in plain text (who is signed in, how many stores, and whether the chosen one is receiving data), and end with one line offering the rest of the setup.

Don't use it for:

- A request that already names a store and a task. Go straight to that skill; it resolves the store itself.
- Any analysis of a store: `store-pulse`, `checkout-analysis`, `product-analysis`, `segment-analysis` or `tech-diagnosis`.
- Writing a business context from scratch: `build-business-context`. This skill saves an existing file and offers that skill at the end.
- Changing a schedule that already exists: the report's own skill.

## Guardrails

- If Noibu tools aren't available, ask the user in one line to finish the Connect prompt, then stop.
- **Interactive only.** On a scheduled or unattended run, say "Noibu setup needs you in the chat, so this run did nothing." and stop.
- **Four writes, each only after the user picks it in a question:** one scheduled prompt (step 8), one pull request on GitHub (step 5), merging that pull request (step 5), and saving a business context file the user supplied (step 6). Never report a write as done without the tool's result.
- **Merge only the pull request this setup opened, and only when the user picks "Merge it for me".** Never merge any other pull request, approve one, change a branch rule, register or run a pipeline, or commit to a default branch. Those are the user's or their developer's.
- **Shopify is read only here.** Shop information, access scopes and the theme list. No mutation, no theme edit, copy, commit or publish, and no product or setting change, even though the plugin has tools for them.
- **Never add a connection or change a security setting for the user.** Say which plugin unlocks the step and where it is connected (Customize → Plugins), then end the turn.
- **Never ask for a token, password, cookie or sign-in code.** Sign-ins happen in the provider's own window.
- **Check before asking.** Every step starts by checking whether it is already done. Already done: say so in one line and move on.
- **One step at a time.** Never ask a later step's question early.
- **Cowork often hides text written before a clickable question, so progress goes where it is shown.**
  - A turn that ends in a question carries its progress inside the question's text. Every question in the setup has the same three parts, in this order, and nothing else:
    1. The label of the step the question belongs to: "Step 4 of 8 · Code host."
    2. One result of six words or fewer for each step finished since the user's last message: "Shopify connected, previews ready." A second question inside the same step has no result.
    3. The question, worded exactly as the reference gives it, ending in a question mark. Where the user has to do something first, one sentence says what, and the question follows it.

    For example: "Step 2 of 8 · The store. Noibu connected as <name>. Which store are we setting up?" Keep the whole text under 40 words. No introduction, no reasoning, no account of what was checked or found on the way, no advice and no tips: those wait for step 7. Plain text only; the question box renders no formatting. Write nothing outside the question.
  - A turn that ends in plain text gives each finished step two lines: its header on a line of its own (`**Step 3 of 8 · Shopify**`), then one result of twelve words or fewer ("Shopify plugin not found. Theme previews have nowhere to go yet."). The same limits apply as in a question: no reasoning, no advice, and no to-dos or who owns them. Those are recorded and wait for step 7.
  - Anything the user has to read in full ends its turn as plain text, with no question after it: the report list in step 8, a pull request link or a pipeline file in step 5, and the checklist in step 7. Where the setup goes on afterwards, the last line is "Say *continue* and I'll carry on."
- **Skippable from step 3 on** ("skip", "later", "not now"). Record the step as skipped.
- **Nothing is a dead end.** When a step can't be finished (no connection available, a missing permission, someone else has to act), record a to-do with who needs to do it and go to the next step. Step 7 lists every to-do.
- **Keep a ledger** in the conversation and never re-ask what it holds: company name, store name, store UUID, store `numId`, platform, Shopify shop, where theme changes go (Shopify plugin, Noibu, or nowhere yet), the scheduled report, code host, repository, branch, component, the pull request or hand-off, whether a release has reached Noibu, the business context state, skipped steps, and every to-do with its owner.
- **Every choice is one clickable question** with 2–5 options, except the report in step 8 and a plugin connection, which the user types. If it is skipped or the reply matches no option, don't pick for the user and don't ask the question again: reply with one plain-text line listing the options, and end the turn there. Call no tool after that line. The user's next message is the answer.
- **Check a connection by using it, every time.** A plugin connected a moment ago can already be usable in this chat, and a tool may not be listed until it is looked for. So never decide a plugin is missing from the tools in view or from an earlier turn: look for its tool by name (through the tool search, if there is one) and call it. The plugin is here when that call succeeds, and missing only when the lookup and the call both fail. Do this again whenever the user says a plugin is connected.
- **A plugin connection is confirmed in a typed message, never a clickable question.** A plugin's tools and its sign-in may not reach the turn that follows a clicked answer; they do after a message the user types. So when a plugin is missing, end the turn in plain text: the step's header, then "Connect the <plugin> plugin under Customize → Plugins → <plugin>. Then say *connected* and I'll check it, or *skip* to move on." Check again when the user replies.
- **Nothing machine-shaped in what the user reads**: no ids, tool names or field names. The one exception is the contents of a pipeline file. Dates read like "Oct 27, 5:44 pm (UTC)".
- **Work quietly.** Don't narrate tool calls.
- If a file this skill needs is missing, say which in one line and stop.
- On every `noibu_*` call, pass `skill: "noibu-setup"` and a short `skillStep` (for example `"step2-store"`).

## Before you start

Run once: `ls references/store.md references/code.md references/finish.md`

On first use Cowork shows a **Connect** prompt that opens a Noibu sign-in window, and this turn can start before the sign-in finishes. If no `noibu_*` tool is available, reply with this line and stop:

"Noibu isn't connected yet. Finish connecting with the Connect prompt, then say *continue* and I'll start your setup."

If the user says they connected and a later message still has no `noibu_*` tool, suggest two things in order: start a new chat and say "continue my Noibu setup", because tools load at the start of a turn; then check that **Customize → Plugins → Noibu** shows **Connected**. Then stop.

Start at step 1 with no introduction: the step labels show where the setup is, and an introduction ends up inside the first question.

Resolve stores and call Noibu's tools the way `querying-noibu-data` describes; if it isn't available, read tool and field names from the live Noibu tool schema.

## Workflow

1. **Noibu connection.** Confirm the sign-in works. Open `references/store.md`.
2. **The store.** Find and confirm the store this setup is for, and check it is receiving data. `references/store.md`.
3. **Shopify** (Shopify stores only). Check the Shopify plugin is connected to this store and where theme changes can go. `references/store.md`.
4. **Code host.** Find where the store's code lives and check the connection to it. Open `references/code.md`.
5. **Release reporting.** A pull request on GitHub, which the user can have merged from the chat so a test release reaches Noibu, or a filled pipeline file for the developer on any other host. `references/code.md`.
6. **Business context.** Check Noibu for a saved one, or save the user's file. Open `references/finish.md`.
7. **Check everything.** Re-check each item live, then list what is left and who does it. `references/finish.md`.
8. **One scheduled report.** The user types which report, picks how often, and it is scheduled. The user is told to untick "Run once now" when approving, so no report starts in this chat. `references/finish.md`.

## Output

Setup is a conversation, not a report: no card.

During the steps, the chat carries only each step's label, its one-line result and its question, placed as the Guardrails say.

Step 7's reply is plain text: the checklist and the to-do list from `references/finish.md`, the closing lines, then step 8's report list. Step 8 ends in plain text too, naming what the user can ask for next. No clickable question follows either.
