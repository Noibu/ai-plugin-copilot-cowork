# Writing the report data

Read this after the workflow has run, when the full analysis is ready to deliver. Write one JSON file in the working folder in the shape below, then follow the Output section of SKILL.md.

Supply values only. Leave a key out when its data isn't populated for this store. Use `null` only for a value that should have been measured and wasn't; never 0 in its place.

## Shape

```json
{
  "skill": "segment-analysis",
  "store": {"name": "<domain name>", "id": "<domain UUID>"},
  "window": {"start": "<window start>", "end": "<window end>"},
  "currency": "<three-letter code>",
  "kpis": {
    "siteWideConversion": 0,
    "siteWideSessions": 0,
    "mobileConversion": 0,
    "mobileSessions": 0,
    "desktopConversion": 0,
    "desktopSessions": 0
  },
  "tables": {
    "countries": [{"country": "<two-letter code>", "sessions": 0, "conversionRate": 0, "revenuePerSession": 0}],
    "bestChannels": [{"channel": "", "sessions": 0, "conversionRate": 0, "revenuePerSession": 0}],
    "mostVisitedChannels": [{"channel": "", "sessions": 0, "conversionRate": 0, "revenuePerSession": 0}]
  },
  "priorities": [
    {"signal": "", "title": "", "shortTitle": "", "evidence": "", "affected": 0}
  ],
  "noPrioritiesReason": ""
}
```

- Timestamps carry their timezone, e.g. `2026-10-03T00:00:00Z`.
- A rate is a percentage: 2.4 means 2.4%. If the tool returns a fraction (0.024), multiply by 100 first.

## Where each value comes from

| Field | Source |
| --- | --- |
| `kpis.siteWideConversion`, `kpis.siteWideSessions` | Site-wide conversion rate (total purchases ÷ total sessions) and total sessions |
| `kpis.mobileConversion`, `kpis.mobileSessions` | The device breakdown's mobile row |
| `kpis.desktopConversion`, `kpis.desktopSessions` | The device breakdown's desktop row |
| `tables.countries` | The country breakdown, by sessions descending, up to 5 rows |
| `tables.bestChannels` | The channel breakdown, ranked by conversion rate descending, up to 5 rows. Leave `(none)/(none)` out |
| `tables.mostVisitedChannels` | The channel breakdown, ranked by sessions descending, up to 5 rows. Keep `(none)/(none)` in |

**Country** goes in as its two-letter code ("US", "CA").

**Channel names** are written for people. The raw source and medium don't appear:

- `sendlane / email` → "Sendlane Email" · `rivo / email` → "Rivo Email" · `facebook / cpc` → "Facebook Ads" · `ig / social` → "Instagram" · `google / cpc` → "Google Ads" · `google / product_sync` → "Google Shopping" · `chatgpt.com / –` → "ChatGPT"
- No obvious mapping → capitalize the source and append the medium: `steam / referral` → "Steam Referral"
- `(none) / (none)` → "Direct / Unknown"
- Never merge two source and medium pairs into one row.

**Things to say in the summary, not in the data:**

- **Untagged traffic.** If "Direct / Unknown" is 5% or more of total sessions, say what share of sessions has no UTM attribution, and that it is likely direct traffic or missing tracking parameters on campaigns.
- **Broken UTM macros.** If channel names contain unfilled macros (such as `{{`), say that campaign links may not be tracking correctly.
- **Excluded segments.** Any segment the bot filter disqualified that is above 1% of sessions, in one sentence.
- **Local currency.** A country whose revenue per session is far above the rest is likely reported in local currency. Set that row's `revenuePerSession` to `null` and say so.

**Currency.** Use the store's order currency. Never add or rank amounts across currencies.

## Priorities

Exactly the signals picked in Step 2, up to 3, ranked by sessions affected, descending. Don't mention or surface further signals.

| Field | What to write |
| --- | --- |
| `signal` | One of: `Low mobile conversion`, `High-traffic underperformer`, `Campaign drag`, `Localization gap`, `High-value channel`, `Device gap` |
| `title` | The segment's name ("Mobile", "Facebook Ads", "Canada") |
| `shortTitle` | The signal and the segment in 5 words or fewer ("Facebook Ads campaign drag") |
| `evidence` | One sentence: the key number and why it matters ("Facebook Ads converts at 0.4% against 1.1% for other paid channels") |
| `affected` | The sessions in that segment in the window |

Rules:

- A priority carries the segment, one sentence and its sessions affected. No actions, tables or bullets.
- A segment the bot filter disqualified is never a priority.
- A device gap is a priority only when the mobile-to-desktop ratio worsened, and a channel only against its peer group (`references/queries.md`, Step 2).
- Text contains no ids, field names, tool names or formulas.

**No priorities.** When no signal clears the rules, send an empty `priorities` list and one sentence in `noPrioritiesReason` saying what the data shows and why nothing stands out.
