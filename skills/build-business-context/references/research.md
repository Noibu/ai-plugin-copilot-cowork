# Checking, setup and research

Read this at the start of a run. It covers everything that happens before the interview: the existing-context check, the two setup questions, the web research, and recorded calls.

## Step 1: Resolve the domain and check for an existing context

Do this before anything else: before the setup questions, before research.

1. **Ask which website or store this is for** and get the actual domain (e.g. `creativebag.com`). Confirm it is the right site: "Just to confirm: this is <domain>, the <one-line description>?"
2. **Resolve it** with `noibu_get_domain` (fall back to `noibu_list_domains`). Keep both the domain **UUID** (`id`) and its integer **`numId`**. The read uses the UUID and the final save uses the `numId`, so holding both now means no resolving again later. Then call `noibu_get_business_context` with the UUID (`domainId`).
3. **Gate on the result.** A context already exists when the response has a `businessContext` with a non-empty `fullContent`. If it does, tell the user and ask in one clickable question whether to regenerate it or keep the existing one. Continue only if they choose to regenerate; the existing context is overwritten at the end. If `businessContext` is null, continue.

Only once cleared to proceed, ask the setup questions.

## Step 2: Setup questions

Ask these together in one short batch. They are quick and they shape everything else.

1. **Do you already have any context files, brand guidelines, personas or a strategy document I should fold in?** If yes, read them before researching, so you don't re-derive what they already wrote.
2. **Do you record customer or sales calls in Gong or Fellow?** If yes, ask whether to pull the transcripts and mine them for context. Call transcripts are one of the richest grounding sources there is: customers describe their pains, goals, buying process and gotchas in their own words, which is far more reliable than anything inferred from a website. If they say yes, note which tool and roughly which calls matter (a specific account, a date range, or all of them) to scope the pull in Step 3b.

If they don't know the domain, or the file is for a business that isn't online yet, adapt. But you almost always need the domain to do useful research.

## Step 3: Deep web research

Now learn everything publicly knowable about this business. Spend real effort here; this is what keeps the eventual recommendations grounded.

This is read-heavy work whose value is the conclusion, not the raw pages. Keep page contents out of the conversation: carry forward a skimmable findings summary with sources and an explicit list of what could not be confirmed.

Answer as many of these as you can from public sources:

- **What they sell**: core product categories, flagship products, price points.
- **Who they sell to**: B2B, B2C or both; consumer or trade; geography.
- **How long they've been around**: founding year, company age, any history or heritage.
- **Ownership structure**: family-owned, private, PE-backed, public, franchise and so on.
- **Size signals**: rough employee count, number of locations, revenue band if public.
- **Ecommerce platform**: Shopify, BigCommerce, Magento/Adobe Commerce, WooCommerce, Salesforce Commerce, custom and so on. Check page source, `myshopify` redirects, `cdn.shopify.com`, BigCommerce headers, technology-lookup signals, and careers pages mentioning the stack.
- **Apps and tech in the stack**: reviews (Yotpo, Okendo), search (Searchanise, Algolia), loyalty, subscriptions, payment and checkout providers, analytics, customer data platforms.
- **Positioning and differentiators**: how they describe themselves, what they claim sets them apart, price posture (premium or value).
- **Competitors**: who they name, or who obviously competes with them.
- **Brand voice**: read their homepage, About page and a few product pages. Note spelling conventions (Canadian or UK spelling, for example), tone and personality.
- **Recent news**: funding, acquisitions, expansions, leadership changes, awards.

Then **report back what you found** in a short, skimmable summary, and explicitly flag what you couldn't confirm. Say something like: "Here's what I dug up. I couldn't confirm your platform or your payment processor from the outside; those are on my question list. Anything below that's wrong, correct me now." Letting the user correct research before the interview is much cheaper than fixing the final file.

Treat every research finding as provisional until the user confirms it. Mark unconfirmed items `[CONFIRM]` in the file; never state them as fact.

## Step 3b: Recorded calls (Gong or Fellow), if the user has them

Only if the user said in setup that they record calls and want them pulled. Skip it entirely otherwise; don't go looking for transcripts nobody asked for.

If the Gong or Fellow connection isn't set up, say in one plain line which connection unlocks this step, and carry on without it.

When it is available, this is often the single highest-value input to the whole file. A website shows how a business markets itself; a sales or success call shows what is actually true: the customer's real goals, the objections, the dollar figures, the "our checkout is held together with tape" admissions. Mine it well and you walk into the interview already knowing half the answers.

1. **Find the relevant calls.** Use the scope the user gave in setup. If they said "all of them", list the available calls first and sanity-check the volume. If there are only a handful, pull them all. If there are dozens or hundreds, don't pull everything blindly: tell the user what you see ("I found about 80 calls going back a year") and confirm whether to pull all of them or focus on a subset (most recent, a named account, customer-facing calls only). Reading hundreds of full transcripts is slow and usually unnecessary.
2. **Read the transcripts and extract context**, mapped to the same themes the interview covers so it slots cleanly into the file:
   - Goals and priorities stated in the customer's own words.
   - Money-leak suspicions and pain points ("we lose people at shipping options").
   - Hard numbers: conversion rate, AOV, ROAS, traffic, revenue. Capture the exact figure and which call it came from.
   - Customer and persona language, and any "this metric is misleading because…" gotchas.
   - Tech stack, platform, checkout, and deployment and dev-team realities.
   - Competitors named, tools mentioned, and recurring complaints.
   - Brand voice, and how the team talks about their own business.
3. **Attribute what you find.** When something comes from a call, note the source ("from the May 2 discovery call") so the user can trust and verify it. A figure from a transcript is more reliable than a web guess, but still confirm the important ones: people misspeak on calls, and numbers drift.

Fold transcript findings into the same report-back you give after web research, clearly labelled as coming from calls. Anything a transcript already answered can be skipped or simply confirmed in the interview.
