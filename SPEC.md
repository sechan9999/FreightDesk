# FreightDesk — Technical Spec

> Companion to [PRD.md](PRD.md). The PRD says *what and why*; this says *exactly how*.
> Hand both to Codex. Where this spec and improvisation disagree, the spec wins.

## 1. Component architecture

```
                                ┌──────────────────────────────────────────┐
   seed.py ──POST──▶            │  api.py (FastAPI)                        │
   webhook / UI     ──────────▶ │  routes, validation, 202 contract        │
                                └───────┬──────────────────────────────────┘
                                        │ dedupe (db.py) then spawn task
                                        ▼
                                ┌──────────────────────────────────────────┐
                                │  pipeline.py  (async, semaphore ≤ 8)     │
                                │  triaged → investigating → drafting →    │
                                │  ready_for_approval | needs_human_review │
                                └───┬───────────┬───────────┬──────────────┘
                                    ▼           ▼           ▼
                              triage.py     agent.py    composer.py
                              GPT-5.6       GPT-5.6     GPT-5.6
                              structured    tool loop   email + plan
                              outputs       (tools.py,  drafts
                                  │          ≤5 rounds)     │
                                  └───────────┴─────────────┘
                                              │
                                        db.py + schema.sql (SQLite)
                                              ▲
                                web/ (Next.js) or streamlit_app.py
                                polls GET endpoints every 2s
```

**Module responsibilities** (one file = one job; no cross-imports except through models):

| File | Owns | Must NOT do |
|---|---|---|
| `freightdesk/config.py` | env settings dataclass (`OPENAI_API_KEY`, `FREIGHTDESK_MODEL`, `MAX_ROUNDS=5`, `CONFIDENCE_THRESHOLD=0.7`, `PIPELINE_CONCURRENCY=8`, `DB_PATH`) | import anything else from the package |
| `freightdesk/models.py` | Pydantic domain models (mirror §3 contracts) | DB or LLM calls |
| `freightdesk/db.py` | connection factory (executes `schema.sql`), repository functions (`insert_message`, `upsert_exception`, `save_assessment`, `save_draft`, `set_status`, queries) | business logic |
| `freightdesk/triage.py` | one function: `triage(raw, channel) -> TriageResult` via structured outputs | writing to DB |
| `freightdesk/tools.py` | mock tool impls + their JSON schemas + `MOCK_SHIPMENTS` table | LLM calls |
| `freightdesk/agent.py` | `investigate(exc) -> Assessment` bounded tool loop | writing to DB |
| `freightdesk/composer.py` | `compose(exc, assessment) -> Draft` | writing to DB |
| `freightdesk/tiering.py` | pure function `tier(severity, window_missed, affected_value)` | anything impure |
| `freightdesk/pipeline.py` | state machine: calls triage→agent→composer, persists at every step, catches everything | HTTP |
| `freightdesk/api.py` | FastAPI app factory + routes; owns the inflight task registry | LLM calls |
| `seed.py` | replay `data/seed_messages.jsonl` at `--rate` msgs/sec | — |

**Status state machine** (single writer: pipeline.py; approve/review/dismiss via API):

```
POST /exceptions ──▶ triaged ──▶ investigating ──▶ drafting ──┬─▶ ready_for_approval ──▶ sent
        │                                                     └─▶ needs_human_review ──▶ sent | dismissed
        └── UNKNOWN type or triage failure ──▶ needs_human_review
```

Illegal transitions return `409` (see §3). `sent` and `dismissed` are terminal.

## 2. Database schema — VALIDATED

DDL lives in [`schema.sql`](schema.sql) (single source; `db.py` executes it on connect).

Validation performed 2026-07-16 by executing the DDL against SQLite and probing it
(keep `tests/test_schema.py` doing the same):
- ✅ full happy-path row set inserts (message → exception → assessment → draft)
- ✅ 10/10 constraint violations rejected: duplicate `hash`, bad `channel`, bad
  `type`, `severity 9`, bad `tier`, bad `status`, `confidence 1.5`, `rounds_used 6`,
  orphan FK, second assessment per exception (UNIQUE)
- ✅ `ON DELETE CASCADE` verified: deleting a message removes exception, assessment, draft
- Note: `PRAGMA foreign_keys = ON` is per-connection — `db.py` must set it on every connect.

