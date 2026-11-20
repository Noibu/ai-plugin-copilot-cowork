# Steps 6–8: business context, the check, one scheduled report

Read this at step 6 and keep it open to the end.

## Step 6 · Business context

The business context is what keeps every Noibu report grounded in how this business works. It lives in Noibu, and every report reads it from there, so a context saved later is picked up on its own.

1. **Look first.** Read the store's business context from Noibu. Never print its contents.
   - One is saved: "Noibu has a business context for <store>, saved <date>." Go to step 7.
2. **None saved:** ask one clickable question, header "Context": "Did Noibu give you a business context file for <store>?" Options:
   - "Yes, I have the file"
   - "No, build one after setup"
   - "Skip for now"
3. **"Yes, I have the file":** ask the user to attach it, or paste its contents, in one line. Read it and confirm it is for this store (its name or address appears in it). If it is for a different store, say which and ask again. Then save it to Noibu with the store's `numId` and the file's full contents, unchanged. Read the context back from Noibu to confirm, and say "Saved your business context to Noibu." If the file can't be read or the save fails, say so in one line and record "Save the business context file to Noibu" as a to-do for the user.
4. **"No, build one after setup":** "No problem: I'll offer to build it as soon as setup is done." Record that the user wants one built. Don't start it here: step 8 ends with the offer.
5. **"Skip for now":** "No problem: your reports run without it, and they'll use it as soon as it's saved in Noibu." Record "Add a business context (your Noibu contact can provide one, or ask me to build it)" as a to-do for the user.

## Step 7 · Check everything

Re-check each item now; don't rely on what an earlier step said. Report one line each, with ✅ (done), ⚠️ (works, something is pending) or ❌ (not done). Leave out a line that doesn't apply to this store.

