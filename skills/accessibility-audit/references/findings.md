# Working on findings

Read this when the user pastes or attaches findings from an audit. It holds how to read them, how to pool and score them, the report data to write, and what can be done after the report.

Work only from what the user provided. If the findings cover some of the audited pages and not others, say which pages the report covers. Never fill a gap from memory of what stores usually get wrong.

## What a finding needs

For each violation: the rule or a description of what fails, its severity (critical, serious, moderate or minor), the page it was found on, and the element (a CSS selector, an HTML snippet, or both). The WCAG criterion helps; when it is missing, take it from the table below.

If the pasted text lacks severities or pages for most findings, say what is missing in one line and ask for it; don't guess a severity. If it lacks only selectors, carry on: the findings can be ranked, but a fix can't be located until the element is known.

For each page, the 30-day pageviews come from Noibu: use the figures from the audit in this conversation, or one `noibu_get_page_visits` call for those URLs.

The checks are structural and programmatic only. They don't judge content quality (alt text accuracy, link text phrasing, heading wording).

## Common violations

| Issue | WCAG criterion | Level |
|---|---|---|
| Colour contrast < 4.5:1 (normal text) | 1.4.3 Contrast (Minimum) | AA |
| Colour contrast < 3:1 (large text / UI) | 1.4.11 Non-text Contrast | AA |
| Heading levels skip (e.g. H1 → H3) | 1.3.1 Info and Relationships | A |
| Interactive control nested inside another interactive control | 4.1.2 Name, Role, Value | A |
| Missing alt attribute on images | 1.1.1 Non-text Content | A |
| Hidden form fields still readable by screen readers | 1.3.1 / 4.1.2 | A |
| Broken link / 404 | 2.4.4 Link Purpose (In Context) | A |
| Missing focus indicators | 2.4.7 Focus Visible | AA |
| Unlabelled form control | 3.3.2 Labels or Instructions | A |

Not exhaustive. Record every finding the user provided.

Wherever a criterion is shown to a person in prose, a PDF, a ticket or a pull request, link it to its W3C page: `https://www.w3.org/WAI/WCAG21/Understanding/<slug>.html` (`1.4.3` → `contrast-minimum`, `4.1.2` → `name-role-value`). Use the help link in the findings to confirm the slug when there is one; don't guess it.

## Recurring patterns

- Promo banners: the most common contrast failure (light text on a saturated background, often just under 4.5:1).
- Nav dropdowns: nested `<a>`/`<button>` → 4.1.2. Fix once in the shared nav or header component.
- Filter and sort labels marked up as `<h2>` for styling → 1.3.1, `moderate`.
- Footer country and currency selectors: visually hidden but present in the DOM.
- Third-party embeds (rewards, chat, reviews): not fixable in site code. `needs-investigation`, with a note to raise it with the vendor. Never patch a third-party embed directly.
- A high-traffic page that returns a 404 is `critical` (2.4.4), but the fix is navigation or a redirect, not code; route it to a person.

## Severity

Use the severity the findings give, as it is: `minor` | `moderate` | `serious` | `critical`.

## Pooling

Before scoring or reporting anything, pool every violation across all the pages into one list. Deduplicate first; this is the most important step.