## 3. API contracts

All bodies JSON. Errors use FastAPI default shape `{"detail": ...}`.

### `POST /exceptions` → **202**
```jsonc
// request
{ "channel": "edi",                    // edi | email | sms | alert
  "raw": "STATUS: CNTR MSKU7401229 SHPMT TRK-40021-A HELD ..." }
// 202 response — ALWAYS 202 on valid input, duplicate or not
{ "id": 17, "duplicate": false }
// duplicate: {"id": 4, "duplicate": true}  (id of the ORIGINAL message)
```
- 422: missing/blank `raw`, invalid `channel` (pydantic)
- Never 500 on weird content: triage failures route to `needs_human_review`

### `GET /exceptions?status=&tier=` → **200**
```jsonc
{ "items": [ { "id": 12, "shipment_ref": "TRK-40045-A", "type": "PORT_DELAY",
    "location": "Port of Savannah", "severity": 5, "tier": "red",
    "summary": "Pharma shipment held; Thursday window at risk",
    "status": "ready_for_approval", "created_at": "2026-07-18T14:02:11.000Z" } ] }
```
Sorted: tier (red→orange→green), then severity desc, then created_at asc.

### `GET /exceptions/{id}` → **200** | 404
```jsonc
{ "exception": { /* as above */ },
  "message": { "channel": "email", "raw": "...", "received_at": "..." },
  "assessment": { "impact_summary": "...", "window_missed": true,
    "affected_value": 25000, "confidence": 0.82, "rounds_used": 3,
    "trace": [ { "round": 1, "tool": "lookup_shipment",
                 "args": {"ref": "TRK-40045-A"}, "result": { /* ... */ } } ] },
  "draft": { "email_subject": "...", "email_body": "...", "action_plan": "- ..." } }
```
`assessment`/`draft` are `null` until their pipeline stage completes.

### `POST /exceptions/{id}/approve` → **200** `{"status": "sent"}`
- 404 unknown id · **409** unless current status is `ready_for_approval` or `needs_human_review`

### `POST /exceptions/{id}/review` → **200** `{"status": "needs_human_review"}`
- 409 unless current status is `ready_for_approval`

### `POST /exceptions/{id}/dismiss` → **200** `{"status": "dismissed"}`
- 409 if status is `sent` (terminal)

### `GET /metrics` → **200**
```jsonc
{ "open": 9, "ready_for_approval": 6, "needs_human_review": 2,
  "sent": 14, "dismissed": 1, "duplicates_dropped": 3, "in_pipeline": 4 }
```

## 4. LLM + agent/tool interfaces

All calls: model = `config.FREIGHTDESK_MODEL`, `temperature=0.2`.

### 4a. Triage (`triage.py`) — structured outputs
One chat completion, `response_format = json_schema (strict)`:
```json
{ "name": "triage_result", "strict": true, "schema": {
  "type": "object", "additionalProperties": false,
  "required": ["shipment_ref","exception_type","location","severity","summary","customer_impact"],
  "properties": {
    "shipment_ref":   {"type": ["string","null"], "description": "TRK-#####-A form if present"},
    "exception_type": {"type": "string", "enum": ["PORT_DELAY","CUSTOMS_HOLD","VESSEL_ROLLOVER","CHASSIS_SHORTAGE","WEATHER_DIVERT","REEFER_TEMP","ACCIDENT","MISSED_CUTOFF","UNKNOWN"]},
    "location":       {"type": ["string","null"]},
    "severity":       {"type": "integer", "minimum": 1, "maximum": 5},
    "summary":        {"type": "string", "maxLength": 200},
    "customer_impact":{"type": "string", "maxLength": 200} } } }
```
Failure policy: any API error / refusal → return `TriageResult(exception_type="UNKNOWN", severity=3, ...)`; pipeline routes to review. Never raise past `triage()`.

