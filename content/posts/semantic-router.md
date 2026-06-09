---
title: The Semantic Router: Tiered Model Selection Across Cost, Latency, and Capability
subtitle: Once intelligence is rented and everyone has the same frontier labs, the model you pick for each sub-task stops being a default and becomes the product decision.
date: 2026-02-24
type: essay
tags: [routing, model-selection, inference-economics, llm-systems]
diagrams: [diagram-semantic-router.svg]
---

Here is a question that sounds trivial and isn't: which model should answer this request? Most teams never ask it. They wire up one model — usually the biggest one they can afford — and send everything to it, from "classify this into one of four buckets" to "reason across these twelve documents and tell me what's wrong." That works in a demo. It falls apart the moment you're paying for it at volume or waiting for it under a latency budget, because you are using a freight plane to deliver postcards and chartering a second one when the first is busy.

The opposite instinct — pick one small, cheap model and use it for everything — is worse. It's not frugal, it's reckless. The small model will confidently get the hard cases wrong, and in the domains I work in a confidently wrong answer is the expensive kind. So neither default survives contact with real traffic. The real answer is that *there is no single right model*. There's a right model per sub-task, and the job is to figure out which one, fast and cheaply, before you commit the expensive resource. That's the semantic router. I'd argue it's the most underrated component in any serious LLM system.

[[diagram:1]]

## Why "biggest model for everything" is an economic mistake

Everyone serious is renting the same two or three frontier labs. That's the defining fact of this moment, and it has a consequence people are slow to absorb: the model is no longer where you differentiate. If your competitor can rent the identical weights tomorrow, the weights aren't your moat. What you do *around* the model is.

And the thing you do around the model that most directly touches your unit economics is *deciding which model runs*. A reasoning model that thinks before it answers costs more — in tokens, in latency, in the case of on-prem in contention for a card you own — than a small model that pattern-matches. If 80 percent of your traffic is routing decisions, short extractions, and quick classifications, and you send all of it to a 32B reasoner, you've inflated your cost and latency by roughly the gap between the tiers, for no gain. The hard 20 percent justified the big model. The other 80 percent just paid for it.

## Why "one small model" is reckless

The mirror image fails for the opposite reason. Small models are excellent at what they're sized for and quietly catastrophic past it. They don't refuse the hard question — they answer it, fluently, wrong. In a chatbot that's an annoyance. In an underwriting pipeline or a document-intelligence flow feeding a regulated decision, it's a defect that ships. The cost you saved on inference you pay back, with interest, downstream.

So the failure modes are symmetric: oversize everything and bleed money and latency; undersize everything and bleed correctness. Routing is how you stop choosing between those two ways to lose.

## How the router actually works

The router I run is a sentence-transformer model that embeds the incoming sub-task and selects a tier across three axes at once:

- **Cost** — what does this call consume, whether that's tokens on a metered API or queue time on hardware I own?
- **Latency** — does this request have a budget a heavy model can't meet?
- **Capability** — does this task *actually require* reasoning or strong vision, or is it within reach of a small model?

The output is a routing decision: send this to the small text model, send that to the lightweight vision model, escalate this one to the heavy reasoner. A sentence-transformer is the right tool because it's cheap enough that the routing decision itself doesn't blow the latency budget it's trying to protect — the embedding-and-classify step costs a rounding error against the inference it's gating. A router that's expensive to run defeats its own purpose.

The principle underneath the mechanism: **send each sub-task to the cheapest model that can actually do it.** Not the cheapest model. The cheapest model that *can do it* — capability is a hard floor, and the router's first job is to never route below that floor. Cost and latency optimization only happen above it.

## Routing as the economic layer

Step back and the shape of the thing is clear. When intelligence becomes a utility — metered, rented, identical across competitors — the layer that decides *how much intelligence to spend on each unit of work* becomes the layer where your economics are won or lost. That's the router. It's the part of the system that turns "we have access to good models" into "we run good models profitably," and those are very different sentences.

This is why I treat model selection as a product decision, not a config value someone sets once and forgets. The choice of which model handles which request shapes your cost structure, your tail latency, and your error profile simultaneously. It deserves the same scrutiny as a pricing decision, because functionally it *is* one. Teams that bury it in a hardcoded default are leaving their margin and their reliability to an accident.

The model is the easy part — you can rent a great one this afternoon. Deciding, request by request, exactly how much of it to spend is the part that's actually yours to get right.
