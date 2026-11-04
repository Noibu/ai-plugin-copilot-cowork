---
name: <skill-folder-name>
description: <One sentence on what it does for the merchant.> Use when <trigger phrases people actually type, e.g. "why is checkout down", "which products don't convert">.
---

<!--
Template for a Noibu Cowork skill. Copy this folder to skills/<skill-folder-name>/, then:
  1. Fill in the <placeholders> and delete these comments.
  2. Run `python design/sync.py` to add references/ux-guidelines.md (and the shared card scripts, once sync owns them).
  3. Keep this file under ~5,000 tokens; put query detail in references/queries.md.
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

Follow `references/ux-guidelines.md`. For this skill:

- **Summary:** <what the 2–3 sentences should lead with, e.g. "the biggest step drop and its size">.
- **Card:** write `noibu.presentation/1` with `workflow: "<skill-folder-name>"` and render it with the card runner (`references/card-quickstart.md`). Use:
  - KPIs: <list, max 5>
  - Visual: <funnel | mix bars | gauge | none>
  - Tables: <list, max 2 in overview>
  - Findings: up to 3, each with one evidence sentence and a `fix` that starts with the Next check
  - Link buttons (≤2, verified console URLs only): <e.g. "View issues in Noibu" (/issues), "View sessions in Noibu" (/sessions)>
- **Next step:** the standard Report options. <Add or swap one skill-specific option if needed, e.g. "Compare by device".>
- **Drill-down ("Investigate N"):** <what extra queries to run> → finding card (buttons: <e.g. Open issue in Noibu · View sessions in Noibu>) → Finding options.
- **Scheduled runs:** preset <e.g. "Weekly · Mon 9 am · Summary · Teams">; window <e.g. last 7 days vs previous 7>; alert-only <yes, threshold: … | no> | <"Not schedulable">.

## Guardrails

- <Skill-specific data rules, e.g. "Payment mix is measured on completed orders only; don't infer gateway failure rates.">
- Reading data never authorizes a write. Writes need an explicit choice plus native approval.
