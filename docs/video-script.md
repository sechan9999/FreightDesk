# Demo video script (<3:00, public YouTube)

> Requirement: audio must explain how **Codex** AND **GPT-5.6** were used.
> Record 1080p; screen + voiceover is enough, face cam optional.
> ⚠️ Final edit pass happens against actual footage — timings below are targets.

## Shot list

**[0:00–0:20] The problem — hook**
- Screen: seed replay running, triage list filling up with the Savannah storm cluster.
- VO: "A storm hits the Port of Savannah, and a freight broker's inbox explodes —
  held containers, missed cutoffs, a pharma shipment with a $25,000 penalty clause.
  Someone has to triage all of it, figure out what actually matters, and write the
  customer emails. This is FreightDesk — an AI exception desk that does the first 90%."

**[0:20–1:20] The product — one exception end-to-end, then the guardrails**
- Screen: click the pharma escalation (TRK-40045-A, severity 5).
- VO beats: raw message → GPT-5.6 structured triage → agent investigation trace
  (tool calls: shipment lookup, ETA impact, port conditions) → "window missed,
  $25k at risk" → drafted customer email + action plan → edit one line → Approve.
- Screen: replay a duplicate message → "duplicate dropped" counter ticks, nothing reprocessed.
- Screen: the malformed feed message → lands in Human Review, app unbothered.
- VO: "Guardrails are first-class: idempotent ingestion, an agent loop hard-capped
  at five steps, and confidence-based escalation to a human."

**[1:20–2:20] How it was built — REQUIRED narration**
- Screen: Codex session recording (scaffold prompt, then the agent-loop milestone).
- VO: "I built FreightDesk in four days inside Codex, working from a PRD. Codex
  scaffolded the FastAPI backend and SQLite layer in the first session, then
  implemented the bounded agent loop — [INSERT REAL ANECDOTE: a decision Codex made,
  e.g. its idempotency-key or trace-storage suggestion]. At runtime, GPT-5.6 does
  three jobs: structured-output triage of raw carrier text, the tool-calling
  investigation agent, and drafting the customer comms."
- Screen: flash the test suite passing + the /feedback session moment.

**[2:20–2:50] Impact + close**
- Screen: metrics header (open / mitigated / escalated / duplicates dropped) after
  the full 30-message seed.
- VO: "Thirty raw messages became a prioritized queue, twelve ready-to-send emails,
  and two escalations a human actually needed to see. For a two-person ops team,
  that's an afternoon back — every bad-weather day. Repo and setup instructions
  in the description."
- End card: repo URL + FreightDesk logo/title.

## Recording checklist
- [ ] Mic check; no background noise
- [ ] Browser at 100% zoom, dark theme consistent
- [ ] Rehearse once against a re-seeded DB (fresh counters)
- [ ] Verify video is PUBLIC on YouTube before submitting
- [ ] Say both "Codex" and "GPT-5.6" explicitly (judging requirement)
