# The chat cards: the findings card, the per-test report card and the implement card

Each test's report file is its full record (previews where they exist, evidence, setup, dev notes). The person reading the chat should not have a report pushed at them the moment the finder finishes, and should not need to open one to act either. Three Adaptive Cards cover that, all rendered by this skill's local runner (`references/card-quickstart.md`): **one `render_ui` per response**, the card is the message, nothing before or after it.

- **The findings card** is the first and only thing in the chat once the finder is done: an "A/B test opportunities" header (domain · window, the goal, and — only when no browser read the site — a one-line "Live site not checked" notice), then one block per test under "Test N": a "What to change" label over the test's title and one sentence on the change, a "Why this test" label over the test's `why`, and **Reply with: Preview test N · Create A/B test N**. Nothing else from a report is repeated: the full evidence, targeting, metric, volume and overlap are on the per-test card and the report file.
- **The per-test report card** appears after a "Preview test N" reply: the test's title and surface, what to change, why, before and after (whether screenshots exist and why not), up to three evidence lines with their numbers, the setup exactly as Noibu will receive it, fix first, overlap, then folded "Dev notes" (with console follow-ups), "Outside your goal" and "Run notes", the report file's name, and **Reply with: Create A/B test N**.
- **The implement card** appears only after a "Create A/B test N" reply produced (or found) a draft: "Created in Noibu · Test N" (or "Already in Noibu"), the title, "Draft <id>" as a link to the test in the Noibu console, the flag key, the reminder that the variation code must be live before it starts, and **Reply with: Automate the implementation N**. Creating and building are two steps in order, so the build is offered once the draft exists rather than as a third hint on the findings card.

## How they are built

`scripts/build_page.py page.json <domain-short>` writes, from the same `page.json`, the report files, `candidates.json` (validated), `findings-report.json` and one `test-report-<rank>.json` per test; `build_page.py page.json implement <rank> <draft id> <flag key> <created|existing>` writes `implement-report-<rank>.json` after a draft exists. These are `noibu.presentation/1` inputs with `workflow: "ab-testing"` and an `abView`; the card layout, copy budget and checks belong to the canonical builder (`scripts/build_presentation.py`). The run never hand-writes card JSON.

Render each with RunScript and the local runner (`references/card-quickstart.md`):

    args = {"skill_dir": "<this skill's loaded directory>", "report": "<run folder>/findings-report.json", "candidates": "<run folder>/candidates.json"}

The runner validates the candidates (`validate_candidates.py`), builds the card, preselects the compact variant only when the full card would exceed 24 KB, makes the single `render_ui` call and returns `status`, `response_policy` and `abReplyMap` (rank → title → createInputHash). Keep `abReplyMap` from the findings card: it binds a later "Create A/B test N" to exactly what was shown.

- `status: rendered`, `response_policy: CARD_ONLY`: stop. No text.
- `status: unknown`: delivery is uncertain, not failed: no replay, no second render; one short neutral sentence at most.
- Explicit failure (`allow_text_fallback: true`): say in one line what failed. For the findings card only, then give each test as one line ("Test N: <title> — <what>") with "Reply with: Preview test N · Create A/B test N", because without the card the person has no other way to act. Never a recap beyond that.

Do not render a card from memory after a context compaction; rebuild it from `page.json` / `candidates.json` first.

## Answering a reply

A reply arrives as the person's next message. It is their decision, made on a card they read, so act on it directly, without re-asking, re-ranking or re-validating the analysis.

**Preview test N** (or "Learn why and preview variation N", "open test N"). Find the test by rank (or title). In one response: render `test-report-<N>.json` with the runner (the response's one `render_ui`), and publish `<domain-short>-test-<N>.html` to the user's output files (`references/output-format.md`, "Delivering a report file"). Then end the turn with no text: the card is the answer. Only when the render or the publish failed, say in one line what failed. Another "Preview" reply for the same test renders the card again and does not republish an unchanged file.

**Create A/B test N** (or "create test N in Noibu"). Then, in order:
1. Find the test in this run's `candidates.json` by `title` (exact, then case-insensitive), falling back to rank; validate the file (`validate_candidates.py`) and compare the test's createInput hash with the `abReplyMap` entry the findings card returned. A mismatch means the file changed since the card was shown: rebuild and show the card again; create nothing.
2. Call `noibu_list_ab_tests` for the domain (all statuses). A test with that title RUNNING or STOPPED: stop and say so in one line, create nothing. A DRAFT: it already exists — use its id and key (`existing`), create nothing.
3. Check every metric code in `createInput` against the tool's current schema enums (`successMetric.metric`, `secondaryMetrics[].metric`, max items). A code the schema no longer accepts is a reason to stop and say which, never to substitute.
4. Call `noibu_create_ab_test` with the test's `createInput` exactly as the file has it, plus `domainId`, `rationale` ("User replied Create A/B test N on the findings card for \"<title>\""), `skill: "ab-testing"` and `skillStep: "create-test"`. This creates a DRAFT only; it never starts, updates or deletes a test. The person's reply is the authorization; any native approval prompt still applies and a denial creates nothing.
5. Take the numeric id and key from the result (when the result lacks the id, look up the exact title or key in `noibu_list_ab_tests`; never use the rank, never create a second test to get a link). On a timeout, reconcile with the roster before retrying or claiming anything.
6. `build_page.py page.json implement <rank> <id> <key> created|existing`, then render `implement-report-<rank>.json`. Output nothing after the card: it carries the id, the flag key, the reminder and the console link.

`scripts/ab_flow.py plan-create` returns the same decision (create / adopt existing draft / stop) deterministically from the file, the roster and the enums. This is the one way the finder half's chat ever creates a test: a reply is a request, and the rule that the run itself never creates one still holds.

**Automate the implementation N** (or a typed "build test N"). The "already picked" entry in SKILL.md, with the reply's test; Stage 2a adopts the named draft instead of creating a second one. The card is an offer, not a gate: a typed request later does the same. The working copy of `candidates.json` in this chat is the only source. A build request in a chat without that working folder: one line, then card 4a.

A second "Automate" reply for a test already being built gets one line pointing at the build already running. A second "Create" reply for a test already drafted shows its implement card again (`existing`).

## Without the card

If the runner reports an explicit failure for the implement card, give the draft id and flag key in one sentence with the console link (`scripts/console_links.py`), then one `AskUserQuestion` (header "Build"): "Automate the implementation of “<title>”?" — "Automate the implementation (Recommended)" ("I'll write the variation code with Noibu's snippet, then you choose what to automate: just the code, a pull request, or an end-to-end test.") · "Not now" ("Keep the draft; build it yourself or come back to it later."). The first is the same build request; "Not now" ends the turn with no text.
