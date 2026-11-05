# Noibu for Copilot Cowork: UX design guidelines

This folder is the single source of truth for how every Noibu skill looks and behaves in Microsoft 365 Copilot Cowork. It is the **look-and-feel layer**: the rules every skill shares. Skill owners decide **what** their skill finds and add skill-specific behaviour on top; these rules decide **how** it is shown, what the user can do next, and how failures read.

The goal is the same experience people get from the Noibu plugin in Claude, rebuilt with Cowork's primitives: a short answer in prose, one calm card with link buttons into Noibu, and a clickable "what next?" question.

| File | Who reads it | Purpose |
| --- | --- | --- |
| `design/README.md` (this file) | People | The full rules, the reasoning behind them, and the PR checklists (section 11) |
| `design/ux-runtime.md` | Copilot, at run time | The compact version of these rules. `design/sync.py` copies it into every skill as `references/ux-guidelines.md` |
| `design/skill-template/SKILL.md` | People starting or updating a skill | Skeleton with the standard sections and the standard Output section |
| `design/examples/` | People changing the card builder | Reference cards (Adaptive Card 1.6, pass `cowork_card_check.py`), next-step question payloads and a scheduled run, all with fictional data |
| `design/sync.py` | People and CI | Copies `ux-runtime.md` into each skill; `--check` fails if any copy has drifted |

> **Why copies?** Cowork loads each skill folder on its own, so a skill can't reliably read a sibling folder at run time. Edit `design/ux-runtime.md` only, then run `python3 design/sync.py`. CI runs `python design/sync.py --check` on every PR.

## Design decisions

| # | Decision | Why |
| --- | --- | --- |
| 1 | **Card + link buttons + clickable question.** Card buttons only open Noibu console pages. Everything that happens inside Cowork is offered by the clickable question after the card, or typed | Cowork cards can't send button clicks back to the chat (tenant test, Oct 28). Link buttons and the question need no server work |
| 2 | **The question offers priorities only; download and scheduling aren't advertised** | Investigating a priority is the decision the user came for. Download and scheduling aren't mentioned in the summary, card or question; they run only when the user asks |
| 3 | **No MCP App widget** | Real in-chat buttons need a widget served by the Noibu MCP server: server-side engineering outside this plugin. See *Future option* in section 3 |
| 4 | **No dashboards** (no Cowork App, no "Save as private Cowork app") | Frontier-only, shared by link, high upkeep. Deep dives go to the Noibu console |
| 5 | **Same turn shape as Claude:** summary → card → question | Users switching between Claude and Cowork get the same experience |
| 6 | **Two layers.** Guidelines (this folder, the runtime rules synced into every skill, and the shared parts of the card builder) change by guidelines PR; everything else in a skill is its owner's | One look and feel across skills, while each skill can still behave the way its output needs |
| 7 | **Every unconfirmed behaviour has a fallback** (section 2.6), tracked in section 9 until confirmed | The plugin stays usable where a host behaviour differs from the docs |

---

## 1. Principles

1. **Answer first.** The first thing the user reads is the answer in plain words, not a loading state, a method note or a wall of numbers.
2. **One card per answer.** A response shows at most one card. The card holds the evidence; the prose holds the headline. Neither repeats the other.
3. **Calm data, colour only for meaning.** Values are monochrome. Colour appears only on change arrows and severity, and never as the only signal.
4. **Every number has a window and a denominator.** "3.1% conversion" is incomplete. "3.1% of 53,212 sessions, Oct 3 – Nov 2 (UTC)" is complete.
5. **Act in chat, deep-dive in Noibu.** Two kinds of next step, never mixed: **buttons on the card open Noibu** (issues, sessions, the A/B draft); **the question after the card acts in Cowork** (investigate a priority). No dashboards in Cowork.
6. **Honest states.** Unmeasured is "Not measured", never 0. A failed card says it failed. A button that can't work isn't drawn: no Submit-style buttons, and no link button without a verified URL.

