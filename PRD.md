# FreightDesk — Product Requirements Document (build spec)

> The single source of truth to hand to Codex. Work through the milestones in
> order; each maps to one focused Codex prompt. Keep the whole build in ONE main
> Codex session where possible — its `/feedback` session ID goes in the Devpost form.

## 1. Problem

Small freight brokerages lack an operations control tower. When disruptions hit
(weather, port congestion, carrier failures), teams manually read dozens of carrier
messages, identify affected shipments, estimate customer impact, write status
updates, and decide what needs escalation. A single disruption can overwhelm a
small team.

**Target user**: freight brokers and operations coordinators at 2–20 person
brokerages.

**Daily moment of pain**: *"I opened my inbox and there are 40 exceptions from the
Savannah storm. Which ones matter, what do I tell customers, and what needs my
attention first?"*

**Core promise**: FreightDesk turns an exception flood into a prioritized action
queue. It does not replace the broker — it removes the 90% of exception work that
prevents brokers from focusing on the 10% requiring judgment.

| Input | Output |
|---|---|
| EDI-style updates | Structured exception record |
| Carrier emails | Impact assessment |
| Driver messages | Customer-ready communication draft |
| Operational alerts | Recommended next action + confidence-based escalation |

## 2. User stories

| # | Story | Feature |
|---|-------|---------|
| U1 | As a broker, I want incoming exceptions automatically classified so I don't manually sort disruptions. | F1 |
| U2 | As a broker, I want shipment impact investigated so I know which customers are at risk. | F2 |
| U3 | As a broker, I want customer emails drafted so I can communicate faster. | F3 |
| U4 | As a manager, I want uncertain cases escalated so AI does not make risky decisions. | F3 |
| U5 | As an operator, I want duplicate and malformed feeds handled safely so the exception desk stays reliable. | F1 |

## 3. Scope (4-day build)

### F1 — Ingestion & triage (U1, U5)
- `POST /exceptions` accepts `{channel, raw}` (raw = free-text carrier message)
- GPT-5.6 with **structured outputs** parses raw → `Exception`:
  `{shipment_ref, exception_type, location, severity (1-5), reported_at, summary}`
- `exception_type` enum: PORT_DELAY, CUSTOMS_HOLD, VESSEL_ROLLOVER, CHASSIS_SHORTAGE,
  WEATHER_DIVERT, REEFER_TEMP, ACCIDENT, MISSED_CUTOFF, UNKNOWN
- **Idempotency**: SHA-256 of normalized raw text; duplicates return 202 with
  `duplicate: true`, no reprocessing — and increment a visible counter
- Unparseable input → `UNKNOWN` + straight to review queue (never crash, never loop)

### F2 — Investigation agent (U2)
- Given a triaged Exception, run a GPT-5.6 agent with **function tools**:
  `lookup_shipment(ref)` → carrier, lane, delivery_window, order_value (mock DB)
  `eta_impact(ref, delay_hours)` → new_eta, window_missed: bool
  `port_conditions(location)` → congestion, weather (mock)
- **Bounded loop: max 5 tool-call rounds**, then force-finalize with what it has
- Output: `Assessment {impact_summary, window_missed, affected_value, confidence (0-1),
  recommended_action}` — full reasoning trace persisted for the UI

### F3 — Mitigation composer (U3, U4)
- GPT-5.6 drafts: (a) customer email (tone: calm, concrete, next step + new ETA),
  (b) internal action plan (bullet list)
- `confidence >= 0.7` → status `ready_for_approval`; else → `needs_human_review`
- "Send" is a mock (log + status change) — no real email integration in scope

### F4 — Prioritized inbox UI
- Single-page app (Next.js preferred; Streamlit acceptable fallback)
- **Priority tiers drive the sort**: 🔴 critical (severity 4-5 or window_missed with
  high affected_value — e.g. the pharma shipment) · 🟠 customer delivery risk
  (severity 3 or window_missed) · 🟢 informational delay (severity 1-2)
