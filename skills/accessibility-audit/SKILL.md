---
name: accessibility-audit
description: Audit website accessibility with approved browser axe-core execution or completed axe exports; when execution is unavailable, guide setup and provide a clearly labelled limited browser review, prioritized with Noibu traffic where available.
---

# Accessibility audit

- Read [shared query guidance](../querying-noibu-data/SKILL.md), [runtime/actions](../querying-noibu-data/references/runtime.md) and [execution setup](references/execution-and-review.md). Use skill `accessibility-audit`.
- Discover browser capabilities before unnecessary traffic queries. Completed axe exports need provenance, not a new browser connection.

## Prerequisites and execution

Follow [execution setup](references/execution-and-review.md) for this product: it says which browser exists, what must be enabled, and whether page-script execution is available. An automated axe scan needs an exposed, documented operation that runs page JavaScript and returns an awaited result, approved for this website. Check prerequisites and ask only for what is missing. Never change tenant or browser security settings; terminal or script-runtime permissions do not grant browser scripting.

- Read the current browser capability and [scan/findings procedure](references/scan-and-findings.md).
- If page-script execution is exposed: confirm readiness, run the minimal approved probe, and only after it succeeds load the bundled checksum-pinned axe and run the bundled scan expression.
- If it is not exposed (the expected case today), say so plainly, keep axe counts unknown and, unless the user asked for axe only, continue the clearly labelled **Browser-based accessibility review — axe not run**.
- Distinguish transient navigation/readiness errors from a missing capability; follow the bounded retry procedure rather than calling a capability unavailable after one transient error, and never call a missing capability a temporary error.
- Results come only from the page. Do not bypass a denial through shell, console, bookmarklets, another automation channel or a remote job.
- Completed exports keep their original URL/time/state/engine/options and are not fresh scans. A separately requested remote job is outside this flow; QUEUED is not findings.

## Scope and resume

- A named-page request covers that page. Full-site audits select up to ten pages by 30-day Noibu pageviews using `noibu_get_page_visits`; explain scope. Traffic ranks priority but is optional for an explicitly supplied URL.
- Reuse selected URLs/window and validate completed evidence on resume; preserve immutable original time/state/options and scan remaining pages only. One completed homepage in ten pages means nine pending, not ten new scans.
- Without approved execution, guide permitted setup and rediscover capabilities. If the host has a browser and the request isn't axe-only, perform the distinct **Browser-based accessibility review — axe not run**; if execution-and-review.md says the host has no browser, return its traffic-ranked scan plan instead using supported snapshots/screenshots/read-only observations. Report reviewed/unreviewed pages, manual observations, verification items and unchecked states.
- Limited review uses [the review exporter](scripts/build_review.py): zero completed axe scans, unknown automated severities, no invented axe violations. If inspection is unavailable or axe-only, return the precise prerequisite and selected scope.

## Findings and deliverables

- Pool confirmed shared-component findings by rule/criterion plus stable selector. Keep per-page nodes and count affected pageviews once per unique page.
- Rank severity weight × log10(max(1, affected pageviews)) × min(2, 1 + 0.2 × affected page count). Missing traffic stays unknown; incomplete checks are verification items, not violations.
- Report distinct violated rules, affected page/target elements, raw rule/node instances, pooled fixes and incomplete checks separately, with completed/failed/unscanned pages and rendered states.
- Follow [report format](references/report.md): verified PDF attachment, concise summary INSIDE the report card from the same normalized evidence, severity/fix table and top finding. Preserve its legal text/disclaimer exactly; automated checks do not certify compliance.
- Keep iframe/shadow-root/hidden-state/manual limits visible; unreviewed pages are not clean. Limited/blocked reports retain unknown axe counts, including in PDFs.
- Use [inline presentation](../querying-noibu-data/references/presentation.md) for **Auto-draft PR** / **Auto-create tickets**, visibly scoped to actual top finding IDs. [Remediation actions](references/remediation-actions.md) resolve connections/destinations after selection; rendering creates nothing.
- Investigate/Get fix/source remediation uses [repository/CI handoff](../tech-diagnosis/references/github-handoff.md). Preserve completed audit evidence while connection/ref/ownership verification is pending; vendor/managed components need owner handoff. Scanning/reporting does not require any repository connection.

## Recurrence

- Follow [connected delivery](../querying-noibu-data/references/scheduling-delivery.md). Confirm audit mode, standard, rendered states and fixed-URL versus traffic-ranked selection rule.
- Verify approved browser readiness/execution in the scheduled runtime before promising fresh axe scans; interactive success does not prove unattended access.
- Missing execution requires a concrete blocker and consent before an alternative. Never replay exports as fresh or silently downgrade axe-only scope.
- Report scheduling does not authorize remediation, PRs, tickets, remote jobs or setup-time delivery.

## In-chat report completion

Successful in-chat reports are CARD ONLY. Put every unique conclusion, priority, window, comparison scope, limitation and next-action hint inside the card before display; stop after the card, with no summary/recap prose before or after it. This does not suppress errors, unavailable-renderer fallbacks, prerequisite questions or separate user-requested action confirmations. Never claim a failed display succeeded. Follow shared card-quickstart.md; at most one render_ui call per response.

Scheduled Email always requires chat confirmation of the exact final recipient email list EVEN IF addresses were supplied; no schedule/send before that gate. Never infer the signed-in user from Email selected. See shared scheduling-delivery.md. Any private app save/build must ask refresh cadence, local time/IANA timezone and notification (manual/decline allowed), verify a same-app unattended DATA writer, and only then create/update a confirmed refresh schedule; no reminder substitute or unverified refresh-success claim.

## Browser prerequisite, only for a requested browser step

Use the local [Edge connection/readiness guide](references/browser-readiness.md). Never prompt for browser setup during ordinary analytics/report display or repeat it when the browser is usable; explain the blocked step and continue nonbrowser work.

## Local report completion contract (21.1.13)

Use this skill’s [local display guide](references/card-quickstart.md), [runner](scripts/show_card.py), [builder](scripts/build_presentation.py), [console helper](scripts/console_links.py), [exact checker](scripts/cowork_card_check.py) and [comparison adapter](scripts/comparison_acquisition.py). This own-skill display route has no sibling filesystem dependency. Load querying-noibu-data by name for query/action guidance at its actual returned location; do not assume that loading markdown materializes its scripts. Comparison acquisition and actual current/prior metric rows follow the [local contract](references/comparison-acquisition.md). A host render acknowledgement is terminal CARD ONLY with no client-visibility gate; unknown delivery never means failed or permits whole-report replay.