---

## 2. The turn: what every response looks like

### 2.1 Report turn (a skill's main output)

```
1. Summary   2–3 sentences of prose. Lead with the most important movement, use real numbers, mix wins and concerns.
2. Card      One render_ui call: the report card (section 4).
3. Next step One AskUserQuestion offering the card's priorities (section 5). Nothing is written after it, unless it is skipped.
```

- The three steps are **sequential, never batched**: the question's options come from the card's priorities, so render the card first, then ask.
- No preamble ("Let me analyze…"), no recap after the card, no "Here's your report".
- The summary is the editorial headline (*what moved and why it matters*), not a list of the card's KPIs.

This mirrors the Claude plugin (summary → widget → closing line → AskUserQuestion); in Cowork the question replaces the closing line.

### 2.2 Focused question ("what was conversion yesterday?")

- Prose answer with the number, window and denominator.
- Optional: a Markdown table of up to 8 rows, or an **Answer card** (section 4.3) when a chart or a small comparison makes it clearer.
- Ask a next-step question only when there's an obvious drill-down (e.g. "Break down by device"). Don't force one.

### 2.3 Drill-down turn (the user picked a priority)

- 1–2 sentences: what the investigation found.
- One **Finding card** (section 4.2): evidence, likely cause, the fix or next check, and links into Noibu.
- Next-step question: Get the fix · Open a ticket · Draft a pull request · Back to the report (only those actually available).

### 2.4 Action turn (create a draft, open a ticket, schedule, download)

- Download, save and schedule start only when the user asks ("download this", "schedule this weekly"). They are never offered or mentioned: not in the summary, the card or the question.
- Use Cowork's **native approval** for anything that writes (tool annotations drive this; see section 7).
- After success: one sentence plus a **Result card** (section 4.4) with what was created and an **Open … in Noibu** button where one exists. Never claim success without the tool's result.
- Choices along the way (destination, cadence, recipients) are AskUserQuestion calls, one decision per question.

### 2.5 Scheduled runs

Nobody should have to click anything once a schedule exists. Questions happen at most once, at setup; every run after that is silent.

**Setup (one time, interactive)**

- If the request already names everything (skill, store, cadence, time, destination), ask nothing; confirm in one sentence.
- Otherwise ask **one** question with the skill's preset first (its SKILL.md names it): label `Weekly on Mondays (Recommended)`, description `9 am · Summary · Teams`; plus `Customize`. Only `Customize` walks through frequency → day → time → timezone → detail → destination, one decision per question.
- Email always confirms the exact recipient addresses in chat, even if supplied.
- Bake every choice into the scheduled prompt: skill, store UUID and name, rolling window and comparison, detail level, destination, confirmed recipients. The prompt must work with no memory of this chat.
- Tell the user once that Cowork drafts scheduled sends for approval unless approved ahead of time, and ask them to approve the first run's send so later runs deliver on their own.
- Offer **alert-only mode** where the skill supports it (e.g. technical diagnosis): deliver only when a stated threshold is crossed or a new priority appears; otherwise the run ends quietly.

**Each run (unattended)**

- No questions, ever. Use the baked-in choices; if one can't be honoured (destination gone, data missing), deliver what's possible and say what was skipped.
- Content: the 2–3 sentence summary, then the report: the card for a Teams post, a PDF attachment for email (body = summary + priorities as bullets with their Noibu links).
- Instead of the question, one copyable line per priority, e.g. *Ask Cowork: "investigate checkout priority 1 for example.com"*.
- Never mention "reply with", the clickable question, or buttons that only exist in chat.

**Dependency:** unattended runs only work if the Noibu MCP read tools carry `readOnlyHint: true`; otherwise Cowork treats them as writes and waits for an approval no one gives (section 9).

### 2.6 Failure turn

