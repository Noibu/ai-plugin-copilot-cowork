# Steps 5–6: the code host and release reporting

Read this at step 5 and keep it open through step 6.

What Cowork can reach:

| Host | Connection in Cowork | Release reporting |
|---|---|---|
| GitHub | Reads the repository and opens pull requests | Pull request |
| Azure DevOps | Reads only; it can't push a file | Hand-off |
| Bitbucket | None | Hand-off |
| GitLab, self-hosted, anything else | None | To-do only |

## Step 5 · Code host

1. **What is connected?** Check this session for GitHub tools and Azure DevOps tools. For each one present, run its proving read: on GitHub, the signed-in account; on Azure DevOps, the list of projects. A host counts as connected only when that read succeeds.
2. **Where does the code live?**
   - Exactly one host is connected and proven: name it in one line ("GitHub is connected as <login>.") and go on with it; the user can correct it.
   - Otherwise look in the business context saved in Noibu for a repository address. If it names a host, confirm it in one line.
   - Otherwise ask one clickable question, header "Code": "Where does your store's code live?" Options "GitHub", "Azure DevOps", "Bitbucket", "GitLab or somewhere else", "I'm not sure". Typed replies: "ADO", "azure" → Azure DevOps; "self-hosted", "our agency has it", "no repo", "we edit it in Shopify" → somewhere else; "don't know", "ask my developer" → not sure.
3. **By host:**
   - **GitHub or Azure DevOps, connected:** go to item 4.
   - **GitHub or Azure DevOps, not connected:** say which plugin connects it and where ("Connect the GitHub plugin in Cowork (Customize → Plugins → GitHub)."), then ask one clickable question with the host as the header: "Let me know when it shows Connected." Options "It's connected" and "Skip for now". Connected and its tools are here: run the proving read and go to item 4. Connected but its tools still aren't here, or skipped: record "Connect <host> to Cowork" as a to-do for the user. Step 6 still runs, as a hand-off.
   - **Bitbucket:** "Cowork has no Bitbucket connection, so I'll prepare the release step for your developer to add." Step 6 runs as a hand-off.
   - **A Shopify store whose theme is edited in Shopify, with no repository:** "Your theme is edited directly in Shopify, so code changes go through the theme path from step 3." Record "Release reporting: no pipeline to report from yet" as a to-do for their developer, skip step 6, and go to step 7.
   - **GitLab or anything else:** say in one line that Cowork can't connect that host. Record "Set up Noibu release reporting on <what they said>" as a to-do for their developer or agency, skip step 6, and go to step 7.
   - **Not sure:** record "Find out where the store's code lives, then say *continue my Noibu setup*" as a to-do for the user, skip step 6, and go to step 7.
4. **Pick the repository.** If the business context names it, confirm it in one line. Otherwise list the repositories the connection can see and ask one clickable question, header "Repository": "Which repository holds the storefront code for <store>?", with up to four likely ones; the user can type another as `owner/name`. With no connection (a hand-off), ask for the repository's name in one line; "not sure" is fine, and the file is prepared without it. Record the repository and, when it can be read, its default branch.

## Step 6 · Release reporting

Release events tell Noibu when code shipped, so errors and conversion changes can be lined up against deploys. A small pipeline step posts one event to Noibu on every push to the release branch.

### 1. Already set up?

Read the store's releases from Noibu. Where the repository is readable, also look for a pipeline file that mentions `webhook.noibu.com` (`.github/workflows/` on GitHub; pipeline YAML files on Azure DevOps).

- Releases are arriving: "Noibu is already receiving releases from <component> (latest <date>)." Go to step 7.
- A Noibu pipeline file exists but no release has arrived: say so, don't add a second one, record "Check why the Noibu release step isn't reporting" as a to-do for their developer, and go to step 7.

### 2. Confirm the details

