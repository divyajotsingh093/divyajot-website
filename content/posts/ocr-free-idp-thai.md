---
title: OCR-Free Document Intelligence in Mixed Thai-English
subtitle: A production pipeline for Attending Physician Statements that had to read clean hospital printouts and a doctor's handwriting in the same breath — and got to 94 percent on real documents.
date: 2025-12-15
type: case-study
tags: [document-intelligence, vision-models, ocr-free, healthcare, production]
---

The document that broke my faith in OCR was an Attending Physician Statement from a private clinic in Thailand. Half of it was printed Thai, half was handwritten English shorthand from a doctor who was clearly not writing for a stranger to read, the date was in the Buddhist Era, and a stamp sat diagonally across the patient name. A traditional OCR-plus-rules pipeline looks at that page and produces confident garbage: a string of characters that is locally plausible and globally meaningless, which your downstream rules then dutifully parse into the wrong record. This is the Generali Thailand IDP pipeline — and it's the project that convinced me OCR-free vision models aren't a research curiosity, they're the right tool for messy multilingual documents.

The job: production document intelligence over APS forms for an insurer, in mixed Thai-English, at extraction accuracy a carrier will actually sign off on. We got to 94 percent on *real* documents — not a curated benchmark, the actual noisy intake — and the customer signed. Here's the war story, because the number at the end is the least interesting part of how we got there.

## Two document classes that share almost nothing

The first thing that breaks a naive pipeline is the assumption that "an APS" is one kind of thing. It is two, and they have almost nothing in common.

- **Public-hospital OPD bundles.** Relatively clean, printed, structured — multi-page outpatient department records with consistent-ish layouts. The kind of document where you can almost imagine OCR working, right up until the Thai diacritics and the Buddhist-Era dates show up.
- **Handwritten private-clinic forms.** A single sheet, often hand-filled, sometimes a photocopy of a fax of a scan, with handwriting that ranges from legible to forensic. There is no layout to rely on. There is barely a form.

A pipeline tuned for one is actively wrong on the other. The clean OPD bundle rewards structure-based extraction; the handwritten form punishes it, because the structure it's keying off of doesn't exist. Any honest system has to handle both *as different problems* while emitting the same clean output schema. That tension — one output contract, two wildly different inputs — is the spine of the whole build.

## Why OCR-free beats OCR-plus-rules here

The old pipeline is OCR first, then rules on top of the OCR text. The fatal flaw is that the two stages can't talk. OCR makes its character-level guesses with no idea what the document *means*, and by the time your rules run, the visual context — the layout, the proximity of a label to a value, the fact that this smudge is obviously a date because of where it sits — has been thrown away. You're parsing a lossy transcript of the page instead of reading the page.

An OCR-free vision model collapses those two stages into one. Qwen2.5-VL-72B looks at the *image* and extracts directly to structured fields, with the visual context intact the entire time. It can use the fact that a number sits in the date box to read an ambiguous digit, the way a human does. For clean printed Thai it's reading text; for the handwritten clinic form it's doing something closer to interpretation — and crucially, it's doing both with the layout still in front of it instead of discarded by an OCR pass that ran blind. For messy multilingual documents this isn't a marginal improvement. It's a different category of approach, and it's the only one that survived our real intake.

## Buddhist-Era dates: a research project hiding in a field

Every APS has dates, and in Thailand those dates are in the Buddhist Era — 543 years ahead of the Gregorian calendar. This sounds like a one-line conversion and is not. The document doesn't announce its calendar. A year written as 2566 is unambiguously Buddhist Era, but a two-digit year, or a date near a century boundary, or a field where someone has *already* converted and someone else hasn't, turns a subtraction into a judgment call. Get it wrong and you've misdated a medical event by 543 years, which is exactly the kind of error that's invisible until it's catastrophic in a claims decision. Handling BE dates correctly — knowing when to convert, when a value is already Gregorian, how to disambiguate — was a research effort in its own right, not a formatting step.

## Three prompt versions, hardened against real noise

You do not write the prompt once. We went through three iterative versions, and the iterations were driven entirely by real-world OCR noise — the stamps over text, the photocopy artifacts, the handwriting that the first prompt confidently misread.

1. **Version one** worked on the clean documents and fell apart on the messy ones — the classic demo-grade prompt that meets its first real photocopy and folds.
2. **Version two** added explicit handling for the failure modes the real intake surfaced: ambiguous dates, occluded fields, the two-document-class split.
3. **Version three** was the hardened one — the prompt that had been beaten against enough genuinely bad documents that its failures were rare and, when they happened, sensible rather than wild.

That progression is the actual work. Production scars, not demos. The 94 percent isn't a number we designed for; it's a number that fell out of three rounds of watching the model fail on real pages and closing the gaps it showed us.

## What the number means

94 percent extraction accuracy on real documents, customer signed. The signature matters more than the percentage — it means the accuracy held on the carrier's own messy intake, not a clean test set, against a bar an insurer was willing to put their name on. We got there not by finding a better model in the abstract but by taking an OCR-free vision model seriously as a system: two document classes handled as two problems, a calendar that demanded real research, and a prompt hardened over three versions against the specific ways real documents are awful.

The OCR-plus-rules pipeline reads a transcript and hopes. The vision model reads the page. On a handwritten Thai-English APS with a Buddhist-Era date and a stamp across the name, that difference is the whole game.
