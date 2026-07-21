# Devpost submission: FreightDesk

## Project name

FreightDesk

## Elevator pitch

FreightDesk turns a flood of carrier updates into a prioritized freight exception queue, customer-ready drafts, and a focused human-review list.

## Project description

### The problem

During a port disruption, a small freight team can receive dozens of EDI updates, emails, and texts in minutes. Every update creates a decision: identify the shipment, estimate the customer impact, decide whether a response is needed, and write it. Duplicate deliveries and malformed carrier feeds make that work even harder.

### The solution

FreightDesk is an exception desk for freight operations. It accepts carrier-style messages, classifies the exception, assesses impact, prioritizes the work, and prepares a customer communication plus an internal action plan.

Operators work from three clear outcomes:

- **Ready for approval** for high-confidence cases with a prepared response.
- **Human review** for ambiguous, malformed, or low-confidence cases.
- **Activity log** for a visible record of received, deduplicated, routed, and sent events.

The Savannah storm replay demonstrates the complete workflow with 32 realistic messages, including three duplicate deliveries, malformed input, and a temperature-sensitive pharma shipment with a missed delivery window and $25,000 at risk.

### What makes it reliable

FreightDesk treats operational guardrails as product features. It suppresses duplicate messages through normalized-message idempotency, limits investigation to five steps, routes uncertainty to humans, and safely sends malformed data to review. The operator always has the final approval before a customer communication is marked sent.

The demo engine is deterministic by default, so judges can replay the exact scenario without an API key or network-dependent output. A live OpenAI triage path is available only through explicit environment configuration.

### How we built it

We built FreightDesk as a tested Streamlit product with structured triage, bounded investigation, impact assessment, draft composition, and confidence routing. Codex accelerated the product build and hardening work, including the replay harness, regression tests, and persistent state that makes the live demo resilient to Streamlit reruns and browser refreshes.

### What we learned

Operational AI earns trust by making uncertainty visible. The useful outcome is not an agent that always acts; it is a system that handles the routine work quickly and reliably surfaces the decisions that still need a person.

### What's next

Authenticated approval, delivery, customer communication preferences, batch feed ingestion, and outcome-driven adaptive routing already shipped. Next: real carrier network connections (EDI VAN integrations, inbound webhook endpoints), SSO-backed operator identity, and analytics on whether chosen mitigations held.

## Submission checklist

- Repository: https://github.com/sechan9999/FreightDesk
- Track: Work & Productivity
- Demo video: add public URL
- Team members: add names
- Codex session/feedback reference: add the applicable session ID
## Judge access and testing instructions

**Paste this into Devpost's private judge-access field:**

No account or API key is required. Open the live app at https://freightdesk.streamlit.app/.

1. In the sidebar, sign in as an operator: any name + demo PIN `2468`. Approvals are authenticated, so **Approve & send stays disabled until this step**.
2. Click **Reset desk** to start from a clean state.
3. Click **Replay the Savannah storm (32 messages)**.
4. Open the top red Inbox item, `TRK-40045-A`, to inspect its assessment, bounded agent trace, impact chain, and the customer draft addressed to the account on file.
5. Click **Approve & send** - the activity log records the approving operator and the delivery mode (mocked here; real SMTP when configured).
6. Open **Disruption map** to see exceptions grouped by disruption source with value at risk per cascade.
7. Open **Human review** to see ambiguous or malformed messages safely routed to an operator.
8. Click **Replay again (all duplicates)** to verify that the duplicate counter rises without creating new work.

The hosted demo uses a deterministic engine, so the same scenario runs without external service credentials. Source and local setup are available at https://github.com/sechan9999/FreightDesk.