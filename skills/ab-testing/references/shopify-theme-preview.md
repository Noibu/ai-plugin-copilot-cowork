# Shopify theme preview: the Noibu theme tools gate, building the preview, and housekeeping

Read this only when Stage 1 step 6a found a Shopify Online Store theme store. In the Claude design the preview theme was built through the Shopify connector and a separate Noibu preview-and-QA skill (`cowork-host-map.md`). In Cowork the Noibu connector carries Shopify theme tools that do the same job more safely: every edit goes into a copy, never the live theme, and nothing can be published from here.

| Tool | What it does |
| --- | --- |
| `noibu_list_store_themes` (`domainNumId`) | Every theme of the store, live first: id, name, role, created date, what may happen to it |
| `noibu_start_theme_change` (`domainNumId`, `title`) | Opens a change to the live theme and returns a `changeId` and every file path. Edits go to a copy. One change can be open per store |
| `noibu_search_theme_files` / `noibu_read_theme_file` | Find and read the code to change (read a file before editing; at most 200 lines per read) |
| `noibu_edit_theme_file` / `noibu_write_theme_file` | Exact-string edits / whole new files (under assets/, blocks/, config/, layout/, locales/, sections/, snippets/, templates/) |
| `noibu_preview_theme_change` (`changeId`) | Writes the change into an unpublished copy of the live theme ("Noibu preview: …") and returns its `previewUrl`; each preview replaces the change's last one; `conflicts` lists files the live theme changed meanwhile |
| `noibu_discard_theme_change` (`changeId`) | Closes the change and deletes its preview theme (unless the merchant published it) |
| `noibu_delete_preview_theme` (`domainNumId`, `themeId`) | Deletes one unpublished "Noibu preview: …" theme; refuses the live theme, themes Noibu did not build, and the preview of an open change |

Publishing is always the merchant's decision in Shopify admin; no tool here publishes, and this skill never asks anyone to publish a preview theme. A Shopify MCP, when connected and matched to this shop (`get-shop-info`), is used read-only (`graphql_query`, e.g. theme file checksums for proof of live in Stage 5); never `graphql_mutation`, never a theme or product write.

## 1. The gate (Stage 1 step 6a)

The theme preview is available — the gate is **open** — only when all hold:
- **a) The store runs on a Shopify Online Store theme.** Signals in order: `candidates.json` `storefront.shopifyOnlineStoreTheme` (the homepage DOM's `Shopify.theme` assignment) or `platform: shopify` with theme assets; Noibu's `siteType` (Shopify / Shopify Plus) plus a theme signal; business context. Shopify without a theme (Hydrogen/Oxygen or a custom front end) is headless: no theme to preview. When the signals disagree or none settles it, ask in the Stage 1 step 6e question ("Is <store> built on Shopify?" — "Shopify theme" · "Headless Shopify" · "Another platform" · "Not sure"); "Not sure", no answer or unattended → not a theme store.
- **b) The theme tools are in the tool list** (`noibu_start_theme_change`, `noibu_edit_theme_file`, `noibu_write_theme_file`, `noibu_preview_theme_change`, `noibu_list_store_themes`).
- **c) Stage 0 returned the domain's `numId`.**

Checking is reading the tool list; no call. A closed gate is not an error: Stage 3 uses the next preview method in Stage 1 step 6c. The gate also closes for the rest of the run when the first theme call refuses the store (no theme access for this domain, a plan without preview themes — Shopify Starter has only one theme): say so once in the Stage 4 summary and use the next preview method.

## 2. Building the preview (Stage 3, or Stage 2c in `theme` mode)

1. Run the room check (section 3 rule 2) first.
2. `noibu_start_theme_change` with a title naming the test ("A/B <flag key>: <short title>"). If a change is already open on the store, the error names it: when it is this run's own change, continue it with its `changeId`; when it is someone else's, don't touch it — ask the person whether to wait or use another preview method (`AskUserQuestion`), never discard it yourself.
3. Write the variation code into the change exactly as Stage 2c wrote it for the repository (the same files and edits, gated by the flag, blast-radius rules applied): `noibu_search_theme_files` → `noibu_read_theme_file` → `noibu_edit_theme_file` (exact strings) / `noibu_write_theme_file` (new snippet or asset). When a repository exists, the theme change mirrors the PR's diff file by file; in `theme` mode without a PR, the theme change is where the code lives and Stage 2e's patch file is generated from the same edits.
4. `noibu_preview_theme_change` → `previewUrl`. When `conflicts` comes back instead, the live theme changed those files since the change caught up: read them again, redo their edits, preview again (once; a second conflict goes in the summary).
5. Open the `previewUrl` in Edge for QA (`references/build/stage-3-qa.md`). The draft returns the control to everyone, so the preview shows A unforced; how B is checked is in Stage 3.

A theme tool failing on authentication mid-run is a dropped connection, not a closed gate: `references/run-modes.md`, "When the pick needs a connection".

## 3. Preview theme housekeeping

Shopify caps how many themes a store holds (by plan: `references/shared/platforms.md`), and every preview theme uses a slot.

1. **Naming.** Noibu names previews "Noibu preview: <change title>". A theme counts as this skill's preview only if its name starts with "Noibu preview:" and `noibu_list_store_themes` says it is unpublished. Never reuse, rename or delete any other theme, and never the live one.
2. **Room check, before starting a change.** `noibu_list_store_themes` and count. Two limits: the store's plan limit (hard; Shopify enforces it) and this skill's own limit of 3 Noibu previews at once (soft; exceeded only with the person's go-ahead). If either is reached, list the Noibu previews with their created dates (and the PR state / Noibu test status you know), then ask with one `AskUserQuestion` (header "Theme room"), reasons in the descriptions:
   - **Create another preview anyway** (only under the plan limit; "(Recommended)" when it is): QA runs on an exact copy of today's live theme; nothing is deleted; show the store count after (e.g. `13/20`).
   - **Free a slot first:** pick one listed preview to delete, then rule 4's question for that exact theme. Best when one belongs to a merged or closed PR; deleting one whose PR is still open removes that PR's preview, so say so.
   - **Skip the theme preview:** use the next preview method in Stage 1 step 6c. Nothing on the store changes.
   At the plan limit with nothing freed: give the list (the person deletes in Shopify admin), and meanwhile use the next preview method. Once the person approves going over the soft limit, don't ask again this run.
3. **Reuse.** An open change from an earlier run of this same test (its title names the flag key): ask with `AskUserQuestion` (header "Reuse") — **Reuse it:** keeps the preview link people may have, but it was copied from the live theme on <date> and later live changes are not in it, so QA may not match production · **Make a fresh one:** discards the old change (that exact one, named) and starts from today's live theme. Within one run, re-previewing fixes on the change this run started needs no question.
4. **Delete only with a go-ahead for that exact theme**, whether room check or end-of-run cleanup (Stage 5 step 5, or "Stop here" on a follow-up question). `AskUserQuestion` (header "Delete"):
   - **Delete it:** frees a slot (show `<used>/<cap>`); the preview isn't needed once the code is live and the test is running; deleting is permanent.
   - **Keep it:** useful to compare against the live site while the test runs, or if the test may be stopped, fixed and re-run; it stays unpublished, shoppers never see it.
   Delete with `noibu_discard_theme_change` (this run's open change) or `noibu_delete_preview_theme` (an older Noibu preview), after re-listing the themes right before the call and confirming the name, the unpublished role and the exact id the person approved (`scripts/ab_flow.py check-write … delete-preview-theme`). A refusal is reported in one line; the person can delete it in Shopify admin.
