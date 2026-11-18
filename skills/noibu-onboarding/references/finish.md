# Steps 7–8: business context, the check, and the close

Read this at step 7 and keep it open to the end.

## Step 7 · Business context

The business context is what keeps every Noibu report grounded in how this business works. It lives in Noibu, and every report reads it from there, so a context saved later is picked up on its own.

1. **Look first.** Read the store's business context from Noibu. Never print its contents.
   - One is saved: "Noibu has a business context for <store>, saved <date>." Go to step 8.
2. **None saved:** ask one clickable question, header "Context": "Did Noibu give you a business context file for <store>?" Options:
   - "Yes, I have the file"
   - "No, build one after setup"
   - "Skip for now"
3. **"Yes, I have the file":** ask the user to attach it, or paste its contents, in one line. Read it and confirm it is for this store (its name or address appears in it). If it is for a different store, say which and ask again. Then save it to Noibu with the store's `numId` and the file's full contents, unchanged. Read the context back from Noibu to confirm, and say "Saved your business context to Noibu." If the file can't be read or the save fails, say so in one line and record "Save the business context file to Noibu" as a to-do for the user.
4. **"No, build one after setup":** "No problem: I'll offer to build it as soon as setup is done." Record that the user wants one built. Don't start it here.
5. **"Skip for now":** "No problem: your reports run without it, and they'll use it as soon as it's saved in Noibu." Record "Add a business context (your Noibu contact can provide one, or ask me to build it)" as a to-do for the user.

## Step 8 · Check everything

Re-check each item now; don't rely on what an earlier step said. Report one line each, with ✅ (done), ⚠️ (works, something is pending) or ❌ (not done). Leave out a line that doesn't apply to this store.

- **Noibu:** the sign-in check succeeds, and whether the store is receiving data.
- **Shopify** (Shopify stores): the plugin returns the matching shop; or the to-do from step 3.
- **Theme previews** (Shopify stores), by where step 3 found they go: through the Shopify plugin (✅ when theme write access is still listed), through Noibu (✅ when Noibu lists the store's themes), or nowhere yet (⚠️ with the to-do). When they go through the Shopify plugin, don't check or mention Noibu's theme access.
- **Scheduled report:** the scheduled prompt from step 4 exists, with its report and when it runs; or the to-do.
- **Code host:** the proving read succeeds and the chosen repository is readable; ⚠️ "read only" for Azure DevOps; or the to-do from step 5.
- **Release reporting:** ✅ when Noibu's release list shows a release from the component. ⚠️ with the pull request's link and its state (open or merged), or "pipeline file handed to your developer", when none has arrived yet. Otherwise the to-do.
- **Business context:** ✅ when Noibu returns one for the store. ⚠️ "to be built next" when the user asked for that. Otherwise the to-do.

Then, under the line "Still to do", list every to-do with who needs to do it: the user, their developer or agency, their Microsoft 365 administrator (for a plugin they can't install), a Shopify store owner, or their Noibu contact. With nothing left, write "Everything is in place." and no list.

## The close

Step 8's reply is plain text and ends the setup. No clickable question follows it, because the checklist above it would not be shown.

After the list, two or three lines: what is connected, when the scheduled report runs, and where the business context lives (in Noibu) or that it is still to come. If a pull request is open, add that *check my releases* confirms the first release once it is merged.

Then one last line naming what to ask for next: "Next, ask me to build your business context, check the store's last 24 hours, analyze checkout, find errors and slow pages, or find A/B test ideas." Leave out "build your business context" when one is saved. If the store isn't receiving data, leave this line out altogether.
