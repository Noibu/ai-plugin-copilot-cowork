# Noibu presentation and actions

Use this layer for full reports and explicit visual requests. Focused factual questions can stay brief text. Keep the user's analysis scope, measured numbers and limitations; visuals do not authorize extra scans, writes or schedules.

## Select the surface

The [runtime guide](runtime.md) for this product (Cowork or Copilot Chat) lists which surfaces and buttons exist and how each is handled. Show only the actions it lists; the board renders the matching labels for the `host` you pass. Discover actual capabilities in this session before using any of them.

## Default report compositions

- Use the screenshot-inspired Noibu report design: rounded overview panels, tabular KPI values, restrained labels/dividers, neutral connected vertical funnels, compact aligned tables, and spacious finding cards with a tag, impact, title, evidence, and Investigate ↗. All four analytics reports use checkout’s light outlined composition: background-colored content, thin borders, subtly tinted headers and unfilled KPI groups; other reports retain soft-neutral panels. The outer conversation remains transparent. Use real focusable buttons with visible focus; no external fonts, icons, or network dependencies. Colors follow the Cowork host theme (light/dark) from MCP Apps host context. This explicitly requested report composition may use five KPI tiles and report panels; do not flatten it into a generic unframed chart or substitute a prose-only report when native rendering works.
- Store Pulse: one or two summary sentences, unfilled Sessions / Engagement / Conversion / AOV / RPS groups when measured, five-stage connected purchase funnel with rates against total sessions and pp/relative deltas, optional requested blocks.
- Checkout: screenshot-style thin-bordered Overview with muted header, compact metrics and neutral connected cart → checkout → payment → completion funnel. First headline is Added to cart COUNT (positive base represents 100%); later headlines and bars are percentages of that SAME added-to-cart population, not previous-step conversion. Each prior series uses its OWN prior cart baseline; signed pp deltas are calculated from measured rates. Full AND compact expose every raw current/prior stage count under Show exact counts. Declare denominator/coverage; missing/zero bases or unknown stages stay Not measured, never clamped/invented. Keep separate completed / started-checkout completion, device/value highlights, explicitly placed observed-abandonment table, and side-by-side payment/delivery bars only for actual populated counts. Supporting data defaults to an expandable section. numbered opportunity cards retain evidence and a concrete Next check with Investigate. The host's download and schedule actions finish the report, with its snapshot-save action kept separate. Missing slices stay omitted.
- Products: outlined Overview with compact metrics and a measured neutral view → cart → purchase funnel (name a focused cohort; never call it global). Show more/Show less reveals the top product/collection tables with five rows, optional normalized session bars and full-label access; additional tables/rows remain expandable. Show up to three tagged investigation opportunities first, retaining measurement caveats and an expandable investigation/verification plan; further real cards appear under their actual count. The final footer contains the host's download/schedule actions and the separate snapshot-save option. Omit unmeasured stages rather than invent a funnel.
- Segments: outlined Overview with site-wide/mobile/desktop CVR and session denominators, a few supported highlights and visible material data notes. Show more/Show less reveals three country/best-converting-channel/most-visited-channel tables (five rows each; all rows retained), with supporting history/campaign/landing data further expandable. Up to three concise tagged opportunity cards have Investigate and expandable investigation/verification; any further real cards retain their actual count. The final footer contains the host's download/schedule actions and the separate snapshot-save option. Preserve peer/intent/traffic-mix distinctions, currency components, bounded ranks and count discrepancies; no forced funnel or invented device regression.
- Technical survey: separate merchant/performance/vendor sections. For measured p75 INP/LCP/CLS use screenshot-inspired performance cards: metric/status header (only observed status), plain-language title/evidence, large value, green/amber/red threshold bands with a measured marker and labelled cutoffs, actual traffic unit/page/device/window, Get fix ↗ and verified Noibu metric link. Populate the contract's structured performance field, not a prose-only gauge. Missing values get no marker or verdict. Retain Investigate, Ignore only for actual issues, optional PR/ticket actions, export/schedule. Focused diagnoses also use measured metric cards but show the proposed fix immediately, not only behind a button.
- Accessibility: for axe, actual completed findings and automated severity summary with incomplete/failed/unscanned coverage separate. If only a limited browser-based review is possible, label the mode prominently, show reviewed/unreviewed pages and evidence-backed manual observations separately, and keep axe scan/severity counts unknown rather than zero. Do not pretend native snapshots are axe findings. Get fix / Investigate and scoped optional PR/ticket actions remain available. Scheduling declares its mode and verifies the required browser/execution in the future runtime; no silent downgrade of axe-only work.
- A/B opportunities (`ab-testing` skill; legacy workflow id `ab-test-opportunity-finder` accepted): ranked test sections with change/hypothesis, measured evidence, traffic, control/variation setup, metric/guardrails/targeting/overlap and developer handoff. Attach the validated candidates file (`noibu.ab-candidates/3`, or legacy `/2`). Create A/B draft in Noibu selects exactly one candidate; no render-time writes or lifecycle advancement. Browser screenshots remain optional. In Cowork the A/B skill renders its own findings / per-test / implement Adaptive Cards through `abView` (see presentation-contract.md).
- Business context: present the actual reviewable context inline or in a OneDrive document; optionally add a save-approval action tied to its exact content hash. No implicit persistence.
- Shared query/Setup: no mandatory chart. A requested funnel or connection summary may use the same layer, without incidental schedules or writes.

