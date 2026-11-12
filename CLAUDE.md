# Noibu plugin for Microsoft 365 Copilot Cowork

This repository is the app package for Noibu's Copilot Cowork plugin. The skills are instructions that Cowork's model reads at run time, so most changes here are prose changes that behave like code changes. `README.md` covers what each skill does and how to build the zip.

The skills were migrated from Noibu's Claude plugin. That migration is finished: write as if Cowork were the only host, and never mention Claude, the old boards or how something used to work inside a skill.

## What Cowork can and can't do

These were confirmed in tenant tests and decide most design questions.

- **A skill can only read its own folder.** It can name another skill (`tech-diagnosis`), never cite a path in one.
- **Cowork can't open a store's pages, run a script in them or take a screenshot.** Skills work from Noibu's data and tools. Where a page has to be looked at, the skill gives the user the link and what to check.
- **One Adaptive Card (1.6) per response, 24,000 bytes at most.** Card buttons can only open links. Anything the user picks goes through one clickable question with 2–5 options.
- **Scripts run only through RunScript**, after the file is copied to `.aether/scripts/`. Only the Python standard library and `aether_tools` are available.
- **Writes need the user.** Tickets, pull requests, drafts, status changes, schedules and sends happen only when the user asks, and Cowork then shows its own approval prompt.
- **Noibu can start an accessibility scan but can't return its results.** `accessibility-audit` ranks findings the user pastes in.

## Limits Cowork enforces silently

Nothing warns when one of these is broken. An oversized `SKILL.md` is cut off, files past the 20th are dropped in path order (so `scripts/` goes first), and the model improvises around what is missing.

| Limit | Value |
| --- | --- |
| Companion files per skill, not counting `SKILL.md` | 20 |
| `SKILL.md` | Under 20,000 characters; aim for 1,800 words or fewer |
| Size | 5 MB per file, 10 MB per skill |
| `name` in the frontmatter | Kebab-case, 1–64 characters, same as the folder name |
| `description` in the frontmatter | 1–1,024 characters |
| Paths | Relative and flat (`references/<file>.md`, `scripts/<file>`); no hidden files, no `..` |

## How a skill is laid out

`SKILL.md` is a short router, in this order:

1. Frontmatter: `name` and `description`.
2. When to use it, and when not to, naming the skill to use in its place.
3. **Guardrails.** They sit near the top so they survive if the file is ever cut off.
4. **Before you start**: one `ls` of the files a run needs, then how to resolve the store and the window.
5. **Workflow**: one line per stage, each naming the reference to open at that stage.
6. **Output.**

References are grouped by when they are read, not by topic: fewer, larger files. State each rule once, in the file that is open when the rule applies.

The **Output** section is the same text in all seven report skills (`store-pulse`, `checkout-analysis`, `product-analysis`, `segment-analysis`, `tech-diagnosis`, `accessibility-audit`, `ab-testing`). Only its last three lines differ: how to run the card, the drill-downs to offer with fewer than two priorities, and the schedule preset. Copy it from an existing skill and keep the shared text identical. `noibu-setup`, `build-business-context` and `querying-noibu-data` show no card, so they carry neither that shared Output text nor `scripts/`. `noibu-setup` has a short Output section of its own.

`querying-noibu-data` is the reference for calling Noibu's tools: field meanings, query limits and store resolution. The other skills refer to tools and fields by role and rely on it, with the live tool schema as the fallback. Put a rule about a Noibu tool there, not in each skill.

## The card builder

`scripts/card.py` is one file, byte-identical in the seven report skills. It turns a small report data file into the card, shows it, and returns the options for the next-step question.

- **Change it in all seven copies together.** Edit one, then copy it over the other six.
- **The builder writes every label, heading and format on the card.** Skills supply values only. Don't put card wording, layout or card JSON in a skill. If a skill needs something the builder can't draw, change the builder.
- **Skills supply current and prior values, never a formatted change.** The builder works out the change.
- **Unmeasured is `null`**, shown as "Not measured". Never `0`.
- `ab-testing` lists `tests` in place of `priorities`.
- `python3 skills/store-pulse/scripts/card.py --help` documents the report data shape for every skill. `--example <skill>` prints a complete report data file.

## Rules for text a skill supplies

- Nothing machine-shaped in what the user reads: no ids, field names, tool names, formulas or ISO timestamps. Dates read like "Oct 27, 5:44 pm (UTC)".
- Every number has a window and a base. State the window and timezone once.
- Links are `console.noibu.com` URLs returned by a tool. No URL, no link.
- One currency per value. Don't sum or rank across currencies.
- Keep measured fact, correlation and likely cause apart, and mark a hypothesis as one.
- Analyze what is present. An empty or null result is normal; a skill skips that slice and never reports missing data as a finding.
- Email always confirms the exact recipient addresses in chat first.

## Check a change

There is no test suite in this repository. Run these from the root after any change to a skill.

```shell
# SKILL.md sizes: every one must be under 20,000
wc -c skills/*/SKILL.md

# Companion files per skill: every count must be 20 or fewer
for d in skills/*/; do echo "$(find "$d" -type f ! -name SKILL.md ! -name .DS_Store | wc -l) $d"; done

# The seven builder copies must be identical: expect one line
md5 -q skills/*/scripts/card.py | sort -u

# The builder still builds every skill's sample report, full and compact
for s in store-pulse checkout-analysis product-analysis segment-analysis tech-diagnosis accessibility-audit ab-testing; do
  python3 skills/$s/scripts/card.py --example $s > /tmp/$s.json &&
  python3 skills/$s/scripts/card.py /tmp/$s.json --out /tmp/$s.card.json &&
  python3 skills/$s/scripts/card.py /tmp/$s.json --compact --out /tmp/$s.compact.json || echo "FAILED $s"
done

# Every skill in the manifest exists, and every skill folder is in the manifest: expect no output
diff <(grep -o 'skills/[a-z-]*' manifest.json | sort) <(ls -d skills/*/ | sed 's|/$||' | sort)

# Nothing left over from the Claude plugin: expect no output
grep -rniE "show_widget|sendPrompt|mcp__|tooltip|claude" skills --include='*.md'
```

Also check by reading: every path a skill cites exists inside that skill, and none contains `../`.

These checks show the package is well formed. They don't show that a skill works. Only a run in a Cowork tenant does, so say plainly when a change is untested there. Worth testing after a change: the card script actually ran (not just that a card appeared), skipping the next-step question shows the recovery line, and the compact card renders.

## Package and release

- The zip command is in `README.md`. Raise `version` in `manifest.json` before uploading a changed package; a tenant may not take a changed package under the same number.
- Keep the `id` in `manifest.json` as it is. It identifies the installed app.
- Adding or removing a skill means changing three places: the folder, `agentSkills` in `manifest.json`, and the table in `README.md`.
- `noibu-mcp-tools.json` is a snapshot of the tools on Noibu's server, and Cowork reads tool descriptions from it. Refresh it when the server's tools change, and check a tool is in it before a skill relies on that tool.
- `.DS_Store`, `__pycache__` and zips are ignored. Never commit them, and never commit `.companion-manifest.json`.
