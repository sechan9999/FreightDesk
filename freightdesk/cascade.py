"""Disruption-cascade view: ontology-style impact propagation.

Inspired by Microsoft's Ontology Playground supply-chain-disruption-path
scenario: a disruption is not an isolated message - it cascades through the
entities it touches (Disruption -> Shipments -> Delivery windows -> Revenue
-> Mitigation). This module derives that graph on the fly from desk state;
it stores nothing, so it cannot break persistence.
"""

from collections import Counter

from .models import ExceptionRecord
from .tools import PORT_CONDITIONS

_TIER_RANK = {"red": 0, "orange": 1, "green": 2}


def _canonical_location(location: str | None) -> str:
    """Merge location aliases so one physical disruption forms one cascade
    (e.g. 'Savannah' and 'Port of Savannah' are the same storm)."""
    if not location:
        return "Unlocated network events"
    low = location.lower()
    if "savannah" in low:
        return "Port of Savannah"
    if "busan" in low:
        return "Busan New Port"
    if "norfolk" in low:
        return "Norfolk Intl"
    return location


def _shipment_facts(record: ExceptionRecord) -> dict:
    """Shipment attributes recovered from the agent's own lookup trace."""
    if not record.assessment:
        return {}
    for step in record.assessment.trace:
        if step.get("tool") == "lookup_shipment" and "error" not in step.get("result", {}):
            return step["result"]
    return {}


def build_cascades(records: list[ExceptionRecord]) -> list[dict]:
    """Group open exceptions by disruption source, worst first."""
    groups: dict[str, list[ExceptionRecord]] = {}
    for record in records:
        groups.setdefault(_canonical_location(record.triage.location), []).append(record)

    cascades = []
    for location, members in groups.items():
        conditions = PORT_CONDITIONS.get(location.lower(), {})
        assessed = [r for r in members if r.assessment]
        windows_missed = sum(1 for r in assessed if r.assessment.window_missed)
        value_at_risk = sum(r.assessment.affected_value for r in assessed)
        commodities = sorted({
            facts["commodity"] for facts in (_shipment_facts(r) for r in members)
            if facts.get("commodity")
        })
        mitigations = Counter(
            r.assessment.recommended_action for r in assessed if r.assessment.window_missed
        )
        cascades.append({
            "location": location,
            "weather": conditions.get("weather"),
            "congestion": conditions.get("congestion_level"),
            "members": sorted(members, key=lambda r: (_TIER_RANK[r.tier], -r.triage.severity)),
            "count": len(members),
            "types": Counter(r.triage.exception_type for r in members),
            "windows_missed": windows_missed,
            "value_at_risk": value_at_risk,
            "commodities": commodities,
            "mitigations": mitigations.most_common(3),
            "worst_tier": min((r.tier for r in members), key=_TIER_RANK.get),
        })
    return sorted(cascades, key=lambda c: (-c["value_at_risk"], -c["count"]))


def format_cascade(cascade: dict) -> str:
    """Render one cascade as an impact-propagation path (ontology-playground style)."""
    trigger = cascade["location"]
    if cascade["weather"] and cascade["weather"].lower() not in ("clear", "unknown"):
        trigger = f"{cascade['weather']} @ {trigger}"
    types = ", ".join(f"{t} x{n}" for t, n in cascade["types"].most_common())
    lines = [
        f"Disruption: {trigger}",
        f"  -> Affects: {cascade['count']} exceptions ({types})",
    ]
    if cascade["commodities"]:
        lines.append(f"  -> Cargo: {', '.join(cascade['commodities'])}")
    lines.append(
        f"  -> Windows missed: {cascade['windows_missed']} of {cascade['count']}"
    )
    lines.append(f"  -> Result: ${cascade['value_at_risk']:,.0f} revenue at risk")
    if cascade["mitigations"]:
        acts = "; ".join(f"{a.split(';')[0]} (x{n})" for a, n in cascade["mitigations"])
        lines.append(f"  -> Mitigation: {acts}")
    else:
        lines.append("  -> Mitigation: monitor; no delivery windows breached yet")
    return "\n".join(lines)


def impact_chain(record: ExceptionRecord) -> str:
    """Per-exception cascade path: how THIS message propagates to money."""
    t, a = record.triage, record.assessment
    if a is None:
        return (
            f"Unclassified input ({t.exception_type})\n"
            "  -> No shipment identity established\n"
            "  -> Routed to human review (no automated action)"
        )
    facts = _shipment_facts(record)
    trigger = t.exception_type.replace("_", " ").title()
    if t.location:
        trigger += f" @ {_canonical_location(t.location)}"
    lines = [f"Disruption: {trigger}"]
    if facts:
        lines.append(
            f"  -> Shipment: {t.shipment_ref} ({facts.get('commodity', '?')} via "
            f"{facts.get('carrier', '?')}, {facts.get('lane', '?')})"
        )
    else:
        lines.append(f"  -> Shipment: {t.shipment_ref or 'not identified'}")
    if a.window_missed:
        lines.append("  -> Delivery window MISSED")
        lines.append(f"  -> Result: ${a.affected_value:,.0f} at risk")
    else:
        lines.append("  -> Delivery window holds (delay absorbed by slack)")
        lines.append("  -> Result: no revenue at risk")
    lines.append(f"  -> Mitigation: {a.recommended_action}")
    return "\n".join(lines)
