# Repository providers: discovery, pull requests, CI previews and the patch hand-off

Read the parts for the provider Stage 1 step 6b selected; ignore the others. Cowork has no git CLI with the person's credentials and no access to their computer's folders, so every repository operation goes through a connected provider's tools, or ends in a patch file.

## Discover and select a provider (Stage 1 step 6b)

Follow the plugin's provider rule (`querying-noibu-data/scripts/action_policy.py` `repository_provider_plan`; explained in `tech-diagnosis/references/github-handoff.md`, the repository/CI handoff):
1. Look in the tool list for connected **GitHub** tools (`get_me`, `search_repositories`, `get_file_contents`, `list_branches`, `create_branch`, `create_or_update_file`, `push_files`, `create_pull_request`, `pull_request_read`, `list_pull_requests`, `search_pull_requests`, `add_issue_comment`, `update_pull_request`) and **Azure DevOps** tools (`core_list_projects`, `repo_repository`, `repo_file`, `repo_branch`, `repo_create_branch`, `repo_pull_request`, `repo_pull_request_write`, `repo_pull_request_thread_wr`, `search_code`, `pipelines_*`). GitLab or Bitbucket count only when a connector for them is actually in the tool list.
2. Verify each with one read (`get_me`; `core_list_projects`). Advertised is not authenticated.
3. Deduplicate several tool surfaces of the **same** account; distinct accounts stay distinct.
4. Zero eligible → recorded as missing (asked about only if a pull-request mode is picked: `run-modes.md`, "When the pick needs a connection"). One → reuse it with a read-only scope check. Several → ask which account in the 6e question.
5. Capabilities are separate: reading the repository, opening a pull request, reading pipelines. A provider that can read but not write still finds the code and builds the patch.

Classify a repository URL the person gives: `github.com` (or GitHub Enterprise) → GitHub; `dev.azure.com` / `*.visualstudio.com` → Azure DevOps; `gitlab.com` or self-hosted GitLab → GitLab; `bitbucket.org` → Bitbucket. Without a connector for that host, say in one clause that this session has no connection for it and use the patch hand-off.

## Find the repository

A URL the person gave; a "Variation code: <PR link>" line in the Noibu draft or a sibling test's hypothesis; existing A/B work; then search the provider (GitHub `search_repositories` / `search_code`; Azure DevOps `search_code`, `repo_repository`) for the store's name, domain and `NoibuFeatureFlag`. One read confirms access. Ask only when all of that fails.

## Pull-request operations (Stage 2d, Stage 3, Stage 5)

| Step | GitHub | Azure DevOps |
|---|---|---|
| Default branch, read files | `get_file_contents`, `list_branches` | `repo_repository`, `repo_file`, `repo_branch` |
| Branch | `create_branch` (`agent/ab-<slug>` from the default branch) | `repo_create_branch` |
| Write files | `push_files` (several files, one commit) or `create_or_update_file` | the provider's file-write operation when its tools offer one; otherwise the patch hand-off and say so |
| Open | `create_pull_request` (as a draft when the tool and repository support it) | `repo_pull_request_write` create with `isDraft` |
| Comment (QA verdict) | `add_issue_comment` on the PR | `repo_pull_request_thread_wr` |
| Merged? | `pull_request_read` (`merged`) | `repo_pull_request` (status `completed`) |
| CI / preview deployment | `pull_request_read` checks and comments | `pipelines_build`, `pipelines_run`, PR threads |

Never call a merge operation (`merge_pull_request`, completing an Azure DevOps PR): the person merges. Never approve your own PR. GitLab/Bitbucket operations go through their connector's own tools only when present.

A write that fails on authentication (401/403, expired token) stops without retrying: `run-modes.md`, "When the pick needs a connection".

## PR templates

Use the repository's template when it has one: `.github/pull_request_template.md`, `.azuredevops/pull_request_template.md`, `.gitlab/merge_request_templates/`, …

## CI preview config (Stage 1 step 6c)

Decide whether the repository posts a per-PR preview deployment (Vercel, Netlify, Cloudflare Pages, Oxygen, Azure Static Web Apps, Amplify, GitLab Review Apps…) from its CI config read through the provider: `.github/workflows/`, `azure-pipelines.yml`, `.gitlab-ci.yml`, `bitbucket-pipelines.yml`, `vercel.json`, `netlify.toml`, …; don't guess.

## The patch hand-off (no way to push, or `preview` mode)

Build a unified diff against the real repository files read through the provider (or against the Noibu theme change's files, `shopify-theme-preview.md`): `python -c` with `difflib.unified_diff` per file, `a/<path>` / `b/<path>` headers, written to the run folder as `ab-<slug>.patch`, then publish it to the person's output files (`references/output-format.md`, "Delivering a report file"; the same file tool). Hand over the PR body ready to paste. When the repository could not be read at all, say the patch can't be made against real paths yet; never a patch with placeholder paths.
