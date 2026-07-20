import json
from pathlib import Path

from freightdesk.cascade import build_cascades, format_cascade, impact_chain
from freightdesk.config import Settings
from freightdesk.pipeline import process_message
from freightdesk.store import Desk

SETTINGS = Settings()
SEED = Path(__file__).parent.parent / "data" / "seed_messages.jsonl"


def replayed_desk() -> Desk:
    desk = Desk()
    for line in SEED.read_text(encoding="utf-8").splitlines():
        if line.strip():
            message = json.loads(line)
            process_message(message["raw"], message["channel"], desk, SETTINGS)
    return desk


def test_savannah_storm_forms_one_cascade():
    desk = replayed_desk()
    cascades = build_cascades(desk.sorted_open())
    savannah = next(c for c in cascades if c["location"] == "Port of Savannah")
    # 'Savannah' and 'Port of Savannah' messages merge into one disruption event
    assert savannah["count"] >= 6
    refs = {r.triage.shipment_ref for r in savannah["members"]}
    assert "TRK-40045-A" in refs
    assert savannah["value_at_risk"] >= 25000
    assert savannah["windows_missed"] >= 1
    assert savannah["worst_tier"] == "red"


def test_cascades_sorted_by_value_at_risk():
    desk = replayed_desk()
    cascades = build_cascades(desk.sorted_open())
    values = [c["value_at_risk"] for c in cascades]
    assert values == sorted(values, reverse=True)


def test_format_cascade_shows_propagation_path():
    desk = replayed_desk()
    savannah = next(c for c in build_cascades(desk.sorted_open())
                    if c["location"] == "Port of Savannah")
    text = format_cascade(savannah)
    assert text.startswith("Disruption:")
    assert "-> Affects:" in text and "-> Result:" in text and "-> Mitigation:" in text
    assert "$" in text


def test_impact_chain_for_pharma():
    desk = replayed_desk()
    pharma = next(r for r in desk.sorted_open()
                  if r.triage.shipment_ref == "TRK-40045-A")
    chain = impact_chain(pharma)
    assert "TRK-40045-A" in chain
    assert "pharmaceuticals" in chain
    assert "$25,000" in chain
    assert "MISSED" in chain


def test_impact_chain_for_unassessed_record():
    desk = Desk()
    record = process_message("@@@#ERR 0x004452 FEED RESYNC ]]]]] NO PAYLOAD {{{{",
                             "edi", desk, SETTINGS)
    chain = impact_chain(record)
    assert "human review" in chain
    assert "No shipment identity" in chain