Work out defaults without asking: the repository from step 5; the branch is its default branch (`main` if it can't be read); the component is `frontend`, or what the business context or the repository's name suggests (for example `checkout`). Then one clickable question, header "Releases":

- GitHub, connected: "I'll open a pull request in <repository> that reports every push to <branch> to Noibu as a <component> release. Each push counts as a successful release, not a verified deploy."
- A hand-off: "I'll prepare a pipeline file that reports every push to <branch> to Noibu as a <component> release, for your developer to add. Each push counts as a successful release, not a verified deploy."

Options "Sounds good", "Change something" and "Skip for now". On "Change something", ask only for what they want changed (branch or component), in one message, then go on. On "Skip for now", record "Set up Noibu release reporting" as a to-do for the user and go to step 7.

### 3. Fill the template

Take the host's template from the end of this file and replace exactly three things: the branch, the component, and `<DOMAIN_UUID>` with the store's UUID (never its `numId`). Change nothing else: not the indentation, not the quoting, not the order. The templates pass the commit message through a variable so that nothing in a commit message can run as a command; rewriting them can undo that.

### 4. GitHub: open the pull request

1. Create a branch named `noibu/release-events` from the default branch.
2. Add the filled template as `.github/workflows/noibu-release.yml`, with the commit message "Add Noibu release event webhook".
3. Read the file back from the branch and confirm it matches the filled template exactly. If it doesn't, fix it on the same branch before going on.
4. Open a pull request against the default branch, titled "Add Noibu release event webhook", with one line saying every push to <branch> will be reported to Noibu as a <component> release. Leave it unmerged.
5. Close the step with the pull request's link and: "Once it's merged, say *check my releases* and I'll confirm the first one reached Noibu." Record the link.

If GitHub refuses the file (workflow files need a permission some connections don't have) or the account can't write to the repository, don't retry and don't try another route into the repository. Say in one line what was refused, delete nothing, and go to the hand-off.

### 5. Hand-off: every other case

Show the filled file in one code block, with one line above it giving the file's name and where it goes, and the developer's actions after it:

- **GitHub** (the pull request was refused, or GitHub isn't connected): the file is `.github/workflows/noibu-release.yml`. "Add it through a pull request; the first push to <branch> after it merges reports a release."
- **Azure DevOps:** the file is `noibu-release.yml` at the repository's root. "Add it through a pull request. Then register it once: Pipelines → New pipeline → Azure Repos Git → <repository> → Existing Azure Pipelines YAML file → `/noibu-release.yml` → Save."
- **Bitbucket:** a repository has only one `bitbucket-pipelines.yml`. "If the repository has none, add this file at its root. If it has one, add the step to the pipeline for <branch>, after the existing steps. If the file only has a `default` pipeline, copy its steps into the new branch pipeline first, because a branch pipeline replaces `default` on that branch. Pipelines also has to be enabled for the repository."

Record "Add the Noibu release step to <repository>" as a to-do for their developer. Draft an email or a ticket to the developer only if the user asks; an email confirms the exact recipient addresses in chat first.

### 6. Checking a release arrived

On "check my releases", and again in step 8: read the store's releases from Noibu. An entry with the confirmed component means it works: say so in one line with its title and date. Never say releases are being reported unless that list shows one.

## Templates

### GitHub Actions

```yaml
name: Noibu release event

on:
  push:
    branches: [main]

jobs:
  report-release:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - name: Report release to Noibu
        env:
          NOIBU_URL: https://webhook.noibu.com/release_webhook/<DOMAIN_UUID>
          COMPONENT: frontend
          REPO_NAME: ${{ github.event.repository.name }}
          RUN_NUMBER: ${{ github.run_number }}
          COMMIT_MESSAGE: ${{ github.event.head_commit.message }}
          COMMIT_AUTHOR: ${{ github.event.head_commit.author.name }}
          ACTOR: ${{ github.actor }}
          COMMIT_SHA: ${{ github.sha }}
        run: |
          author="${COMMIT_AUTHOR:-$ACTOR}"
          payload=$(jq -n \
            --arg component "$COMPONENT" \
            --arg title "$REPO_NAME release $RUN_NUMBER" \
            --arg description "$COMMIT_MESSAGE — by $author" \
            --arg version "$COMMIT_SHA" \
            --arg release_time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
            '{component: $component, title: $title, description: $description, status: "success", version: $version, release_time: $release_time}')
          curl --fail --silent --show-error --max-time 30 \
            -H "Content-Type: application/json" \
            -d "$payload" \
            "$NOIBU_URL"
```

### Azure Pipelines

```yaml
trigger:
  branches:
    include:
      - main

pr: none

pool:
  vmImage: ubuntu-latest

steps:
  - bash: |
      payload=$(jq -n \
        --arg component "$COMPONENT" \
        --arg title "$BUILD_REPOSITORY_NAME release $BUILD_BUILDNUMBER" \
        --arg description "$BUILD_SOURCEVERSIONMESSAGE" \
        --arg version "$BUILD_SOURCEVERSION" \
        --arg release_time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        '{component: $component, title: $title, description: $description, status: "success", version: $version, release_time: $release_time}')
      curl --fail --silent --show-error --max-time 30 \
        -H "Content-Type: application/json" \
        -d "$payload" \
        "$NOIBU_URL"
    displayName: Report release to Noibu
    timeoutInMinutes: 5
    env:
      NOIBU_URL: https://webhook.noibu.com/release_webhook/<DOMAIN_UUID>
      COMPONENT: frontend
```

### Bitbucket Pipelines

```yaml
pipelines:
  branches:
    main:
      - step:
          name: Report release to Noibu
          image: alpine:3.20
          max-time: 5
          script:
            - apk add --no-cache curl git jq
            - export NOIBU_URL="https://webhook.noibu.com/release_webhook/<DOMAIN_UUID>"
            - export COMPONENT="frontend"
            - |
              description="$(git log -1 --pretty=%B)"
              payload=$(jq -n \
                --arg component "$COMPONENT" \
                --arg title "$BITBUCKET_REPO_FULL_NAME release $BITBUCKET_BUILD_NUMBER" \
                --arg description "$description" \
                --arg version "$BITBUCKET_COMMIT" \
                --arg release_time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
                '{component: $component, title: $title, description: $description, status: "success", version: $version, release_time: $release_time}')
              curl --fail --silent --show-error --max-time 30 \
                -H "Content-Type: application/json" \
                -d "$payload" \
                "$NOIBU_URL"
```
