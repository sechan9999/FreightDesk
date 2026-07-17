# FreightDesk

An AI exception desk for freight operations. FreightDesk turns raw carrier messages into a prioritized queue, impact assessments, customer-ready drafts, and a focused human-review list.

Built for [OpenAI Build Week](https://openai.devpost.com/) in the Work & Productivity track.

## Try it

Open the live demo: [freightdesk.streamlit.app](https://freightdesk.streamlit.app/)

No credentials, API key, or account are required. The demo uses a deterministic engine so each judge can reproduce the same outcome.

1. Click **Reset desk**.
2. Click **Replay the Savannah storm (32 messages)**.
3. Open the top red item, `TRK-40045-A`, to inspect the assessment, trace, draft, and action plan.
4. Click **Approve & send** to complete the human-controlled workflow.
5. Open **Human review** to see uncertain or malformed messages safely escalated.
6. Click **Replay again (all duplicates)** to see repeat deliveries suppressed.

## Why it matters

Freight operations fail under exception volume, not a lack of notifications. One port disruption can produce dozens of EDI updates, emails, texts, and redeliveries. FreightDesk makes the first pass visible and reviewable:

- High-confidence cases are prepared for operator approval.
- Ambiguous or malformed messages route to human review.
- Duplicate messages are counted and suppressed.
- Investigation is capped at five steps.
- Customer communication remains editable and human-approved.

The included Savannah storm scenario has 32 messages: 29 unique inputs, three duplicate deliveries, and a temperature-sensitive pharma shipment with a missed delivery window and $25,000 at risk.

## Run locally

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Run the test suite:

```bash
python -m pytest
```

## What's next

The next step is to connect real carrier channels: EDI 214/315 feeds, email ingestion, and webhook events. From there, FreightDesk can add authenticated approval, real email delivery, customer-specific communication preferences, and feedback from review outcomes to improve routing over time.

## Project links

- Live app: https://freightdesk.streamlit.app/
- Repository: https://github.com/sechan9999/FreightDesk
- Devpost write-up: [docs/submission-draft.md](docs/submission-draft.md)
- Live demo script: [docs/video-script.md](docs/video-script.md)

## License

MIT. See [LICENSE](LICENSE).