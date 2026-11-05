---
name: noibu-setup
description: Connect and verify Noibu in Microsoft 365 Copilot Cowork, choose an authorized store, and explain which optional capabilities (report cards, browser, scheduling, GitHub and ticket connectors) are available. Use for "set up Noibu", "connect Noibu", "is Noibu working", "which stores can I see", or a first Noibu request.
---

# Set up Noibu

- Use this plugin's **Noibu** connector. On first use Cowork shows a **Connect** prompt in the chat that opens a Noibu sign-in window; this turn may start before sign-in finishes. If `noibu_*` tools aren't available, say "Noibu isn't connected yet. Finish connecting with the Connect prompt, then say *continue* and I'll check your access and stores." and stop. If tools are still missing after the user confirms they connected, follow the runtime guide's troubleshooting steps. Do not add a second connector, ask for pasted tokens or cookies, or retry in a loop.
- Read [shared query guidance](../querying-noibu-data/SKILL.md) and [Cowork runtime](../querying-noibu-data/references/runtime.md). Use skill `noibu-setup` and call `noibu_get_current_user` to confirm access; do not display more identity fields than needed.
- List authorized stores with `noibu_list_domains`, `pagination: {limit: 50, offset: 0}`, continuing pagination as needed. Use a sole store or ask which one. An empty list may mean missing company or domain access in Noibu, not a broken connection.
- Resolve the chosen domain, keep its UUID and integer `numId`, and load saved business context.
- Offer the relevant workflow. Setup does not run analytics, scans, drafts or schedules.

## Optional capabilities

Report each one as **available**, **not available** or **not checked**, based on what this session actually exposes. Never claim one from documentation alone.

- **Report cards.** Reports appear as a card in the chat with Noibu links and clickable next steps. If a card can't be shown, the same report appears as text and tables.
- **Browser.** Cowork's browser is the user's Microsoft Edge from Cowork on the web, when the administrator has enabled browser access. It is optional for analytics. Automated axe scanning additionally needs page-script execution, which Cowork does not document; see [accessibility execution](../accessibility-audit/references/execution-and-review.md). Otherwise a clearly labelled limited review is available.
- **Files.** OneDrive saves (Word) and downloads (PDF) use Cowork's built-in file creation.
- **Scheduling.** Scheduled prompts are managed under Automations; see [scheduling and delivery](../querying-noibu-data/references/scheduling-delivery.md). Email and Teams are built in; Slack and Notion need their plugins. Scheduled sends need the user's approval once, on the first run.
- **A/B testing.** Recommendations and requested DRAFT creation use Noibu only; the live-site check uses the local Edge browser when connected. Building a test additionally uses a GitHub or Azure DevOps connector (or a patch file) and, on Shopify theme stores, Noibu's theme preview tools. Nothing is merged, published or started without the user's confirmation.
- **Source and tickets.** Technical fixes and PRs need a GitHub (or Azure DevOps) connector approved by the administrator; tickets need Linear, Jira (Atlassian), GitHub or Notion. Do not change security settings or add connectors on the user's behalf.

## Output

Follow the [UX guidelines](references/ux-guidelines.md). This is a conversation workflow: answer in short prose, and offer every choice (store, next workflow, save or not) as a clickable question. The card rules apply only if an optional report card is shown.

## Browser prerequisite, only for a requested browser step

Use the local [Edge connection/readiness guide](references/browser-readiness.md). Never prompt for browser setup during ordinary analytics/report display or repeat it when the browser is usable; explain the blocked step and continue nonbrowser work.
