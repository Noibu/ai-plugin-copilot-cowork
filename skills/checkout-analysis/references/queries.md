# Checkout query specs

The query definitions for every route. A quick answer runs one or two of these. A full analysis runs the whole battery, Step 1 to Step 4. An investigation reuses a Step 4 breakdown and goes deeper.

## Session tool: what it can group and filter by

- **Group by:** device, country, browser, OS, UTM source/medium, landing URL, bounced, discount-applied, and **funnel depth** (how far the session got).
- **Filter on:** device, country, bounced, checkout-completed, landing URL, UTM source.
- **Funnel depth: confirm the exact field name; the prefix matters.** It is groupable (working name ~`CONVERSION_FUNNEL_DEPTH`), but near-variants are rejected. If a group-by is rejected, look up the exact name and retry; only fall back to per-stage count measures if it truly isn't available.
- **Payment and delivery method are not groupable.** Attempt those slices only if the schema exposes such a field; if not, skip them.
- **Checkout sub-step submission counts (contact / address / shipping / payment) and cart value are per-session fields, not group-by dimensions.** They feed Q1b's abandonment classification (row-level, one row per session), not the grouped session queries. These are standard fields on every account: run Q1b unconditionally, and leave out its results (all of them, or single buckets) only if they come back empty.

## Signal model: what earns a priority

Absolute levels are misleading in checkout: a high cart-to-checkout drop, and mobile converting below desktop (or the reverse), are normal. So the report flags **change, not level**:

- **Change-based signals (most of them)**: funnel step drops, device conversion, market/country conversion, discount patterns. Flagged **only when the metric regressed against the previous comparable window**, never because the absolute level looks bad or differs from another segment or the site average.
- **Qualified active errors (the one absolute trigger)**: a checkout error earns a priority when it's active *and* genuinely fixable (see Q5), regardless of trend. Everything else must be a regression.

### The comparison window

The **previous comparable window** is the equal-length window immediately before the current one (last 30 days → the 30 days before that). All change-based signals compare against it.

- **A regression worth flagging** = the rate dropped by **≥ 3 pp absolute or ≥ 10% relative** against the previous window, **and** the segment clears the volume threshold (Step 4). Keep the current absolute numbers for context, but the *trigger* is the drop.
- **No or low-volume previous window** (new store, sparse history): change-based signals can't be computed. Say so briefly and lean on the qualified errors and the overview numbers. **Do not** fall back to absolute-level flags; that is the false-positive trap this model avoids.
- **Seasonality:** the previous window is calendar-adjacent, so a window spanning a seasonal shift (a sale period, for example) can move rates for benign reasons. Note it when relevant.

## Step 1: Broad overview (current and previous windows)

- First tell the user what you're doing, e.g. "Starting with a broad look across your checkout, comparing the last 30 days to the 30 before."
- Fire the **current-window** battery (Q1–Q7, with Q1b) and, in parallel, the **previous-window** counterparts for the change-detection metrics (Q1, Q1b, Q2, Q6, Q7). Q3/Q4 (payment/delivery, descriptive) and Q5 (errors, recency-based) need no previous copy.
- **No minimum session thresholds at this stage.** Skip any empty or null slice silently.

**Q1: Full funnel by depth** (current + previous). Session tool, group by funnel depth, measure session count, order by sessions desc.

- One row per depth: 0/null = no action, 1 = added to cart, 2 = checkout started, 3 = payment submitted, 4 = completed. Compute drop-off in post-processing.
- If depth group-by is unavailable: one all-sessions query measuring total sessions, per-stage event counts, and the predefined conversion rate. Those intermediate counts are event proxies, so lean on total → completed.
- If intermediate buckets are near zero while completions are healthy, the steps between aren't instrumented: use cart to completion.
- **Express checkout inflates depth-4 against depth-3.** Apple Pay, Shop Pay and similar bypass the payment-info page, so depth-4 > depth-3 is normal. Explain it; don't treat it as an error.

