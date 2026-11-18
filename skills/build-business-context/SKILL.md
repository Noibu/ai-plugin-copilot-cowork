---
name: build-business-context
description: "Builds a rich business-context Markdown file so Noibu skills reason with real context about the business and stop falling back on generic e-commerce assumptions. Use this skill whenever someone wants to create, set up, or improve their business context file, onboard a new store to Noibu, 'build my MD file', 'make a context file', capture company background for the AI, or asks why the analysis keeps getting their business wrong. Also trigger on looser phrasings like 'help the AI understand my business', 'document my store for the AI', 'what should I tell you about my company', or when a user is starting with Noibu and has no context file yet. Even if the user just says 'build the MD file' or 'set up context', use this skill. It does deep web research on the business, interviews the user about goals, money leaks, deployment process, and team setup, writes a clean Markdown file, then saves the context to Noibu for the domain."
---

# Build business context

Noibu's analysis is far more useful with real context about the business. Without it, analysis falls back on generic e-commerce assumptions and produces confidently wrong conclusions: flagging a product page as broken when it has a deliberate minimum-order quantity, or treating B2B abandonment like B2C abandonment. This skill captures that context once, in one Markdown file, so nobody has to spend an hour pushing back to get to the truth.

**The job:** produce one well-structured Markdown file by combining deep web research with a focused interview about things only the user knows. The output is a file, not a chat answer.

## When to use it

Use it to create, set up or improve a store's business context, to onboard a new store to Noibu, or when the user says the analysis keeps getting their business wrong.

Don't use it to analyse the store. That is `store-pulse`, `checkout-analysis`, `product-analysis`, `segment-analysis` or `tech-diagnosis`.

## Guardrails

- If Noibu tools aren't available, ask the user in one line to finish the Connect prompt, then stop.
- Reading data never permits a write. Never say the context is saved to Noibu without the tool's result.
- If a file this skill needs is missing, say which in one line and stop.
- **Grounded, never guessed.** Every claim in the file comes from research you can point to or from the user directly. Never print a researched fact (platform, payment processor, ownership) as confirmed; mark it `[CONFIRM]`.
- **Check first.** Resolve the domain and check for an existing context before any research. If one exists, get the user's go-ahead to regenerate before doing the work.
- **Research before the interview**, and report the findings before asking questions, so the user corrects bad research cheaply.
- **Calls only on request.** Ask whether the user records calls in Gong or Fellow, and pull transcripts only if they say yes and ask for it. Agree the scope of a large pull first; never silently read hundreds of calls. Attribute every transcript-derived fact to the call it came from.
- **Small batches.** Ask interview questions 3–4 at a time, never as one wall of questions.
- **The output is always a saved Markdown file**, never just a chat response, and it is always saved to Noibu at the end.
- Don't skip straight to writing the file.
- On every `noibu_*` call, pass `skill: "build-business-context"` and a short `skillStep`.

## Before you start

Run once: `ls references/research.md references/interview.md references/file.md`

## Workflow

One line per stage. Each names the file to open at that stage.

1. **Check for an existing context.** Resolve the domain and look for a context already saved for it: `references/research.md`, "Step 1".
2. **Setup.** Two quick questions: existing documents to fold in, and recorded calls: `references/research.md`, "Step 2".
3. **Research.** Deep web research on the business, then recorded calls if the user asked for them; report what was found and what couldn't be confirmed: `references/research.md`, "Step 3" and "Step 3b".
4. **Interview.** Ask the user, in small conversational batches, what research can't tell you: `references/interview.md`.
5. **Assemble.** Write the Markdown file, marking anything unconfirmed: `references/file.md`, "Assemble".
6. **Deliver.** Save the file and hand it over, with what to verify: `references/file.md`, "Deliver".
7. **Save to Noibu.** Store the finished context against the domain: `references/file.md`, "Save to Noibu".

### Test mode (fetch and save only)

This mode exercises only the two Noibu integration points, the fetch in step 1 and the save in step 7, without the research, calls, interview or assembly.

Use it only when the user explicitly asks for "test mode" (or "persist-only test") **and** uploads a Markdown file to use as the context. Never infer it.

1. **Run step 1 as written**: resolve the domain, keep both the UUID and the integer `numId`, and call `noibu_get_business_context`. Skip the regenerate question: if a context already exists, tell the user it will be overwritten and continue.
2. **Skip steps 2–6 entirely.** Use the uploaded file's contents exactly as uploaded. Don't edit, reformat or summarize them.
3. **Run step 7 as written**: call `noibu_insert_business_context` with the `numId` as `domainNumId` and the uploaded file's full contents as `fullContent`. Then confirm it is saved to Noibu for the domain.
