# Steps 1–3: Noibu, the store, Shopify

Read this at step 1 and keep it open through step 3.

## Step 1 · Noibu connection

Call `noibu_get_current_user`.

- It succeeds: "Noibu is connected as <name or email>." Go to step 2.
- It fails: the connection isn't working. Say so in one line, ask the user to reconnect from the Connect prompt, and stop. Noibu can't be skipped.
- The user says they have no Noibu account: say the setup needs one and that their Noibu contact can create it, and stop.

## Step 2 · The store

1. If the user named a store or gave a UUID, resolve it. Otherwise list the stores the account can see, paging while a full page comes back.
2. **No stores:** the account has no store access. Say that, and that a Noibu administrator on their team can grant it. Stop.
3. **One store, or a store the user named:** ask one clickable question, header "Store": "Is <store> the store we're setting up?" Options "Yes, that's it" and "No, a different store".
4. **Two to five stores:** ask one clickable question, header "Store": "Which store are we setting up?" with the stores as options (four at most, most likely first); the user can type another.
5. **More than five stores, or stores across several companies:** ask the same question, "Which store are we setting up?", with no options, so the user types its address. Don't list the stores, name examples or describe the account. Resolve the reply, then confirm it with item 3's question.
   **"No, a different store":** ask "Which store are we setting up?" with no options, resolve the reply and confirm once more. If it isn't in their Noibu account, say so, and that a Noibu administrator on their team can add them. Stop there.
6. Record the store's name, UUID, `numId` and platform (`siteType`).
7. Call `noibu_get_company` once. Record the company name. If the company has other stores (a separate checkout store is common), mention them in one line; the rest of the setup is for the confirmed store.
8. Call `noibu_check_data_connection`. If the store isn't receiving data, say the Noibu script may not be installed or may have stopped sending, and that reports will be empty until it is. Record "Get the Noibu script sending data on <store>" as a to-do for their developer, and carry on: the connections are still worth setting up.

## Step 3 · Shopify

Everything in this step is a read. Nothing in the store changes.

1. **Platform.** `Shopify` or `Shopify Plus` as the store's platform means Shopify. If the platform is missing, check the business context in Noibu for it. If neither settles it, ask one clickable question, header "Platform": "Which platform is <store> built on?" Options "Shopify", "BigCommerce", "Salesforce Commerce Cloud", "Something else". Record it.
2. **Not Shopify:** "<store> runs on <platform>, so there's no store connection to set up." Go to step 4.
3. **Is the Shopify plugin here?** Find out by trying: look for the Shopify shop-information tool (`get-shop-info`) and call it. It is here when the call returns a shop.
   - Not here: ask one clickable question, header "Shopify": "Connect the Shopify plugin under Customize → Plugins → Shopify, so Cowork can read your store and build theme previews. Is it connected?" Options "It's connected" and "Skip for now".
   - "It's connected": look for the tool and call it again; never answer this from the earlier check. It returns a shop: carry on at item 4.
   - "It's connected" and the lookup and the call both still fail: record "Check the Shopify plugin shows Connected, then say *continue my Noibu setup* in a new chat" as a to-do for the user, and go to item 6.
   - "Skip for now": record "Connect the Shopify plugin" as a to-do for the user, and go to item 6.
4. **Is it this store?** Read the shop's information. Its primary domain or its `myshopify.com` domain must match the Noibu store, ignoring `www.`.
   - It matches: record the shop.
   - It is a different shop: ask one clickable question, header "Shopify": "The Shopify plugin is on <other shop>. Switch it to <store>'s shop?" Options "Yes, switch" and "Skip for now". On yes, switch with the plugin's own shop-switching tool and check again. If the right shop isn't offered, record "Connect the Shopify plugin with the account that owns <store>" as a to-do for the user and go to item 6.
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
