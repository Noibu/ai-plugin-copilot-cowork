---
name: <skill-folder-name>
description: <One sentence on what it does for the merchant.> Use when <trigger phrases people actually type, e.g. "why is checkout down", "which products don't convert">.
---

<!--
Template for a Noibu Cowork skill. Copy this folder to skills/<skill-folder-name>/, then:
  1. Fill in the <placeholders> and delete these comments.
  2. Run `python3 design/sync.py` to add references/ux-guidelines.md, and copy the card scripts from an existing report skill.
  3. Mark any later edit to this skill's copy of the card builder with `# SKILL-SPECIFIC (<skill>): <why>` (design/README.md section 4).
  4. Keep this file under ~5,000 tokens; put query detail in references/queries.md.
The Output section below is standard. Change only the <placeholders> in it.
-->

# <Skill title>

<One or two sentences: what question this skill answers and for whom.>

## When to use

- <Typical request 1>
- <Typical request 2>

## When not to use

- <Request that belongs to another skill> → `<other-skill>`
- Single factual lookups with no analysis → `querying-noibu-data`

## Before you start

- Read `references/ux-guidelines.md` for everything the user sees: response shape, card rules, next-step question, copy and failure handling.
- Read `../querying-noibu-data/SKILL.md` for store resolution, query rules and tool metadata (`skill: "<skill-folder-name>"`). If the link doesn't open, load `querying-noibu-data` by name.
- Default window: <last 30 days vs the preceding 30 days | rolling 24 hours vs the preceding 24 hours>. Honour requested dates.

## Workflow

1. **Resolve the store** and load its business context (`querying-noibu-data`).
2. **Query.** Run every independent query in one parallel batch, current and prior windows together. See `references/queries.md`.
3. **Analyse.** <The skill's own logic: thresholds, ranking rule, what counts as a finding.> Rank findings by sessions affected; keep at most 3.
4. **Report** (see Output).

## Output

Follow the [UX guidelines](references/ux-guidelines.md) for everything the user sees: a 2–3 sentence summary, then one card, then the next-step question offering the card's priorities. The card carries Noibu link buttons only. Download, save and schedule run only when the user asks and are never offered or mentioned. No dashboards. In a scheduled run, ask nothing.

- Build the card with this skill's [local display guide](references/card-quickstart.md): write the `noibu.presentation/1` report, then run the [runner](scripts/show_card.py), which uses the [builder](scripts/build_presentation.py), [console helper](scripts/console_links.py), [checker](scripts/cowork_card_check.py) and [comparison adapter](scripts/comparison_acquisition.py) in this folder. Never hand-write card JSON; at most one render_ui call per response. Build the next-step question from the runner's `priorityOptions`.
- Load querying-noibu-data by name for query and action guidance. Current/prior comparisons follow the [local contract](references/comparison-acquisition.md).
- Scheduled email always confirms the exact recipient addresses in chat, even if supplied ([connected delivery](../querying-noibu-data/references/scheduling-delivery.md)).
- **Summary leads with:** <e.g. "the biggest step drop and its size">.
- **Card:** KPIs <list, max 5> · visual <funnel | mix bars | gauge | none> · tables <list, max 2> · up to 3 findings, each with a `shortTitle` (≤5 words), a ≤60-character title, one evidence sentence and a `fix` that starts with the Next check · link buttons <e.g. "View issues in Noibu" (/issues), "View sessions in Noibu" (/sessions)>.
- **Drill-down options** (one priority: added as the second option; no priorities: both): <e.g. "Break down by device"> · <e.g. "Change the date range">.
- **After a priority is picked:** <what extra queries to run> → finding card (buttons: <e.g. Open issue in Noibu · View sessions in Noibu>) → Get the fix · Open a ticket · Draft a pull request · Back to the report.
- **Scheduled runs (only when asked):** preset <e.g. label "Weekly on Mondays", description "9 am · Summary · Teams">; window <e.g. last 7 days vs previous 7>; alert-only <yes, threshold: … | no> | <"Not schedulable">.

## Guardrails

- <Skill-specific data rules, e.g. "Payment mix is measured on completed orders only; don't infer gateway failure rates.">
- Reading data never authorizes a write. Writes need an explicit choice plus native approval.
