---
title: RLVR vs. RLHF: When Verifiable Rewards Beat Preference Labels
subtitle: Human preference labels taught the world's best chatbots to be agreeable. In regulated insurance, agreeable is worthless — what you need is a reward function that cannot be charmed.
date: 2026-02-10
type: essay
tags: [rlvr, rlhf, alignment, insurance-ai, reward-design]
---

RLHF — Reinforcement Learning from Human Feedback — built the assistants everyone now uses. A model generates two answers, a human picks the one they prefer, and you train a reward model on millions of those preferences until the model learns to produce outputs people like. It works beautifully for an enormous class of problems. It is also the wrong tool for the workflow I spend my days on, and understanding *why* is the most useful distinction in applied AI right now.

The alternative is RLVR — Reinforcement Learning with Verifiable Rewards. Same reinforcement-learning skeleton, completely different reward source. Instead of a human's preference, the reward comes from a verifier: a piece of code that checks whether the output is *correct* against a definition of correctness that exists outside the model. The narrow, valuable claim of this essay is that wherever correctness is objectively definable, a verifier beats a preference label — and in regulated insurance, correctness is defined by policy, schema, and business rules, not by what a reviewer happens to like.

## The failure mode RLHF can't escape

Human preference is a measure of *plausibility*, not *truth*. Ask a person to rate two insurance eligibility determinations and they will reliably prefer the one that reads better — more confident, better structured, more fluent. That preference is exactly the thing you do not want to optimize, because fluent and wrong is the single most dangerous output a regulated system can produce. A model that learned from human raters learns to be *persuasive*. In a domain where being persuasive and being correct are different axes, optimizing the first while ignoring the second is how you ship confident hallucinations into a compliance-bound process.

I have watched an LLM judge — a sophisticated one — get fooled by a well-formatted output that asserted a coverage limit nowhere in the source document. It read like a correct answer. A human rater would have preferred it. A schema validator and a fact-grounding check did not, because the asserted value simply was not in the document and no amount of fluency could put it there. That asymmetry is the entire argument. Preference labels reward the surface. Verifiers reward the substance, and they cannot be charmed.

## Why insurance is the ideal home for verifiable rewards

Most of the world is not like this. "Write me a warmer email" has no verifier — correctness genuinely is preference, and RLHF is the right tool. But regulated insurance sits in a rare band where "correct" is pinned down by external authorities:

- **Policy** defines what coverage applies, what's excluded, what conditions trigger eligibility. It is written down. It is checkable.
- **Schema** defines the exact shape every output must take for the downstream system of record. A field is valid or it is not.
- **Business rules** define the logic a compliance officer would apply by hand — limits, thresholds, mandatory disclosures.

None of these are matters of taste. Each one can be encoded as a deterministic check that returns true or false with no model in the loop. When you can do that, you don't *need* a human to express a preference — you have something stronger than preference. You have proof. On one regulated workflow, replacing the implicit "does this look good" loop with explicit verification moved accuracy from 78 to 94 percent on the same foundation model. I didn't change the model. I changed what the model was rewarded for being.

## Be fair: RLHF is still the right tool, often

I am not arguing RLVR is universally superior, and anyone who tells you that is selling something. RLVR only works where you can write the verifier. The moment correctness becomes genuinely subjective — tone, helpfulness, the thousand soft judgments of a general assistant — there is no check function to write, and human preference is the *only* signal that means anything. RLHF earns its place across the entire surface of open-ended language.

The honest framing is a spectrum, not a winner. On one end: tasks where correctness is objective and externally defined — math, code that must compile, schema-bound extraction, regulated determinations. RLVR dominates there because the reward is incorruptible. On the other end: tasks where correctness is preference — creative writing, conversation, style. RLHF owns that end because there is nothing to verify. Most real systems live somewhere in the middle and need both: verifiers for the parts that have a right answer, preference for the parts that don't.

The mistake is reaching for the preference-trained reflex in a domain that has a right answer. If your workflow is bound by policy and schema, and you are still tuning it on "which output looks better," you are leaving the strongest signal you have on the table — and worse, you are training your system to optimize the exact quality that hides its errors.

---

The reason verifiable rewards work in insurance is the same reason they're useless for poetry: insurance has a referee and poetry doesn't. Find the referee. If there's a definition of correct that lives outside your model — a policy clause, a schema, a rule a regulator wrote down — build the check, not the preference. A schema validator never gets impressed by a confident sentence. That's not a limitation. In a regulated workflow, it's the whole point.
