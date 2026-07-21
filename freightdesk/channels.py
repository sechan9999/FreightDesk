"""Multi-channel batch ingestion: EDI-style feed drops, email dumps, JSONL."""

import json


def parse_batch(text: str) -> list[tuple[str, str]]:
    """Split a raw feed drop into (channel, message) pairs.

    Accepts JSONL lines ({"channel": ..., "raw": ...}) and plain text lines;
    plain lines are channel-guessed (EDI status feeds vs email-style prose).
    Malformed JSON falls back to plain-text handling - ingestion never raises.
    """
    items: list[tuple[str, str]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("{"):
            try:
                obj = json.loads(line)
                raw = obj.get("raw", "")
                if raw:
                    items.append((obj.get("channel", "edi"), raw))
                    continue
            except (json.JSONDecodeError, AttributeError, TypeError):
                pass
        channel = "edi" if line.upper().startswith("STATUS") else "email"
        items.append((channel, line))
    return items
