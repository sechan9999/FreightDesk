# FreightDesk

An AI exception desk for freight operations. FreightDesk turns raw carrier messages into a prioritized queue, impact assessments, customer-ready drafts, and a focused human-review list.

Built for [OpenAI Build Week](https://openai.devpost.com/) in the Work & Productivity track.

## Try it

Open the live demo: [freightdesk.streamlit.app](https://freightdesk.streamlit.app/)

No account or API key is required. The demo uses a deterministic engine so each judge can reproduce the same outcome.

1. In the sidebar, sign in as an operator: any name + demo PIN `2468` (approvals are authenticated - the Approve button stays disabled until you do).
2. Click **Reset desk**.
3. Click **Replay the Savannah storm (32 messages)**.
4. Open the top red item, `TRK-40045-A`: assessment, bounded agent trace, impact chain, and a customer draft addressed to the customer on file (NovaPharm, with QA on cc).
5. Click **Approve & send** - the send is recorded with your operator name in the activity log (real SMTP delivery only when configured; mocked otherwise, and it says so).
6. Open **Disruption map** - open exceptions grouped by disruption source, with cargo, missed windows, and dollars at risk per cascade.
7. Open **Human review** - uncertain or malformed messages safely escalated.
8. Click **Replay again (all duplicates)** - repeat deliveries suppressed, workload unchanged.

## Why it matters

Freight operations fail under exception volume, not a lack of notifications. One port disruption can produce dozens of EDI updates, emails, texts, and redeliveries. FreightDesk makes the first pass visible and reviewable - and keeps the judgment calls human.

The included Savannah storm scenario has 32 messages: 29 unique inputs, three duplicate deliveries, one malformed feed, and a temperature-sensitive pharma shipment with a missed delivery window and $25,000 at risk.

## Capabilities

- **Multi-channel ingestion** - manual inject, plus feed-drop upload (EDI-style text or JSONL batches) from the sidebar.
- **Structured triage** - raw text becomes a typed exception: type, severity, shipment, location, delay.
- **Bounded investigation** - tool-calling agent capped at 5 rounds, with a persisted, inspectable trace; exhaustion caps confidence and routes to a human.
- **Prioritization** - red/orange/green tiers; the **Disruption map** groups exceptions by shared disruption source (one storm = one cascade, not 29 rows).
- **Customer-aware drafting** - per-account profiles set recipient, tone (formal vs brief), and cc; drafts stay editable.
- **Authenticated approval** - operator name + PIN required to send; every send is audited (`by=<operator> delivery=smtp|mock`).
- **Real or mocked delivery** - SMTP when `FREIGHTDESK_SMTP_HOST` is configured; explicit mock with a stated reason otherwise.
- **Adaptive routing** - review outcomes nudge per-type confidence thresholds (approve-from-review lowers, demote raises; clamped +/-0.15), persisted across sessions.
- **Reliability guardrails** - normalized-message idempotency, malformed input quarantined to review, terminal states protected, state snapshot survives reruns and refreshes.

## Run locally

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Run the test suite (28 tests: triage, tiering, pipeline, cascade grouping, channels, delivery, adaptive routing, persistence):

```bash
python -m pytest
```

## Configuration

| Variable | Purpose | Default |
|---|---|---|
| `FREIGHTDESK_APPROVAL_PIN` | Operator approval PIN | `2468` (demo) |
| `FREIGHTDESK_SMTP_HOST` / `_PORT` / `_USER` / `_PASSWORD` / `_FROM` | Real email delivery | unset = mocked |
| `FREIGHTDESK_CONFIDENCE_THRESHOLD` | Base auto-queue threshold | `0.7` |
| `FREIGHTDESK_MAX_ROUNDS` | Agent tool-round cap | `5` |
| `FREIGHTDESK_DEMO_MODE` | Deterministic engine (set `0` to allow live LLM) | `1` |
| `FREIGHTDESK_USE_OPENAI` + `OPENAI_API_KEY` | Live GPT triage path (requires demo mode off) | off |
| `FREIGHTDESK_STATE_PATH` | Desk snapshot location | `.freightdesk_state.json` |

## What's next

Real carrier network connections (EDI VAN integrations, inbound webhook endpoints), SSO-backed operator identity in place of the shared PIN, and outcome analytics - did the chosen mitigation hold? - feeding the adaptive router.

## Project links

- Live app: https://freightdesk.streamlit.app/
- Repository: https://github.com/sechan9999/FreightDesk
- Devpost write-up: [docs/submission-draft.md](docs/submission-draft.md)
- Live demo script: [docs/video-script.md](docs/video-script.md)

## License

MIT. See [LICENSE](LICENSE).
