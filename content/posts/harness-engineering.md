---
title: "Harness Engineering: Why Verifiable Handoffs Beat Prompt Chains"
subtitle: The model picks the words. The harness decides which model to call, carries the state, writes to the system of record, and knows when to stop. That second thing is the product.
date: 2026-02-03
type: essay
tags: [harness, enterprise-ai, agents, verification, insurance]
diagrams: [diagram-harness-vs-chain.svg]
---

There is a demo every AI vendor gives this year. A submission goes in, a model reads it, three more models do something to it, and a clean recommendation comes out the other side. It looks like a system. It is usually a prompt chain — one model's output stuffed into the next model's input, repeated until someone calls it an agent.

I have built both. The difference is not subtle, and it is not academic. A prompt chain is brittle and amnesiac: every step is a fresh roll of the dice, nothing carries reliable state, and when step seven needs a fact that step two established, it re-derives it, guesses it, or quietly drops it. A harness is the opposite. It is the control surface that decides *which* model to call for *which* sub-task, holds state across many steps so step seven remembers what step two figured out, calls tools, writes to the system of record, and — the part nobody demos — knows when to stop, escalate, or commit. The model was always the easy part. Every serious team is renting the same two or three frontier labs. The harness is what you actually own.

[[diagram:1]]

## What a prompt chain forgets

Take an underwriting submission — the kind that runs through Vortic. A broker sends an email with a loss run attached, a schedule of values in a spreadsheet, and a cover note that contradicts both. Nine specialist agents need to turn that into an audit-ready decision memo in under thirty seconds.

A prompt chain handles this the way a relay team handles a baton when nobody agreed where the handoff zone is. The extraction step pulls a total insured value. The pricing step needs the *currency* of that value, which the extraction step saw but didn't pass along, so pricing assumes USD. The exposure step needs to know which buildings were already flagged as vacant, but that lived three prompts ago and is now outside the context window. Each step is individually plausible and collectively wrong. There is no place where the system holds *the submission* as a single, growing, inspectable object. There is only the last message.

This is the failure mode that matters in regulated work. It is never "the model wrote a bad sentence." It is "the model assumed two facts were consistent when nothing in the pipeline guaranteed they were."

## What a harness carries

The harness makes the submission a first-class object with state that persists across the whole run. Each agent reads from it and writes to it through a defined contract, not a free-text message. When the extraction agent records a total insured value, it records the currency, the source document, and the page it came from — because the contract requires those fields, and the handoff fails if they're missing. Step seven doesn't re-derive what step two knew; it reads it, with provenance attached.

That changes what each step can refuse to do. A few things a real harness does that a chain structurally cannot:

1. **Route by sub-task, not by accident.** Cheap, fast model for classification and extraction; a stronger model for the reasoning step that weighs conflicting exposure signals; a deterministic function — no model at all — for arithmetic and limit checks. The harness decides. A chain just forwards text to whatever it was wired to next.
2. **Carry state with provenance.** Every fact in the working memory is tagged with where it came from. That's what makes the final memo *audit-ready* instead of merely confident.
3. **Gate the writes.** The moment a step wants to commit something to the system of record — bind a quote, update a policy, post a number — the harness applies the verifier layer and the approval policy *before* the write, not after.
4. **Know when to stop.** When the documents disagree and the disagreement is material, the harness holds. It surfaces the conflict and asks for one decision. It does not manufacture a tidy answer to keep the demo moving.

That last point is the whole game. A helpful model, asked to reconcile a loss run that doesn't match the cover note, will produce a confident, plausible reconciliation — because that is what models do. A harness with a deterministic verifier checks: is this schema valid, is this number grounded in a source document, does this satisfy the business rule? Binary pass or fail. No prose, nothing to charm. When the verifier says no, the run stops at that step instead of laundering the error into the next one. That check — the hard check no LLM can talk its way past — is the line between a harness and a prompt chain wearing a trench coat.

## Recoverable, not just auditable

There is a second property a harness buys you that rarely makes the slide. Because state is explicit and each step is inspectable, a run is *recoverable*. When something fails at step six — a tool times out, a document is unreadable, a rule trips — you don't restart the whole pipeline and pray for a different dice roll. You see exactly which fact was missing, fix the one thing, and resume. A prompt chain has no such seam. It is one long breath; if it fails, you take it again from the top and hope.

This is the unglamorous engineering that separates the systems insurers actually deploy from the ones that win the bake-off and die in pilot. Guidewire, Duck Creek, Pega, the low-code platforms — they sell you the workflow boxes. The interesting work was never the boxes. It was the layer that makes a business intent true across systems that were never built to agree, and that refuses to lie when it can't.

So when someone shows me four models in a trench coat and calls it agentic, I ask one question: what happens when the documents disagree? If the answer is "it picks one," that's a prompt chain. If the answer is "it stops and shows me why," someone built a harness.

The model gets replaced next quarter. The harness gets sharper every run.