There is no saved-dashboard action (UX guidelines: no dashboards); in Cowork, next steps come from the question after the card. Use explicit measured `changeDirection` on KPI, funnel and highlight comparisons to render numeric declines orange; retain units/arrows and business interpretation separately. Missing comparators stay unknown; captions are not changes.

## Build and render

Read [the input contract](presentation-contract.md) and assemble a `noibu.presentation/1` object from measured data only.

**In-chat board.** In Cowork the in-chat report is one Adaptive Card built by this skill's runner ([adaptive-card-board.md](adaptive-card-board.md), [card-quickstart.md](card-quickstart.md)), with the prose summary before it and the next-step question after it ([UX guidelines](ux-guidelines.md)). The `noibu_show_report` widget is not used. If the card fails, use text and tables as the last resort, keeping the same section order (overview, funnel counts, highlights, tables, findings, caveats), then the next-step question. If display fails, name the error/fallback once.

**Text fallback must match the board's numbers.** Use the same rates and denominators the board declares: checkout stages against cart-reaching sessions; Store Pulse stages against all sessions; product stages against the named viewer cohort. Show the denominator in the table heading. A step-to-step conversion may be added only as an extra column labelled "of previous stage". Keep the board's section order: summary, overview context, KPIs, funnel, highlights, overview tables, findings with Next check, caveats, then the available actions as a short list.

Keep the tool input compact; the widget receives at most 64 KiB of tool result. Prefer the contract's row caps; do not paste raw tool payloads.

**Standalone file.** When the user asks for an HTML file, or a PDF needs an HTML source, and script execution is available, run:

```text
python <querying-noibu-data>/scripts/build_presentation.py <task-output>/report.json --output <task-output>/noibu-report.html --standalone
```

Add `--candidates <task-output>/candidates.json` for A/B boards; the candidate validator runs first. Helpers use only the Python standard library. Never write runtime reports into the skill folder. A standalone file is static: its buttons reveal copyable requests and never execute anything.

The [board template](../assets/board.html) (with its embedded stylesheet) and [action controller](../assets/presentation.js) are the same assets the server widget uses. Keep all data escaped, keep fixed action kinds and evidence identity, and never add model-written JavaScript or free-form action prompts.

## Schedule picker

Where the runtime guide offers scheduling, the seven schedulable workflows (checkout, product, segment, Store Pulse, technical diagnosis, accessibility audit, A/B opportunities) share one picker with a workflow-specific heading: frequency, day or date, quick times plus custom time, IANA timezone, report detail and the host's destinations. Weekly, Every 2 weeks and Monthly apply to all seven; Store Pulse alone adds Daily. Weekly is initially selected; no output is preselected. Selections stay local until **Schedule analysis** is pressed. Labels never claim that an app is connected. Setup, business context and shared-query workflows have no schedule button. Technical reporting never implies fixes; recurring audits must verify execution in the scheduled run; A/B scheduling produces recommendations, not drafts.

## Widget behaviour

- Theme, locale, timezone and fonts come from the host context; the board does not load external fonts, scripts or images.
- Inline the board fits the host frame (Cowork: 200–720 px wide, up to 640 px high). The report header has **Expand**, which requests fullscreen; long content scrolls inside the frame rather than shrinking text.
- Buttons are disabled while a request is pending and after it is sent, so a double click sends once. Each shows *Sending…*, then *Sent — waiting for the reply* or a failure that can be retried. None of these states claims the action completed.
- Conversational actions post a structured request as the user's turn (`ui/message`). Noibu server operations (A/B draft creation, approved-context save) call app-only Noibu tools via `tools/call`; the host may ask the user to confirm them, and the widget shows only what the server returned.
- Links to `console.noibu.com` open through the host's link confirmation.
- Without a host bridge (static file, unsupported host) the board reveals a copyable request and states that nothing was saved, scheduled or created.

## Handle action requests

Full accessibility audits default to an attached PDF and concise summary INSIDE the report card from the same normalized results, plus **Auto-draft PR** / **Auto-create tickets** for visibly selected top findings. Follow [audit report](../../accessibility-audit/references/report.md) and [remediation](../../accessibility-audit/references/remediation-actions.md). A limited browser review keeps axe counts unknown. Empty or unconfirmed findings get no batch actions. The report itself creates no ticket or PR.

Technical, performance and accessibility finding cards always show **Open a Ticket**, regardless of connected ticket tools. Follow the [destination-first workflow](ticket-handoff.md): ask "Where should the ticket go?" with Linear, Jira, GitHub Issues and Notion plus free text and Skip, wait for the answer, then resolve the chosen provider. Nothing is created on the first click.

Save, download and schedule actions follow the [runtime guide](runtime.md); none of them schedules a refresh unless that is the selected action. Preserve verified Noibu links using [console link guidance](console-urls.md); links are navigation, not actions. **Open draft in Noibu** requires a confirmed creation.

Read [action handling](presentation-actions.md). An action references a real report ID, workflow, domain, window and target; verify these against conversation evidence. Widget state is not a security boundary.

For technical and fix actions, mark actual merchant/performance/accessibility findings with the matching category so Investigate routes to the shared repository/CI handoff. Do not label a UX or operations finding technical just to show a connection prompt. Vendor ownership stays a vendor handoff.
