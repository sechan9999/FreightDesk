from freightdesk.channels import parse_batch
from freightdesk.config import Settings
from freightdesk.customers import profile_for
from freightdesk.delivery import deliver
from freightdesk.feedback import effective_threshold, record_demotion, record_promotion
from freightdesk.models import Draft
from freightdesk.pipeline import process_message
from freightdesk.store import Desk

SETTINGS = Settings()

PHARMA_MSG = (
    "Escalation: TRK-40045-A is temperature-sensitive pharma with a hard delivery "
    "window Thursday 08:00-12:00. Current Savannah hold puts arrival at Thursday "
    "15:40. Client contract has a $25k OTIF penalty clause. Need options today please."
)
RETAIL_MSG = (
    "STATUS: CNTR TCLU5583010 SHPMT TRK-40022-B HELD PORT OF SAVANNAH "
    "REASON WX SEVERE RAIN EST DELAY 14HRS NEXT UPDATE 0600"
)


# ---- channels --------------------------------------------------------------

def test_parse_batch_mixed_jsonl_and_plain():
    text = "\n".join([
        '{"channel": "sms", "raw": "reefer alarm trk-40079-a temp -11C"}',
        "STATUS: SHPMT TRK-40080-B HELD SAVANNAH DELAY 6HRS",
        "Hi team, customs flagged TRK-40081-C at Long Beach.",
        "",
        '{"broken json',
    ])
    batch = parse_batch(text)
    assert len(batch) == 4
    assert batch[0] == ("sms", "reefer alarm trk-40079-a temp -11C")
    assert batch[1][0] == "edi"       # STATUS prefix -> edi
    assert batch[2][0] == "email"     # prose -> email
    assert batch[3][0] == "email"     # malformed json falls back to plain text


def test_feed_drop_flows_through_pipeline():
    desk = Desk()
    for channel, raw in parse_batch(RETAIL_MSG + "\n" + PHARMA_MSG):
        process_message(raw, channel, desk, SETTINGS)
    assert desk.counters["ingested"] == 2


# ---- customer preferences --------------------------------------------------

def test_customer_profiles_resolve():
    assert profile_for("TRK-40045-A")["code"] == "NOVAPHARM"
    assert profile_for("TRK-40022-B")["tone"] == "brief"
    assert profile_for("TRK-99999-Z")["code"] == "GENERIC"
    assert profile_for(None)["code"] == "GENERIC"


def test_drafts_honor_customer_tone_and_recipient():
    desk = Desk()
    pharma = process_message(PHARMA_MSG, "email", desk, SETTINGS)
    retail = process_message(RETAIL_MSG, "edi", desk, SETTINGS)

    assert pharma.draft.email_to == "ops@novapharm.example"
    assert "NovaPharm Logistics" in pharma.draft.email_body
    assert "qa@novapharm.example" in pharma.draft.action_plan  # cc surfaced to operator

    assert retail.draft.email_to == "dispatch@atlretail.example"
    # brief tone is materially shorter than formal
    assert len(retail.draft.email_body) < len(pharma.draft.email_body)


# ---- delivery --------------------------------------------------------------

def test_delivery_mocked_without_smtp(monkeypatch):
    monkeypatch.delenv("FREIGHTDESK_SMTP_HOST", raising=False)
    draft = Draft(email_subject="s", email_body="b", action_plan="-", email_to="x@y.example")
    mode, detail = deliver(draft)
    assert mode == "mock" and "SMTP not configured" in detail


def test_delivery_sends_via_smtp_when_configured(monkeypatch):
    sent = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            sent["host"], sent["port"] = host, port
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def send_message(self, message):
            sent["to"] = message["To"]
            sent["subject"] = message["Subject"]

    monkeypatch.setenv("FREIGHTDESK_SMTP_HOST", "mail.example")
    monkeypatch.setattr("freightdesk.delivery.smtplib.SMTP", FakeSMTP)
    draft = Draft(email_subject="Update", email_body="b", action_plan="-",
                  email_to="ops@novapharm.example")
    mode, detail = deliver(draft)
    assert mode == "smtp"
    assert sent == {"host": "mail.example", "port": 587,
                    "to": "ops@novapharm.example", "subject": "Update"}


def test_delivery_mocked_without_recipient():
    draft = Draft(email_subject="s", email_body="b", action_plan="-", email_to="")
    mode, detail = deliver(draft)
    assert mode == "mock" and "no recipient" in detail


# ---- adaptive routing feedback ---------------------------------------------

def test_feedback_adjusts_threshold_and_clamps():
    desk = Desk()
    base = 0.70
    assert effective_threshold(desk, "CUSTOMS_HOLD", base) == 0.70
    record_promotion(desk, "CUSTOMS_HOLD")
    assert effective_threshold(desk, "CUSTOMS_HOLD", base) == 0.65
    for _ in range(10):
        record_promotion(desk, "CUSTOMS_HOLD")
    assert effective_threshold(desk, "CUSTOMS_HOLD", base) == 0.55  # clamped at -0.15
    for _ in range(10):
        record_demotion(desk, "CUSTOMS_HOLD")
    assert effective_threshold(desk, "CUSTOMS_HOLD", base) == 0.85  # clamped at +0.15


def test_feedback_changes_pipeline_routing():
    """A type whose threshold rose above a case's confidence routes to review."""
    desk = Desk()
    for _ in range(3):
        record_demotion(desk, "REEFER_TEMP")  # +0.15 -> threshold 0.85
    record = process_message(PHARMA_MSG, "email", desk, SETTINGS)  # confidence 0.82
    assert record.status == "needs_human_review"


def test_feedback_survives_snapshot(tmp_path):
    desk = Desk()
    record_demotion(desk, "PORT_DELAY")
    desk.save(tmp_path / "d.json")
    restored = Desk.load(tmp_path / "d.json")
    assert restored.feedback["PORT_DELAY"]["demotions"] == 1
