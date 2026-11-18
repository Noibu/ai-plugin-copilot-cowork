# Diagnosing a specific issue

Read this when a specific signal is named: an error, a metric and a page, a Noibu issue number, a page URL, or a priority picked from a scan. It runs from identifying the signal to the closing question. A priority picked from a scan starts at Step 2; the store, platform and window are already known.

## Step 1: Identify the signal

Translate the request into symptom, scope and context. If it is clear, fetch immediately; don't narrate it back. If it is ambiguous, ask one clarifying question.

| Request | Signal |
|---|---|
| "Why is LCP poor on checkout?" | Page speed: LCP on checkout |
| "What's causing errors on Safari mobile?" | Errors on Safari mobile |

## Step 2: Fetch focused data

Targeted queries only; no broad surveys. Run in parallel where possible.

- **Errors**: priority issues matching the scope; full detail for the top 1–2. If this issue had related issues noted when the scan deduplicated, fetch those too, and say in the fix: "This fix should also resolve issue #<number>: same root cause, different trigger path."
- **Page speed**: the metrics at p75 for the affected URLs or page group, by device and browser.
- **Combined**: both, scoped to the relevant page or segment.

Apply the error filters before surfacing any error:

- **No stack trace** → skip. Without frames pointing to specific code there is no path to a root-cause fix.
- **Pure third-party** → not a fixable finding. If every stack frame is from a third-party domain, the store owner can't action it.

Rank by severity, then page criticality, then sessions. Cap at 3–5 findings.

## Step 3: Write the summary

For each finding:

1. The finding's title as a `##` heading.
2. A 2–3 sentence narrative: impact only. Who is affected, how many, what they experience, and the trend. No error codes or endpoint names.
3. The impacted sessions: the session count and its share of all sessions in the window, in one sentence.
4. **Top pages affected:** a 3–5 row table of URL and sessions.

## Step 4: Trace the cause

Use what is available, in this order. If a source errors, skip it at once and continue; treat it as unavailable, with no retries.

- **Noibu's diagnosis**: use its why and impact as the basis for the cause.
- **Noibu's page data**: for INP, the clicked selectors on the affected page; for any metric, its p75 by device and browser, and the page's visual error count.
- **The code repository**, when GitHub is connected: search for the affected element and fetch about 20 lines of context.
- **Store data**, when the platform's connection is available: query it to confirm or refute the hypothesis.

Nothing here can open the page, read its source or measure it. What the data and the code don't show is reasoned from patterns, and said to be so.

**Naming a connection.** When the cause or the fix stops short because a connection is missing, say which in one plain line, once:

- No file and line: "Connecting GitHub would let me point to the exact file and line."
- On Shopify with no GitHub: "Connecting Shopify would let me check the live theme and settings."

**Write the cause** under `### What's likely causing it`. Open with: *From here on, I'm reasoning over the data rather than reporting it…* Then 1–2 sentences: the hypothesis only, starting from why. Commit to the primary cause; note alternatives in one sentence.

### Reading errors

- **Third-party origin.** Name the specific service and be explicit that the fix path is contacting the vendor, not a code change. Don't imply a fix the operator can't ship.
- **Third-party scripts that slow a page** (analytics pixels, email capture tools, loyalty apps) can't be edited directly, but their impact can be reduced: load with `async` or `defer`, reserve space in CSS to prevent layout shift, or ask the vendor for a lighter embed.
- **Infrastructure-level fixes** (server-side rendering changes, CDN configuration, server response time): flag these as needing backend or DevOps access, distinct from theme or code changes.
- **Cookie-consent check.** If an error fires on a consent-related endpoint (OneTrust, Cookiebot, TrustArc) and the impacted sessions are very short with no further navigation, this is likely an observability gap: the consent platform may be removing Noibu's script and ending the recording early. Flag it as a data limitation, not user impact, and name the platform when identifiable.
- **Reading frames.** Classify each frame with `references/platforms.md`. Identify whether the frame is merchant-owned (fixable), platform (not fixable) or vendor (share with vendor), and the function or operation running when the error fired. Monitoring and recording wrappers (Sentry, rrweb) affect data collection, not user experience; flag them but don't treat them as user-impacting.
- If the root cause can't be determined from the available data, say so. Don't ship a suppression.

### Reading page speed

