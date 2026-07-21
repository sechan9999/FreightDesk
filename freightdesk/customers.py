"""Customer communication preferences: recipient, tone, and cc per account."""

from .tools import MOCK_SHIPMENTS

PROFILES: dict[str, dict] = {
    "NOVAPHARM": {
        "name": "NovaPharm Logistics",
        "email": "ops@novapharm.example",
        "tone": "formal",
        "cc": ["qa@novapharm.example"],
    },
    "ATLRETAIL": {
        "name": "Atlanta Retail Group",
        "email": "dispatch@atlretail.example",
        "tone": "brief",
        "cc": [],
    },
    "GENERIC": {
        "name": "",
        "email": "",
        "tone": "formal",
        "cc": [],
    },
}


def profile_for(shipment_ref: str | None) -> dict:
    facts = MOCK_SHIPMENTS.get(shipment_ref or "", {})
    code = facts.get("customer", "GENERIC")
    profile = dict(PROFILES.get(code, PROFILES["GENERIC"]))
    profile["code"] = code
    return profile
