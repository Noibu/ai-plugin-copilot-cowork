# After a snapshot

Read this when the user picks a thread from the next-step question, or types a request to schedule or download. Each section is one request.

## A thread is picked

Arrives as a picked option, or typed ("why did conversion fall?").

Treat it as a fresh question. Don't answer from the snapshot alone: the snapshot shows that something moved, not why. Let the right skill take it, and frame it in the user's terms:

- A checkout or funnel-completion move: `checkout-analysis`.
- A product or collection move: `product-analysis`.
- A channel, device or country move: `segment-analysis`.
- An error or a slow page: `tech-diagnosis`.

If none fits, answer it with the Noibu tools directly, with the number, its window and its base.

## Schedule

Only when the user asks ("schedule this", "send me this every morning").

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

**The scheduled prompt** runs with no conversation behind it, so it carries everything: *Run Store Pulse for <store> over <window rule> in <timezone>, compared to the period of the same length before.* Add the blocks to include if the user named any (top products, channel performance, paid ad performance), and any delivery below. The Output section of SKILL.md says what a scheduled run delivers in Cowork.

Confirm in one sentence once the schedule exists, saying when it will run. If a delivery was set up, add that the first run's send needs approving once, after which later runs deliver without asking.

### Sending it elsewhere

Only if the user names a destination: email or Slack. Ask the user which detail level they want only if a destination is set: **Summary** (the summary and the headline numbers) or **Full report** (adds the funnel and any blocks included).

For each destination, check its connection first. If it isn't set up, say in one plain line which connection unlocks it, leave that destination out, and carry on with the rest. If no destination is left, the schedule still runs in Cowork; say so.

**Email is a draft, never sent.** The run creates a draft in the user's connected mail account (Outlook or Gmail; ask which if both are connected), and the user reviews and sends it. Confirm the exact recipient addresses in chat before creating the schedule, even if the user already gave them.

- Subject: "Store Pulse: <period>".
- Body, in order: the summary paragraph; the headline table (Sessions, Engagement, Conversion, AOV, RPS, each with its current value and its change against the previous period).
- Full report only, one table per included block:
  - Purchase funnel: step, share of sessions, sessions, previous share, previous sessions, change.
  - Top products: product, sessions, add-to-cart rate, with the site-wide add-to-cart rate for the period stated above it.
  - Channel performance: channel, sessions, engagement, conversion, RPS.
  - Paid ad performance: platform, sessions, conversions, revenue. Always the three platforms; `0` where a platform has no tagged traffic.
- A closing line: "Generated <date and time> from Store Pulse for <store>."
- Tables only. No charts, no images, no attachments.

**Slack** posts to the channel the user names; ask which if they didn't.

- Summary: one message with the title "Store Pulse: <period>", the summary paragraph, then one line per headline number.
- Full report: a canvas titled "Store Pulse: <period>" holding the summary, a "Headline metrics" table, and one section per included block (the funnel as a list, the others as tables); then a posted message, not a draft, with the title and the canvas link. A draft message is visible only to the person who made it.
- If canvases aren't available on the workspace's plan, post the summary message and add: "Full canvas report requires a paid Slack plan."

**When a run goes wrong:**

- A destination can't be reached: say so in the run ("Couldn't reach <destination>; the connection may need signing in again") and still deliver to the others. Never skip the whole run silently.
- The window has no traffic: still deliver, saying there was no traffic in this window.
- End the run with one line naming every destination that received a draft or a message. Don't repeat the message body.

## Download

Only when the user asks ("download this").

Reuse the figures from the snapshot in this conversation; don't query again. If there is no snapshot in this conversation, run one first.

Save a PDF in the Cowork output folder, in this order: a title with the store and period; the summary paragraph; the headline table; the funnel table (step, share of sessions, sessions, previous share, change); then a table for each block that was included. Reply with one line saying where the file is.