- **Card failed** (explicit error): one sentence saying so and why (the runner's `fallback_lead`), then the same report as Markdown in the **same section order** (summary → KPIs → funnel → priorities → caveats), keeping every number, window and denominator. Then the next-step question.
- **Delivery unknown** (the host didn't confirm): don't replay or re-render; one short sentence at most, then the next-step question.
- **Noibu not connected:** one line asking the user to finish the Connect prompt, then stop. No partial numbers.
- **A button or link didn't open** (the user says so): give the same destination as a plain URL in one sentence. Don't re-render the card.
- **The question didn't appear** (tool error, or the user asks what to do next): the "Reply with one: …" fallback line (section 5).
- **The question was skipped or left unanswered:** the one-line recovery from section 5, and ask it again when the user says *next steps*.

---

## 3. Surfaces: what to use when

| Need | Use | Don't use |
| --- | --- | --- |
| Headline, explanation, short answer | Prose | Card text that repeats the prose |
| Up to ~8 rows, no visual needed | Markdown table | HTML in chat (not reliably rendered) |
| KPIs, funnel, ranked priorities, gauges, small charts | **Adaptive Card** via `render_ui` (one per response) | Hand-written card JSON (the builder script makes it) |
| Pick a priority, a destination, a cadence | **AskUserQuestion** (Cowork's clickable choices) | Submit-style card buttons; "Reply with:" text (fallback only) |
| Confirm a write (draft, ticket, PR, send) | Native approval prompt | "Are you sure?" in prose instead of the approval |
| Deep exploration, replays, filters | **Link button on the card** (`console.noibu.com`) | A Cowork App dashboard |
| More than ~8 rows of data | **Excel file** in the output folder, plus the top 5 in the card | A 50-row card table |
| A report to keep, print or forward | **PDF** in the output folder, when the user asks | Calling HTML a PDF |
| A recurring view | **Scheduled prompt** that delivers a fresh report, when the user asks | A "live" dashboard |

**Out of scope:** Cowork App / "Save as private Cowork app" dashboards.

**Future option (needs Noibu MCP server work):** Cowork renders MCP App widgets (since June 2026), whose buttons can post a message into the chat or call a Noibu tool. The skills already ship widget assets (`assets/board.html`, `assets/presentation.js`) for a `noibu_show_report` tool. If the server ever adds that tool, the widget replaces the Adaptive Card and its buttons replace the question; turn shape, layout, copy and data rules stay the same.

---

## 4. The card system

Cards are built by the card builder (`scripts/build_presentation.py`) from one `noibu.presentation/1` JSON (see `querying-noibu-data/references/presentation-contract.md`). **Skills write data, never card JSON.** The runner (`scripts/show_card.py`) builds the card, renders it, and returns `priorityOptions` for the next-step question (section 5).

**Builder copies.** Every report skill carries its own copy of the card scripts. The builder belongs to the guidelines layer, but a skill's owner may change their own copy when the skill's output needs it, even if the change doesn't suit other skills. To keep that manageable:

- Mark each skill-specific edit with a comment: `# SKILL-SPECIFIC (<skill>): <why>`.
- Leave the **shared components** as they are, unless it's a guidelines PR: section and header strip, KPI tile, change/delta, severity, link button, inline link, footer, colours (sections 4.5 and 4.6).
- A guidelines PR that changes the builder applies the change to every copy, keeping each skill's marked edits.
- Run the card check (section 10) before every PR that touches a builder copy.

### 4.1 Report card

Order, top to bottom. Omit any section that has no data; never pad.

| # | Section | Contents |
| --- | --- | --- |
| 1 | **Overview** header strip | Left: `OVERVIEW`. Right: `domain · window` (e.g. `example.com · Oct 3 – Nov 2 (UTC)`) |
| 2 | Context line | One line, ≤120 chars: population and reach (e.g. `53,212 sessions · 8.4% added to cart`) |
| 3 | KPI tiles | Up to 5 tiles (rows of 3; Store Pulse 5). Label, value, change arrow. No detail text on the tile |
| 4 | Funnel / chart | One primary visual: funnel tiles, mix bars, gauge or grouped bars (section 4.5) |
| 5 | Overview table(s) | Up to 2 tables, 5-row preview each; the rest behind **Show more** |
| 6 | Priorities | Up to 3 numbered priorities, ranked by sessions affected (tech diagnosis: up to 2 per merchant / performance / vendor section). Compact form, section 4.2 |
| 7 | More priorities line | Only when there are more than shown: names them, e.g. `2 more: Slow cart drawer, PayPal button error. Ask for "priority 4" or "priority 5".` |
| 8 | Evidence & coverage | Collapsed accordion: caveats, definitions, exact counts. Never removed |
| 9 | Link buttons | Up to 2 Noibu buttons (section 4.5) |
| 10 | Footer | Small, subtle: `Generated Nov 2, 2026, 9:00 pm UTC · Last 30 days vs the preceding 30 days` |

**Not on the card:** the summary paragraph (it's in the prose; accessibility audits are the exception and keep their summary in the card), Submit-style buttons, Cowork actions (investigate, download, schedule), "Reply with:" hints, a "Download & schedule" section, a "Save as private Cowork app" row.

### 4.2 Priority (finding)

**Compact, inside a report card:**

```
PRIORITY 1 · Device gap                              ~4,200 sessions
Checkout completion fell on mobile                   ← title: metric + move (≤60 chars)
41.0% vs 46.3% of mobile checkouts, Oct 3 – Nov 2.   ← one evidence sentence: key number + comparison
▸ Next check                                          ← accordion: the specific check + how to verify
Open in Noibu ↗                                       ← inline link, only with a verified console link
```

The priority's **short name** (≤5 words, e.g. "Mobile checkout completion drop") is what the next-step question shows (section 5). Put it in the finding's `shortTitle` field: written for people, keeping the words that tell two priorities apart. Without it the builder cuts the title to 5 words, which reads worse.

Performance priorities keep the number too: `PRIORITY 3 · LCP · Poor`.

**Detail card** (after the user picks a priority): header strip (`PRIORITY 1 · tag`, impact chip), title, evidence (up to 3 lines with numbers), likely cause (labelled a hypothesis unless proven), fix or next check, verification step. Link buttons: `Open issue in Noibu` · `View sessions in Noibu`.

### 4.3 Answer card

For focused questions that benefit from a visual: header strip (`metric · domain · window`), up to 3 KPI tiles **or** one chart **or** one table (≤8 rows), plus a one-line caveat if needed. Optional single link button. Nothing else.

### 4.4 Result card

After a successful write: header strip (`CREATED IN NOIBU` / `TICKET CREATED` / `SCHEDULED`), the object's name and its key facts (ID, flag key, destination, cadence) as a FactSet. One link button (`Open draft in Noibu`, `Open ticket`), or none for a schedule. Built from the tool's returned IDs only.

### 4.5 Components

| Component | Spec |
| --- | --- |
| **Section** | A header strip followed by its body. **No border or rounded panel around sections**: Cowork already frames the card, and a second frame wastes width on every side. Sections are separated by spacing (`Medium`) and the header strip's background |
| **Header strip** | `emphasis` container, `bleed: true`. Left: UPPERCASE, Small, Bolder, subtle label. Right: Small subtle meta or an impact chip (≤32 chars). Weighted columns 3:2, never `auto` |
| **KPI tile** | `emphasis` column. UPPERCASE Small label → Bolder Large value → Small arrow delta. Labels in a row share a height so values line up. With 4+ tiles use short names (AOV, RPS, Conversion) and put the currency in the label (`AOV · CAD`) |
| **Change / delta** | `↑ 8.8%` Good, `↓ 0.4 pp` Warning (orange), `— flat` default. Rates change in **pp**, counts and money in **%**. Never `+`/`−` alone; never colour without the arrow |
| **Severity** | Poor = Attention, Needs improvement = Warning, Good = Good, always with the word |
| **Funnel** | One row of stage tiles: label, value, and the stage's change under it (`↑ 2.8 pp`). The first stage shows its count (the 100% base); later stages show % of that same base, not of the previous step. Current and prior each use their own base. One short base line under the tiles (≤120 chars, e.g. `% of 101,686 sessions that added to cart`); the full explanation goes to **Details & definitions**. Per-stage current/prior rows and raw counts go under **Show exact counts**, never repeated as visible text. An optional chart may follow, but not alongside a visible per-stage text list |
| **Table** | Hairline row dividers, no vertical grid. UPPERCASE Small header row. Names regular weight, left-aligned; numbers right-aligned. The table title is the first column header. 5-row preview; names >40 chars end in "…" |
| **Mix bars** | Label · quiet ProgressBar (share of the largest row) · value right-aligned. Payment and delivery side by side |
| **Core Web Vitals** | Large value + `p75 · band` in severity colour, `Chart.Gauge` with good / needs-improvement / poor segments, threshold legend (INP 200/500 ms, LCP 2,500/4,000 ms, CLS 0.1/0.25) |
| **Accordion** | `Accordion` → `AccordionPage` with `headerTitle`. For Show more, Next check, Evidence & coverage, Show exact counts, Details & definitions. Starts collapsed |
| **Link button** | A row near the foot of the card: one `emphasis` Column per link, each with `selectAction` → `Action.OpenUrl` and a Bolder, Accent label ending in ↗. Built in the card **body**, not top-level `actions`, because the runner passes only the body to `render_ui`. At most 2 per card. Label verb-first, ≤4 words plus "in Noibu" (`View issues in Noibu`, `Open draft in Noibu`). URL: an HTTPS `console.noibu.com` page per `console-urls.md` (returned `issueUrl`/`jazzUrl`, or a documented route from `console_links.py`). No verified URL → no button. Never a non-Noibu URL, never a Cowork action. The builder renders the first 2 report-level `noibuLinks` as these buttons |
| **Inline link** | `selectAction` → `Action.OpenUrl` on a TextRun reading `Open in Noibu ↗`, `Accent` colour. For per-priority links inside a report card. Same URL rules |
| **Empty state** | One **No priorities** section with one sentence (e.g. "No checkout step moved more than 3 pp versus the previous 30 days.") |

### 4.6 Colour and type

- **Ink:** default text colour for values, bars and charts. Subtle for labels and meta. `Accent` only for links.
- **Semantic:** `Good` / `Warning` / `Attention` for deltas and severity only. Never colour a value for being big, small or top-ranked.
- **Charts:** `neutral` or one sequential colour for magnitude; `good` / `warning` / `attention` only for bands. Categorical colours only when categories genuinely need telling apart (≤4).
- **Type:** Bolder for values and titles; Small for labels, meta and footers; UPPERCASE only for eyebrows and table headers; sentence case everywhere else.
- **Dark mode:** host colour names only (never hex), so cards follow the Cowork theme.

### 4.7 Hard limits

| Limit | Value | Why |
| --- | --- | --- |
| Cards per response | 1 | `render_ui` accepts one call per response |
| Card size | 24,000 bytes (compact JSON) | Larger cards become a "too large" placeholder; the builder switches to compact *before* rendering |
| Schema | Adaptive Card **1.6** | `render_ui` rejects other versions |
| Actions | `Action.OpenUrl` only, as `selectAction` | `render_ui` allows only OpenUrl/ShowCard; no `ActionSet`, `Action.Submit`, `Action.Execute`, `Action.ToggleVisibility`, no inputs. ShowCard is untested, so we don't use it |
| Card width | Set by Cowork | Not controllable from the card today (section 9) |
| KPI tiles | ≤5 | Scannable in one row on desktop |
| Priorities on a report | ≤3 (tech diagnosis: ≤2 per section) | 15-second triage |
| Table preview | 5 rows (≤50 behind Show more) | Beyond that, export to Excel |
| Charts per section | 1 | |

### 4.8 Reference cards

`design/examples/` holds one hand-built card per type with fictional data for `example.com`. They're the visual spec for builder changes; skills don't copy them. Each passes `cowork_card_check.py`.

| File | Shows |
| --- | --- |
| `report-card.json` | Checkout report: Overview, 3 KPIs, funnel tiles with deltas, exact counts, payment mix, 2 priorities with inline links, more-priorities line, Evidence & coverage, 2 link buttons, footer |
| `finding-card.json` | Detail card after picking priority 1: evidence, hypothesis, next check, verify, 2 link buttons |
| `answer-card.json` | Focused question: conversion by device, 1 link button |
| `result-card.json` | After creating an A/B test draft, `Open draft in Noibu` button |
| `next-step-questions.json` | The AskUserQuestion payloads after each card, plus the fallback and skipped-question lines |
| `scheduled-run.md` | A schedule end to end: the one setup question, the stored prompt, and what a run delivers to Teams and email |

To preview a card, paste it into the Adaptive Cards designer (adaptivecards.microsoft.com/designer) with a Microsoft Teams host selected. Accordion and charts may not render outside a Teams/Copilot host; the real check is Cowork.

---

## 5. Next steps: the "what next?" question

The question offers the **priorities on the card**. Everything else in Cowork (download, save, schedule, tickets after a drill-down) starts when the user types it or picks it from a later question. Never put a Noibu link in the question, and never put a Cowork action on the card.

**Shape** (from the A/B skill's tested pattern):

- `header` ≤12 characters (`Next step`).
- `question`: one short line, e.g. `Which priority should I investigate for example.com?`
- Options: the card's priorities **in card order, up to 5**. Use the runner's `priorityOptions` as given: label = the priority's short name (≤5 words), description = `Priority N · <impact chip>` (e.g. `Priority 1 · ~4,200 sessions`). No "Investigate #N" labels.
- More than 5 priorities: name the others in the question text (`…or say "priority 6"`).
- Exactly **one** priority: Cowork needs two options, so add the skill's natural drill-down (its SKILL.md names it, e.g. `Compare by device`).
- **No** priorities: the skill's drill-downs only (e.g. `Compare by device` · `Change the date range`).
- No catch-all "Other" option: the user can always type, and typed replies are matched like clicks ("priority 2", "investigate 2", the priority's name).
- Nothing is written after the question; it ends the turn.

**After a detail card:** `Get the fix` · `Open a ticket` · `Draft a pull request` (only with a code host connected) · `Back to the report`.
**After a result card:** the next step in that flow (e.g. `Automate the implementation` after an A/B draft) · `Done for now`.
**After an answer card:** only if a natural drill-down exists.
**A/B testing** keeps its own option sets (`Preview test N`, `Create A/B test 1`, …; see `ab-testing/references/findings-card.md`). **Accessibility audits** offer their scoped remediation (`Auto-draft PR`, `Auto-create tickets`) as described in their skill.

**Fallback:** if AskUserQuestion is unavailable or fails, end with one line: `Reply with one: <short name> · <short name> · …`. This is the only place "Reply with" text is allowed.

**Skipped or unanswered:** once the user skips or closes the question, or replies with something that matches no option, Cowork doesn't show it again. Recover in one line, then stop:

> Say **next steps** anytime to see these options again, or type one: Mobile checkout completion drop · Delivery step exits.

When the user later says "next steps", "options", "what now" or similar, ask the same question again for the most recent card (same report, same options). Questions inside a flow (goal, destination, schedule setup) recover the same way with "say **continue** to see this question again".

**Reading the answer:** map the chosen label (or typed paraphrase) to **the report shown in that card**: same workflow, domain, window and evidence. If it's unclear which report or priority is meant, ask; never act on a different report.

---

## 6. Copy and voice

- **Sentence case.** UPPERCASE only for eyebrows and table headers.
- **Titles name the metric and the move:** "Checkout completion fell on mobile", not "Mobile issue detected".
- **No** "successfully", "please", exclamation marks, emoji, "I've analyzed…", or hedging filler.
- **Verb-first actions:** "Get the fix", "Open a ticket", "View issues in Noibu".
- **Copy budget:**

| Field | Budget |
| --- | --- |
| Prose summary | 2–3 sentences |
| Context line, table note, funnel base line | 1 line, ≤120 chars |
| Priority title | ≤60 chars |
| Priority short name (question label) | ≤5 words |
| Priority evidence | 1 sentence, ≤160 chars, key number + comparison |
| Impact chip | ≤32 chars (`~4,200 sessions affected`) |
| KPI label | Metric name only |
| KPI value | One number, one currency |

- **Never on screen:** citation tags, "Source: …" sentences, tool or request IDs, raw field names (`CHECKOUT_COMPLETED`), formulas, ISO timestamps (write `Oct 27, 5:44 pm (UTC)`), customer identifiers.
- Methodology and definitions go to **Details & definitions** or **Evidence & coverage**: moved, never dropped.

---

## 7. Data honesty (every surface)

- State the window and timezone once, explicitly. Default comparison: the equal-length window right before.
- Null / unmeasured is **Not measured**, never 0 and never a bar.
- Rates: pp change. Counts and money: % change; undefined when the prior is 0.
- One currency per value; never sum or rank across currencies without a verified conversion.
- Distinct sessions are not event sums. Express checkout can skip stages; say so when it matters.
- Separate measured fact, correlation and hypothesis. Revenue-at-risk figures are directional and only shown when asked.
- Low-volume or vendor-owned issues go to Evidence & coverage, not the priorities. Never pad priorities to fill the question.

**Writes and approvals**

- Reading data never authorizes a write. Every write (draft, ticket, PR, status change, schedule, send) is an explicit user choice, then Cowork's native approval. A declined approval means "not done".
- Every Noibu MCP tool carries annotations: `readOnlyHint: true` for reads, `destructiveHint` where it applies. Unannotated tools are treated as destructive and prompt every time.
- Email delivery always confirms the exact recipient addresses in chat, even if supplied.

---

## 8. Claude → Cowork mapping

| Claude plugin | Cowork plugin |
| --- | --- |
| Prose summary before the widget | Same |
| `show_widget` HTML board (Overview, priorities, action bar) | One Adaptive Card; Noibu link buttons instead of an action bar |
| Widget buttons (`sendPrompt`): Investigate, Get fix… | AskUserQuestion after the card, priorities only |
| Widget Download / Schedule buttons | Typed requests ("download this", "schedule this weekly") |
| Widget "Investigate ↗" / console links | Link buttons and inline links |
| Choice cards (goal, pages, run mode) | AskUserQuestion, one decision per question |
| Hover tooltips | Accordions (`Show exact counts`, `Details & definitions`) |
| "Save as artifact" live dashboard | Dropped. Noibu console link + scheduled report |
| Schedule form widget | One AskUserQuestion with a preset first; `Customize` walks through the details |
| "Run it once manually to grant permissions" | Approve the first scheduled send |
| `SuggestConnectors` tiles | One plain line naming the connection that would unlock the step |

---

## 9. Capability status

The rules rest on this table. Whoever sees an ⚠️ or ❓ item work (or fail) in Cowork updates its row in their next PR.

| Capability | Status | If it fails | Source |
| --- | --- | --- | --- |
| Adaptive Card display via `render_ui` (v1.6) | ✅ Works | Markdown fallback (2.6) | Tenant test, Oct 28, 2026 |
| Accordion, Table, ColumnSet, Chart.*, ProgressBar, Badge | ✅ In the `render_ui` allow-list; used by the builder | Element `fallback` text | `cowork_card_check.py` |
| Submit-style card buttons reaching the chat | ❌ Don't work | Not used | Tenant test, Oct 28, 2026 |
| AskUserQuestion after a card | ✅ Seen in testing (Nov 5) | "Reply with one: …" line | Team testing |
| Skipped question reappearing | ❌ Doesn't reappear | One-line recovery (5) | Team testing |
| Link buttons / inline links opening the console | ⚠️ Not yet confirmed | Plain URL in one sentence (2.6) | `render_ui` allow-list |
| Card width | ⚠️ Set by Cowork; ask Copilot whether its render-ui skill offers a full-width option | Keep cards compact (4.5) | — |
| `Action.ShowCard` | ⚠️ Untested | Not used | — |
| Native approval for non-read-only tools | ✅ Documented | — | Microsoft Learn, *Build plugins for Cowork* |
| `readOnlyHint` on Noibu MCP read tools | ❓ Ask the MCP server owner | Scheduled runs stall on approvals | Microsoft Learn, *Build plugins for Cowork* |
| Scheduled sends without per-run approval | ⚠️ User must approve ahead of time | Run drafts the send and waits | Microsoft Learn, *Use Copilot Cowork* |
| Formatted cards in Teams posts | ✅ Documented (April 2026) | Plain-text summary | Microsoft Learn, *What's new in Copilot Cowork* |
| MCP App widget (`noibu_show_report`) | ⏸ Not available: needs Noibu MCP server work | — | Microsoft Learn, *MCP apps plugin author guide for Cowork* |

---

## 10. Testing a change

- **Your own dev build.** Cowork won't publish a second plugin with the real plugin's manifest ID. Build a zip with your own ID and name (e.g. "Noibu Cowork (dev – Tri)") and publish it **Only you**; turn the original Noibu plugin off while testing. Never commit a dev ID to the repo.
- **Card check.** Build your skill's card from a sample report with `python scripts/build_presentation.py <report.json> --format adaptive-card --output card.json`, then `python scripts/cowork_card_check.py card.json`. Try `--compact` too.
- **In Cowork:** run the skill and check summary → card → question; skip the question and confirm the recovery line; pick a priority; type "download this" and "schedule this weekly".

---

## 11. PR checklists

### 11.1 Guidelines PR (changes to this folder or to the shared card components)

- [ ] `design/README.md`, `design/ux-runtime.md`, the template and the examples agree with each other.
- [ ] `python3 design/sync.py` run; `python3 design/sync.py --check` passes.
- [ ] Builder changes applied to every skill's copy, keeping each skill's `# SKILL-SPECIFIC` edits.
- [ ] Card check (section 10) passes for every report skill, full and compact; the reference cards in `design/examples/` still pass.
- [ ] Section 9 updated with anything confirmed in Cowork.

### 11.2 Skill PR (changes inside one skill)

- [ ] `SKILL.md` keeps the standard Output section from `design/skill-template/SKILL.md`, with its placeholders filled for this skill: summary lead, card contents, drill-down for the one-/no-priority case, scheduled-run preset.
- [ ] `references/ux-guidelines.md` is the synced copy, never edited by hand.
- [ ] Report turns: summary → one card → question with the card's priorities (from `priorityOptions`); nothing after the question except the skipped-question line.
- [ ] Findings carry a `shortTitle` (≤5 words) and a ≤60-character title; ≤3 on the card (tech diagnosis: ≤2 per section), ranked by sessions affected, never padded.
- [ ] Download and scheduling are never offered or mentioned; they run only when asked.
- [ ] Every number has a window and a denominator; unmeasured values are null.
- [ ] Card buttons are only verified Noibu links (≤2). No Submit-style buttons, "Reply with" hints or dashboard offers.
- [ ] Any edit to this skill's builder copy is marked `# SKILL-SPECIFIC (<skill>): <why>` and leaves the shared components alone.
- [ ] Every write goes through an explicit choice plus native approval.
- [ ] Copy follows section 6.
- [ ] Tested with your dev build (section 10); section 9 updated with anything you confirmed.