**Q1b: Checkout sub-step abandonment** (current + previous). Run this unconditionally, same as Q1. The fields below (contact / address / shipping / payment submission counts, cart value, visual-error flag, exit URL) are standard session-table fields on every account, so don't gate this query on confirming they exist first. What varies by platform is whether they're *populated*: judge the **results**, not whether to run the query.

Session tool, filter to funnel depth ≥ 2 (checkout-entered sessions only; cart-only sessions are out of scope here), row-level (one row per session, not grouped), selecting: the checkout sub-step submission-count fields (contact / address / shipping / payment), `MAX_CART_VALUE` (alias `cart_value`), the visual-error flag, and the exit-URL field.

- Exclude completed sessions. This query only classifies *abandoned* checkout sessions.
- Classify each remaining session into exactly one bucket by the furthest step reached, first match wins:
  1. **Attempted payment, didn't complete**: payment submitted ≥ 1 but not completed.
  2. **Experienced technical issues**: the session's visual-error flag is set.
  3. **Dropped at payment step**: reached shipping/address (≥ 1) but zero payment submissions.
  4. **Dropped after adding contact info**: contact submitted ≥ 1, nothing further.
  5. **Left checkout without any action**: checkout started, zero sub-steps submitted.
  6. **Left checkout to keep browsing**: zero progress, and the exit page is a product/collection page rather than checkout.
- Per bucket, sum session count and `cart_value` (sum of `MAX_CART_VALUE`).
- **After running the query**, judge what came back: if every bucket is zero or null, this data isn't populated for this account, so leave the abandonment table out. If only some buckets have real counts (sub-step counts are populated but the visual-error flag never fires, say), keep the populated buckets and drop the zero ones. Don't require every bucket before showing any.
- Feeds the abandonment table (buckets ranked by session count, at most 5) and, per bucket, the regression check in Step 3.

**Q2: Cart and order value baseline** (current + previous). Session tool, filter to funnel depth ≥ 2, group by discount-applied, measure session count + median completed order value + median product quantity, order by sessions desc.

- Depth ≥ 2 avoids null discounts on pre-checkout sessions. Gives the discount rate among checkout-entering sessions and whether discounted orders differ in size.
- **Use the completion-time discount value, not checkout-start.** Checkout-start discount fields significantly undercount usage.
- **Discount survivorship bias.** Only checkout-reaching sessions can have a discount, so this discount rate is among checkout-entering sessions only.

**Q3: Payment method mix** (current only). *Only if a payment-method dimension exists.* Filter to completed checkouts, group by payment method names (array join, limit 20), measure session count + median completed order value, order by sessions desc. If unavailable, skip.

- **Completed orders only (applies to Q4 too).** Payment and delivery fields populate only on completed sessions. Never imply a method was rejected because of low volume; it may just not have been chosen by completers.

**Q4: Delivery method mix** (current only). *Only if a delivery/shipping dimension exists.* Filter to completed checkouts, group by delivery method names (array join, limit 20), measure session count + median completed order value + median shipping cost, order by sessions desc. If unavailable, skip.

**Q5: Active fixable checkout errors.** Priority errors tool, priority-type issues on URLs containing "checkout". Then **qualify** each candidate and keep only the genuinely fixable ones. Fetch stack trace + error-type detail for the top candidates by occurrence, and keep an error only if **all** hold:

- **Active**: last seen within **48 hours** (drop anything older, even if still flagged priority).
- **Has a stack trace**: no stack trace → skip (no path to a fix).
- **Not a 4XX HTTP type**: any 4XX is platform-class; skip (the HTTP type overrides frame analysis).
- **Not pure third-party**: if every frame is a third-party domain, the merchant can't action it → skip; keep only errors with merchant-owned (first-party) frames.
- **Not a script error, even if first-party**: exclude script-origin errors (third-party tags, pixels and opaque cross-origin "Script error.") regardless of frame ownership.

What remains = active, fixable checkout errors. These earn priorities regardless of trend. If none qualify, there's no error priority, and that's fine.

**Q6: Device conversion split** (current + previous). Session tool, group by device, measure session count + conversion rate, order by sessions desc. Feeds the mobile and desktop conversion numbers and the device regression check.

