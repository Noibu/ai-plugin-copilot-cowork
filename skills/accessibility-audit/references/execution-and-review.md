# Audit execution setup and limited browser review

Use this before choosing the audit mode. An accessibility audit request authorizes inspection of the selected pages, not security-setting changes, hidden execution channels or a different scanner deployment.

## Choose from actual capabilities

1. Discover the browser and read its current API documentation and advertised capabilities. Distinguish navigation/screenshots/accessibility-tree inspection, read-only DOM evaluation, and approved page-script execution returning awaited results. Tool names, extension installation and a setting's label alone do not establish the last capability.
2. If actual approved page-script execution is exposed, follow [axe scanning](scan-and-findings.md). If a completed export is supplied, validate its URL/state, timestamp, engine/options and violations/incomplete arrays, then use that evidence with its original provenance; importing a file is not a fresh browser scan. A raw standard axe result can be wrapped as one COMPLETED page only when its actual URL and completed result arrays are present. Missing metadata is unknown, not invented.
3. If only read-only evaluation is exposed, **do not run axe there**. Explain the specific boundary and the user-controlled setup below. Unless the user requested axe-only output, continue with an explicitly labelled **limited browser-based accessibility review** of authorized rendered pages while automated scanning remains pending. Manual review is a supplement, not a substitute labelled as axe. If no browser inspection is available, retain the selected scope and explain that neither scan nor browser review completed.

Record the mode and actual capability evidence in the report. A blocked automated scan must keep unknown scanner counts, even when manual observations exist. Do not retry the same unsupported evaluator on every page or repeatedly refetch the traffic list to discover the same prerequisite.

## User-controlled setup for automated axe in Cowork

Cowork's browser runs in the user's local Microsoft Edge from Cowork on the web, with organizational browsing enabled and first-run host consent; follow the local [Edge readiness guide](browser-readiness.md) when disconnected. Microsoft's documentation describes navigation, reading pages and filling forms with approvals; it does not describe running page JavaScript or returning script results. Track each prerequisite as verified, user-confirmed, pending or unavailable:

1. Cowork on the web (not the desktop or mobile app) with browser access enabled by the administrator.
2. Edge connected and Edge/Cowork signed in with the same work account; the browser uses the user's own sign-ins, so do not audit authenticated areas unless asked.
3. A documented, approved page-script operation exposed in this session.

If item 3 is missing, explain that automated axe scanning is not available through Cowork's browser today, that a separate authorized scanner integration would be a product decision, and continue the limited review unless the request is axe-only. Never toggle settings, edit tenant policy, or route around the browser through shells, raw debugging connections, console typing, bookmarklets or another provider.

Resume the existing selected URL list and traffic window; do not rerun Noibu queries unless the user asks for refreshed scope. Keep manually reviewed, axe-scanned, failed and untouched page counts separate.

## Readiness and approved execution probe

Use serial operations on the selected tab; do not overlap navigation, readiness checks and script operations. Prefer a dedicated audit tab; if Browser Use has left navigation/response handling pending, use the same browser's normally loaded authorized tab or ask the user to finish opening it. Do not close a user tab or reuse a tab containing unsaved work.

1. Read the actual browser capability documentation. Never invent a capability or open a separate debugging connection.
2. Verify the intended final URL and rendered state using supported normal browser operations. If the documented API exposes a load-state wait, use it before the execution probe. A load event is not proof that lazy images, recommendations or all interaction states are ready; inspect those states separately for scan coverage. Do not accept cookies, authenticate, dismiss security warnings or alter carts merely to make the test pass.
3. Through the advertised, documented and approved execution capability only, run a minimal read-only probe. The probe expression is `({url: location.href, readyState: document.readyState})`, returned by value and awaited. Use the exact actual API rather than assuming every host exposes this signature. Inspect exception/error fields, actual URL and readiness; a resolved tool call alone is not probe success. Record operation, elapsed time and result. Allow normal native approval time; do not infer failure from a short delay or impose an arbitrary sub-second timeout.
4. Only after the probe succeeds and scanner execution is approved, load the pinned engine and run the scan. Never inject axe in the read-only Playwright evaluator. Record engine checksum/version, options, time, viewport and relevant visible/loading/preview state. Remove only the temporary engine loaded by this workflow, or reload/close its dedicated tab after exporting the result; do not remove a site-owned axe object.

