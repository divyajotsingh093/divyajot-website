---
title: "Orchestration vs. Coordination: What an Agentic Platform Actually Sells"
subtitle: An orchestrator calls a model and waits for a human to do the real work. A coordination layer makes a business intent true across systems — and tells you when it can't.
date: 2026-03-18
type: essay
tags: [coordination, orchestration, enterprise-ai, agents, bpmn]
---

Most things sold as "agents" right now are orchestration. A script fires, it calls a model, the model generates something, a dashboard renders it, and then a human opens the actual system of record and does the actual work. The agent summarised; the person executed. We have automated the narration and left the labour exactly where it was. That is automation with better grammar, and there is a lot of it being sold at enterprise prices.

Coordination is a different thing, and the gap is not a matter of degree. Orchestration sequences calls. Coordination makes a *business intent* true across systems that were never designed to agree with each other — and, just as importantly, refuses to declare it true when it can't prove it. The first is a flowchart that happens to call an LLM in one of its boxes. The second is the layer that turns "update the pricing" or "endorse this policy" into a safe, correct write across a CRM, a billing engine, and a policy admin system that each believe slightly different things about the same customer. One is a tool. The other is the product.

## The price-update that isn't one update

Take something an operations person says in four words: *update the pricing.* A rate change lands on a product line. Stated as a verb it sounds atomic. It is not.

An orchestrator's version: a model drafts the new rate sheet, posts it to a dashboard, and pings someone in pricing to go key it into the billing system. Helpful. The human still does the load-bearing part, and the system has no idea whether the change actually took.

The coordination version treats the intent as the unit of work. The new rate has to reach the policy admin system, the billing engine that generates invoices, and the CRM that quotes prospects — and they have to *end up agreeing*. Which is where it gets interesting, because they won't agree on their own. The billing engine keys customers by account number. The CRM keys them by a different ID and carries duplicates from a migration three years ago. Some in-flight policies are mid-renewal and shouldn't take the new rate until their term rolls. A few accounts have a negotiated override that the new sheet would silently stomp.

A coordination layer does the unglamorous middle: resolves which records across all three systems are *the same customer*, figures out which ones are eligible for the change now versus at renewal, applies the override carve-outs, and stages every write behind a policy gate so nothing commits until the whole set is consistent. Then it commits — or it holds the entire change and tells you why, rather than updating two systems out of three and leaving the third to be discovered by a customer's wrong invoice.

## The tell is what it does with ambiguity

Here is the test I use to tell the two apart, and it has nothing to do with model quality.

Feed the system an ambiguous case. An entity reconciliation across CRM and billing where two records *might* be the same customer — same company name, different address, no shared key. A helpful model will give you a confident, plausible answer: *yes, these are the same, here is the merged record.* It will sound right. It might even be right. But it cannot prove it, and it will not tell you that, because "I'm not sure" is not what a model trained to be helpful produces under pressure.

A coordination layer says: *I can't prove this yet.* It holds. It shows you the two records, the fields that match, the fields that don't, and the one missing join key that would settle it — and it asks for that single decision instead of manufacturing a merge that might fuse two real customers into one billing nightmare. The difference between those two behaviours is the difference between a system you can put near a general ledger and a system you can put near a slide deck.

This is why coordination is not "another flavour of BPMN." A BPMN engine — and the low-code platforms built on that lineage, Appian, Pega, Mendix — is declarative all the way down. You draw every branch at design time. Every decision a human anticipated becomes a box; every decision they didn't becomes an exception queue. That model assumes the world holds still long enough to be fully diagrammed. Enterprise data does not hold still.

## Declarative at design-time, emergent at runtime

The shape that actually works is split. At design time you declare *intent and constraints*, not the full branching tree: this is what "update the pricing" means, these are the systems of record, these are the invariants that must hold — no customer's records may disagree, no override may be silently overwritten, no write commits until the set is consistent. You do not enumerate every path, because you can't.

At runtime the path is *emergent*. The layer discovers the actual mess in front of it — the duplicate, the in-flight renewal, the missing join key — and works out the steps live, against the constraints you declared, calling models where judgment is needed and deterministic checks where proof is needed. When the constraints can be satisfied, it acts. When they can't, it stops at exactly the constraint that failed and surfaces it. A drawn flowchart can't do this; it can only run the branches someone already imagined and dump everything else into a queue for a human — which is precisely the labour we claimed to automate.

That is the line. Orchestration moves outputs around and waits for a person to make the intent true. Coordination makes the intent true itself, across systems that disagree, and has the discipline to stop when "true" can't yet be proven.

A confident wrong answer is the easiest thing in the world to ship. The product is the system that knows the difference between *I did it* and *I can prove I did it* — and will only say the first when it means the second.
