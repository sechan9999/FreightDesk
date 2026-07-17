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

Next steps are real carrier integrations (EDI 214/315, email, and webhooks), authenticated approval, email delivery, customer-specific communication preferences, and feedback from review outcomes to improve routing over time.

## Submission checklist

- Repository: https://github.com/sechan9999/FreightDesk
- Track: Work & Productivity
- Demo video: add public URL
- Team members: add names
- Codex session/feedback reference: add the applicable session ID