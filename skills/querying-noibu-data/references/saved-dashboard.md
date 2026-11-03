# Private Cowork app save/build and automatic refresh — ALL skills

Every `save-dashboard` or equivalent “save/build a private app” request from ANY skill follows this guide. A saved snapshot is not continuously live data. No account, sharing/access-grant or security-setting change is authorized here. Private app deployment is not storefront code deployment or sharing.

## Private initial save

1. Recover actual workflow, store UUID/name, evidence windows/comparison, currency, checks, caveats and verified links. Ask for missing evidence; never invent numbers.
2. Verify the App skill and actual owner-only create/update capability. If unavailable name the blocker and offer OneDrive report or download as choices, never silent substitutions.
3. Find the user's existing app for this workflow/domain; preserve its immutable app ID and verify ownership/privacy. `AppLoad` identifies an existing app, not creates one. Ask if ambiguous; never duplicate an app to refresh it.
4. Explain stored Noibu data remains owner-only; sharing can expose the snapshot without viewers' own Noibu permissions. Never call `AppShare` share/unshare or add/change grants here. `AppShare` action=list may be used only for a scoped read-only access check through the loaded App skill. If the app is already shared, stop and ask rather than silently revoking access. Do not equate private app build/deploy with sharing: current `AppPublish` publish/deploy pushes/builds/deploys and does not itself grant access. Let the loaded App skill own its actual build/deploy flow; a supported same-app snapshot writer MAY use an explicitly scoped private app deployment ONLY when owner-only/unshared access is verified before AND after, no grants/public artifacts or ACL broadening occur, and native approvals are honored. If that privacy-preserving route cannot be verified, block the writer honestly; never bypass approvals or substitute public publication.
5. Build/update through a supported authorized private writer, retaining measured layout/caveats and metadata: capturedAt, window, comparison, currency, domain, workflow, passed checks and limits. Exclude credentials, customer identifiers and raw payloads. Validate sessions/events/orders, denominators, express-checkout skips and currency before writing; failed validation never overwrites a good snapshot. No fake Noibu action buttons.
6. Reread the SAME app and verify values and private access. Only a matching reread supports `saved privately, persistence verified`; otherwise `saved, verification pending` plus exact gap and actual app identity.

## Mandatory refresh-preferences chat question

For EVERY private save/build from ANY skill, ask in chat: **“How often should this app refresh (daily, weekly, every two weeks, monthly, custom, or manual/no refresh)? At what local time and IANA timezone, and should you be notified on every run, only errors, or not at all?”** Collect day/first-run date/month day when relevant. Reuse explicit confirmed preferences; always ask missing cadence/time/timezone/notification choices. This is mandatory, not a weekly-only offer. Explicit manual/decline or deferred answer does not block initial private save. Save does not authorize scheduling.

## Verify capabilities, then actually schedule when supported

Discover the scheduler, future Noibu access, an authenticated authorized unattended SAME-app DATA writer, a reread path, privacy-preserving scope and approval mode. Record actual evidence, not advertised tool names. `DataSourceRefresh` regenerates typed client/schema only; it does NOT refresh business snapshot values. `AppBuild` builds a pushed commit; it alone proves neither business-data update nor private persistence. Never infer a writer from either name.

- If writer/privacy/unattended execution/approval capability is unknown or unavailable: retain the initial private snapshot; say **auto-refresh blocked** and name the missing capability. Do not create a misleading reminder or manual-command schedule. Offer a scheduled report through scheduling-delivery.md only as a separate consented alternative.
- If capabilities ARE verified and cadence/local time/IANA timezone/notification and scoped automation intent are confirmed: inspect existing schedules including paused ones; match immutable app ID/workflow/domain, reuse/update the SAME schedule, keep paused unless asked to resume. Actually create/update the approved refresh schedule, not just offer instructions. No duplicates, permission grants or approval bypass.
- Email notification always follows scheduling-delivery.md: resolve exact addresses and confirm the final list in chat EVEN IF addresses were supplied. No schedule/send until recipient confirmation; notification approval does not authorize the app writer.

## Self-contained refresh prompt and execution

Include immutable app ID, owner/private scope, workflow, domain UUID/name, fresh rolling windows and explicit comparison rule, currency/denominator checks, data/schema version, exact cadence/local time/IANA timezone, notification rule/provider/destination (explicit confirmed email list when selected), verified same-app data-write/reread path and approval mode. No dependence on prior conversation or a manual “ask Cowork to refresh” command.

Each run: **fresh Noibu queries → validate totals/coverage/currency → update the SAME private app ID through the verified data writer → reread values/capturedAt/privacy → record lastSuccessfulRefreshAt, window, verification and per-step errors → notify by confirmed rule and actual approval gates**. Retain last good snapshot marked stale on failure. Never label old data fresh, duplicate apps or hide errors. Reread partial/ambiguous writes before retry.

Confirm separately: actual `schedule created/updated` ID/state/cadence/time/timezone/next run if returned; `automatic writes pre-authorized` OR `each run waits for approval`; and `auto-refresh not yet verified`. Only a completed fresh-data update AND matching same-app reread becomes **auto-refresh verified**. Schedule creation is not execution. No run shares, adds grants, merges, deploys storefront/source fixes or broadens access. Explicitly scoped private app snapshot update/build/deploy remains allowed ONLY through the verified owner-only route above. Sharing is outside this workflow and needs a separate explicit request and access disclosure/approval.
