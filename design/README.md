# Noibu for Copilot Cowork — UX design guidelines

This folder is the single source of truth for how every Noibu skill looks and behaves in Microsoft 365 Copilot Cowork. Skill authors own **what** a skill finds. This system owns **how** it is shown, what the user can do next, and how failures read.

The goal is the same experience people get from the Noibu plugin in Claude, rebuilt with Cowork's primitives: a short answer in prose, one calm card with link buttons into Noibu, and a clickable "where next?" question.

## Design decisions

| # | Decision | Why |
| --- | --- | --- |
| 1 | **Cards + link buttons + clickable question.** Card buttons only open Noibu console pages (`Action.OpenUrl`). Anything that happens inside Cowork (investigate, download, schedule, create) is offered by the clickable question after the card | Cowork cards can't send button clicks back to the chat (tenant test, Oct 28). Link buttons and the question need no server work |
| 2 | **No MCP App widget** | Real in-chat buttons need a widget served by the Noibu MCP server, which is server-side engineering outside this plugin. See *Future option* in section 3 |
| 3 | **No dashboards** (no Cowork App, no "Save as private Cowork app") | Frontier-only, shared by link, high upkeep. Deep dives go to the Noibu console; recurring views are scheduled reports |
| 4 | **Same turn shape as Claude:** summary → card → question | Users switching between Claude and Cowork get the same experience |
| 5 | **Every unconfirmed behaviour has a fallback.** Untested behaviours have a recovery rule (section 2.6) and are tracked in section 9 until confirmed in real use | The plugin stays usable even where a host behaviour differs from the docs |

| File | Who reads it | Purpose |
| --- | --- | --- |
| `design/README.md` (this file) | People | The full rules, the reasoning behind them, and the PR checklist |
| `design/ux-runtime.md` | Copilot, at run time | The compact version of these rules. `design/sync.py` copies it into every skill as `references/ux-guidelines.md` |
| `design/skill-template/SKILL.md` | People starting a skill | Skeleton with the standard sections and the standard Output block |
| `design/examples/` | People updating the card builder | Reference cards (Adaptive Card 1.6, checked with `cowork_card_check.py`) and next-step question payloads |
| `design/sync.py` | People and CI | Copies `ux-runtime.md` into each skill; `--check` fails if any copy has drifted |

