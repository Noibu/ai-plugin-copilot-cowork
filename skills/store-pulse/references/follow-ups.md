# After a snapshot

Read this when the user picks a thread or the schedule option from the next-step question, or types a request to schedule or download. Each section is one request.

## A thread is picked

Arrives as a picked option, or typed ("why did conversion fall?").

Treat it as a fresh question. Don't answer from the snapshot alone: the snapshot shows that something moved, not why. Let the right skill take it, and frame it in the user's terms:

- A checkout or funnel-completion move: `checkout-analysis`.
- A product or collection move: `product-analysis`.
- A channel, device or country move: `segment-analysis`.
- An error or a slow page: `tech-diagnosis`.

If none fits, answer it with the Noibu tools directly, with the number, its window and its base.

## Schedule

When the user picks the schedule option in the next-step question, or asks ("schedule this", "send me this every morning").

**One schedule per store.** The scheduled prompt is named `store-pulse-<domain with dots as dashes>`, e.g. `store-pulse-example-com`. Before creating one, look for a scheduled prompt with exactly that name. If it exists, this is an edit: change that one. Match on the exact name, never on the domain alone, and never touch another store's schedule.

**How often.** If the request already names it, ask nothing more about timing. Otherwise ask one clickable question, header "Schedule", with these options:

1. "Weekly on Mondays (Recommended)": 9 am · the preceding 7 days
2. "Daily": 9 am · yesterday
3. "Every 2 weeks on Mondays": 9 am · the preceding 14 days
4. "Monthly": 9 am on the 1st · the previous calendar month

The send time is 9 am unless the user names another.

**The window follows the frequency.** All windows are computed in the user's timezone.

| Frequency | Window | Runs |
|---|---|---|
| Daily | yesterday, midnight to midnight | every day at the chosen time |
| Weekly | the preceding 7 days, ending at midnight on the chosen weekday | the chosen weekday at the chosen time |
| Every 2 weeks | the preceding 14 days, ending at midnight on the chosen weekday | the chosen weekday at the chosen time, every other week |
| Monthly | the previous calendar month, from the 1st to the 1st | the 1st of the month at the chosen time |

If the scheduler has no every-other-week option, schedule it weekly and have the prompt stop without sending on the off weeks, by comparing the week number's parity with the week it was set up.

**Where to send it.** Once the timing is settled and before creating the schedule, ask one clickable question, header "Send to": "Where should each report be sent?" Skip it if the request already names where.

1. "Email": through Outlook
2. "Teams": a channel or chat
3. "Notion": a page
4. "Only in Cowork": nowhere else

More than one of the first three may be chosen. Every run shows its report in Cowork, whatever is picked. The details for each destination are under "Sending it elsewhere".

**The scheduled prompt** runs with no conversation behind it, so it carries everything: *Run Store Pulse for <store> over <window rule> in <timezone>, compared to the period of the same length before.* Add the blocks to include if the user named any (top products, channel performance, paid ad performance), and one send line per destination: *Then send the <summary or full report> to <destination>.* Apart from a send line, write nothing into the prompt about what the run delivers: the Output section of SKILL.md decides that when it runs.

Confirm in one sentence once the schedule exists, saying when it will run and where each report is sent. If a destination was set up, add that the first run's send needs approving once, after which later runs deliver without asking.

### Sending it elsewhere

For each destination picked:

- **Check its connector first**: Outlook for email, Teams, or Notion. If it isn't installed or connected, recommend it in one plain line ("To get this by email, install the Outlook connector in Cowork, then ask me to add email to this schedule"), leave that destination out, and carry on. The schedule is still created.
- If at least one destination is left, ask which detail level the user wants: **Summary** (the summary and the headline numbers) or **Full report** (adds the funnel and any blocks included).

**Email is a draft, never sent.** It goes through Outlook only: the run creates a draft in the user's Outlook, and the user reviews and sends it. Confirm the exact recipient addresses in chat before creating the schedule, even if the user already gave them.

- Subject: "Store Pulse: <period>".
- Body, in order: the summary paragraph; the headline table (Sessions, Engagement, Conversion, AOV, RPS, each with its current value and its change against the previous period).
- Full report only, one table per included block:
  - Purchase funnel: step, share of sessions, sessions, previous share, previous sessions, change.
  - Top products: product, sessions, add-to-cart rate, with the site-wide add-to-cart rate for the period stated above it.
  - Channel performance: channel, sessions, engagement, conversion, RPS.
  - Paid ad performance: platform, sessions, conversions, revenue. Always the three platforms; `0` where a platform has no tagged traffic.
- A closing line: "Generated <date and time> from Store Pulse for <store>."
- Tables only. No charts, no images, no attachments.

**Teams** posts to the channel or chat the user names; ask which if they didn't.

- Summary: one message with the title "Store Pulse: <period>", the summary paragraph, then one line per headline number.
- Full report: the same message, followed by the headline table and one table per included block, as in the email.

**Notion** adds a page under the page the user names; ask which if they didn't. The page is titled "Store Pulse: <period>" and holds what the email body holds at the chosen detail level.

**When a run goes wrong:**

- A destination can't be reached: the report still appears in Cowork and still goes to the other destinations. The Output section of SKILL.md gives the line to add. Never skip the whole run silently.
- The window has no traffic: still deliver, saying there was no traffic in this window.
- End the run with one line naming every destination that received a draft, a message or a page. Don't repeat the message body.

## Download

Only when the user asks ("download this").

Reuse the figures from the snapshot in this conversation; don't query again. If there is no snapshot in this conversation, run one first.

Save a PDF in the Cowork output folder, in this order: a title with the store and period; the summary paragraph; the headline table; the funnel table (step, share of sessions, sessions, previous share, change); then a table for each block that was included. Reply with one line saying where the file is.
