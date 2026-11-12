# After a scan or a diagnosis

Read this when the user picks an option from a next-step question, or types one of the requests below. Each section is one request. Act on the finding the request refers to; if more than one could be meant, ask which.

## A priority is picked from a scan

Arrives as a picked option, or typed ("fix issue #445", "fix LCP on the collection pages").

- A fixable error or a page-speed finding: run the diagnosis in `references/diagnosis.md` from Step 2. The store, platform and window are already known.
- A vendor error: go to "Share with a vendor" below.

## Show me the fix

Write the fix only, under `### How to fix it`. Don't repeat the summary or the cause.

- The specific change only: the code or the setting, a note on how to test it, and a pointer to the alternative if there is one.
- Then ask the closing question from `references/diagnosis.md` again, without "Show me the fix".

## Technical details

Only when the user asks, or picks them when sharing. Write exactly these fields in this order, leaving out any with no data. No placeholder text and no commentary between fields.

**For an error:**

- **Issue ID**: the plain identifier (e.g. `#445`)
- **Issue type**: one descriptive line ("HTTP 422 Unprocessable Entity", "JavaScript TypeError")
- **Error message**: exact, in code style
- **Error signature**: when available
- **Pattern**: the short description Noibu provides of when it occurs
- **Stack trace**: the top 3–5 frames, each labelled first-party or third-party
- **HTTP debug data**: request headers, response headers, request payload, response body. Only when the tool populates them. May contain sensitive data
- **Browser impact**: share of occurrences for the top 5 browsers, with a line for the rest
- **OS impact**: same format
- **Browser version impact**: only when one version holds 30% or more of occurrences
- **OS version impact**: only when one version holds 30% or more of occurrences
- **File and line**: only when the code repository was read

**For page speed:**

- **Score**: one combined line: `<Metric> p75 <value>: <band>`
- **Sub-metric breakdown**: when available
- **Affected element**: the CSS selector, from Noibu's clicked selectors or the code repository
- **Detected anti-pattern**: the specific pattern found in the code, when the repository was read
- **Browser impact**: when applicable
- **OS impact**: when applicable
- **File and line**: only when the code repository was read

## Draft a pull request

Needs both: GitHub connected with the store's repository named, and a specific file and line identified from the repository.

- GitHub isn't connected: say in one plain line that connecting GitHub unlocks drafting the pull request, and stop.
- No repository named: ask "What's the repo? (e.g. `mycompany/my-store`)".
- No file and line identified: say so, and show the fix so it can be applied by hand.

When both hold:

1. **Confirm the fix.** Restate the specific change in plain language and ask the user to confirm before touching their code.
2. **Create a branch**, named descriptively (`fix/<plain-English-description>`).
3. **Apply the fix**: write the exact code change to the correct file in the repository.
4. **Open a pull request.** Title: a plain-English summary of what was fixed. Body: Summary → Cause → Fix, in Markdown, with the Noibu issue number.
5. **Confirm it's ready.** Give the link the tool returned and say that someone needs to review and approve it before it goes live.

## Open a ticket

Only for **fixable errors** and **page-speed findings**. Never for vendor issues; those are third-party in origin and not actionable by the operator's team.

A ticket always carries the full content: Summary, Technical details, Cause and Fix.

1. **Ask where the ticket should go**: one clickable question, header "Destination", with four options: Linear, Jira, GitHub Issues, Notion.
2. If the chosen destination isn't connected, say in one plain line which connection unlocks it, and stop.
3. **Ask for the destination details** the platform needs (team, project or page), all in one message, before creating anything.
4. **Create the tickets**, one per eligible finding:
   - Title: `<severity> <summary> (affecting <segment>)`
   - Body in Markdown: Summary → Technical details → Cause → Fix
   - Priority, where supported: critical → high; standard → medium; third-party origin → default or low
   - Labels, only if they already exist: `tech-diagnosis`, `error` or `performance`, the severity, `noibu`
   - Assignee: unset unless the user names one
5. **Give the ticket links** the tool returned. Report partial failures honestly.

## Share findings

Ask two clickable questions, in this order:

1. "Where should these findings go?", header "Destination": PDF, Email, Slack, Notion. More than one may be chosen.
2. "What should be included? (Summary is always included.)", header "Include": Cause (Recommended), Fix (Recommended), Technical details. More than one may be chosen.

