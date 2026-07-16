# Devpost project story

> Paste into the Devpost "Project story" fields. Sections marked
> `[AFTER BUILD: ...]` MUST be replaced with what actually happened in the
> Codex build - judges reward specifics, and the repo is testable.

## Inspiration

Earlier this year I published a case study on asynchronous multi-agent exception
management for logistics ([IntelTrans](https://github.com/sechan9999/IntelTrans)) -
an architecture where a delayed container triggers an agent that investigates and
drafts mitigations without blocking the ingest path. It was a reference design with
simulated data. Build Week was the push to answer the obvious next question:
*could that architecture become a product a real freight broker would open every
morning?* Small brokerages (2-20 people) still triage exception storms by hand -
one weather event over the Port of Savannah means forty held containers, forty
impact assessments, and forty customer emails nobody has time to write.

## What it does

FreightDesk is an AI exception desk. Raw carrier messages - terse EDI feeds,
rambling emails, driver texts - go in. GPT-5.6 turns each into a structured
exception (type, severity, shipment, location) via structured outputs. A
tool-calling investigation agent, hard-capped at five steps, works out the blast
radius: the new ETA, whether the delivery window breaks, the dollar value at risk.
It then drafts the customer email and an internal action plan. High-confidence
results wait in an inbox for one-click approval; low-confidence ones route to a
human review queue. Duplicate feed deliveries are suppressed by idempotency keys,
and a malformed message lands safely in review instead of crashing anything.

## How we built it

The build ran from a written PRD with six milestones, executed in Codex with
GPT-5.6: FastAPI + SQLite core with structured-output triage, then the bounded
investigation agent with function tools (shipment lookup, ETA impact, port
conditions), then the confidence-routed mitigation composer, then the inbox UI,
then a seed-replay harness and pytest suite. [AFTER BUILD: 1-2 sentences on your
actual Codex workflow - e.g., one long main session vs. milestone sessions, and
one concrete decision Codex drove, like the idempotency-key design or the trace
storage format.] At runtime GPT-5.6 does three jobs: triage parsing, agent
reasoning over tools, and comms drafting. The demo replays 32 realistic seed
messages - including three exact duplicates, one garbage feed message, and a
coherent Savannah storm cluster with a $25k-penalty pharma escalation.

## Challenges we ran into

[AFTER BUILD: replace with your real top 2-3. Candidates you'll likely hit, based
on the prior architecture work: (1) making the "answer instantly, work in the
background" contract testable - background tasks that run inside the response
cycle hide the latency you're trying to prove; (2) keeping the agent loop honest -
an agent that can't parse a tool payload will happily retry forever, so the 5-step
cap needed a forced-finalize path, not just an exception; (3) confidence
calibration - deciding when a draft is safe to queue for one-click send vs. must
see a human.]

## Accomplishments that we're proud of

- Guardrails as product features, not afterthoughts: idempotent ingestion, a
  bounded agent loop, and confidence-based escalation are all *visible in the UI* -
  the duplicates-dropped counter and review queue are part of the demo, not buried
  in logs.
- A complete product experience in four days: not a chat wrapper, but an inbox a
  judge can click through end-to-end with seeded data.
- The demo's emotional arc is real ops: a storm floods the queue, and the pharma
  shipment with a hard Thursday delivery window and a $25,000 OTIF penalty clause
  surfaces to the top with a ready-to-send plan.

## What we learned

[AFTER BUILD: your genuine takeaways. Likely candidates: what Codex is best at
(scaffolding from a tight PRD, test generation) vs. where you steered; that
hostile data - redelivered feeds, malformed payloads - shapes agent architecture
more than the happy path does; that "draft + human approve" earns more trust than
auto-send.]

## What's next for FreightDesk

Real carrier integrations (EDI 214/315, email parsing webhooks), actual email
dispatch behind the approve button, per-customer tone profiles for drafts, and an
outcomes loop - did the mitigation hold? - feeding a weekly ops report. Longer
term: the review queue becomes training signal, so the confidence threshold adapts
to each team's risk tolerance.
