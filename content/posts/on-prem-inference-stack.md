---
title: On-Prem Inference for Regulated Buyers: QwQ-32B on Bare-Metal A100
subtitle: When a data-residency clause in a tier-one carrier contract is the binding constraint, the cloud is off the table — and the architecture gets a lot more interesting.
date: 2026-01-27
type: architecture
tags: [on-prem, inference, regulated-industries, model-serving, edge]
diagrams: [diagram-onprem-topology.svg]
---

The hardest constraint I work under isn't a latency budget or a token bill. It's a sentence in a contract. Tier-one insurers in Asia and the Gulf sign data-residency and data-handling clauses that say, in effect, *this data does not leave our perimeter*. Not "encrypt it in transit." Not "use a region in-country." It does not go over the wire to a model you don't control. Once you've read that clause, every clean architecture diagram that ends in an API call to a frontier lab is dead on arrival.

This is the part people building AI demos never hit. The model is rentable, identical for everyone, and improving on its own schedule. The thing that actually decides whether a regulated buyer can deploy you is whether the *inference happens inside their walls* — and that is an infrastructure problem, not a model problem. So I went and built the infrastructure. What follows is the on-prem inference stack I run for privacy-sensitive workloads, and the trade-offs you make when the cloud is genuinely not an option.

[[diagram:1]]

## Why residency is the real constraint, not the tech

It would be convenient if "can't use the cloud" were a technical limitation you could engineer around with a VPC and a compliance checkbox. It isn't. It's a *legal* boundary the customer's own lawyers drew, and they drew it because their regulator drew one upstream. An APS containing a claimant's full medical history, a KYC bundle, an underwriting file — these are exactly the documents the clause exists to protect. The buyer cannot grant you an exception even if they want to. So the design question stops being "which model is best" and becomes "what is the best model I can run on hardware that physically sits where the data is allowed to sit."

That reframing is the whole post. Everything below is downstream of it.

## The heavy tier: QwQ-32B on bare-metal A100 80GB

For the workloads that actually need to reason — multi-step analysis, the cases where a wrong-but-confident answer is worse than a slow one — I evaluated QwQ-32B on a bare-metal A100 80GB. Not a virtualized slice, not a shared tenancy: bare metal, because when the customer audits where their data lives, "a dedicated card in a box you can point to" is an answer that survives the audit. A virtual GPU abstracted across an orchestration layer you don't fully control is an answer that invites a follow-up question you don't want.

A 32B reasoning model is a deliberate pick. It's large enough to handle genuine chains of reasoning and small enough to fit, weights and KV cache, on a single 80GB card without sharding across nodes. Sharding is where on-prem stacks go to die — the moment your model spans two machines, your failure modes multiply and your latency gets hostage to interconnect you may not have. One card, one model, one box you can show an auditor. That constraint is a feature.

The heavy tier is the expensive tier, in every sense — capital cost, power, the latency of a reasoning model that thinks before it answers. So you do not send everything to it. Which is the entire reason the rest of the stack exists.

## The light tier: a three-node K3s + Ollama edge cluster

Most requests are not reasoning problems. They're classification, short extraction, a quick vision pass over a clean page. Putting those on the A100 is like chartering a freight plane to mail a letter. So underneath the heavy tier I run a three-node K3s cluster — lightweight Kubernetes, the kind that runs on hardware you can actually fit in a regulated buyer's rack — with Ollama serving two small models:

- **phi-3-mini** for the text-light tasks: routing decisions, short structured extraction, the boring high-volume work that makes up the bulk of real traffic.
- **Qwen2.5-VL-3B** for lightweight vision: a fast first look at a document, layout and modality classification, deciding whether a page even *needs* the heavy vision model before it gets one.

Three nodes, not one, for the unglamorous reason that on-prem hardware fails and the customer still expects answers. K3s gives me scheduling, restarts, and rolling updates across the three without dragging in the operational weight of full Kubernetes. The edge cluster is where the volume lives; the A100 is where the hard cases go.

## The trade-offs you actually make

Take the cloud off the table and three trade-offs move to the foreground:

1. **Cost is now capital, not consumption.** No per-token meter. You buy the A100 and the edge nodes once and amortize. This flips the economics of model selection: the marginal cost of a heavy inference isn't a line item, it's contention for a card you already own — so routing is about *throughput and queueing*, not dollars per call.
2. **Latency is bounded by your own iron.** No autoscaling to hide behind. If the A100 is busy, the next reasoning request waits. That's why the light tier matters so much — every request the edge cluster absorbs is one that doesn't queue behind a 32B model mid-thought.
3. **Capability is capped by what fits.** You don't get the latest trillion-parameter frontier model. You get the best thing that runs on hardware inside the perimeter. The engineering is in making a 32B reasoner and two small models *cover the surface area* that buyers assume requires a frontier API — and most of the time, with the right routing, it does.

None of this is hypothetical future-proofing. It's the stack that lets a carrier who legally cannot send a claimant's medical file over the wire still get document intelligence on it. The clause is the constraint. The hardware is the answer to the clause. The model is the easy part — it always was.

The cloud is a wonderful place to build things for people who are allowed to use it. My buyers aren't. So the interesting work moved into the rack.