- **Noibu:** the sign-in check succeeds, and whether the store is receiving data.
- **Shopify** (Shopify stores): the plugin returns the matching shop; or the to-do from step 3.
- **Theme previews** (Shopify stores), by where step 3 found they go: through the Shopify plugin (✅ when theme write access is still listed), through Noibu (✅ when Noibu lists the store's themes), or nowhere yet (⚠️ with the to-do). When they go through the Shopify plugin, don't check or mention Noibu's theme access.
- **Code host:** the proving read succeeds and the chosen repository is readable; ⚠️ "read only" for Azure DevOps; or the to-do from step 4.
- **Release reporting:** ✅ when Noibu's release list shows a release from the component. ⚠️ with the pull request's link and its state (open or merged), or "pipeline file handed to your developer", when none has arrived yet. Otherwise the to-do.
- **Business context:** ✅ when Noibu returns one for the store. ⚠️ "to be built next" when the user asked for that. Otherwise the to-do.

Then, under the line "Still to do", list every to-do with who needs to do it: the user, their developer or agency, their Microsoft 365 administrator (for a plugin they can't install), a Shopify store owner, or their Noibu contact. With nothing left, write "Everything is in place." and no list.

Still in the same reply, two or three closing lines: what is connected, and where the business context lives (in Noibu) or that it is still to come. If a pull request is open, add that *check my releases* confirms the first release once it is merged.

This reply is plain text and goes straight on into step 8's header and report list. No clickable question follows it, because the checklist above it would not be shown.

## Step 8 · One scheduled report

The schedule's first run should be its next scheduled time, never now: a report that starts in this chat takes the chat over, and the business context build may be about to start here. Only the user can prevent that, in Cowork's approval prompt, so this step tells them to. The step is still last, so that if a run starts anyway the setup has nothing left to lose.

Cowork sets up one schedule from a chat, so the user picks one report. If the store isn't receiving data, skip this step: say in one line that a report is worth scheduling once data is arriving, and go to item 6.

1. **Already scheduled?** Look for a scheduled prompt with one of the names in the table below, for this store. If one exists, say "Your <report> is already scheduled (<when>)." and go to item 6.
2. **List the reports.** This is the one choice in the setup that is typed, not clicked: the message below is plain text, with no clickable question. It closes the same reply as step 7's checklist: after the closing lines, this step's header on a line of its own, a blank line, then the message. Then wait for the reply.

   "Which report should I schedule? Type its name, or *skip*.

   - **Store pulse**: the store's headline numbers and purchase funnel
   - **Checkout analysis**: where shoppers drop off in checkout
   - **Product analysis**: which products and collections are winning or losing
   - **Segment analysis**: how devices, countries and channels convert
   - **Tech diagnosis**: the highest-value errors and slow pages
   - **A/B test ideas**: new test opportunities from your data"

3. **Read the reply**, matching loosely: "pulse", "store health" → store pulse; "checkout" → checkout analysis; "products" → product analysis; "segments", "channels", "devices" → segment analysis; "tech", "errors", "slow pages" → tech diagnosis; "ab tests", "experiments" → A/B test ideas. More than one named: take the first, and say the rest can be scheduled from each report. "Skip", "later", "none" → the result is "No report scheduled. Ask me to schedule one any time."; go to item 6. A reply that matches nothing: send the list once more; a second miss counts as a skip.
4. **Ask how often**, unless the reply already said (for example "checkout, every Monday"). One clickable question, header "Schedule": "In the approval box that comes next, untick Run once now. How often should <report> run?" All times are 9 am in the user's timezone.

   - Store pulse: "Weekly on Mondays (Recommended)", "Daily", "Every 2 weeks on Mondays", "Monthly", "Skip for now".
   - Every other report: "Weekly on Mondays (Recommended)", "Every 2 weeks on Mondays", "Monthly", "Something else", "Skip for now". On "Something else", ask for the day and time in one line.

   Monthly runs on the 1st. If the scheduler has no every-other-week option, say so and offer weekly or monthly. "Skip for now" is the same as a skip in item 3.
5. **Create it** as a Cowork scheduled prompt at the chosen time, shown only in Cowork, set to run in a new conversation. Use the row's name and prompt exactly; they are the ones each report uses for its own schedule, so that report's "change my schedule" finds it later.

   **Its first run is the next scheduled time.** A schedule has no start date; it first runs at the next occurrence of the chosen day and time. What starts a report in this chat is the "Run once now" box in Cowork's approval prompt, which is ticked unless the user unticks it. So the one line written just before creating the schedule is exactly: "Untick Run once now before you approve, so the report doesn't start in this chat." Write nothing else there, and no reasoning about the scheduler. If the scheduler lets you turn the run on creation off yourself, do that too. Never run the report yourself to "test" the schedule.

   | Report | Name | Prompt |
   |---|---|---|
   | Store pulse | `store-pulse-<store with dots as dashes>` | *Run Store Pulse for <store> over <window> in <timezone>, compared to the period of the same length before.* |
   | Checkout analysis | `checkout-analysis-<store>` | *Run the full checkout analysis for <store>.* |
   | Product analysis | `product-analysis-<store>` | *Run the full product analysis for <store>.* |
   | Segment analysis | `segment-analysis-<store>` | *Run the full segment analysis for <store>.* |
   | Tech diagnosis | `tech-scan-<store>` | *Run a tech diagnosis scan for <store>.* |
   | A/B test ideas | `ab-testing-<store>` | *Look for new A/B test opportunities for <store> for the goal All goals. Ask nothing. Do not create any Noibu test, branch or pull request.* |

   Store pulse's window follows how often it runs: daily, "yesterday, midnight to midnight"; weekly, "the preceding 7 days, ending at midnight on Monday"; every 2 weeks, "the preceding 14 days, ending at midnight on Monday"; monthly, "the previous calendar month". Write nothing else into any prompt.
6. **Close.** Every path through this step ends here. The result is one of: "<Report> scheduled, <when>. Its first run is <date>. It appears in Cowork. To get it by email or in Teams, or to schedule another report, run that report and ask."; one line saying it wasn't created (the approval was declined, or no scheduler is available); or the line an earlier item gave.

   If a run of the scheduled report has started in this chat all the same, write nothing more, ask nothing and don't start the business context build: the report is the reply.

   - **The user asked in step 6 for a business context to be built:** the setup ends with the offer, as one clickable question, header "Context". Its text follows the Guardrails, so the result is cut to six words ("Store pulse scheduled, Mondays 9 am." or "No report scheduled."): "Step 8 of 8 · One scheduled report. <result> Setup is done. Build <store>'s business context now?" Options "Yes, build it now", with the description "A few questions about the business, then it is saved to Noibu", and "Not now".
     - "Yes, build it now": start `build-business-context` for <store>, handing it the store and company from the ledger.
     - "Not now": "No problem. Say *build my business context* whenever you're ready.", then the last line below without "build your business context".
   - **Otherwise:** the result as plain text, then the last line of the setup, naming what to ask for next: "Next, ask me to build your business context, check the store's last 24 hours, analyze checkout, run a tech diagnosis, or find A/B test ideas." Leave out "build your business context" when one is saved.
