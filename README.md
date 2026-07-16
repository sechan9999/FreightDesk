# FreightDesk 🚚📬

**An AI exception desk for freight operations.** Raw carrier status messages go in;
triaged exceptions, impact assessments, drafted customer emails, and mitigation
plans come out — with a human review queue for anything the agent isn't sure about.

Built for **[OpenAI Build Week](https://openai.devpost.com/)** · Track: **Work & Productivity**
· Built with **Codex + GPT-5.6**

> **Repo status:** working Streamlit demo + tested engine (`freightdesk/`), running
> on a **deterministic stub engine** standing in for GPT-5.6 (zero tokens, fully
> reproducible). For the hackathon submission, the core is rebuilt/extended in a
> Codex session per the rules — this implementation is the reference and demo fallback.

## The problem

Small freight brokers and shippers handle exception storms by hand: a weather event
hits a port and suddenly there are 40 emails about held containers, each needing
triage ("how bad?"), investigation ("which orders miss their delivery windows?"),
and a customer email nobody has time to write. It's high-volume, formulaic-but-
judgment-laden work — exactly what an agent with guardrails should do.

## How it works

```
raw carrier msgs ──▶ GPT-5.6 triage ──▶ investigation agent ──▶ draft email + plan ──▶ inbox UI
 (paste / webhook)   (structured out)   (tools, max 5 steps)    (confidence-scored)   approve / edit
                            │                                          │
                            ▼                                          ▼
                     duplicate suppression                    low confidence → human
                     (idempotency key)                        review queue
```

Production guardrails are first-class: idempotent ingestion (carrier feeds redeliver),
a bounded agent loop (no runaway token bills), and confidence-based human escalation.

## Quickstart

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Click **"Replay the Savannah storm (32 messages)"** — then open the 🔴 pharma
exception at the top of the inbox, inspect the agent trace, edit the drafted
customer email, and approve it. Try **"Replay again"** to watch idempotency drop
all 32 as duplicates.

Optional live-LLM triage: `FREIGHTDESK_USE_OPENAI=1` + `OPENAI_API_KEY`
(+ `pip install openai`); the stub remains the fallback on any API failure.

Run the tests:

```bash
pytest        # 10 tests: triage, tiering, idempotency, bounded agent, full seed replay
```

## Sample data

[`data/seed_messages.jsonl`](data/seed_messages.jsonl) — 30 realistic carrier
status messages (EDI-style, email-style, SMS-style; includes duplicates and one
malformed message) for demos and judge testing. Spec: [`data/SEED_SPEC.md`](data/SEED_SPEC.md).

## How Codex and GPT-5.6 were used

_TBD after the build — this section will document, with session references:_
- what Codex scaffolded vs what was hand-edited
- key design decisions made inside the Codex session
- where GPT-5.6 runs at runtime (triage structured outputs, investigation
  reasoning, comms drafting)

## Docs

- [PRD.md](PRD.md) — product requirements: user stories, scope, demo flow
- [SPEC.md](SPEC.md) — technical spec: components, validated schema, API contracts, agent interfaces
- [BUILD_CHECKLIST.md](BUILD_CHECKLIST.md) — milestone-by-milestone execution checklist with verification gates
- [docs/video-script.md](docs/video-script.md) — demo video script + shot list
- [docs/submission-draft.md](docs/submission-draft.md) — Devpost submission text

## License

MIT — see [LICENSE](LICENSE).
