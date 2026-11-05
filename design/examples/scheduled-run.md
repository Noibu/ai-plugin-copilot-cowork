# Example: a scheduled run, set up once and delivered without clicks

Fictional data for `example.com`. Shows the setup question, the self-contained scheduled prompt, and what a run delivers by email and to Teams. Rules: README section 2.5.

## 1. Setup question (asked once, only if the request didn't name everything)

```json
{"questions": [{"header": "Schedule", "question": "How should the checkout report for example.com run?", "multiSelect": false, "options": [
  {"label": "Weekly on Mondays (Recommended)", "description": "9 am · Summary · last 7 days vs the previous 7 · Teams channel you pick"},
  {"label": "Customize", "description": "Choose frequency, day, time, timezone, detail and where it goes"}]}]}
```

If the user had said "send me the checkout report for example.com every Monday at 9 to #ecom-team", there would be no question. Cowork would confirm in one sentence and ask the user to approve the first run's post.

## 2. The scheduled prompt (written by the skill, stored by Cowork)

```text
Run the Noibu checkout-analysis skill for example.com (domain 00000000-0000-4000-8000-000000000000).
Window: the last 7 full days ending yesterday, America/Toronto, compared with the 7 days before that.
Detail: Summary. Alert-only: no.
Deliver to: Teams, team "Ecommerce", channel "ecom-team".
This is an unattended run: ask no questions. If data or the destination is unavailable, deliver what you can and say what was skipped.
Follow the skill's references/ux-guidelines.md, "Scheduled run".
```

## 3. What the run delivers

**Teams post:** the summary as the message text, the report card underneath (same card as in chat, with its Noibu link buttons), then:

> Follow up in Cowork:
> • *Ask Cowork: "investigate checkout priority 1 for example.com"* (payment submission fell on mobile)
> • *Ask Cowork: "investigate checkout priority 2 for example.com"* (more shoppers leave at delivery options)

**Email (if chosen instead):**

```text
Subject: Checkout report · example.com · Oct 27 – Nov 2

Checkout completion fell 5.3 pp to 41.0% this week, mostly on mobile where fewer
shoppers submit payment. Desktop held steady, and average order value rose 2.1%.

Priorities
1. Payment submission fell on mobile: 22.5% vs 25.0% of cart sessions (~1,900 sessions).
   View in Noibu: https://console.noibu.com/00000000-0000-4000-8000-000000000000/issues
2. More shoppers leave at delivery options: 31% vs 26% of checkout starts (~640 sessions).

Follow up in Cowork: ask "investigate checkout priority 1 for example.com".
Full report attached (PDF).
```

No "reply with", no clickable question, no buttons that only exist in chat.