### 4b. Investigation agent (`agent.py`)
Tool definitions (OpenAI function-calling format):
```jsonc
[{ "type": "function", "function": { "name": "lookup_shipment",
   "parameters": { "type": "object", "required": ["ref"],
     "properties": { "ref": {"type": "string"} } } }},
 { "type": "function", "function": { "name": "eta_impact",
   "parameters": { "type": "object", "required": ["ref", "delay_hours"],
     "properties": { "ref": {"type": "string"}, "delay_hours": {"type": "number"} } } }},
 { "type": "function", "function": { "name": "port_conditions",
   "parameters": { "type": "object", "required": ["location"],
     "properties": { "location": {"type": "string"} } } }}]
```
Mock returns (`tools.py`; deterministic off `MOCK_SHIPMENTS` keyed by ref, seeded fallback for unknown refs):
- `lookup_shipment` → `{carrier, lane, delivery_window_end, order_value_usd, commodity, temperature_controlled}`
- `eta_impact` → `{new_eta, window_missed, hours_past_window}`
- `port_conditions` → `{congestion_level, weather, avg_dwell_hours}`

**Loop algorithm** (the part to get exactly right):
```python
async def investigate(exc) -> Assessment:
    msgs = [system_prompt, user_context(exc)]
    trace = []
    for round in range(1, MAX_ROUNDS + 1):              # MAX_ROUNDS = 5
        rsp = await llm(msgs, tools=TOOLS)              # tool_choice="auto"
        if not rsp.tool_calls:
            return finalize(rsp, trace, rounds=round)   # parse Assessment (structured output)
        for call in rsp.tool_calls:
            result = dispatch(call)                     # KeyError/bad args -> {"error": "..."} result, never raise
            trace.append({"round": round, "tool": call.name, "args": call.args, "result": result})
            msgs.append(tool_result_msg(call, result))
    # rounds exhausted: force a final answer, no tools allowed
    rsp = await llm(msgs + [finalize_instruction], tools=None)   # tool_choice="none"
    a = finalize(rsp, trace, rounds=MAX_ROUNDS)
    a.confidence = min(a.confidence, 0.5)               # exhaustion caps confidence -> review
    return a
```
`finalize` uses a second strict json_schema: `{impact_summary, window_missed, affected_value, confidence, recommended_action}`.

### 4c. Composer (`composer.py`)
One completion, strict schema `{email_subject, email_body, action_plan}`.
Prompt constraints: calm tone; concrete next step; include new ETA if known; never
promise compensation; ≤180 words body. Routing (in pipeline, not composer):
`confidence >= 0.7 → ready_for_approval`, else `needs_human_review`.

## 5. Implementation order (with test gates)

| Step | Build | Gate before moving on |
|---|---|---|
| 1 | `schema.sql` (already in repo) + `config.py` + `models.py` + `db.py` | `tests/test_schema.py`: constraint probes from §2 pass |
| 2 | `tools.py` (mocks + schemas) | `tests/test_tools.py`: known ref returns pharma fixture; unknown ref deterministic |
| 3 | `triage.py` | 3 fixture messages parse to expected type/severity; garbage → UNKNOWN (mock LLM in tests) |
| 4 | `agent.py` | loop terminates: (a) natural finish, (b) 5-round exhaustion w/ confidence cap; trace recorded |
| 5 | `composer.py` + `tiering.py` + `pipeline.py` | end-to-end on 3 messages with mocked LLM: statuses + tiers correct |
| 6 | `api.py` | httpx tests: 202 contract, duplicate=true, 409 on illegal approve |
| 7 | `seed.py` + run against real GPT-5.6 | 32-message seed completes; metrics match SEED_SPEC expectations (3 dups, ≥1 review) |
| 8 | `web/` inbox UI | PRD §5 demo flow clickable end-to-end |
| 9 | README quickstart + `.env.example` + deploy | fresh-clone run from README alone |

**Testing rule**: steps 1–6 run with the LLM mocked (inject a fake client via
`config`); only step 7+ spends real tokens. Keep the pathological loop fixture
(tool that always errors) in the suite — it's the demo's loop-guard story.

## 6. Failure policy (uniform)

| Failure | Behavior |
|---|---|
| Triage LLM error/refusal | UNKNOWN exception → `needs_human_review`; log |
| Tool dispatch error | error result into trace; agent continues (bounded) |
| Agent/composer LLM error | status `needs_human_review`, assessment/draft nullable |
| Duplicate message | 202 `duplicate: true`; counter++ ; nothing else |
| Any pipeline exception | caught at pipeline root; status `needs_human_review`; never kills the worker |