> **Why copies?** Cowork loads each skill folder on its own, so a skill can't reliably read a sibling folder at run time (the repo already ships byte-identical copies of the card scripts for the same reason). Edit `design/ux-runtime.md` only, then run `python design/sync.py`.
>
> To enforce it, add `python design/sync.py --check` as a required CI step (it exits 1 when any skill's copy is missing or stale).

---

## 1. Principles

1. **Answer first.** The first thing the user reads is the answer in plain words, not a loading state, a method note or a wall of numbers.
2. **One card per answer.** A response shows at most one card. The card holds the evidence; the prose holds the headline. Neither repeats the other.
3. **Calm data, colour only for meaning.** Values are monochrome. Colour appears only on change arrows and severity, and never as the only signal.
4. **Every number has a window and a denominator.** "3.1% conversion" is incomplete. "3.1% of 53,212 sessions, Oct 3 – Nov 2 (UTC)" is complete.
5. **Act in chat, deep-dive in Noibu.** Two kinds of next step, never mixed: **buttons on the card open Noibu** (issues, sessions, the A/B draft); **the question after the card acts in Cowork** (investigate, download, schedule, create). We don't build dashboards in Cowork.
6. **Honest states.** Unmeasured is "Not measured", never 0. A failed card says it failed. A button that can't work isn't drawn: no Submit-style buttons, and no link button without a verified URL.

---

## 2. The turn: what every response looks like

### 2.1 Report turn (a skill's main output)

```
1. Summary   2–3 sentences of prose. Lead with the most important movement, use real numbers, mix wins and concerns.
2. Card      One render_ui call: the report card (section 4).
3. Next step One AskUserQuestion: "Where next?" (section 5). Nothing is written after it, unless it is skipped (section 5).
```

- These three steps are **sequential, never batched**. The question's options come from the findings in the card, so render the card first, then ask.
- No preamble ("Let me analyze…"), no recap after the card, no "Here's your report".
- The summary must not restate the card's KPIs one by one. It is the editorial headline: *what moved and why it matters.*

This mirrors the Claude plugin (summary → widget → closing line → AskUserQuestion). In Cowork the question replaces the closing line.

### 2.2 Focused question ("what was conversion yesterday?")

- Prose answer with the number, window and denominator.
- Optional: a Markdown table of up to 8 rows, or an **Answer card** (section 4.3) when a chart or a small comparison makes it clearer.
- Ask a next-step question only when there's an obvious next move (e.g. "Break this down by device?"). Don't force one.

### 2.3 Drill-down turn ("Investigate #2")

- 1–2 sentences: what the investigation found.
- One **Finding card** (section 4.2): evidence, likely cause, the fix or next check, and links into Noibu.
- Next-step question: Get the fix · Open a ticket · Draft a pull request · Back to the report (only those actually available).

### 2.4 Action turn (create a draft, open a ticket, schedule)

- Use Cowork's **native approval** for anything that writes (tool annotations drive this; see section 7).
- After success: one sentence plus a **Result card** (section 4.4) with what was created and an **Open … in Noibu** button. Never claim success without the tool's result.
- Choices along the way (destination, cadence, recipients) are AskUserQuestion calls, one decision per question.

### 2.5 Scheduled runs

People shouldn't have to click anything once a schedule exists. Questions happen at most once, at setup; every run after that is silent.

**Setup (one time, interactive)**

- If the request already names everything (skill, store, cadence, time, destination), ask nothing; confirm in one sentence.
- Otherwise ask **one** question with a ready-made preset first, e.g. `Weekly · Mon 9 am · Summary · Teams (Recommended)`, plus `Customize`. Only `Customize` walks through frequency → day → time → timezone → detail → destination.
- Email always confirms the exact recipient addresses in chat, even if supplied.
- Bake every choice into the scheduled prompt: skill, store UUID and name, rolling window and comparison, detail level, destination, confirmed recipients. The prompt must work with no memory of this chat.
- Tell the user once that Cowork drafts sends for approval unless they approve them ahead of time, and ask them to approve the first run's send so later runs deliver on their own.
- Offer **alert-only mode** where it fits (e.g. technical diagnosis): deliver only when a metric moves past a stated threshold or a new priority appears; otherwise the run ends quietly.

**Each run (unattended)**

- No questions, ever. Use the baked-in choices; if one can't be honoured (destination gone, data missing), deliver what's possible and say what was skipped.
- Content: the 2–3 sentence summary, then the report: the card for a Teams post, a PDF attachment for email (body = summary + priorities as bullet points).
- Next steps become things people can do without a click in Cowork: the Noibu link buttons / links, plus one copyable line per priority, e.g. *Ask Cowork: "investigate checkout priority 1 for example.com"*.
- Never mention "reply with", the clickable question, or buttons that only exist in chat.

**Dependency:** unattended runs only work if the Noibu MCP read tools carry `readOnlyHint: true`. Without it Cowork treats them as writes and waits for an approval no one gives (see section 9).

### 2.6 Failure turn

- If the card can't be built or shown: one sentence saying so and why (use the runner's `fallback_lead`), then the same report as Markdown in the **same section order** (summary → KPIs → funnel → findings → caveats). Keep every number, window and denominator. Then the next-step question as usual.
- If delivery is *unknown* (the host didn't confirm): don't replay or re-render the report; one short sentence at most, then the next-step question.
- If Noibu isn't connected: one line asking the user to finish the Connect prompt, then stop. No partial numbers.
- If the user says a button or link didn't open: reply with the same destination as a plain URL in one sentence. Don't re-render the card.
- If the clickable question didn't appear (the user asks what to do next, or the tool errored): send the "Reply with one: …" fallback line (section 5).
- If the question was skipped or left unanswered: the one-line recovery from section 5 ("Say **next steps** anytime…"), and ask it again when the user says *next steps*.

---

## 3. Surfaces: what to use when

| Need | Use | Don't use |
| --- | --- | --- |
| Headline, explanation, short answer | Prose | Card text that repeats the prose |
| Up to ~8 rows, no visual needed | Markdown table | HTML in chat (not reliably rendered) |
| KPIs, funnel, ranked findings, gauges, small charts | **Adaptive Card** via `render_ui` (one per response) | Hand-written card JSON (the builder owns it) |
| Next step inside Cowork (investigate, download, schedule, create) | **AskUserQuestion** (Cowork's clickable choices) | Submit-style card buttons; "Reply with:" text (fallback only) |
| Confirm a write (draft, ticket, PR, send) | Native approval prompt | Asking "Are you sure?" in prose instead of the approval |
| Deep exploration, replays, filters | **Link button on the card** (`Action.OpenUrl` → `console.noibu.com`) | A Cowork App dashboard |
| More than ~8 rows of data | **Excel file** in the output folder, plus the top 5 in the card | A 50-row card table |
| A report to keep, print or forward | **PDF** in the output folder | Calling HTML a PDF |
| A recurring view | **Scheduled prompt** that delivers a fresh report | A "live" dashboard |

**Out of scope:** Cowork App / "Save as private Cowork app" dashboards (Frontier-only, shared by link, high maintenance).

**Future option (needs Noibu MCP server work):** Cowork renders MCP App widgets (since June 2026), whose buttons can post a message into the chat or call a Noibu tool. The skills already ship the widget assets (`assets/board.html`, `assets/presentation.js`) for a `noibu_show_report` tool. If the Noibu MCP server ever adds that tool, the widget replaces the Adaptive Card and its buttons replace the clickable question; the turn shape, layout, copy and data rules stay the same.

---

## 4. The card system

All cards are built by the shared builder from one `noibu.presentation/1` JSON (see `querying-noibu-data/references/presentation-contract.md`). **Skills write data, never card JSON.** If a skill needs a new visual, add it to the builder so every skill gets it.

### 4.1 Report card (the board)

Order, top to bottom. Omit any section that has no data; never pad.

| # | Section | Contents |
| --- | --- | --- |
| 1 | **Overview** header strip | Left: `OVERVIEW`. Right: `domain · window` (e.g. `example.com · Oct 3 – Nov 2 (UTC)`) |
| 2 | Context line | One line, ≤120 chars: population and reach (e.g. `53,212 sessions · 8.4% added to cart`) |
| 3 | KPI tiles | Up to 5 tiles (rows of 3; Store Pulse 5). Label, value, change arrow. No detail text on the tile |
| 4 | Funnel / chart | One primary visual: funnel, mix bars, gauge or grouped bars |
| 5 | Overview table(s) | Up to 2 tables, 5-row preview each; the rest behind **Show more** |
| 6 | Priorities | Up to 3 numbered findings, ranked by sessions affected (section 4.2 compact form) |
| 7 | Evidence & coverage | Collapsed accordion: caveats, definitions, exact counts. Never removed |
| 8 | Link buttons | Up to 2 Noibu buttons (section 4.5) |
| 9 | Footer | Small, subtle: `Generated Nov 2, 2026, 9:00 pm UTC · Last 30 days vs the preceding 30 days` |

What is **not** on the card: the summary paragraph (it's in the prose), Submit-style buttons, buttons for Cowork actions (investigate, download, schedule), "Reply with:" hints, a "Download & schedule" section or a "Save as private Cowork app" row. Cowork actions live in the question.

### 4.2 Finding

**Compact (inside a report card):**

```
PRIORITY 1 · Device gap                              ~4,200 sessions
Checkout completion fell on mobile                   ← title: metric + move
41.0% vs 46.3% of mobile checkouts, Oct 3 – Nov 2.   ← one evidence sentence, key number + comparison
▸ Next check                                          ← accordion: the specific check + how to verify
Open in Noibu ↗                                       ← inline text link, only with a verified console link
```

Findings inside a report use an inline text link to keep the card compact; the two link buttons are reserved for the report-level destinations.

**Detail (its own Finding card, after "Investigate N"):** header strip (`FINDING · tag`, impact chip), title, evidence (up to 3 lines with numbers), likely cause (labelled as hypothesis if not proven), fix or next check, verification step. Buttons: `Open issue in Noibu` · `View sessions in Noibu`.

### 4.3 Answer card

For focused questions that benefit from a visual: header strip (`metric · domain · window`), up to 3 KPI tiles **or** one chart **or** one table (≤8 rows), plus a one-line caveat if needed. Optional single button to the matching Noibu page. Nothing else.

### 4.4 Result card

After a successful write: header strip (`CREATED IN NOIBU` / `TICKET CREATED` / `SCHEDULED`), the object's name and its key facts (ID, flag key, destination, cadence) as a FactSet. One button: `Open draft in Noibu` / `Open ticket` / none for a schedule. Built from the tool's returned IDs only.

### 4.5 Components

| Component | Spec |
| --- | --- |
| **Header strip** | `emphasis` container. Left: UPPERCASE, Small, Bolder, subtle label. Right: Small subtle meta or an impact chip (≤32 chars). Weighted columns 3:2, never `auto` |
| **KPI tile** | `emphasis` column. UPPERCASE Small label → Bolder Large value → Small arrow delta. Rows share label height so values line up. With 4+ tiles use short names (AOV, RPS, Conversion) and put the currency in the label (`AOV · CAD`) |
| **Change / delta** | `↑ 8.8%` Good, `↓ 0.4 pp` Warning (orange), `— flat` default. Rates change in **pp**, counts and money in **%**. Never `+`/`−` alone; never colour without the arrow |
| **Severity** | Poor = Attention, Needs improvement = Warning, Good = Good, always with the word |
| **Funnel** | First stage shows its count (= 100% base); later stages show % of that same base, not of the previous step. Current and prior each use their own base. Exact counts under **Show exact counts** |
| **Table** | Hairline row dividers, no vertical grid. UPPERCASE Small header row. Names regular weight, left-aligned; numbers right-aligned. The table title is the first column header. 5-row preview, names >40 chars end in "…" |
| **Mix bars** | Label · quiet ProgressBar (share of the largest row) · value right-aligned. Payment and delivery side by side |
| **Core Web Vitals** | Large value + `p75 · band` in severity colour, `Chart.Gauge` with good/needs-improvement/poor segments, threshold legend (INP 200/500 ms, LCP 2,500/4,000 ms, CLS 0.1/0.25) |
| **Accordion** | `Accordion` → `AccordionPage` with `headerTitle`. Used for Show more, Next check, Evidence & coverage, Show exact counts. Starts collapsed |
| **Link button** | A row at the foot of the card: one `emphasis` Column per link, each with `selectAction` → `Action.OpenUrl` and a Bolder, Accent label ending in ↗. Built in the card body (not top-level `actions`) because Cowork's `render_ui` receives only the body. At most 2 per card. Title verb-first, ≤4 words, names the destination (`Open issue in Noibu`, `View sessions in Noibu`, `Open draft in Noibu`). URL is an HTTPS `console.noibu.com` page that follows `console-urls.md` (returned `issueUrl`/`jazzUrl`, or a documented route built by `console_links.py`). No verified URL → no button. Never a non-Noibu URL, never a Cowork action. The builder renders the first 2 report-level `noibuLinks` as these buttons |
| **Inline link** | `Action.OpenUrl` as a `selectAction` on a TextRun reading `Open in Noibu ↗`, `Accent` colour. For per-finding links inside a report card. Same URL rules as the link button |
| **Empty state** | One **No priorities** block with one sentence (e.g. "No checkout step moved more than 3 pp versus the previous 30 days.") |

### 4.6 Colour and type

- **Ink:** default text colour for values, bars and charts. Subtle for labels and meta. `Accent` only for links.
- **Semantic:** `Good` / `Warning` / `Attention` for deltas and severity only. Never colour a value for being big, small or top-ranked.
- **Charts:** `neutral` or a single sequential colour for magnitude; `good` / `warning` / `attention` only for bands. Categorical colours only when categories genuinely need telling apart (≤4).
- **Type:** Bolder for values and titles; Small for labels, meta and footers; UPPERCASE only for eyebrows and table headers; sentence case everywhere else.
- **Dark mode:** use host colour names only (never hex), so cards follow the Cowork theme.

### 4.7 Hard limits

| Limit | Value | Why |
| --- | --- | --- |
| Cards per response | 1 | `render_ui` accepts one call per response |
| Card size | 24,000 bytes (compact JSON) | Teams-based hosts swap larger cards for a "too large" placeholder; the builder switches to compact *before* rendering |
| Schema | Adaptive Card **1.6** | `render_ui` rejects other versions |
| Actions | `Action.OpenUrl` only, as `selectAction`: ≤2 link buttons in the body, plus inline links | `render_ui` allows only OpenUrl/ShowCard; no `ActionSet`, `Action.Submit`, `Action.Execute`, `Action.ToggleVisibility`, no inputs. ShowCard is untested, so we don't use it |
| KPI tiles | ≤5 | Scannable in one row on desktop |
| Priorities on a report | ≤3 (tech diagnosis: ≤2 per section) | 15-second triage |
| Table preview | 5 rows (≤50 behind Show more) | Beyond that, export to Excel |
| Charts per section | 1 | |

### 4.8 Reference cards

`design/examples/` holds one hand-built card per type, using fictional data for `example.com`. They're the visual spec for the builder, not something skills copy. Each passes `cowork_card_check.py`.

| File | Shows | Size (compact) |
| --- | --- | --- |
| `report-card.json` | Checkout report: Overview, 3 KPIs, funnel chart, exact counts, payment mix, 2 priorities with inline links, Evidence & coverage, footer, 2 link buttons | ~12.2 KB |
| `finding-card.json` | Drill-down after "Investigate #1": evidence, hypothesis, next check, verify, 2 link buttons | ~3.2 KB |
| `answer-card.json` | Focused question: conversion by device, 1 link button | ~2.8 KB |
| `result-card.json` | After creating an A/B test draft, `Open draft in Noibu` button | ~1.7 KB |
| `next-step-questions.json` | The AskUserQuestion payload that follows each card, plus the text fallback | — |
| `scheduled-run.md` | A schedule end to end: the one setup question, the stored prompt, and what a run delivers to Teams and email | — |

To preview one, paste it into the Adaptive Cards designer (adaptivecards.microsoft.com/designer) with a Microsoft Teams host selected. Accordion and chart elements may not render outside a Teams/Copilot host, so the real check is a Cowork tenant.

---

## 5. Next steps: the "Where next?" question

The question covers everything that happens **inside Cowork**; the card's link buttons cover Noibu. Never put a Noibu link in the question, and never put a Cowork action on the card. In Claude, the same moment is an AskUserQuestion after the widget; Cowork has the same clickable choices.

**Shape** (from the A/B skill's tested pattern):

- `header` ≤12 characters (e.g. `Next step`).
- `question`: one short line naming the context (`What next for example.com's checkout?`).
- 2–5 options. Labels ≤5 words, verb-first; each with a one-line description that says what will happen.
- Most useful option first; add `(Recommended)` only when one is clearly best.
- No catch-all "Other" option: the user can always type, and typed replies are matched like clicks.
- Nothing is written after the question. The question ends the turn, unless it is skipped (below).
- More than 5 possibilities: show the top ones and name the rest in the question text ("…or type *Investigate 4*").

**Standard option sets**

| After | Options (in order, only those available) |
| --- | --- |
| Report card | `Investigate #1` (description: the finding title) · `Investigate #2` · `Investigate #3` · `Download as PDF` · `Schedule this report` |
| Report card, no findings | `Change the date range` · `Compare by device` (or the skill's natural drill) · `Download as PDF` · `Schedule this report` |
| Finding card | `Get the fix` · `Open a ticket` · `Draft a pull request` (only with a code host connected) · `Back to the report` |
| Result card | The next step in that flow (e.g. `Automate the implementation` after an A/B draft), plus `Done for now` |
| Answer card | Only if a natural drill-down exists (e.g. `Break down by device`) |

**Fallback:** if AskUserQuestion is unavailable or fails, end with one line: `Reply with one: Investigate 1 · Investigate 2 · Download as PDF`. This is the only place "Reply with" text is allowed.

**Skipped or unanswered questions:** once the user skips or closes the question, or replies with something that matches no option, Cowork does not show it again, so the flow would stall. Recover in one line, then stop:

> Say **next steps** anytime to see these options again, or type one: Investigate 1 · Download as PDF · Schedule this report.

When the user later says "next steps", "options", "what now" or similar, ask the same question again for the most recent card (same report, same options). A typed label always works, with or without the question showing. Choice questions inside a flow (goal, destination, schedule setup) recover the same way, with "say **continue** to see this question again".

**Reading the answer:** map the chosen label (or typed paraphrase) to the action for **the report shown in that card**: same workflow, domain, window and evidence. If it's ambiguous which report or finding is meant, ask; never act on a different report.

---

## 6. Copy and voice

- **Sentence case.** UPPERCASE only for eyebrows and table headers.
- **Titles name the metric and the move:** "Checkout completion fell on mobile", not "Mobile issue detected".
- **No** "successfully", "please", exclamation marks, emoji, "I've analyzed…", or hedging filler.
- **Verb-first actions:** "Investigate", "Get the fix", "Open a ticket".
- **Copy budget:**

| Field | Budget |
| --- | --- |
| Prose summary | 2–3 sentences |
| Context line, table note, funnel definition | 1 line, ≤120 chars |
| Finding title | ≤60 chars |
| Finding evidence | 1 sentence, ≤160 chars, key number + comparison |
| Impact chip | ≤32 chars (`~4,200 sessions affected`) |
| KPI label | Metric name only |
| KPI value | One number, one currency |

- **Never on screen:** citation tags, "Source: …" sentences, tool or request IDs, raw field names (`CHECKOUT_COMPLETED`), formulas, ISO timestamps (write `Oct 27, 5:44 pm (UTC)`), customer identifiers.
- Methodology and definitions go to **Evidence & coverage**. They're moved, never dropped.

---

## 7. Data honesty (applies to every surface)

- State the window and timezone once, explicitly. Default comparison: the equal-length window right before.
- Null / unmeasured is **Not measured**, never 0 and never a bar.
- Rates: pp change. Counts and money: % change; undefined when the prior is 0.
- One currency per value; never sum or rank across currencies without a verified conversion.
- Distinct sessions are not event sums. Express checkout can skip stages; say so when it matters.
- Separate measured fact, correlation and hypothesis. Revenue-at-risk figures are directional and only shown when asked.
- Low-volume or vendor-owned issues go to Evidence & coverage, not the priorities.

**Writes and approvals**

- Reading data never authorizes a write. Every write (draft, ticket, PR, status change, schedule, send) is an explicit user choice, then Cowork's native approval.
- Annotate every Noibu MCP tool: `readOnlyHint: true` for reads, `destructiveHint` where it applies. Unannotated tools are treated as destructive and prompt every time.
- Email delivery always confirms the exact recipient addresses in chat, even if supplied.

---

## 8. Claude → Cowork mapping

| Claude plugin | Cowork plugin |
| --- | --- |
| Prose summary before the widget | Same |
| `show_widget` HTML board (Overview, priorities, action bar) | One Adaptive Card from the builder; Noibu link buttons instead of an action bar |
| Widget buttons (`sendPrompt`): Investigate, Get fix, Schedule… | AskUserQuestion after the card |
| Widget "Investigate ↗" / console links | Link buttons and inline links (`Action.OpenUrl`) |
| AskUserQuestion "where next?" | Same, as the last thing in the turn |
| Choice cards (goal, pages, run mode) | AskUserQuestion, one decision per question |
| Hover tooltips | Accordion (`Show exact counts`, `Details & definitions`) |
| "Save as artifact" live dashboard | Dropped. Noibu console link + scheduled report |
| Schedule form widget | One AskUserQuestion with a preset first; `Customize` walks through the details (section 2.5) |
| "Run it once manually to grant permissions" | Approve the first scheduled send (section 2.5) |
| Download report (PDF) | PDF in the Cowork output folder |
| `SuggestConnectors` tiles | One plain line naming the connection that would unlock the step |

---

## 9. Capability status

Keep this table current: it's what the rules rest on. Whoever first sees an ⚠️ or ❓ item work (or fail) in Cowork updates its row in their next PR.

| Capability | Status | If it fails | Source |
| --- | --- | --- | --- |
| Adaptive Card display via `render_ui` (v1.6) | ✅ Works | Markdown fallback (2.6) | Tenant test, Oct 28, 2026 (`adaptive-card-board.md`) |
| Accordion, Table, ColumnSet, Chart.*, ProgressBar, Badge | ✅ In the `render_ui` allow-list; Accordion and charts used by the current builder | Element `fallback` text | `cowork_card_check.py` |
| Submit-style card buttons reaching the conversation | ❌ Don't work | Not used | Tenant test, Oct 28, 2026 |
| Link buttons (`selectAction` → `Action.OpenUrl`) opening the console | ⚠️ Allowed by schema; not yet clicked in a tenant | Plain URL in one sentence (2.6) | `render_ui` allow-list |
| Inline links (`selectAction` on TextRun) | ⚠️ Rendered by the current builder; click not confirmed | Plain URL in one sentence (2.6) | `build_presentation.py` |
| `Action.ShowCard` | ⚠️ Untested | Not used | — |
| AskUserQuestion clickable choices | ✅ Used by the A/B skill | "Reply with one: …" line (5) | `ab-testing/references/choice-cards.md` |
| Text and a question after a `render_ui` call in the same turn | ⚠️ Not yet confirmed | Fallback line (5) | — |
| Native approval for non-read-only tools | ✅ Documented | — | Microsoft Learn, *Build plugins for Cowork* |
| `readOnlyHint` on Noibu MCP read tools | ❓ Ask the MCP server owner | Scheduled runs stall on approvals | Microsoft Learn, *Build plugins for Cowork* |
| Scheduled sends without per-run approval | ⚠️ Needs the user to approve ahead of time | Run drafts the send and waits | Microsoft Learn, *Use Copilot Cowork* (via `scheduling-delivery.md`) |
| Formatted cards in Teams posts | ✅ Documented (April 2026) | Plain-text summary | Microsoft Learn, *What's new in Copilot Cowork* |
| MCP App widget (`noibu_show_report`) | ⏸ Not available: needs Noibu MCP server work | — | Microsoft Learn, *MCP apps plugin author guide for Cowork* |

---

## 10. Skill author checklist (use in every PR)

- [ ] `SKILL.md` follows `design/skill-template/SKILL.md` and its Output section points to `references/ux-guidelines.md`.
- [ ] `references/ux-guidelines.md` is a synced copy (`python design/sync.py --check` passes).
- [ ] Report turns: summary → one card → next-step question. No preamble, no recap, nothing after the question except the skipped-question line (section 5).
- [ ] The skill writes `noibu.presentation/1` data; it never hand-writes card JSON.
- [ ] Every number in the card has a window and a denominator; unmeasured values are null.
- [ ] Findings are ≤3, ranked by sessions affected, each with one evidence sentence and a Next check.
- [ ] Next-step options come from section 5's standard sets; only actions actually available are offered.
- [ ] Card buttons are only Noibu link buttons (≤2, verified URLs per `console-urls.md`). No Submit-style buttons, Cowork actions, "Reply with" hints, dashboards or "Save as private Cowork app" on the card.
- [ ] Every write goes through an explicit choice plus native approval; tools are annotated.
- [ ] The skill has a defined unattended default (or says it can't be scheduled), and its scheduled output follows section 2.5.
- [ ] Copy follows section 6 (no IDs, field names, ISO timestamps or citation tags on screen).
- [ ] If you ran it in Cowork, you updated any ⚠️ rows in section 9 you saw work or fail.
