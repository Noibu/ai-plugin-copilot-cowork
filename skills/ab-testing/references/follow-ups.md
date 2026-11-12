# After the tests are shown

Read this when the user picks a test from the next-step question, or types one of the requests below. Each section is one request. Work from this conversation's `candidates.json`; never re-run the finder, re-rank or re-validate to answer one of these.

Find a test by its title (exact, then ignoring case), falling back to its rank ("test 2"). If neither matches, say which tests this run has and ask which one.

## A test is picked: show its detail

Arrives as a picked option, or typed ("show test 2", "tell me more about the quick add test").

Give the test's full record, in this order, as plain text with these headings. Everything comes from the test's entry in `candidates.json`.

1. **The test's title**, as the heading.
2. **What to change:** `what`.
3. **Why this test:** `why`, then the evidence behind it as a short list, one line per `evidence[]` entry with its numbers. Label correlational evidence.
4. **Setup, as Noibu will receive it:** the six `setup` fields as a two-column table: Title, Hypothesis, Success metric, Secondary metrics, Targeting, Variations.
5. **Traffic:** `metricVolume`.
6. **Overlap** and **Fix first**, each only when present.
7. **Dev notes:** each variation's `devNotes`.
8. **Not confirmed on the store:** the test's `unconfirmed` lines, when there are any, with one sentence saying they are checked against the store's code when the test is built.
9. **Run notes:** the data line and the run's `caveats`, as a short list.

Then ask one clickable question, header "Next step":

- "Create A/B test in Noibu": "Creates a draft. It serves no traffic until it's started."
- "Not now": "Keep the idea; nothing is created."

Write nothing after the question. "Not now" ends the turn with no text.

## Create the test in Noibu

Arrives as that option, or typed ("create test 2 in Noibu"). This is the only way a draft is created outside a build.

1. Call `noibu_list_ab_tests` for the domain first. A test with that title that is RUNNING or STOPPED: stop and say so. A DRAFT: it already exists, so answer with its id and key; don't create a second one.
2. Check every metric code in the test's `createInput` against the `noibu_create_ab_test` tool's current schema enums. A code the schema does not accept is a reason to stop and say which, never to substitute.
3. Call `noibu_create_ab_test` with the test's `createInput` exactly as the file has it, plus `domainId`, `rationale` ("User asked to create the A/B test \"<title>\""), `skill` and `skillStep: "create-test"`.
4. After the tool returns the draft, reply with one sentence: "Draft <id> · flag key <key>. It serves no traffic until it's started, and its variation code has to be live first." Link "Draft <id>" to `https://console.noibu.com/<domainId>/ab-tests/<id>`, built only from the ids the tools returned. If the test has `consoleFollowUps`, add them as one line.
5. Then ask one clickable question, "Automate the implementation of “<title>”?":
   - "Automate the implementation (Recommended)": "I'll write the variation code with Noibu's snippet, then you choose what to automate: just the code, a pull request, or an end-to-end test."
   - "Not now": "Keep the draft; build it yourself or come back to it later."

If the create call fails, say what failed in one line and ask nothing. A second request to create a test that is already drafted gets the same sentence and question, with "Already in Noibu" in place of a new draft.

Shoppers placed in a variation whose code is not live see the control while being counted against it, and that data cannot be repaired. That is why the reminder is in the sentence.

## Automate the implementation

Arrives as that option, or typed ("build test 2", "automate the quick add test").

The test is picked; don't ask which again. Open `references/build.md` and start at "Before anything is created". The draft named in the request is adopted in Stage 2a.

If this conversation has no finder run for that domain (the working folder is gone, or the request names a test from somewhere else), say in one line that the tests from that run aren't available here and that looking for new opportunities will produce a fresh set, then ask the opening question from SKILL.md.

## Download a test's report

Only when the user asks ("download this", "give me test 2 as a PDF"). One PDF per test, saved in the Cowork output folder as `<domain>-test-<rank>.pdf`.

Use the figures in `candidates.json`; don't query again. The report is for a busy merchant: what the test is, why the data supports it, and the setup. It has no images of the page. In this order:

1. Title: "Recommended test: <title>", with the store, the goal and the data line under it.
2. **What to change:** `what`.
3. **Why this test:** `why`.
4. **Why this test, in numbers:** the test's `evidence[]`, one line each. Label correlational evidence.
5. **Setup:** the six `setup` fields as a table, then `metricVolume`.
6. **Overlap** and **Fix first**, each only when present.
7. **Dev notes**, then the test's `unconfirmed` lines under "Not confirmed on the store", when there are any.
8. **Outside your goal:** the run's `outsideGoal` lines, when there are any.
9. The run's `caveats`, as closing lines.

Reply with one line saying where the file is.

## Schedule

Only when the user asks ("run this every Monday", "look for new tests each month"). What is scheduled is the finder only: looking for new opportunities with the goal fixed in the prompt, ending at the report. A scheduled run never creates a draft, a branch or a pull request.

- If a scheduled prompt for this store's A/B test finder already exists, change that one; don't add a second.
- If the request already names how often and when, ask nothing more about timing.
- Otherwise ask one clickable question, header "Schedule", with these options:
  1. "Weekly on Mondays (Recommended)": 9 am · last 30 days
  2. "Every 2 weeks on Mondays": 9 am
  3. "Monthly": 9 am on the 1st
  4. "Something else": the user names the day and time
- The goal: if this conversation already ran the finder for the store, use that run's goal. Otherwise ask the goal question from `references/finder.md` once. "All goals" is a valid answer.

Set it up as a Cowork scheduled prompt named `ab-testing-<store>`, with this prompt: *Look for new A/B test opportunities for <store> for the goal <goal>. Ask nothing. Do not create any Noibu test, branch or pull request.* The Output section of SKILL.md says what a scheduled run delivers.

Confirm in one or two sentences: how often, the goal and the store. Then offer to run it once now, so a wrong store or goal shows up immediately. Run it only if the user says yes.
