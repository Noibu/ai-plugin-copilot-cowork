# The scan

Read this for a scan: no specific issue named. It holds the error scan, the page-speed scan, the ranking, and the report data to write from them.

## Step 1: Scan for errors

**Before fetching any errors**, read the store's platform section in `references/platforms.md` and take from it the merchant code paths, platform paths and telemetry paths. These are the patterns used to classify frames. Do not skip this.

Two passes, in parallel.

**Pass 1: fixable errors.** Use an error search query, **not the pre-ranked priority list**, so you control the candidate pool.

Search the last 7 days of errors, sorted by occurrence count highest first, 30 per page, active states only (new, open, in-progress). **Exclude at query time:** HTTP errors (4XX/5XX), network/connection errors (status 0, ERR_NETWORK), and the "Script error" type. Metadata only; no stack traces in this call.

**Always fetch up to 3 pages.** Process each page before fetching the next, using the pagination cursor from the response. Stop early only if you already have 2 or more fixable candidates. After 3 pages, or when no more pages are available, proceed with whatever you found.

For each candidate on each page, apply filters:

1. **Recency**: at least one occurrence in the last 48 hours. If not, skip.
2. **Volume**: more than 10 occurrences in the 7-day window. If not, skip.

For each survivor, fetch the full error detail individually to get the JavaScript stack trace frames. Classify with the platform paths:

- **No frames** → skip. Without frames pointing to specific code there is no path to a root-cause fix.
- **All frames match platform or telemetry paths** → skip.
- **At least one frame matches a merchant path** → keep as a fixable candidate.

Before taking the top 2, **deduplicate**: if two candidates share the same primary file and error message or type, keep only the higher-scoring one and note the other's issue number as a related issue. The second slot goes to the next distinct error.

**Pass 2: vendor errors.** The same search: last 7 days, sorted by occurrence count, 30 per page. Apply the 48-hour recency and the more-than-10 volume floor. For each survivor, fetch the full error detail individually and classify its frames. Take the top 2 vendor candidates by score.

**Classification**

- **Fixable**: at least one frame in merchant-owned code paths.
- **Platform**: frames only in core platform infrastructure; or any HTTP error (4XX/5XX) with no JS stack trace; or any network/connection failure (status 0, ERR_NETWORK, request aborted) with no JS stack trace. Discarded whatever the endpoint. No exceptions.
- **Telemetry**: frames in known analytics, pixel or beacon scripts. Discard silently.
- **Vendor**: third-party frames that aren't telemetry, including `*.shopifyapps.com` and Shopify product endpoints with their own support channel (Shop app, Shop Pay).

Discard platform and telemetry. **Classification is mechanical; no judgment calls.**

**Score:** `occurrences (7-day total) × criticality_weight`. Weights: Checkout=5, Cart=4, Product page=3, Collection=2, Home=1, Other=0.5.

## Step 2: Scan for page speed

Fetch LCP, INP and CLS across all page groups. Keep the pages with at least one metric outside the Good band:

| Metric | Good | Needs improvement | Poor |
|---|---|---|---|
| LCP | ≤ 2.5s | ≤ 4.0s | > 4.0s |
| CLS | ≤ 0.1 | ≤ 0.25 | > 0.25 |
| INP | ≤ 200ms | ≤ 500ms | > 500ms |

**Score:** `traffic_weight × severity_score`. traffic_weight is normalized (highest = 1.0). Severity: Poor = 3 points, Needs improvement = 1 point, per metric.

Take the top 2. Capture for each: the page or page group, its worst metric and p75 value, the band, and the traffic volume.

## Step 3: Rank

Within each kind, rank by score, with ties broken by page criticality. That gives up to 2 fixable errors, up to 2 page-speed findings and up to 2 vendor errors.

Order the report's priorities so each kind is seen: the top fixable error, the top page-speed finding, the top vendor error; then the second of each, in the same order.

## Report data

Write one JSON file in the working folder in this shape, then follow the Output section of SKILL.md. Supply values only; leave out any field with no data.

```json
{
  "skill": "tech-diagnosis",
  "store": {"name": "<domain name>", "id": "<domain UUID>"},
  "window": {"start": "<window start>", "end": "<window end>"},
  "priorities": [
    {
      "kind": "fixable",
      "status": "Active",
      "title": "",
      "shortTitle": "",
      "evidence": "",
      "errorType": "",
      "occurrences": 0,
      "lastSeen": "<timestamp>",
      "where": "",
      "affected": 0,
      "link": "<issue URL>"
    },
    {
      "kind": "performance",
      "status": "Active",
      "title": "",
      "shortTitle": "",
      "evidence": "",
      "vital": {"metric": "LCP", "value": 0},
      "where": ""
    },
    {
      "kind": "vendor",
      "title": "",
      "shortTitle": "",
      "evidence": "",
      "vendor": "",
      "errorType": "",
      "occurrences": 0,
      "where": ""
    }
  ],
  "noPrioritiesReason": "",
  "links": ["<console URL>"]
}
```

| Field | What to write |
| --- | --- |
| `kind` | `fixable`, `performance` or `vendor` |
| `status` | `Active`, `Re-emerging` or `Improving`, when Noibu's data shows which. Leave out otherwise |
| `title` | A plain-English title for the finding |
| `shortTitle` | The same finding in 5 words or fewer ("Add to cart failure") |
| `evidence` | One sentence. Error: what's wrong, where, and who it touches. Page speed: what's slow, where, and how bad. Vendor: what's happening, which vendor, and the impact |
| `errorType` | The kind of error in plain words ("JavaScript error") |
| `vendor` | The third-party service by name ("Klaviyo") |
| `occurrences` | The 7-day occurrence count |
| `lastSeen` | When it last occurred, as a timestamp with its timezone |
| `where` | Error: the pages, then the browser or OS where it concentrates. Page speed: the page group, the device and the traffic volume ("Collection pages · mobile · 12,000 page views") |
| `vital` | Page speed only: the worst metric and its p75. LCP and INP in milliseconds (4.2 s is 4200), CLS as its score |
| `affected` | The number of sessions the issue was present in, when the tool returns it. Leave out otherwise |
| `link` | For an error: the issue URL the Noibu tool returned. Never build one |

- The window is the scan's window. Error counts cover the last 7 days; say so in the evidence sentence when a count appears in it.
- A page-speed value that wasn't measured is `null`.
- Text contains no ids, field names, tool names or formulas. An issue is referred to by its number only in the summary, never in a title.
- `links` takes up to two `console.noibu.com` URLs that a Noibu tool returned in this run.

**Empty kinds.** When one kind has nothing, say so in the summary: "No active errors found that you can fix directly", "No significant performance issues found", or "No third-party app errors detected". When all three are empty, send an empty `priorities` list and put the three facts in one sentence in `noPrioritiesReason`.

**More than the question can hold.** The card draws the first three priorities and the next-step question offers the first five. Name any finding beyond those in the summary.
