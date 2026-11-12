---
name: noibu-setup
description: "Connect and verify Noibu in Microsoft 365 Copilot Cowork: confirm the sign-in works, list the stores the user can see, pick one, check that it is receiving data and has a saved business context, and say which optional capabilities (report cards, downloads, scheduling, code host and ticket connections) this session has. Use for \"set up Noibu\", \"connect Noibu\", \"is Noibu working\", \"which stores can I see\", or a first Noibu request with no store chosen yet."
---

# Set up Noibu

Gets a user from "I installed the plugin" to a chosen store and a first workflow. It confirms the Noibu connection, lists the stores the account can see, checks the chosen store, and says what this session can and can't do.

## When to use it

Use it for "set up Noibu", "connect Noibu", "is Noibu working", "which stores can I see", or a first Noibu request that names no store and no task.

Don't use it for:

- Any analysis of a store: `store-pulse`, `checkout-analysis`, `product-analysis`, `segment-analysis` or `tech-diagnosis`.
- Writing a store's business context: `build-business-context`.
- A request that already names a store and a task. Go straight to that skill; it resolves the store itself.

## Guardrails

- If Noibu tools aren't available, ask the user in one line to finish the Connect prompt, then stop.
- Reading data never permits a write. Never report a write as done without the tool's result.
- **Setup runs nothing else.** No analytics, scans, drafts, files or schedules. It ends by offering a workflow; the skill for that workflow does the work.
- **Use this plugin's Noibu connection only.** Never add a second connection, never ask for a pasted token, cookie, password or sign-in code, and never retry a failed call in a loop.
- **Never add a connection or change a security setting for the user.** Say which connection unlocks a step and leave the rest to them or their administrator.
- **Report only what this session shows.** A capability is "available" only when its tool or connection is present in this session, never from documentation or from what the user intends to set up.
- **Show the least identity that answers the question**: the signed-in name or email. No ids, roles or permission lists unless asked.
- **Work quietly.** Don't narrate tool calls. The chat carries the status, the store question and the next-step question.
- On every `noibu_*` call, pass `skill: "noibu-setup"` and a short `skillStep`.

## Before you start

On first use Cowork shows a **Connect** prompt in the chat that opens a Noibu sign-in window, and this turn can start before the sign-in finishes. If no `noibu_*` tool is available, reply with this line and stop:

"Noibu isn't connected yet. Finish connecting with the Connect prompt, then say *continue* and I'll check your access and stores."

If the user says they connected and a later message still has no `noibu_*` tool, suggest two things in order: start a new chat, because tools load at the start of a turn; then check that **Customize → Plugins → Noibu** shows **Connected**, and reconnect if it doesn't. Mention a problem with the plugin itself only after both, never first. Then stop.

## Workflow

1. **Confirm the sign-in.** Call `noibu_get_current_user`. An error here means the connection isn't working: say so in one line, ask the user to reconnect from the Connect prompt, and stop.
2. **List the stores.** Call `noibu_list_domains` with `pagination: {limit: 50, offset: 0}`, and keep paging while a full page comes back. An empty list usually means the Noibu account has no company or store access, not a broken connection: say that, and that a Noibu administrator can grant it.
3. **Pick the store.** If the user already named one, resolve it the way `querying-noibu-data` describes. With one store in the list, use it. With several, ask which in one clickable question with the header "Store", listing up to five; with more than five, say how many there are and that the user can type a store's name.
4. **Check the store**, both calls together, with the store's UUID. Keep its UUID and its integer `numId` for the skills that follow.
   - `noibu_check_data_connection`: whether the store is receiving data. If it isn't, say the Noibu script may not be installed or may have stopped sending, and that the reports will be empty until it is. Don't investigate further.
   - `noibu_get_business_context`: whether a business context is saved. Don't print its contents.
5. **Report**, in short prose: who is signed in, the chosen store, whether it is receiving data, whether a business context is saved, and the optional capabilities below, one line each.
6. **Offer a workflow**: the Output section below.

## Optional capabilities

Give each one as **available**, **not available** or **not checked**.

- **Report cards.** The report skills show their report as a card in the chat, with links to Noibu and a next-step question. If a card can't be shown, the same report appears as text and tables. Not checked until a report runs.
- **Store pages.** Cowork can't open a store's pages or run code in them. Every skill works from Noibu's data; where a page has to be looked at, the skill gives the link and what to check. Always not available.
- **Downloads.** A report can be saved as a PDF when the user asks for it.
- **Scheduling.** A report can run as a Cowork scheduled prompt when the user asks for one. Sending the result to email, Slack or Notion needs that connection; email recipients are always confirmed in chat first.
- **A/B testing.** Test ideas and Noibu drafts need only Noibu. Building a test also needs a connection to the store's code host (GitHub, GitLab, Bitbucket or Azure DevOps), or on a Shopify theme store Noibu's theme preview. Nothing is merged, published or started without the user.
- **Accessibility audits.** Noibu starts the scan but can't return its results here, so findings are reported once the user pastes them in.
- **Code and tickets.** Drafting a pull request needs GitHub connected. Tickets need Linear, Jira, GitHub or Notion connected.

## Output

Setup is a conversation, not a report: no card.

After the report in step 5, ask one clickable question with the header "Next step" and the question "What should I do first for <store>?". Options, in this order:

1. "Check the store's last 24 hours"
2. "Analyze checkout"
3. "Find errors and slow pages"
4. "Find A/B test ideas"
5. "Build the business context" when none is saved; otherwise "Analyze products"

Write nothing after the question. A picked option, or the same request typed, starts that workflow's skill for the chosen store. If the question is skipped or the reply matches no option, don't pick for the user: send one line listing the options, and stop.

If the store isn't receiving data, don't ask the question. End on the report.
