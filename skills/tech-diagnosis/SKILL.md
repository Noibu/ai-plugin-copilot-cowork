---
name: tech-diagnosis
description: Diagnose Noibu errors and Core Web Vital performance issues, explain likely causes, and recommend or draft a requested fix.
---

# Technical diagnosis

- For Noibu data work, first invoke skill `querying-noibu-data` and use its actual loaded directory for [shared query guidance](../querying-noibu-data/SKILL.md); reading a sibling link alone does not load its executable assets. If the shared skill cannot load, report that query-guidance blocker rather than inventing a filesystem path or fetching without its rules. Open its [runtime/actions](../querying-noibu-data/references/runtime.md) only for a connection problem or a save, export, schedule, ticket or browser action. Use skill `tech-diagnosis`; resolve store/platform and saved context. An already measured technical report can still use the self-contained local display path below; it needs no shared sibling files.
- Specific issue/error/page/metric requests are focused diagnoses; general “what is broken” requests are surveys. Default performance is current 30 days versus the immediately preceding equal 30 days, acquired together before presentation; label the active-error survey's separate seven-day window.

## Survey

- Read the matching `references/platform-<name>.md` file (shopify, bigcommerce, magento, woocommerce), or `references/platform-generic.md`. Search active errors by occurrences, up to three pages of 30, and in the same parallel batch fetch the p75 vitals below; stop paging when sufficient distinct candidates exist.
- Active fix candidates need last occurrence within 48 hours, >10 seven-day occurrences, usable stack and merchant-owned frames. Deduplicate primary file/signature; distinguish infrastructure/telemetry/vendors.
- Rank by occurrences × page criticality: checkout 5, cart 4, product 3, collection 2, home 1, other 0.5. Vendor code receives an owner handoff. Low-volume vendor signals (for example 8 events/4 sessions) are monitoring coverage, not padded priorities unless a material justified critical impact is evidenced. Set disposition: monitor and retain counts/window/uncertainty/next check; structured errorRecency is seven-day events plus actual lastSeenHours. Merchant active-fix threshold stays >10 events in seven days and last seen within 48 hours.
- Fetch p75 LCP/INP/CLS by page/group/device using [performance guidance](references/performance.md); rank by traffic/severity without mixing unlike score scales.
- Present separate merchant/performance/vendor sections, at most two findings each, with windows, occurrences/traffic, last seen and next actions.

## Focused diagnosis

- Read [error guidance](references/errors.md) or [performance guidance](references/performance.md); fetch matching details, diagnosis, trends and segment evidence.
- Separate observations, Noibu AI explanations and causal hypotheses. Exact source lines/element claims need inspection.
- Return impact, evidence, likely cause/uncertainty, proposed fix and verification together; do not hide essential guidance behind a button.
- Initial Noibu diagnosis does not require a browser or repository connection. For Investigate/Get fix or natural-language source diagnosis/fix/PR requests, follow [repository/CI handoff](references/github-handoff.md): verify/reuse connection, otherwise prompt to connect; resolve repository/ref and inspect merchant source. Keep useful unverified guidance while access is pending.

## Presentation and actions

- Use the **local** [report display](references/card-quickstart.md) and linked [display runner](scripts/show_card.py), [canonical builder](scripts/build_presentation.py) and [console helper](scripts/console_links.py). Resolve `skill_dir` to the actual loaded **tech-diagnosis** directory containing this SKILL.md, not the shared skill, the copied wrapper or the package root. This local Adaptive Card path remains complete when skills are materialized independently; no sibling filesystem assumption or wide path search. Performance findings need structured p75 cards: value/units, threshold bands/marker, page/device/traffic/window and observed status only. Missing values remain unknown.
- Include [verified Noibu links](../querying-noibu-data/references/console-urls.md); metric overview URLs do not imply preserved filters.
- Offer Investigate / Get the fix and **Open a ticket** in the next-step question, even before an integration is connected. Ticket clicks use the [destination-first chooser](../querying-noibu-data/references/ticket-handoff.md); wait for selection before provider discovery/creation. Ignore requires an actual issue and supported status tool.
- Investigate/Get fix permit read-only source inspection and a proposal, not edits/PRs. Repository writes, draft PRs, tickets, status changes and vendor messages require their requested scope and approvals; never merge/deploy. Missing integrations yield an explicitly unsaved draft/specification.
- Data does not prove every session was blocked. Revenue-loss projections are only for requested money impact; redact sensitive HTTP fields.
- Requested schedules use [connected delivery](../querying-noibu-data/references/scheduling-delivery.md), retaining focused/survey scope and fresh error/performance windows. Reporting does not require a repository connection or authorize automatic remediation/status writes.

## Output

Follow the [UX guidelines](references/ux-guidelines.md) for everything the user sees: a 2–3 sentence summary, then one card, then the next-step question. The card carries Noibu link buttons only; investigate, download and schedule are offered by the question. No dashboards. In a scheduled run, ask nothing.

- Build the card with this skill's [local display guide](references/card-quickstart.md): write the `noibu.presentation/1` report, then run the [runner](scripts/show_card.py), which uses the [builder](scripts/build_presentation.py), [console helper](scripts/console_links.py), [checker](scripts/cowork_card_check.py) and [comparison adapter](scripts/comparison_acquisition.py) in this folder. Never hand-write card JSON; at most one render_ui call per response.
- Load querying-noibu-data by name for query and action guidance. Current/prior comparisons follow the [local contract](references/comparison-acquisition.md).
- Scheduled email always confirms the exact recipient addresses in chat, even if supplied ([connected delivery](../querying-noibu-data/references/scheduling-delivery.md)).
- A dependency failure keeps the exact missing filename/path and supplied root; don't infer an absent ZIP member or tenant filesystem cause.
- Scheduled runs: preset "Weekly · Mon 9 am · Summary" with alert-only offered (deliver only when a new merchant error passes the active-fix threshold or a vital crosses into Poor).

## Browser prerequisite, only for a requested browser step

Use the local [Edge connection/readiness guide](references/browser-readiness.md). Never prompt for browser setup during ordinary analytics/report display or repeat it when the browser is usable; explain the blocked step and continue nonbrowser work.
