import hashlib
import re
from datetime import datetime, timezone

from .models import Assessment, Draft, ExceptionRecord, TriageResult

TIER_ORDER = {"red": 0, "orange": 1, "green": 2}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


def normalize_hash(raw: str) -> str:
    return hashlib.sha256(re.sub(r"\s+", " ", raw.strip().lower()).encode()).hexdigest()


class Desk:
    """In-memory exception desk state (one per Streamlit session)."""

    def __init__(self):
        self._hashes: set[str] = set()
        self.exceptions: dict[int, ExceptionRecord] = {}
        self.logs: list[str] = []
        self.counters = {"ingested": 0, "duplicates": 0, "sent": 0, "dismissed": 0}
        self._next_msg = 0
        self._next_exc = 0

    # -- logging ------------------------------------------------------------
    def log(self, level: str, event: str, **kw) -> None:
        rest = " ".join(f"{k}={v}" for k, v in kw.items())
        self.logs.insert(0, f"{_now()} {level.upper():<7} {event} {rest}".rstrip())
        del self.logs[400:]

    # -- ingestion ----------------------------------------------------------
    def seen_or_add(self, raw: str) -> bool:
        h = normalize_hash(raw)
        if h in self._hashes:
            return True
        self._hashes.add(h)
        return False

    def add_exception(self, raw: str, channel: str, t: TriageResult) -> ExceptionRecord:
        self._next_msg += 1
        self._next_exc += 1
        rec = ExceptionRecord(
            id=self._next_exc, message_id=self._next_msg, raw=raw, channel=channel,
            triage=t, created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )
        self.exceptions[rec.id] = rec
        return rec

    # -- transitions (single choke point so illegal moves can't happen) -----
    def set_status(self, exc_id: int, status: str) -> None:
        rec = self.exceptions[exc_id]
        if rec.status in ("sent", "dismissed"):
            raise ValueError(f"exception {exc_id} is terminal ({rec.status})")
        rec.status = status
        if status == "sent":
            self.counters["sent"] += 1
        if status == "dismissed":
            self.counters["dismissed"] += 1

    def save_assessment(self, exc_id: int, a: Assessment) -> None:
        self.exceptions[exc_id].assessment = a

    def save_draft(self, exc_id: int, d: Draft) -> None:
        self.exceptions[exc_id].draft = d

    # -- queries -------------------------------------------------------------
    def sorted_open(self) -> list[ExceptionRecord]:
        open_recs = [r for r in self.exceptions.values()
                     if r.status not in ("sent", "dismissed")]
        return sorted(open_recs, key=lambda r: (
            TIER_ORDER[r.tier], -r.triage.severity, r.created_at))

    def by_status(self, status: str) -> list[ExceptionRecord]:
        return [r for r in self.exceptions.values() if r.status == status]

    def metrics(self) -> dict:
        by = {}
        for r in self.exceptions.values():
            by[r.status] = by.get(r.status, 0) + 1
        risk = sum(r.assessment.affected_value for r in self.exceptions.values()
                   if r.assessment and r.status not in ("sent", "dismissed"))
        return {
            "ingested": self.counters["ingested"],
            "duplicates": self.counters["duplicates"],
            "ready": by.get("ready_for_approval", 0),
            "review": by.get("needs_human_review", 0),
            "sent": self.counters["sent"],
            "value_at_risk": risk,
        }
