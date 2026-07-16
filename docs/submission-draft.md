# Devpost submission draft

> Fill the [BRACKETS] after the build. Form fields per the hackathon page.

## Project name
FreightDesk — an AI exception desk for freight ops

## Category / track
Work and productivity

## Elevator pitch (short)
When a storm holds 40 containers, FreightDesk triages the flood, investigates the
impact, and drafts every customer email — escalating only what a human must see.

## Project description

**The problem.** Small freight brokers handle exception storms by hand. Every held
container needs triage (how bad?), investigation (which delivery windows break?),
and a customer email nobody has time to write. It's high-volume, formulaic-but-
judgment-laden work — and missing one means OTIF penalties and churned customers.

**What FreightDesk does.** Raw carrier messages (EDI feeds, emails, driver texts)
go in. GPT-5.6 turns each into a structured exception via structured outputs. A
tool-calling investigation agent — hard-capped at 5 steps — assesses blast radius:
new ETA, missed windows, dollar value at risk. It then drafts the customer email
and an internal action plan. High-confidence results wait for one-click approval;
low-confidence ones route to a human review queue. Duplicate feed deliveries are
suppressed by idempotency keys, so redelivered messages never double the work.

**Why the guardrails matter.** Most agent demos assume happy paths. Freight data
is hostile: feeds redeliver, messages arrive malformed, and an agent that retries
forever is an unbounded API bill. FreightDesk treats idempotency, bounded loops,
and confidence-based human escalation as product features — visible in the UI.

**How Codex accelerated the build.** [REQUIRED — real anecdotes: what Codex
scaffolded, a design decision it drove, time saved. Reference the milestones in
PRD.md. Example shape: "Codex built the FastAPI+SQLite core from the PRD in one
session, proposed hashing normalized message text for the idempotency key, and
wrote the pathological-input test that caught my loop-guard off-by-one."]

**How GPT-5.6 is used at runtime.** (1) structured-output triage of free-text
carrier messages into typed exceptions; (2) the investigation agent's reasoning
over function tools; (3) drafting customer comms and action plans.

**Prior art, disclosed.** The architecture pattern evolves my earlier public
case study of async exception handling (github.com/sechan9999/IntelTrans). No code
was reused; FreightDesk was built from scratch in Codex with a new product surface.

## Form fields checklist
- [ ] Demo video URL (public YouTube, <3 min): [LINK]
- [ ] Repo URL: https://github.com/sechan9999/FreightDesk (public, MIT)
- [ ] Codex `/feedback` Session ID: [PASTE — from the main build session]
- [ ] Track selection: Work and productivity
- [ ] Team members: [solo / list]
