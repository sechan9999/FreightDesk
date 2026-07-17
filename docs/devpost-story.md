# FreightDesk: AI exception management for freight operations

## Elevator pitch

When a port disruption floods a broker's inbox, FreightDesk turns raw carrier updates into a prioritized exception queue, customer-ready drafts, and a focused human-review list.

## Inspiration

Freight operations rarely fail because a team lacks data. They fail because a small team has too much of it at the worst possible moment. One storm can create dozens of carrier updates: terse EDI notices, broker emails, SMS alarms, and duplicate feed deliveries. Each message demands the same urgent questions: Which shipment is this? What is the customer impact? Does it need a response now?

FreightDesk makes that first pass fast, visible, and reviewable.

## What it does

FreightDesk is an exception desk for freight operations. It accepts carrier-style messages, classifies the exception, assesses operational impact, prioritizes the work, and prepares a customer communication plus an internal action plan.

The operator sees three outcomes instead of an unstructured inbox:

- Ready for approval: high-confidence cases with a prepared response.
- Human review: ambiguous, malformed, or low-confidence cases that need judgment.
- Activity log: a concise record of what the system accepted, suppressed, routed, and sent.

The Savannah storm replay demonstrates the complete flow with 32 realistic messages. It includes duplicate deliveries, malformed input, and a temperature-sensitive pharma shipment whose delivery window is missed and carries a $25,000 penalty risk.

## Why it matters

FreightDesk does not treat reliability as invisible plumbing. The safeguards are part of the product experience:

- Idempotency prevents redelivered carrier messages from becoming duplicate work.
- A bounded five-step investigation keeps reasoning predictable.
- Confidence-based routing keeps uncertain decisions with a person.
- Malformed messages fail into review instead of taking down the desk.
- Persistent demo state survives Streamlit reruns and browser refreshes, so the operational picture remains intact during a live walkthrough.

The result is not automatic customer communication without oversight. It is a smaller, prioritized decision queue where operators retain the final send action.

## How we built it

FreightDesk was built as a tested Streamlit product with a deterministic demonstration engine. The engine models the full agent workflow: structured triage, bounded investigation, impact assessment, customer-draft composition, and confidence routing. This makes the live demo repeatable, including its duplicates and failure cases.

Codex accelerated the build and hardening work, including the replay harness, guardrail tests, and persistent state for a reliable live demo. The project can also enable a live OpenAI triage path only through explicit environment configuration; demo mode stays deterministic by default.

## Challenges we ran into

The interesting problem was not producing a draft. It was deciding when not to trust one. Freight messages can be incomplete, duplicated, or malformed, so the workflow needed to make uncertainty operationally useful rather than hide it. That led to three design constraints: suppress repeats, cap investigation work, and expose low-confidence cases in a dedicated human-review queue.

We also treated demo reliability as a product requirement. A judge should be able to refresh the page, replay the scenario, and see the same decision flow without relying on a network call or a lucky model response.

## Accomplishments we're proud of

- A complete operator workflow, from raw message to reviewed customer draft.
- The $25,000-risk pharma exception reliably rises to the top of the storm queue.
- Failure modes are visible and safe: duplicates are counted, malformed data is routed to review, and no message is silently discarded.
- A repeatable live demo with automated coverage for replay, duplicate suppression, terminal states, persistence, and demo-mode safety.

## What we learned

For operational AI, trust is earned at the boundaries. The useful product is not a system that always acts; it is a system that makes the routine work easy and makes uncertainty unmistakable.

## What's next

The next step is to connect real carrier channels: EDI 214/315 feeds, email ingestion, and webhook events. From there, FreightDesk can add authenticated approval, real email delivery, customer-specific communication preferences, and feedback from review outcomes to improve routing over time.

## Submission details

- Repository: https://github.com/sechan9999/FreightDesk
- Track: Work & Productivity
- Demo: use the Savannah storm replay in the running Streamlit app