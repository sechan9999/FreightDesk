# Seed data spec

`seed_messages.jsonl` — one JSON object per line: `{"id", "channel", "raw"}`.
Channels: `edi` (terse system feeds), `email` (verbose human messages), `sms` (fragments).

Deliberate properties for the demo:
- 30 messages covering all 8 exception types + UNKNOWN
- 3 exact duplicates (ids d1/d2/d3 duplicate earlier messages) → idempotency demo
- 1 malformed/garbage message (id m1) → review-queue / never-crash demo
- Severity spread: a few window-critical reefer/customs cases, plenty of routine delays
- Shipment refs follow `TRK-#####-A` so the mock `lookup_shipment` tool can key on them
- A "Savannah weather event" cluster (8 messages) so the burst demo tells one coherent story
