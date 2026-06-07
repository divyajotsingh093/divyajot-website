# Cross-post variants — The System of Action & Coordination

Companion adaptations for manual posting. Not rendered to the site. The canonical
long-form essay lives in `system-of-action.md`.

---

## LinkedIn

A "System of Coordination" is a specific piece of engineering, not a vibe. Worth defining it precisely, because the term is getting thrown around.

It sits between a business request and the systems that actually hold the data — the CRM, the billing system, the ERP, the warehouse. Its job: take one instruction stated in business terms and turn it into a correct, reversible action across those systems. Four mechanisms do that work.

1. Entity resolution. The same customer is a different ID in every system. Coordination holds the join keys — account reference, contract number — so a record in Billing can be matched to its counterpart in the ERP. Skip this and every cross-system answer is a guess.

2. Tool selection and sequencing. Each system speaks a different protocol — REST, SOAP, SQL, SAML. The layer picks the right call for each sub-task and orders them, so step seven can use what step two retrieved.

3. State across steps. It carries context through a multi-step task instead of treating every call as amnesiac.

4. Verification before write. Deterministic checks run before anything commits, and anything irreversible stops for a human approval.

Now put it together. I asked it: "Close the books for last month, and schedule a close on the 1st of every month."

It didn't return "done." It returned three blockers, each with evidence:

- A credit note created on a return and never applied — one approval to clear it.
- Two overdue receivables, real and not errors, that need a human call: pursue, defer, or write off.
- A batch of cancelled orders it refused to clear, because there was no join key between the cancellation records and the invoices. It couldn't prove none were still open, so it said so instead of assuming.

The fix was the join: "the reference number is the key here too." Once the records matched across systems, the reconciliation went from plausible to proven, and the close completed behind a single approval.

That is the whole value. Not an agent that closes your books — an agent that knows which records it can't yet match, and stops there. The model was the easy part. The coordination is the product.

---

## X / Twitter (thread)

1/
Operators don't think in APIs. They think in verbs.

Check the balance. Update the pricing. Close the books.

The work nobody wants: making those verbs land across Snowflake, the CRM, Billing, Core systems, the ERP — each a different system of record. That's a System of Action & Coordination.

2/
One business command goes in. Underneath, the coordination layer:

→ understands the context
→ chooses the right tool from a mess of REST/SOAP/SQL/OAuth/schemas/rate limits
→ applies policy + approval before it writes

Same intent. Different systems. One layer.

3/
The demo that makes the point:

"Close the books for last month, and schedule a close on the 1st of every month."

It came back 🔴 blocked. On purpose.

4/
Not "done." Not a confident wrong summary. It pulled cross-system evidence and surfaced 3 things:

• a credit memo created but never applied
• 2 overdue receivables needing a human call
• cancelled contracts it refused to wave through

5/
Why refuse the cancelled batch? No direct join key between Billing account IDs and ERP records. It couldn't *prove* none still carried open revenue, so it didn't pretend.

It even caught a rounding mismatch the size of a coffee.

6/
Then the unlock, one line:

"The account reference is the key for Billing too, like the CRM."

Cross-system entity resolution. The join that makes a reconciliation trustworthy instead of plausible.

7/
A system that stops, shows its evidence, and asks for one approval beats ten that cheerfully close your books on data they never verified.

The model was never the hard part. The coordination layer is.

One command. Many systems. Approvals.
