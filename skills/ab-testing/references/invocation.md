# Invocation: where a run starts, the restart question, and the task list

Read this from SKILL.md once the Setup check is done, before Stage 0.

## Where to start when the skill is invoked

Once the Setup check is done, every invocation starts at Stage 0 unless this chat already has a run of it in progress. "In progress" means an earlier invocation in this same conversation got past Stage 0 and has not reached its end (the closing line of a partial mode's follow-up question, a started test, or a run the user told you to stop). A new chat, or a chat where the only earlier invocation was the one that just opened, has no run in progress: start at Stage 0, with nothing carried over from anything you may remember about this domain.

When a run is in progress and the skill is invoked again, the person means either "that went wrong, start again" or "carry on". Ask with one `AskUserQuestion` right after the Setup check and before anything else, not even the Stage 0 lookup:

- **Question (header "Restart?"):** "You've started this again for <domain>. Should I start over or continue where we left off?" When the new request names a different domain, say both: "…for <new domain>, while a run for <old domain> is in progress…".
- **"Start over (Recommended)"** — "Begin again from the domain lookup and the first question. Anything in progress is dropped." Recommend "Continue" instead only when the run is past Stage 2 (a draft, branch, PR or preview theme already exists), since starting over would leave those behind.
- **"Continue where we left off"** — "Pick up at <the last gate or step reached>." Name the step in plain words ("the goal question", "the run-mode question", "the pull request on GitHub").

**Start over** means a clean run: delete every pending or in-progress task of the earlier run (completed ones stay), forget the domain UUID, the picked test, the goal, the environment profile and the run mode, close any browser tab the earlier run opened, then run Stage 0 and ask card 4a. A finder run that already finished in this chat keeps its working folder, so its tests still appear under "Implement an existing test"; only the interrupted work is dropped. Nothing the earlier run created in Noibu, on the repository or in the theme library is deleted (de-duplication in Stage 1 step 3 and step 6d picks them up). **Continue** means resume at the last gate or step with everything kept; when the new request names a different domain, point that out in one line and still continue the old run.

No answer: do not pick for them. Send one short message asking them to reply "start over" or "continue", and wait.

This question is for a bare re-invocation only. A request in the "already picked" shape (below) is a decision, not a restart.

## The task list (the progress bar the user watches)

When `TaskCreate`/`TaskUpdate` are available, the task list is the progress bar; when they are not, skip it silently. Every task reads as a plain-language line about what is being done for *them*: never "Stage 0", "Stage 1b", "step 6", "finder", "environment profile", "candidates.json" or any other internal term, and no numbering. Mark each in progress when its work starts and done when it ends; don't narrate updates.

| When | Task (adapt the wording) |
|---|---|
| At the start | "Choose what to test on <domain>" |
| At the start | "Check your store and code setup" |
| At the start | "Choose what to automate" |
| Stage 2, always | "Draft the test in Noibu and write the variation code" (in `pr` and `full` add "Open a pull request"; in `preview` and `theme`, "Prepare the code preview") |
| Stage 3, in `full` and `theme` | "Preview the change and run QA" |
| Stage 4, always | `full`: "Hand off for your review and merge"; partial modes: "Show what was built and offer the next step" |
| Stage 5, in `full` | "Confirm the code is live and start the test" |

The finder's own tasks are "Analyze 30 days of Noibu data", "Check the live store" and "Prepare your ranked test ideas". A task whose work is skipped is deleted, not left pending.
