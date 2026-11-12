# Running an audit

Read this when the user asks for an accessibility audit, or asks to schedule one. It holds how the pages are chosen, how a scan is started, what to reply, and the schedule.

The scan runs on Noibu's side: a crawler loads the page and runs WCAG checks on it. A scan is started with a tool, takes about a minute, and its results open in the Noibu console. No tool returns the results, so nothing about what a scan found can be said here.

## 1. Choose the pages

The top 10 pages by 30-day pageviews. One `noibu_get_page_visits` call over the last 30 days:

```json
{"measures":[{"aggregate":{"measureFunc":"COUNT","target":{"field":"PAGE_VISIT_ID"},"measureAlias":"pageviews"}}],"groupBy":{"fieldSegments":["URL"]},"orderBy":{"measureAlias":"pageviews","direction":"DESCENDING"},"limit":10}
```

- If the user named pages, scan those and look up their pageviews the same way.
- A page that plainly can't be scanned on its own (a checkout step, an account page behind a sign-in, a cart that is empty without a session) is left out and named in the reply; take the next page down.
- If the window has no pageviews, say the store has no traffic in the last 30 days and ask which pages to scan.

## 2. Start one scan per page

For each page, call `noibu_start_ada_audit` with:

- `domainNumId`: the domain's integer `numId` (not the UUID).
- `url`: the absolute address, `https://<domain name><path>`.

Start them together. Each call returns its run, queued, with an id. Keep each page's run id.

If a start fails, don't retry it in a loop: note the page and the reason, and carry on with the rest.

## 3. Reply

One reply, in this order, and nothing after it:

1. One sentence: how many pages were sent for scanning, that they are the store's busiest by 30-day pageviews, and that results appear in about a minute.
2. A table: Page (a short name, such as "Homepage" or "Bracelets collection") · 30-day pageviews · Results (a link reading "Open results").

   The link for a page is `https://console.noibu.com/<domain UUID>/ada-audit/runs?ids=<run id>`, built only from the domain's UUID and the run id the tool returned.
3. Any page that could not be sent, with its reason, in one line.
4. One sentence on what happens next: "The results open in the Noibu console. Paste or attach the findings here and I'll pool the repeats, rank them by severity and traffic, and draft the fixes."

Say nothing about what the scans found. Don't show the report card: it needs findings.

## Schedule

Only when the user asks ("schedule this", "run this every week").

- If a scheduled prompt for this store's audit already exists, change that one; don't add a second.
- If the request already names how often and when, ask nothing more about timing.
- Otherwise ask one clickable question, header "Schedule", with these options:
  1. "Weekly on Mondays (Recommended)": 9 am
  2. "Every 2 weeks on Mondays": 9 am
  3. "Monthly": 9 am on the 1st
  4. "Something else": the user names the day and time

Set it up as a Cowork scheduled prompt named `accessibility-scan-<store>`, with this prompt: *Run an accessibility audit for <store>: start a scan on each of the top 10 pages by 30-day pageviews and list each page with its pageviews and its results link. Ask nothing.*

A scheduled run delivers the same reply as section 3. It never reports findings and never creates a pull request or ticket, because it has no findings to work from.

**A digest** is sent only if the user names a destination: email, Slack or Notion.

- If that connection isn't set up, say in one plain line which connection unlocks it, and leave that destination out.
- Email: confirm the exact recipient addresses in chat before creating the schedule, even if the user already gave them.
- Add to the prompt, once per destination: *Send the list of pages and results links to <destination>.*

Confirm in one or two sentences once the schedule exists: how often, and any digest destinations. Then offer to run it once now. Run it only if the user says yes.