## Classify failures before suggesting a fix

- **Capability absent/read-only only:** no approved execution API is exposed. Explain what is missing; check allowed setup once rather than trying hidden routes.
- **Approval pending or access explicitly denied:** wait for the native user decision or report the precise denial. Do not call it temporary, retry to evade it or change permissions.
- **Transient navigation or readiness error:** a page still loading, a redirect or an interstitial is an execution-state blocker, not proof of a missing capability. Preserve the error, finish normal navigation through supported operations, and make at most one bounded retry after an observable readiness change. If it repeats, stop that page and report it as failed with the error; do not force responses, start competing browser tasks or switch providers.
- **Disconnected/stale session or execution exception:** follow the documented recovery for that actual error; preserve completed evidence. Do not label every failure as a missing permission or fabricate a setting change.

A successful readiness/probe sequence is a supported test path, not proof that a load wait alone caused recovery. If the user requests an execution-only test, do not substitute a limited review. Report prerequisites, readiness, probe, engine load and completed scan as separate outcomes.

## Limited review using permitted browser operations

Use the browser's rendered accessibility/DOM snapshot, screenshots and supported read-only DOM inspection. The packaged [DOM observation expression](../scripts/observe-page.js) is optional: it only returns bounded facts, not an axe result, accessibility-tree name computation, severity or WCAG verdict. Load its source and pass it only to an API explicitly permitting read-only DOM inspection. If that operation is unavailable or blocked, use native snapshots/screenshots and state the narrower coverage; do not try another execution route to bypass a denial.

Inspect each selected page/state through actual rendered evidence; the top-page list alone is not a review. Record final URL, time, viewport/state, evidence source, inspected controls and unchecked areas. Safe navigation and ordinary non-destructive UI inspection are in scope; personal information, checkout submission, cart changes, sign-in and security changes need their applicable authorization. Keyboard testing is recorded only when actually performed through supported controls. Do not claim screen-reader testing from an accessibility snapshot.

Useful checks include page title/language, heading/landmark structure, visible text alternatives, observed names/labels and instructions for interactive controls, and keyboard focus/order/obstruction where tested. Interpret carefully: no `aria-label` does not prove an unnamed control; associated labels, referenced text, content and native semantics can supply its name. A title/placeholder is not automatically a sufficient label. Empty alt can be correct for decorative imagery. Missing H1, duplicate links or an unusual heading order is not by itself a confirmed WCAG failure. Screenshots alone do not prove programmatic names, keyboard behavior, exact contrast or hidden-frame/shadow-root coverage.

For each check use **issue observed**, **needs verification**, **not observed in inspected state**, or **not tested**. Confirm a manual issue only from cited evidence and explain its user impact and verification step. A screenshot-based concern without corroborating semantic/measurement evidence stays needs-verification. Assign a manual priority only when justified; leave uncertain impact unknown. Do not turn DOM observations into violations automatically or count traffic as affected users. Repeated shared-component pooling requires actual component verification.

## Output and persistence

Use [report guidance](report.md). Label “Browser-based accessibility review — axe not run” prominently. Show automated scan count zero and all automated severity counts unknown; show reviewed/unreviewed/failed pages and observed/manual-review findings separately. Never send review observations to the axe `build_report.py` as fake `violations`.

When file execution is available, [the review report helper](../scripts/build_review.py) validates `noibu.accessibility-review/1` evidence and exports an escaped HTML report plus JSON, independently of axe. Each reviewed page needs an inspection timestamp and checks; a confirmed issue needs evidence, source, target and recommendation. The helper validates the evidence contract, not whether the underlying observation is true. Without file execution, present the same distinctions inline. If some pages have actual axe findings, keep their automated report separate and report the combined scope without treating manual-only pages as scanned.

Scheduling must declare its mode and inspect the future runtime's browser/execution availability. A successful interactive scan or manually enabled setting does not prove unattended axe access. Do not silently downgrade a scheduled axe-only audit to a manual/DOM review or send old findings as fresh. Investigation/fix actions use the repository/CI handoff, discovering applicable GitHub and Azure DevOps accounts, with separate write authorization.

Official source (checked 2026-10-23): [Use Copilot Cowork with your local browser](https://learn.microsoft.com/microsoft-365/copilot/cowork/cowork-local-browser).
