# FreightDesk Build Checklist

**Purpose:** Execution checklist for building FreightDesk from [SPEC.md](SPEC.md).
Follow milestones in order. Do not skip verification gates. Each milestone should
leave the repository in a working state.

## Build Principles

- Keep implementation aligned with SPEC.md — where this checklist and SPEC.md
  disagree, SPEC.md wins.
- Prefer small, testable modules.
- Do not expand scope beyond the defined MVP (PRD §4 non-goals).
- Every AI capability must have:
  - clear input/output contract
  - failure handling
  - traceability
  - human escalation path
- Keep agent behavior bounded and observable.

---

## Milestone 0 — Project Foundation

### Tasks
- [ ] Create project structure according to SPEC §1.
- [ ] Configure Python environment.
- [ ] Add dependency management (`pyproject.toml` or `requirements.txt`).
- [ ] Add environment configuration (`config.py`, `.env.example`).
- [ ] Create SQLite initialization (`db.py` executes `schema.sql`; sets
      `PRAGMA foreign_keys = ON` on every connection).
- [ ] Add logging configuration.
- [ ] Add test framework setup (pytest; LLM client injectable/mockable).

### Verification Gate
```bash
pytest
```
Expected: test framework executes successfully; application imports without errors.

---

## Milestone 1 — Data Models and Ingestion

**Goal:** Accept raw carrier messages and convert them into structured exceptions.

### Tasks

Database
- [ ] Apply `schema.sql` (already validated — see SPEC §2): messages, exceptions,
      assessments (incl. trace storage), drafts.
- [ ] Idempotency via `messages.hash` (SHA-256 of normalized raw).
- [ ] Mock shipment data lives in `tools.py` (`MOCK_SHIPMENTS`), not a DB table (SPEC §4b).

API
- [ ] Implement `POST /exceptions`.
- [ ] Validate request schema (422 on bad channel / blank raw).
- [ ] Generate idempotency key.
- [ ] Reject duplicate ingestion safely (202 with `duplicate: true`, original id).

Triage
- [ ] Implement GPT structured extraction (SPEC §4a strict schema).
- [ ] Extract: exception type · severity · shipment ref · location · summary ·
      customer impact.
- [ ] Failure policy: LLM error/refusal → UNKNOWN → review queue. Never raise.

### Verification Gate
Send identical carrier message twice.
Expected: first request creates exception; second is marked duplicate;
no duplicate AI processing occurs.

---

## Milestone 2 — Investigation Agent

**Goal:** Determine operational impact using bounded tool calls.

### Tasks

Implement tools (`tools.py`):
- [ ] `lookup_shipment()`
- [ ] `eta_impact()`
- [ ] `port_conditions()`

Implement agent (`agent.py`):
- [ ] Create investigation loop (SPEC §4b algorithm).
- [ ] Store tool traces.
- [ ] Enforce maximum 5 tool rounds.
- [ ] Add forced finalization (`tool_choice="none"` after exhaustion).
- [ ] Downgrade confidence after exhaustion (cap at 0.5 → routes to review).
- [ ] Tool dispatch errors become trace results, never exceptions.

### Verification Gate
Agent receives a shipment delay.
Expected: agent calls appropriate tools; completes within step limit;
trace is persisted; failure does not crash workflow.

---

## Milestone 3 — Mitigation Composer

**Goal:** Generate customer communication and internal action plans.

### Tasks
- [ ] Generate customer email draft (calm tone, concrete next step, new ETA,
      never promise compensation, ≤180 words).
- [ ] Generate internal mitigation plan.
- [ ] Include shipment facts, impact assessment, recommended actions.

Confidence routing (in pipeline, threshold 0.7):
```text
confidence >= threshold  →  ready_for_approval
confidence <  threshold  →  needs_human_review
```

### Verification Gate
High confidence: appears in approval inbox.
Low confidence: appears in human review queue.

---

## Milestone 4 — Workflow Pipeline

**Goal:** Connect all components into an asynchronous exception workflow.

### Tasks

Implement states (matches `schema.sql` status enum; ingestion itself is recorded
as a `messages` row — there is no separate `received` status):
```text
triaged → investigating → drafting ─┬─→ ready_for_approval → sent
                                    └─→ needs_human_review → sent | dismissed
```

- [ ] Implement pipeline orchestration (single writer of status).
- [ ] Handle failures safely (any exception → needs_human_review; worker survives).
- [ ] Persist state transitions.
- [ ] Persist traces.
- [ ] Bound concurrency (semaphore ≤ 8).

### Verification Gate
Replay full workflow.
Input: carrier message.
Output: structured exception · investigation result · mitigation draft · approval state.

---

## Milestone 5 — Inbox UI

**Goal:** Create the broker-facing control surface.

### Tasks

Display:
- [ ] Exception list (tier-sorted: red → orange → green).
- [ ] Severity ranking.
- [ ] Confidence score.
- [ ] Customer draft (editable).
- [ ] Internal action plan.
- [ ] Trace information.
- [ ] Review queue.

Highlight:
- [ ] Duplicate count.
- [ ] Critical shipment.
- [ ] High-risk exceptions.

### Verification Gate
A user can: view exceptions · inspect AI reasoning · approve drafts ·
send uncertain cases to review.

---

## Milestone 6 — Demo Harness

**Goal:** Create a deterministic judge-ready demonstration.

### Tasks

Seed dataset — ✅ already in repo (`data/seed_messages.jsonl`, spec in `data/SEED_SPEC.md`):
- [x] 32 realistic messages.
- [x] 3 exact duplicates.
- [x] 1 malformed message.
- [x] Savannah storm scenario.
- [x] Pharma shipment escalation ($25,000 penalty risk).

Replay script:
- [ ] Load messages (`seed.py --rate`).
- [ ] Execute pipeline.
- [ ] Populate inbox.

### Verification Gate
Demo must show:
1. Exception storm enters system.
2. Duplicates are removed.
3. AI identifies highest-risk shipment.
4. Agent investigates impact.
5. Customer response is drafted.
6. Human approval remains required.

---

## Testing Checklist

Unit tests
- [ ] Schema validation (constraint probes from SPEC §2).
- [ ] Idempotency.
- [ ] Database operations.
- [ ] Tool functions.
- [ ] Confidence routing.
- [ ] Pipeline transitions.

Integration tests (LLM mocked until milestone 6)
- [ ] API ingestion flow.
- [ ] Agent execution (incl. pathological always-erroring tool fixture).
- [ ] Draft generation.
- [ ] Review routing.

Replay test
- [ ] Full 32-message scenario succeeds (real GPT-5.6; metrics match SEED_SPEC).

---

## Final Submission Checklist

Product
- [ ] Demo starts reliably.
- [ ] Main user story is obvious.
- [ ] AI value is visible.
- [ ] Human control is visible.

Technical
- [ ] Agent limits documented.
- [ ] Failure handling demonstrated.
- [ ] Traceability available.
- [ ] Tests passing.

Devpost
- [ ] Architecture screenshot added.
- [ ] Demo video recorded (<3 min, public, narrates Codex + GPT-5.6).
- [ ] Codex workflow documented (+ `/feedback` session ID captured).
- [ ] Lessons learned completed (`docs/devpost-story.md` brackets filled).
- [ ] Future roadmap completed.

---

## Commit Discipline

Before committing:
```bash
git status
pytest
git diff
```

One commit per milestone, conventional format, e.g.:
```bash
git commit -m "feat: milestone 2 - bounded investigation agent"
```

> Execution note: run this checklist milestone-by-milestone in Codex and mark each
> verification gate complete — no broad multi-milestone changes.