- If the same **selector + criterion** appears on several pages, it is one shared-component violation, not several. Collapse it into a single pooled entry and sum the traffic across every page it appears on.
- "Selector" means the shared-component identifier (a class, snippet or section, such as `.promo-banner` or `header nav a`), not every literal DOM node. 33 product-card titles sharing one CSS rule are one pooled entry with 33 instances, not 33 entries.
- Two violations with the same rule but different selectors (body text contrast and a banner's contrast, say) are different pooled entries. They are different fixes, even under the same rule.
- Severity should be uniform within a pooled entry. If it isn't, use the most severe value present.

## Priority

One ranking, used the same way in the report and when drafting pull requests or creating tickets. Pool first, then score each pooled entry:

```
priority = severity_weight × log10(total_30d_pageviews_affected) × breadth_multiplier

severity_weight:
  critical  5.0
  serious   3.0
  moderate  1.5
  minor     0.5

breadth_multiplier:
  1.0 + (0.2 × number of pages the violation appears on), capped at 2.0
```

Traffic is log-scaled deliberately: a violation shouldn't get 9x the weight just because its page has 9x the pageviews of another. Breadth is scored separately from traffic, so a shared-component violation ranks above a single-page violation with comparable per-page traffic.

Sort descending by `priority`. Don't compute it differently for the report and for fix selection.

## Report data

Write one JSON file in the working folder in this shape, then follow the Output section of SKILL.md. Supply values only.

```json
{
  "skill": "accessibility-audit",
  "store": {"name": "<domain name>", "id": "<domain UUID>"},
  "window": {"start": "<start of the 30-day pageview window>", "end": "<end>"},
  "kpis": {
    "pagesScanned": 0,
    "pageviews": 0,
    "violationInstances": 0,
    "uniqueFixes": 0,
    "critical": 0,
    "serious": 0,
    "moderate": 0,
    "minor": 0
  },
  "tables": {
    "pagesScanned": [{"page": "", "pageviews": 0, "instances": 0}],
    "keyFindings": [{"finding": "", "wcag": "", "severity": ""}]
  },
  "priorities": [
    {"severity": "", "title": "", "shortTitle": "", "evidence": "", "affected": 0, "wcag": "", "pages": 0}
  ],
  "noPrioritiesReason": ""
}
```

| Field | What to write |
| --- | --- |
| `kpis.pagesScanned` | Pages the provided findings cover |
| `kpis.pageviews` | Total 30-day pageviews across those pages |
| `kpis.violationInstances` | Raw violation instances across the pages, before pooling |
| `kpis.uniqueFixes` | Pooled entries: the unique fixes |
| `kpis.critical`, `serious`, `moderate`, `minor` | Pooled entries at each severity. Always send all four; a severity with none is a 0 |
| `tables.pagesScanned` | One row per page, by pageviews descending: a short page name ("Homepage", "Bracelets collection"), its 30-day pageviews, its violation instances |
| `tables.keyFindings` | One row per pooled entry, in priority order: the finding in plain English, its criterion as text ("1.4.3 Contrast (Minimum)"), its severity |
| `priorities` | The top pooled entries in priority order, up to 5. The card draws the first three and the next-step question offers all five |

Each priority:

| Field | What to write |
| --- | --- |
| `severity` | `critical`, `serious`, `moderate` or `minor` |
| `title` | The finding in plain English ("Text contrast is too low") |
| `shortTitle` | The same in 5 words or fewer ("Low text contrast") |
| `evidence` | One sentence: what fails and where ("Body text fails the 4.5:1 contrast ratio on all 10 scanned pages") |
| `affected` | 30-day pageviews across every page the pooled entry appears on |
| `wcag` | The criterion as text ("1.4.3 Contrast (Minimum)") |
| `pages` | How many pages it appears on |

- A value the findings don't give is `null`, never a guess.
- Text contains no selectors, rule ids, field names or tool names. Those belong to a finding's detail.

**The summary** covers, in 2–3 sentences: how many pages the findings cover; that many instances repeat the same issue across pages, so pooling reduces them to the unique fixes; the single highest-priority finding by name; and the sentence on what an automated audit is.

**No priorities.** When the findings list no violations, send an empty `priorities` list and one sentence in `noPrioritiesReason`.

## After the report

Each section is one request. Work from the pooled findings in this conversation.

### A finding's detail

Arrives as a picked priority, or typed ("show me the contrast finding", "see every finding"). For each finding asked about, in this order:

1. **Severity:** <SEVERITY> | Pages affected: <N> | Pageviews affected (30-day, est.): <N>
2. **WCAG violation:** the criterion, linked to its W3C page.
3. A plain-English description of what fails and who it affects.
4. The CSS selector and an example HTML snippet, each in a code block, when the findings gave them.
5. **Suggested fix**, with the ticket or pull request link if one exists.
6. **Pages affected:** every page the pooled finding appears on, each linked to its live URL. Never bare page names.

### Download the report

Only when the user asks ("download this", "give me the PDF"). Build it from the pooled, ranked findings and save it as a PDF in the Cowork output folder.

- **File name:** `<Domain> Accessibility Audit <MM> <DD> <YYYY>` (e.g. `Carsncards.com Accessibility Audit 09 09 2026`).
- Title, subtitle (domain, standard, page count), audit date, then a divider.
- **Disclaimer**, word for word: *"This skill generates automated WCAG 2.1 AA accessibility reports. Automated tools detect 30%–90% of issues on the pages that were scanned. Results are informational only, not legal advice or a compliance certification. Manual testing by a qualified professional is required for complete coverage."*
- **Executive summary**: an intro paragraph, a stats paragraph, then severity cards. No specific finding is named here.
  - **Intro** (2–3 sentences): the pages covered and why, the total pageviews covered, that AA is the legal standard, and, if tickets or pull requests were already created, how many findings were filed.
  - **Stats paragraph**: the raw instance count and the pooled unique-fix count, with the relationship spelled out, e.g. *"We found 271 violation instances across the pages. Many repeat the same issue on multiple pages; once pooled, that's 27 unique fixes."*
  - **Severity cards**: one row of four equal-width cards (Critical, Serious, Moderate, Minor), each a large bold number over a small label. A severity with none still gets a card. The number and its label must not overlap.
- **Pages scanned**: a table of page (linked to its live URL), 30-day pageviews, violation instances.
- **Key findings**: a table of #, Finding (linked to its detail section), WCAG (linked), Severity, and Automated tickets (only if at least one exists).
- **One detail section per finding**, with the six parts listed under "A finding's detail". Give every element its own block with real space above and below.
- The whole document is left-aligned; only the severity cards' numbers and labels are centred. No appendix and no per-page violation matrix. A link is a real link, never styled text.

Before handing it over, check that a link resolves in each of: a Pages scanned row, a Key findings row, a WCAG criterion, and a finding's Pages affected line. Check every finding's detail section for overlapping elements. Fix any defect first. Reply with one line saying where the file is.

### Auto-draft PR, or create tickets

Only when the user asks ("draft PRs for these", "open tickets for the top findings"). Never suggest either.

> **Fix-selection rule:** for the top 10 fixable pooled findings, by priority, draft a pull request or open a ticket, whichever was asked for. A finding not traceable to a file gets a ticket only, labelled `needs-investigation`, and doesn't use one of the 10. Never touch checkout code or merchant-managed settings. Never merge anything.

1. **Settle what the path needs,** if it isn't known yet in this conversation:
   - **Auto-draft PR:** GitHub. If it isn't connected, say in one plain line that connecting GitHub unlocks drafting pull requests, and stop. Once it is, ask once: "Which GitHub repo holds the theme? (owner/name)".
   - **Tickets:** the ticket platform and its team or project, asked once. If that platform isn't connected, say in one plain line which connection unlocks it, and stop.
2. **Apply the rule.** For pull requests, find each fix's location with `references/fix-locations.md`. A finding with no selector can't be located: it gets a `needs-investigation` ticket. Every ticket and pull request description carries the six parts listed under "A finding's detail" (or the `needs-investigation` note in place of a fix), with each page as a real link to its live URL.
3. **Reply with one line per finding that got something created:** the finding's name, an arrow, then the ticket or pull request reference linked to the address the tool returned. Never post a bare reference with no link.
4. With more than 10 fixable findings, add: "N more findings weren't addressed this run."

A report already delivered isn't regenerated.
