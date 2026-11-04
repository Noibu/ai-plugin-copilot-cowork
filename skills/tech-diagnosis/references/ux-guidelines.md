# Noibu UX guidelines (runtime)

<!-- Source: design/ux-runtime.md. Synced into every skill as references/ux-guidelines.md by design/sync.py. Do not edit the copies. -->

Every Noibu skill follows these rules for what the user sees. Where a skill's own instructions add detail, follow both. Where they conflict on presentation, these rules win, except for data rules in the skill's query references.

## 1. Shape of a response

**Full report** (the skill's main output), in this order, as separate steps:

1. **Summary:** 2–3 sentences of prose. Lead with the most important movement, use real numbers with their window, mix wins and concerns. Don't list every KPI.
2. **Card:** exactly one `render_ui` call, built by this skill's card runner from a `noibu.presentation/1` report (see `references/card-quickstart.md`). Never hand-write card JSON.
3. **Next step:** one `AskUserQuestion` (section 3). It is the last thing in the turn. Write nothing after it, unless it is skipped (section 3).

Never batch steps 2 and 3 together. The question's options come from the findings in the card. No preamble ("Let me look…"), no recap after the card.

**Focused question:** prose with the number, window and denominator. Add a Markdown table (≤8 rows) or a small answer card only if it makes the answer clearer. Ask a next-step question only if an obvious drill-down exists.

**Drill-down** (after "Investigate N"): 1–2 sentences, then one finding card (evidence, likely cause labelled as a hypothesis unless proven, fix or next check, verification, Noibu links), then the next-step question.

**After a write** (draft, ticket, PR, schedule): one sentence, then a result card with the IDs the tool returned and an "Open … in Noibu" link button. Never claim success without the tool's result.

**Scheduled run** (no one is watching): ask nothing, ever. Use the choices baked into the scheduled prompt; if one can't be honoured, deliver what you can and say what was skipped. Deliver the summary plus the report: the card for a Teams post, a PDF for email (body = summary + priorities as bullets). Instead of the next-step question, add the Noibu links and one copyable line per priority, e.g. *Ask Cowork: "investigate checkout priority 1 for example.com"*. Never mention "reply with", the clickable question, or chat-only buttons.

## 2. Card rules

- One card per response. Adaptive Card 1.6 only. Over 24 KB, the runner picks compact before rendering.
- The card holds the evidence; the prose holds the headline. Don't put the summary paragraph in the card, and don't repeat the card's numbers in prose.
- Report card order: Overview header (`domain · window`) → context line → ≤5 KPI tiles → one funnel or chart → ≤2 tables (5-row preview) → ≤3 priorities ranked by sessions affected → Evidence & coverage (collapsed) → link buttons → footer. Omit empty sections; never pad.
- **Buttons open Noibu, nothing else.** A card may have up to 2 link buttons (the builder draws them with `selectAction` → `Action.OpenUrl`), e.g. "Open issue in Noibu", "View sessions in Noibu", "Open draft in Noibu". Findings inside a report use an inline "Open in Noibu ↗" link instead. Every URL is an HTTPS `console.noibu.com` page from a tool result or a documented route (`console-urls.md`); no verified URL means no button.
- Never `Action.Submit`, `Action.Execute`, `ActionSet`, `Action.ToggleVisibility` or inputs (Cowork cards don't support them), and don't use `Action.ShowCard` (untested).
- Cowork actions (investigate, download, schedule, create) never appear on the card, and neither do "Reply with:" hints, a "Download & schedule" section, or "Save as private Cowork app" or any other dashboard offer. They go in the question.
- Values are monochrome. Colour only on change arrows (↑ Good, ↓ Warning, — default) and severity (Poor = Attention, Needs improvement = Warning, Good = Good), always with an arrow or a word.
- With no ranked findings, show one "No priorities" block with one sentence.

## 3. Next-step question

The question covers what happens inside Cowork; the card's link buttons cover Noibu. Don't put Noibu links in the question.

One `AskUserQuestion`:

- `header` ≤12 characters (e.g. "Next step"); `question` one short line naming the store and topic.
- 2–5 options. Labels ≤5 words, verb-first, each with a one-line description of what will happen. Most useful first; mark `(Recommended)` only when one is clearly best.
- No "Other" option: the user can type, and a typed reply is matched like a click. With more than five possibilities, name the rest in the question text.
- Offer only actions that are actually available in this session.

Standard options:

| After | Options |
| --- | --- |
| Report | Investigate #1 · Investigate #2 · Investigate #3 (descriptions = finding titles) · Download as PDF · Schedule this report |
| Report with no findings | The skill's natural drill-down (e.g. Compare by device) · Change the date range · Download as PDF · Schedule this report |
| Finding | Get the fix · Open a ticket · Draft a pull request (only with a code host connected) · Back to the report |
| Result | The next step in that flow · Done for now |

If `AskUserQuestion` is unavailable or fails, end with one line: "Reply with one: <label> · <label> · …". This is the only place "Reply with" is allowed.

**If the question is skipped, dismissed or left unanswered** (the user skips it, closes it, or replies with something that matches no option), Cowork does not show it again. Reply with one line and stop: "Say **next steps** anytime to see these options again, or type one: <label> · <label> · …". When the user later says "next steps", "options", "what now" or similar, ask the same question again for the most recent card: same report, same options. A typed label (e.g. "Investigate 2") always works, with or without the question showing.

A chosen option or typed reply applies to the report shown in that card: same workflow, domain, window and evidence. If it's unclear which report or finding is meant, ask.

## 4. Choices during a flow

Every pick-one moment (store, goal, destination, recipients) is one `AskUserQuestion` with the same rules as section 3, one decision per question. A skipped or unanswered one gets the same one-line recovery: the options as text and "say **continue** to see this question again".

**Setting up a schedule** (the only time a schedule asks anything):

- If the request names the skill, store, cadence, time and destination, ask nothing and confirm in one sentence.
- Otherwise ask one question with a preset first, e.g. "Weekly · Mon 9 am · Summary · Teams (Recommended)", plus "Customize". Only "Customize" asks, in order: frequency → day or date → time → timezone → detail → destination.
- Email always confirms the exact recipient addresses in chat, even if supplied.
- Write the scheduled prompt so it works with no memory of this chat: skill, store UUID and name, rolling window and comparison, detail, destination, confirmed recipients.
- Tell the user once that Cowork drafts scheduled sends for approval unless approved ahead of time, and ask them to approve the first run's send.
- Where it fits (e.g. technical monitoring), offer alert-only: deliver only when a metric crosses a stated threshold or a new priority appears.

## 5. Copy

- Sentence case; UPPERCASE only for card eyebrows and table headers. Titles name the metric and the move ("Checkout completion fell on mobile").
- No "successfully", "please", exclamation marks, emoji or filler. Actions are verb-first.
- Finding: title ≤60 characters, evidence one sentence ≤160 characters with the key number and the comparison, impact chip ≤32 characters.
- Never show citation tags, "Source:" sentences, tool or request IDs, raw field names, formulas, ISO timestamps (write "Oct 27, 5:44 pm (UTC)") or customer identifiers. Methodology and definitions go to Evidence & coverage, never dropped.

## 6. Data honesty

- State the window and timezone. Default comparison: the equal-length window immediately before.
- Unmeasured is "Not measured" (null), never 0. Rates change in pp, counts and money in %; undefined when the prior is 0. One currency per value.
- Keep fact, correlation and hypothesis separate. Show money-at-risk only when asked, labelled as directional.
- Reading data never authorizes a write. Every write needs the user's explicit choice plus Cowork's native approval. A declined approval means "not done".

## 7. When things fail

- **Card failed** (explicit error): one sentence saying the card couldn't be shown and why (the runner's `fallback_lead`), then the same report as Markdown in the same order (summary → KPIs → funnel → findings → caveats), keeping every number, window and denominator. Then the next-step question.
- **Delivery unknown** (no confirmation either way): don't replay or re-render. One short sentence at most, then the next-step question.
- **Noibu not connected:** one line asking the user to finish the Connect prompt and then ask again or say *continue*. Stop; no partial numbers.
- **Data missing:** check sibling domains first (checkout often lives on another domain), then say what's missing and offer another window or store.
- **A button or link didn't open** (the user says so): give the same destination as a plain URL in one sentence. Don't re-render the card.
- **The question didn't appear** (the tool errored, or the user asks what to do next): send the "Reply with one: …" line from section 3.

## 8. Never

- Dashboards or Cowork apps as an output or an offer.
- More than one card in a response.
- A card button that isn't a verified Noibu console link.
- Prose after the next-step question, except the one-line recovery when it is skipped.
- Raw HTML or card JSON pasted into chat.
- Describing a button, link or file that doesn't exist.