- Views: triage list (tier-sorted, status chips) · exception detail (raw msg,
  parsed fields, **agent reasoning trace**, drafted email — editable, Approve & Send /
  Send to review buttons) · review queue · metrics header (open / mitigated /
  escalated / **duplicates dropped**)
- Live-ish updates (poll every 2s is fine)

### F5 — Demo & test harness
- `seed.py` replays `data/seed_messages.jsonl` against the API with configurable rate
- pytest: triage parses 3 fixture messages; duplicate suppressed; agent loop
  terminates ≤5 rounds on a pathological fixture; confidence routing works

## 4. Non-goals (do not expand — dilutes the core idea)

- Full TMS replacement
- Autonomous customer communication (human always approves sends)
- Real carrier integrations (EDI networks, email parsing webhooks)
- Complex optimization algorithms
- Auth/multi-tenant, mobile, persistence beyond SQLite

## 5. MVP demo flow (what judges must see, in order)

Scenario: **Savannah port storm** (seed data is authored for this narrative)

1. **Ingest** — replay 32 inbound messages; duplicates-dropped counter ticks ×3;
   the malformed feed message routes safely to review
2. **AI triage** — raw text becomes typed exceptions (type, severity, shipment,
   location, customer impact)
3. **Investigation** — open one exception, show the agent's tool calls
   (shipment lookup → ETA impact → port conditions) in the trace
4. **Prioritization** — inbox sorted: 🔴 pharma shipment ($25k OTIF penalty) ·
   🟠 delivery-window risks · 🟢 informational delays
5. **Human approval** — judge clicks: approve email draft · send to review ·
   inspect reasoning trace

**The message**: *"40 containers delayed. AI found the one that could cost $25k and
drafted the customer response before the broker even opened the ticket."*

## 6. Data model (SQLite)

- `messages(id, hash UNIQUE, channel, raw, received_at)`
- `exceptions(id, message_id FK, shipment_ref, type, location, severity, tier, summary, status)`
  - status: `triaged | investigating | ready_for_approval | needs_human_review | sent | dismissed`
- `assessments(id, exception_id FK, impact_summary, window_missed, affected_value, confidence, trace_json)`
- `drafts(id, exception_id FK, email_subject, email_body, action_plan)`

## 7. API surface

- `POST /exceptions` → 202 `{id, duplicate}`
- `GET /exceptions?status=&tier=` → list
- `GET /exceptions/{id}` → full detail incl. assessment + draft + trace
- `POST /exceptions/{id}/approve` → status `sent` (mock)
- `POST /exceptions/{id}/review` → status `needs_human_review`
- `POST /exceptions/{id}/dismiss`
- `GET /metrics`

## 8. Milestones → Codex prompts

| # | Day | Prompt focus | Done when |
|---|-----|--------------|-----------|
| 1 | Jul 17 | FastAPI + SQLite + F1 triage w/ structured outputs + idempotency | curl a seed msg → parsed row; duplicate returns `duplicate: true` |
| 2 | Jul 18 | F2 agent: tools, bounded loop, confidence, trace persistence | pathological input finalizes ≤5 rounds |
| 3 | Jul 18 | F3 composer + confidence routing | low-confidence lands in review queue |
| 4 | Jul 19 | F4 inbox UI: tier sort, all views, trace display | MVP demo flow (§5) clickable end-to-end |
| 5 | Jul 19 | F5 seed replay + pytest | seed of 32 runs clean; tests green |
| 6 | Jul 20 | Polish: README quickstart, .env.example, deploy, error states | judge can run it from README alone |

## 9. Judge-facing differentiators (keep visible in demo + description)

1. **Agents with boundaries** — bounded investigation steps, tool use, confidence
   routing, human approval. Production-minded, not "AI does everything."
2. **Reliability features are visible** — duplicate counter, review queue,
   failed-message handling, agent trace. Proof of an operational system, not a chatbot.
3. **The emotional moment** — the pharma escalation surfacing from the storm flood
   with a drafted response.

## 10. Runtime configuration

`OPENAI_API_KEY` via `.env`; model id for all calls configurable via `FREIGHTDESK_MODEL`
(default: the GPT-5.6 model id — confirm exact string in the hackathon quickstart docs).
