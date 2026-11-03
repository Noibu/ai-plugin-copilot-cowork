## The browser (chosen once, in Block 2)

"The run" here is the finder route (Blocks 1 to 4 and Phases 1 to 5). The build half uses the same browser by the rules in `references/build/stage-3-qa.md` and SKILL.md's `console.noibu.com` rule.

Cowork has one browser: the person's own **Microsoft Edge**, driven through `browser_actions`. It does every browser step of the run — the homepage and policy read, the goal's surfaces, the cart round trip, the before looks — at the size of the person's Edge window (a desktop window). What it can and cannot do decides everything below:

| Can | Cannot |
| --- | --- |
| `create_tab` / `navigate_to` an absolute http(s) URL (each in its own call) | run page JavaScript or inject CSS (no walkthrough scripts, no injected "after" preview, no forced variation) |
| `get_dom`: the page DOM inline up to 48 KB; when the host can, the **full** DOM saved to a workspace file ("Full output saved to: <path>") | resize the window or emulate a phone (no phone-size capture) |
| `get_screenshot`: an image returned to you (do not assume it is saved as a file) | download files, open `edge:`/`about:`/devtools pages, or change browser settings |
| `click`/`dom_click`, `type`/`dom_type`, `scroll`/`dom_scroll`, `keypress`, `wait` (up to 8 actions per call) | read another browser, or the person's other devices |
| `request_browser_interaction` (CAPTCHA, verification, a step only the person may do) and `request_user_form_fill` (logins) | type or ask for secrets in chat |

**Pick it in this order (Block 2):**

1. **Is `browser_actions` in the tool list** (loaded or deferred)? No → no browser (step 3). Yes → the readiness message opens the run's tab with `create_tab` on the store URL (`intention: other`, `step_title` "Open your store"). Any result with a tab id means the browser is usable: keep that tab id; it is the run's tab for the read and the before looks.
2. **The tab could not be opened** (no local browser connected, a client error, a timeout after the tool's one allowed retry): follow `references/browser-readiness.md` in one short message — only now, because a browser step is actually blocked — and continue every non-browser step. If the person makes the browser available before Block 3, use it; otherwise the run has no browser. Do not retry in a loop.
3. **Neither:** no browser. Continue on Noibu data alone (Phase 1's no-browser path, description-only previews), and a footer line suggests running again with Cowork open in Edge. Never stop the run for want of a browser (scheduled runs with a required live-site check are the one exception, in SKILL.md).

Say nothing else in chat about the browser; the reports' capture line and footer name what was read.

**How each step is done**

| Step | Cowork |
| --- | --- |
| The run's tab | `create_tab` with the store URL (readiness message); reuse it with `navigate_to` for every later page. Open a second tab only when two pages must stay loaded side by side (never needed in the finder) |
| Read a page | `navigate_to` (own call) → `wait` 3 + `get_dom` + `get_screenshot` (one call). When `get_dom` names a saved file, run `python <skill-dir>/scripts/dom_facts.py <file> --surface <surface> --url <path> --into <run folder>/walkthrough.json`. When it does not (the DOM fit inline, or the host has no file storage), read the inline DOM and the screenshot against the surface's checklist in `references/site-validation.md` and record the facts by hand under the same keys, marking selectors `"source": "inline-dom"` |
| Look at a surface (above the fold, visibility, what a shopper sees) | the `get_screenshot` image. It is your look, not a file: describe what it shows in `walkthrough.json` (`look` entries), never claim an image was saved |
| Cart add / remove (cart and checkout goals) | `dom_click` on the page's own add-to-cart control (node id from `get_dom`), `wait`, re-read; later `dom_click` the remove control of **that line only** (`references/site-validation.md`, "Cart round trip") |
| Consent banner or popup in the way | Leave the person's existing consent choices alone. Only when a banner or popup covers the content you must read, close it with its decline or close control (never Accept), and say so in `walkthrough.json` `meta.fixUps` |
| Bot check, login wall, CAPTCHA | Never bypassed: SKILL.md "Switching mid-run" (`request_browser_interaction`, or continue without that surface) |
| A tab that vanished (`tab-not-found`) | The tool's rule: one `create_tab` with the URL, retried once on timeout; then say the tab could not be reopened and continue without the browser |
| Mobile | No phone-size view exists. Mobile layout claims come from the scroll/click data and are marked inferred. Only when the person asks to see mobile, ask them (one line) to narrow their Edge window to phone width themselves; shoot it with `get_screenshot` and caption it "narrow desktop window, not a phone" |
| End of the run | There is no close-tab action: leave the run's tab on the store page it last showed (never on a checkout step). Say nothing about it unless the person asks |

Every `browser_actions` call carries `intention: {category: "other", reason: …}` with a plain reason ("Read your product page", "Add one item to the cart to read the cart, then remove it"). No step of this skill ever needs `checkout`, `payment`, `credit_card_info`, `form_submit_with_pii`, `account_change` or `data_deletion`: an action that would is out of scope — stop it.
