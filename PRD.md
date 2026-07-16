# FreightDesk — Product Requirements Document

> Purpose: the single source of truth to hand to Codex. Work through the milestones
> in order; each maps to one focused Codex prompt. Keep the whole build in ONE main
> Codex session where possible — its `/feedback` session ID goes in the Devpost form.

## 1. Problem & audience

Small freight brokers / shipper ops teams (2–20 people) triage carrier exceptions
by hand. One weather event = dozens of held containers = hours of repetitive
triage + customer emails. Missed ones become OTIF penalties and churned customers.

**User**: the ops coordinator working the exception inbox.
**Job to be done**: "When carrier noise floods in, tell me what matters, what it
affects, and draft what I'd send — I'll approve or fix."

## 2. Scope (4-day build)

### F1 — Ingestion & triage
- `POST /exceptions` accepts `{channel, raw}` (raw = free-text carrier message)
- GPT-5.6 with **structured outputs** parses raw → `Exception`:
  `{shipment_ref, exception_type, location, severity (1-5), reported_at, summary}`
- `exception_type` enum: PORT_DELAY, CUSTOMS_HOLD, VESSEL_ROLLOVER, CHASSIS_SHORTAGE,
  WEATHER_DIVERT, REEFER_TEMP, ACCIDENT, MISSED_CUTOFF, UNKNOWN
- **Idempotency**: SHA-256 of normalized raw text; duplicates return 202 with
  `duplicate: true`, no reprocessing
- Unparseable input → `UNKNOWN` + straight to review queue (never crash, never loop)

### F2 — Investigation agent
- Given a triaged Exception, run a GPT-5.6 agent with **function tools**:
  `lookup_shipment(ref)` → carrier, lane, delivery_window, order_value (mock DB)
  `eta_impact(ref, delay_hours)` → new_eta, window_missed: bool
  `port_conditions(location)` → congestion, weather (mock)
- **Bounded loop: max 5 tool-call rounds**, then force-finalize with what it has
- Output: `Assessment {impact_summary, window_missed, affected_value, confidence (0-1),
  recommended_action}`

### F3 — Mitigation composer
- GPT-5.6 drafts: (a) customer email (tone: calm, concrete, next step + new ETA),
  (b) internal action plan (bullet list)
- `confidence >= 0.7` → status `ready_for_approval`; else → `needs_human_review`
- "Send" is a mock (log + status change) — no real email integration in scope

### F4 — Inbox UI
- Single-page app (Next.js preferred; Streamlit acceptable fallback)
- Views: triage list (severity-sorted, status chips) · exception detail
  (raw msg, parsed fields, agent reasoning trace, drafted email — editable,
  Approve & Send button) · review queue · metrics header (open / mitigated /
  escalated / duplicates dropped)
- Live-ish updates (poll every 2s is fine)

### F5 — Demo & test harness
- `seed.py` replays `data/seed_messages.jsonl` against the API with configurable rate
- pytest: triage parses 3 fixture messages; duplicate suppressed; agent loop
  terminates ≤5 rounds on a pathological fixture; confidence routing works

## 3. Non-goals

Real EDI parsing, real email sending, auth/multi-tenant, carrier API integrations,
mobile, persistence beyond SQLite.

## 4. Data model (SQLite)

- `messages(id, hash UNIQUE, channel, raw, received_at)`
- `exceptions(id, message_id FK, shipment_ref, type, location, severity, summary, status)`
  - status: `triaged | investigating | ready_for_approval | needs_human_review | sent | dismissed`
- `assessments(id, exception_id FK, impact_summary, window_missed, affected_value, confidence, trace_json)`
- `drafts(id, exception_id FK, email_subject, email_body, action_plan)`

## 5. API surface

- `POST /exceptions` → 202 `{id, duplicate}`
- `GET /exceptions?status=` → list
- `GET /exceptions/{id}` → full detail incl. assessment + draft + trace
- `POST /exceptions/{id}/approve` → status `sent` (mock)
- `POST /exceptions/{id}/dismiss`
- `GET /metrics`

## 6. Milestones → Codex prompts

| # | Day | Prompt focus | Done when |
|---|-----|--------------|-----------|
| 1 | Jul 17 | FastAPI + SQLite + F1 triage w/ structured outputs + idempotency | curl a seed msg → parsed row; duplicate returns `duplicate: true` |
| 2 | Jul 18 | F2 agent: tools, bounded loop, confidence | pathological input finalizes ≤5 rounds |
| 3 | Jul 18 | F3 composer + confidence routing | low-confidence lands in review queue |
| 4 | Jul 19 | F4 inbox UI, all four views | full flow clickable end-to-end |
| 5 | Jul 19 | F5 seed replay + pytest | seed of 30 runs clean; tests green |
| 6 | Jul 20 | Polish: README quickstart, .env.example, deploy, error states | judge can run it from README alone |

## 7. Acceptance criteria (map to judging)

- **Tech implementation**: agent uses real function-calling with a bounded loop and
  a visible reasoning trace; non-trivial test suite; majority built in Codex session
- **Design**: complete inbox product a judge can click through in 2 minutes via seed data
- **Impact**: demo tells the broker story start-to-finish; metrics header quantifies work saved
- **Novelty**: guardrails-first agent design (idempotency, bounded loops, confidence
  escalation) vs typical chat-wrapper entries; concept evolved from the author's prior
  IntelTrans architecture study (cited, not reused)

## 8. Runtime configuration

`OPENAI_API_KEY` via `.env`; model id for all calls configurable via `FREIGHTDESK_MODEL`
(default: the GPT-5.6 model id — confirm exact string in the hackathon quickstart docs).