**Q7: Country conversion split** (current + previous). Session tool, group by country code (limit 25), measure session count + conversion rate, order by sessions desc. Feeds the market regression check.

## Step 2: Cross-reference and period-over-period

Compute current rates **and the change against the previous window**, for metrics whose inputs are populated. depth-N = sessions reaching at least that stage.

**Current rates (from Q1):**

- Add-to-cart rate = depth-1+ ÷ total · Checkout start = depth-2+ ÷ total · Checkout → payment = depth-3+ ÷ depth-2+ · Payment → completion = depth-4 ÷ depth-3+ · Overall completion = depth-4 ÷ depth-2+ (or the predefined conversion rate).
- If intermediate events are uninstrumented, use cart → order (depth-4 ÷ depth-1+). depth-4 > depth-3 is expected (express checkout; see the Q1 note).

**Period-over-period deltas** (current − previous), for each populated metric: every funnel step rate, overall completion, each device's conversion (Q6), each market's conversion (Q7), the discount rate and discounted-against-full conversion (Q2). A metric is a **candidate signal** only if its delta is a regression past the threshold above.

**Cart profile (from Q2):** discount rate, median order value (discounted against full-price), median products per order. Context only; not a signal unless the discount rate or discounted conversion regressed.

## Step 3: Pick signals (change-based, top 3)

From the Step 2 deltas, pick the top 3 **regressions** by sessions affected (fewer is fine). A normal-but-stable level is **not** a signal; only a drop against the previous window is.

| If a metric regressed against the previous window… | Consider this follow-up |
|---|---|
| Overall checkout completion fell | Device split (Q6 current against previous) to locate the new friction; cart-exit journeys if the cart→checkout step drove it |
| Checkout → payment or payment → completion fell | Device or payment-method breakdown: find where the new drop concentrates |
| A device's conversion fell against its own previous | That device's funnel: isolate the step that moved |
| A market's conversion fell against its own previous | Country cross-tab: shipping, payment or localization change |
| Discount rate or discounted conversion moved materially | Promo mix: did a campaign change the picture |
| A checkout sub-step abandonment bucket (Q1b) grew, proportionally, against its own previous share | That bucket's example sessions |

- **Markets are relative.** Flag a country only when its conversion *regressed* against its own previous window. A chronically low or chronically 0% market that didn't change is **not** a signal (it's likely a market they don't serve). A market with no previous baseline can't be assessed; don't flag it.
- **Sub-step buckets are relative too.** Flag a Q1b bucket only when its share of abandoned sessions regressed against its own previous window. A chronically large "dropped at payment step" bucket that hasn't changed is not a signal.
- **Discount-value gap is benign.** "Discounted orders complete at a lower value" is normal coupon behaviour and never a priority on its own. Only surface discounts if the rate or discounted conversion regressed.
- **The only non-regression priority is a qualified active error** (Q5).

## Step 4: Deeper follow-ups (confirming a regression, or an investigation)

Device and country baselines are already in Step 1; these go deeper on a flagged regression or when an investigation needs more.

**Traffic thresholds, calibrated to store volume** (also gate which regressions are worth flagging):

- High (>500K sessions/mo): segment ≥ ~0.1–0.2% of total · Mid (50K–500K): ~0.3–0.5% · Low (<50K): keep very low or skip.

- **Device funnel breakdown**: filter to depth ≥ 1 (or ≥ 2 when checkout-start is reliable), group by device, measure session + completion (+ intermediate where populated). Find the step where the regression concentrates.
- **Country cross-tab**: for a market whose conversion regressed, break the funnel down to see whether it's a shipping/payment block or a UX change.
- **Payment method completion**: when payment → completion regressed and payment data is populated: depth ≥ 3, group by payment method, completion per method.
- **Cart-page exit journeys**: when cart → checkout regressed: user journeys tool anchored to `/cart`, loose mode, forward paths only, max depth 5. Forward-nav back to product = purchase uncertainty; exits to external URLs = distraction or price comparison.
- **Error detail**: Q5 already qualified the fixable errors. Deeper root cause and the fix belong to `tech-diagnosis`.