Then collect what each destination needs before sending anything:

- PDF: nothing more. Save it in the Cowork output folder as `tech-diagnosis-<domain>-<date>.pdf` and say where it is.
- Email: if it isn't connected, say in one plain line which connection unlocks it. Confirm the exact recipient addresses in chat, even if the user already gave them.
- Slack: if it isn't connected, say which connection unlocks it. Ask which channel.
- Notion: if it isn't connected, say which connection unlocks it. Ask which page or database.

**The content,** in order: Summary → Technical details (if chosen) → Cause (if chosen) → Fix (if chosen). Rewrite it as a standing document:

- No "let me know if" or "want me to walk through" lines, and nothing that waits for direction.
- An alternative fix reads as a plain statement: "If the primary fix doesn't resolve it, the alternative is <X>."
- The reasoning note becomes a single-line caveat at the top.
- No console or replay links. Issue numbers as plain identifiers are fine. Links only when the user asks for them.

**Per destination:**

- **Email**: subject "Tech findings for <domain>: <N> items to investigate". A scannable body.
- **Slack**: lead-in "Tech findings for <domain>: <N> items, last <window>." One section per finding.
- **Notion**: title "Tech findings for <domain>, <date>". One section per finding.

## Share with a vendor

Arrives as a picked vendor priority, or typed ("share issue #512 with the vendor").

Fetch the error detail. Write a vendor-facing summary the user can copy: what is happening, which pages, the occurrence count, and the browser and OS breakdown.

Don't ask where to send it. Present the summary as copyable text. Then, only if email or Slack is already connected, ask in one line: "Want me to send this via email or Slack?" If neither is connected, give the summary only.

## Ignore an issue

Only when the user asks ("ignore issue #445").

Take the issue number. Call `noibu_update_issue` to mark it ignored. After the tool returns success, confirm: "Issue #<number> marked as ignored." Nothing more.

## Schedule

Only when the user asks ("schedule this", "scan every week").

- If a scheduled prompt for this store's scan already exists, change that one; don't add a second.
- If the request already names how often and when, ask nothing more about timing.
- Otherwise ask one clickable question, header "Schedule", with these options:
  1. "Weekly on Mondays (Recommended)": 9 am
  2. "Every 2 weeks on Mondays": 9 am
  3. "Monthly": 9 am on the 1st
  4. "Something else": the user names the day and time

Set it up as a Cowork scheduled prompt named `tech-scan-<store>`, with this prompt: *Run a tech diagnosis scan for <store>.* The Output section of SKILL.md says what a scheduled run delivers. Confirm in one sentence once the schedule exists.

**Automations** are added only when the user names them in the request. Never suggest them. For each one named, check its connection first; if it isn't set up, say in one plain line which connection unlocks it, and leave that automation out.

- **Draft pull requests** (GitHub, with the repository named): add to the prompt: *For each fixable error and fixable page-speed finding, determine the fix, create a branch named `fix/<plain-description>` in <repo>, commit the change and open a draft pull request titled with a plain-English summary. Collect each link.*
- **Create tickets** (Linear, Jira, GitHub Issues or Notion, with the team or project named): add: *For each fixable error and page-speed finding, not vendor issues, create a ticket in <platform> / <team>. Title: `<severity> <summary> (affecting <segment>)`. Body: Summary → Technical details → Cause → Fix, with any alternative. Priority: critical → high; standard → medium. Collect each link.*
- **Send a digest** (email, Slack or Notion, with the destination named; for email, confirm the exact recipient addresses in chat first): add: *Then send the digest to <destination>.*

**The digest:**

- Title: "Tech scan: <store>, <date>".
- Findings in a fixed order: fixable errors, page-speed findings, vendor issues. Up to 2 of each.
- Each finding: its kind, a one-line description, its occurrence or session count, then one line per completed automation with its link ("Draft PR: <link>", "Ticket: <link>").
- For anything that could not run (a connection unavailable, a fix that isn't a code change), give a line the reader can copy:
  - Fixable error: *Ask Cowork: "use tech-diagnosis to fix issue #<number> on <store>"*
  - Vendor error: *Ask Cowork: "use tech-diagnosis to share issue #<number> on <store> with the vendor"*
  - Page speed: *Ask Cowork: "use tech-diagnosis to fix <LCP, INP or CLS> on <page URL> for <store>"*
