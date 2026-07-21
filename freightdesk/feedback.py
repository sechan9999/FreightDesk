"""Adaptive routing: review outcomes nudge per-type confidence thresholds.

When a human approves a case the AI sent to review, the AI was too cautious
for that exception type - its threshold drops slightly. When a human demotes
an auto-queued draft back to review, the AI was overconfident - the threshold
rises. Deltas are small and clamped, so one outcome never swings routing."""

STEP = 0.05
MAX_DELTA = 0.15


def _entry(desk, exception_type: str) -> dict:
    return desk.feedback.setdefault(
        exception_type, {"delta": 0.0, "promotions": 0, "demotions": 0}
    )


def effective_threshold(desk, exception_type: str, base: float) -> float:
    delta = desk.feedback.get(exception_type, {}).get("delta", 0.0)
    return round(min(0.95, max(0.40, base + delta)), 2)


def record_promotion(desk, exception_type: str) -> None:
    """Human approved a case out of review: trust the AI more for this type."""
    entry = _entry(desk, exception_type)
    entry["promotions"] += 1
    entry["delta"] = max(-MAX_DELTA, round(entry["delta"] - STEP, 2))


def record_demotion(desk, exception_type: str) -> None:
    """Human demoted an auto-queued draft: trust the AI less for this type."""
    entry = _entry(desk, exception_type)
    entry["demotions"] += 1
    entry["delta"] = min(MAX_DELTA, round(entry["delta"] + STEP, 2))