| Metric | Good | Needs improvement | Poor |
|---|---|---|---|
| LCP | ≤ 2.5s | ≤ 4.0s | > 4.0s |
| CLS | ≤ 0.1 | ≤ 0.25 | > 0.25 |
| INP | ≤ 200ms | ≤ 500ms | > 500ms |
| FCP | ≤ 1.8s | ≤ 3.0s | > 3.0s |
| TTFB | ≤ 800ms | ≤ 1.8s | > 1.8s |

**What Noibu provides** (`noibu_get_page_visits`):

- p75 scores per page or URL (LCP, CLS, INP, FCP, TTFB).
- `CLICKED_SELECTORS_WITH_COUNTS`: CSS selectors and click counts per page. For INP, cross-reference the most-clicked elements on a high-INP page to narrow down candidates.
- Visual error count per page.

**What Noibu's data can't show:** the specific LCP element (tag, source, attributes), the CLS shift sources (which elements move and by how much), and the specific slow INP element with its phase breakdown. Those need someone to measure the page in a browser's developer tools.

So use `CLICKED_SELECTORS_WITH_COUNTS` as supporting context for INP, the code repository when it is connected, and pattern-based recommendations for LCP and CLS. Name the one measurement that would confirm the cause, as a step for the user's developer:

- Measure on the device where Noibu's data shows the issue is worst. A mobile finding has to be measured at phone size on a throttled connection, with the cache disabled; a desktop measurement misses mobile CLS and LCP problems.
- To check whether a script or element is in the initial HTML response, view the page's source. The inspector shows the page after scripts have run and misleads on load-order questions.

**LCP.** Use Noibu's recommended bucket to direct the investigation:

| Bucket | Where to look |
|---|---|
| TTFB | Server response time, CDN configuration, app or plugin overhead |
| Load Delay | Render-blocking scripts, missing preload hint, resource discovery order |
| Load Duration | Image file size, format (WebP against JPEG), CDN delivery |
| Render Delay | JS blocking paint, lazy-loaded element, CSS blocking render |

The key question for the developer: is the LCP image in the initial HTML? If the image URL only appears after scripts run, it can't be discovered early whatever else is optimised.

**CLS.** Only shifts where `hadRecentInput` is `false` count toward CLS. Common causes, in rough order of frequency: images missing `width`/`height`, late-injected content (popovers, loyalty embeds, banners), carousels with no height before scripts run, font swap with a large metrics difference, client-rendered results grids injecting after paint.

**INP.** The dominant phase says where to dig:

| Dominant phase | Likely cause |
|---|---|
| Input Delay | Main thread busy at click time: third-party scripts initialising, carousels, analytics |
| Processing Time | Event handler too heavy: large re-renders, synchronous DOM queries, complex filter logic |
| Presentation Delay | Layout thrashing, large paint area, expensive animation |

If SVG sub-elements appear as separate tap targets in Noibu's data, the fix is `pointer-events: none` on the SVG children plus wrapping the SVG in a `<button>`.

**Data and code disagree.** If Noibu shows a poor score but the code looks clean (no lazy hero image, no missing dimensions, scripts deferred), the cause is likely at runtime: server response time, a slow CDN, or render-blocking script execution that doesn't show in static code. Don't conclude "no issue found" from clean code alone.

## Step 5: The closing question

Work out the fix, but **don't write it yet**. Commit to the most likely fix.

After the cause, ask one clickable question with the header "Next step" and these options:

1. "Show me the fix"
2. "Draft a pull request", described as "<low, medium or high> risk · accept the pull request to apply the fix". Only when the fix is a code change. When it isn't, leave the option out and say in one line before the question: "The fix for this issue isn't a code change, so there's no file to edit automatically."
3. "Open a ticket"
4. "Share findings"

Write nothing after the question. `references/follow-ups.md` handles each choice.

## What a finding looks like

```
## <Finding title>

### Summary
<2–3 sentences: impact only. No error codes or endpoint names.>
<Session count and share of all sessions.>
**Top pages affected:** 3–5 row table

### What's likely causing it
*From here on, I'm reasoning over the data rather than reporting it…*
<1–2 sentences: the hypothesis only. Start from why.>

<the closing question>
```

`### How to fix it` and `### Technical details` are written only when the user asks for them; `references/follow-ups.md` has both.
