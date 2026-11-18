# Steps 1–4: Noibu, the store, Shopify, one scheduled report

Read this at step 1 and keep it open through step 4.

## Step 1 · Noibu connection

Call `noibu_get_current_user`.

- It succeeds: "Noibu is connected as <name or email>." Go to step 2.
- It fails: the connection isn't working. Say so in one line, ask the user to reconnect from the Connect prompt, and stop. Noibu can't be skipped.
- The user says they have no Noibu account: say the setup needs one and that their Noibu contact can create it, and stop.

## Step 2 · The store

1. If the user named a store or gave a UUID, resolve it. Otherwise list the stores the account can see, paging while a full page comes back.
2. **No stores:** the account has no store access. Say that, and that a Noibu administrator on their team can grant it. Stop.
3. **One store:** ask one clickable question, header "Store": "Is <store> the store we're setting up?" Options "Yes, that's it" and "No, a different store".
4. **Several stores:** pick the most likely one (the one the user named, else the first that looks like a production storefront) and ask the same question, with up to three other stores as options plus "A different store". Don't print a long list; the user can type any store's name.
5. **A different store:** ask for its address, resolve it and confirm once more. If it isn't in their Noibu account, say so, and that a Noibu administrator on their team can add them. Stop there.
6. Record the store's name, UUID, `numId` and platform (`siteType`).
7. Call `noibu_get_company` once. Record the company name. If the company has other stores (a separate checkout store is common), mention them in one line; the rest of the setup is for the confirmed store.
8. Call `noibu_check_data_connection`. If the store isn't receiving data, say the Noibu script may not be installed or may have stopped sending, and that reports will be empty until it is. Record "Get the Noibu script sending data on <store>" as a to-do for their developer, and carry on: the connections are still worth setting up.

## Step 3 · Shopify

Everything in this step is a read. Nothing in the store changes.

1. **Platform.** `Shopify` or `Shopify Plus` as the store's platform means Shopify. If the platform is missing, check the business context in Noibu for it. If neither settles it, ask one clickable question, header "Platform": "Which platform is <store> built on?" Options "Shopify", "BigCommerce", "Salesforce Commerce Cloud", "Something else". Record it.
2. **Not Shopify:** "<store> runs on <platform>, so there's no store connection to set up." Go to step 4.
3. **Is the Shopify plugin here?** It is when a Shopify shop-information tool (`get-shop-info`) is available in this session.
   - Not here: say "To let Cowork read your Shopify store and build theme previews, install and connect the Shopify plugin (Customize → Plugins → Shopify)." and ask one clickable question, header "Shopify": "Let me know when Shopify shows Connected." Options "It's connected" and "Skip for now".
   - "It's connected" and the tool is now here: carry on at item 4.
   - "It's connected" and the tool still isn't here: record "Check the Shopify plugin shows Connected, then say *continue my Noibu setup* in a new chat" as a to-do for the user, and go to item 6.
   - "Skip for now": record "Connect the Shopify plugin" as a to-do for the user, and go to item 6.
4. **Is it this store?** Read the shop's information. Its primary domain or its `myshopify.com` domain must match the Noibu store, ignoring `www.`.
   - It matches: record the shop.
   - It is a different shop: say which shop the plugin is connected to, and ask one clickable question, header "Shopify": "Switch the Shopify plugin to <store>'s shop?" Options "Yes, switch" and "Skip for now". On yes, switch with the plugin's own shop-switching tool and check again. If the right shop isn't offered, record "Connect the Shopify plugin with the account that owns <store>" as a to-do for the user and go to item 6.
5. **Can it change themes?** Through the plugin's query tool, and only as a query, read the app's access scopes:

   ```graphql
   query { currentAppInstallation { accessScopes { handle } } }
   ```

   - `write_themes` is listed: theme changes go through the **Shopify plugin**. Count the store's themes:

     ```graphql
     query { themes(first: 50) { nodes { id role } } }
     ```

     Close the step with "Shopify is connected to <shop>, and theme previews can be built there." With 18 or more themes, add in the same line that Shopify allows 20 and each preview adds one, so old previews are worth deleting in Shopify admin. Go to step 4.
   - `write_themes` is missing: the plugin stays connected for store data. Go to item 6 for theme changes.
6. **Noibu's theme access (the backup).** Only reached when the plugin is missing, skipped, on the wrong shop, or can't write themes. List the store's themes through Noibu, with the store's `numId`.
   - It lists themes: theme changes go through **Noibu**. "Theme previews will be built through Noibu (live theme: <name>)."
   - It fails or lists nothing: theme changes have nowhere to go yet. Record "Enable Noibu's Shopify theme access for <store>" as a to-do for their Noibu contact, and say so in one line.

## Step 4 · One scheduled report

Cowork sets up one schedule from a chat, so the user picks one report here. The others can be scheduled later by running that report and asking to schedule it.

1. **Already scheduled?** Look for a scheduled prompt with one of the names in the table below, for this store. If one exists, say "Your <report> is already scheduled (<when>)." and go to step 5. Never create a second schedule with the same name.
2. **Ask** one clickable question, header "Report":

   "Which report should I schedule? Store pulse (daily), checkout analysis, product analysis, segment analysis, errors and slow pages, or A/B test ideas (each weekly on Mondays). Pick one below or type its name."

   Options, in this order: "Store pulse, daily", "Checkout analysis, weekly", "Errors and slow pages, weekly", "A/B test ideas, weekly", "Skip for now".
3. **Read the reply.** A picked option, or a typed name matched loosely: "pulse", "the daily one" → store pulse; "checkout" → checkout analysis; "products" → product analysis; "segments", "channels", "devices" → segment analysis; "errors", "tech", "slow pages" → errors and slow pages; "ab tests", "experiments" → A/B test ideas. More than one named: schedule the first, and say the rest can be scheduled from each report. "Skip", "later", "none" → record "Schedule a recurring Noibu report" as a to-do for the user and go to step 5.
4. **Create it** as a Cowork scheduled prompt, at 9 am in the user's timezone, shown only in Cowork. Use the row's name and prompt exactly; they are the ones each report uses for its own schedule, so that report's "change my schedule" finds it later.

   | Report | Runs | Name | Prompt |
   |---|---|---|---|
   | Store pulse | Daily | `store-pulse-<store with dots as dashes>` | *Run Store Pulse for <store> over yesterday, midnight to midnight, in <timezone>, compared to the period of the same length before.* |
   | Checkout analysis | Mondays | `checkout-analysis-<store>` | *Run the full checkout analysis for <store>.* |
   | Product analysis | Mondays | `product-analysis-<store>` | *Run the full product analysis for <store>.* |
   | Segment analysis | Mondays | `segment-analysis-<store>` | *Run the full segment analysis for <store>.* |
   | Errors and slow pages | Mondays | `tech-scan-<store>` | *Run a tech diagnosis scan for <store>.* |
   | A/B test ideas | Mondays | `ab-testing-<store>` | *Look for new A/B test opportunities for <store> for the goal All goals. Ask nothing. Do not create any Noibu test, branch or pull request.* |

   Write nothing else into the prompt.
5. **Confirm** in one sentence once the schedule exists: which report, when it runs, and that it appears in Cowork. Add one line: "To get it by email or in Teams, or to schedule another report, run that report and ask." If the schedule wasn't created (the approval was declined, or no scheduler is available), record "Schedule a recurring Noibu report" as a to-do for the user.
