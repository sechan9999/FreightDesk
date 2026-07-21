import json
import os
from pathlib import Path

import streamlit as st

from freightdesk.cascade import build_cascades, format_cascade, impact_chain
from freightdesk.channels import parse_batch
from freightdesk.config import Settings
from freightdesk.delivery import deliver, smtp_config
from freightdesk.feedback import effective_threshold, record_demotion, record_promotion
from freightdesk.pipeline import process_message
from freightdesk.store import Desk

APPROVAL_PIN = os.getenv("FREIGHTDESK_APPROVAL_PIN", "2468")

st.set_page_config(page_title="FreightDesk - AI Exception Desk", page_icon="FD", layout="wide")

SEED_PATH = Path(__file__).parent / "data" / "seed_messages.jsonl"
STATE_PATH = Path(os.getenv("FREIGHTDESK_STATE_PATH", Path(__file__).parent / ".freightdesk_state.json"))
TIER_BADGE = {"red": "RED", "orange": "ORANGE", "green": "GREEN"}
STATUS_LABEL = {
    "ready_for_approval": "ready for approval",
    "needs_human_review": "needs human review",
    "triaged": "triaged", "investigating": "investigating", "drafting": "drafting",
    "sent": "sent", "dismissed": "dismissed",
}

SAMPLE_MESSAGES = {
    "Port delay (EDI)": "STATUS: CNTR MSKU9911223 SHPMT TRK-40077-B HELD PORT OF SAVANNAH REASON WX EST DELAY 18HRS",
    "Customs hold (email)": "Hi team, customs flagged shipment TRK-40078-C for documentation exam at Long Beach. Broker says 2-3 days. Consignee expects delivery Friday.",
    "Reefer alarm (SMS)": "reefer alarm trk-40079-a temp -11C setpoint -18C tech dispatched",
    "No reference (email)": "A container is held at customs, no booking reference available yet, broker investigating documentation exam status.",
    "Malformed feed": "@@@#ERR 0x11 FEED RESYNC ]]]]] NO PAYLOAD {{{{",
}


def get_desk() -> Desk:
    if "desk" not in st.session_state:
        load_snapshot = getattr(Desk, "load", None)
        st.session_state.desk = load_snapshot(STATE_PATH) if callable(load_snapshot) else Desk()
        st.session_state.replayed = bool(st.session_state.desk.exceptions)
    return st.session_state.desk


def load_seed() -> list[dict]:
    return [json.loads(line) for line in SEED_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]


def persist_and_rerun() -> None:
    save_snapshot = getattr(desk, "save", None)
    if callable(save_snapshot):
        save_snapshot(STATE_PATH)
    st.rerun()



desk = get_desk()

with st.sidebar:
    st.header("Operator")
    operator = st.text_input("Name", key="op-name", placeholder="e.g. J. Park")
    pin = st.text_input("Approval PIN", key="op-pin", type="password",
                        help="Approvals are authenticated: set FREIGHTDESK_APPROVAL_PIN (demo default: 2468).")
    authed = bool(operator.strip()) and pin == APPROVAL_PIN
    if authed:
        st.caption(f"Signed in as **{operator.strip()}** - approvals enabled.")
    else:
        st.caption("Enter name + PIN to enable Approve & send (demo PIN: 2468).")

    st.header("Desk settings")
    threshold = st.slider(
        "Confidence threshold for auto-queue", 0.50, 0.90, 0.70, 0.05,
        help="Drafts at or above this confidence go to the approval inbox; below it, a human reviews first.",
    )
    if desk.feedback:
        st.caption("**Adaptive routing** (learned from review outcomes):")
        for exc_type, entry in sorted(desk.feedback.items()):
            st.caption(
                f"- {exc_type}: threshold {effective_threshold(desk, exc_type, threshold):.2f} "
                f"({entry['promotions']} promoted, {entry['demotions']} demoted)"
            )

    st.header("Ingest a carrier feed drop")
    feed_file = st.file_uploader("EDI-style / JSONL batch (.txt, .jsonl)", type=["txt", "jsonl"])
    if st.button("Ingest feed drop", use_container_width=True, disabled=feed_file is None):
        batch = parse_batch(feed_file.getvalue().decode("utf-8", errors="replace"))
        for channel, raw in batch:
            process_message(raw, channel, desk, Settings(confidence_threshold=threshold))
        desk.log("info", "feed_drop_ingested", messages=len(batch), source=feed_file.name)
        persist_and_rerun()

    st.header("Inject a single message")
    sample_key = st.selectbox("Sample", list(SAMPLE_MESSAGES.keys()))
    custom = st.text_area("Or paste a raw carrier message", height=90, placeholder="STATUS: CNTR ... / any email or SMS text")

    settings = Settings(confidence_threshold=threshold)
    if st.button("Inject message", use_container_width=True):
        raw = custom.strip() or SAMPLE_MESSAGES[sample_key]
        process_message(raw, "email" if custom.strip() else "edi", desk, settings)
        persist_and_rerun()
    st.caption(
        "Demo mode uses a deterministic stub engine (zero tokens, reproducible). "
        "Set FREIGHTDESK_DEMO_MODE=0 plus FREIGHTDESK_USE_OPENAI=1 and OPENAI_API_KEY to enable live triage. "
        "[Repo](https://github.com/sechan9999/FreightDesk)"
    )

st.title("FreightDesk")
st.caption(
    "**An AI exception desk for freight ops.** Raw carrier messages are triaged, "
    "investigated with a bounded agent, prioritized, and drafted for one-click approval."
)

b1, b2, b3 = st.columns([2, 2, 1])
if b1.button("Replay the Savannah storm (32 messages)", type="primary", use_container_width=True):
    for message in load_seed():
        process_message(message["raw"], message["channel"], desk, settings)
    st.session_state.replayed = True
    persist_and_rerun()
if b2.button("Replay again (all duplicates)", use_container_width=True,
             help="Re-sends the same 32 messages: idempotency drops every one.",
             disabled=not st.session_state.get("replayed")):
    for message in load_seed():
        process_message(message["raw"], message["channel"], desk, settings)
    persist_and_rerun()
if b3.button("Reset desk", use_container_width=True):
    if STATE_PATH.exists():
        STATE_PATH.unlink()
    st.session_state.clear()
    st.rerun()

metrics = desk.metrics()
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Ingested", metrics["ingested"])
c2.metric("Duplicates dropped", metrics["duplicates"])
c3.metric("Ready for approval", metrics["ready"])
c4.metric("Needs human review", metrics["review"])
c5.metric("Sent", metrics["sent"])
c6.metric("Value at risk", f"${metrics['value_at_risk']:,.0f}")

if st.session_state.get("replayed"):
    reds = [record for record in desk.sorted_open() if record.tier == "red"]
    if reds:
        top = reds[0]
        st.error(
            f"**{metrics['ingested']} messages triaged.** Highest risk: "
            f"**{top.triage.shipment_ref or 'unidentified'}** - "
            f"{top.assessment.impact_summary if top.assessment else top.triage.summary}. "
            "Customer response is drafted below."
        )

open_records = desk.sorted_open()
review_records = desk.by_status("needs_human_review")
inbox_records = [record for record in open_records if record.status != "needs_human_review"]
cascades = build_cascades(open_records) if open_records else []
tab_inbox, tab_map, tab_review, tab_log = st.tabs([
    f"Inbox ({len(inbox_records)})",
    f"Disruption map ({len(cascades)})",
    f"Human review ({len(review_records)})",
    "Activity log",
])


def render_exception(record, namespace: str) -> None:
    triage, assessment, draft = record.triage, record.assessment, record.draft
    title = (
        f"{TIER_BADGE[record.tier]} | {triage.shipment_ref or 'NO-REF'} | "
        f"{triage.exception_type} | sev {triage.severity} | {STATUS_LABEL[record.status]}"
    )
    with st.expander(title, expanded=False):
        left, right = st.columns([3, 2])
        with left:
            st.markdown(f"**Summary:** {triage.summary}")
            st.markdown(f"**Customer impact:** {triage.customer_impact}")
            if assessment:
                st.markdown(f"**Assessment:** {assessment.impact_summary}")
                st.markdown(
                    f"**Confidence:** {assessment.confidence:.2f} | **Rounds:** {assessment.rounds_used}/5 | "
                    f"**Window missed:** {'yes' if assessment.window_missed else 'no'} | "
                    f"**At risk:** ${assessment.affected_value:,.0f}"
                )
                st.markdown("**Impact chain**")
                st.code(impact_chain(record), language="text")
            if draft:
                recipient = draft.email_to or "no address on file (send will be recorded, not delivered)"
                st.caption(f"To: {recipient}")
                st.text_input("Email subject", draft.email_subject, key=f"{namespace}-subj-{record.id}")
                st.text_area("Customer email draft (editable)", draft.email_body,
                             height=200, key=f"{namespace}-body-{record.id}")
                st.markdown("**Internal action plan**")
                st.markdown(draft.action_plan)
        with right:
            st.markdown("**Raw message**")
            st.code(record.raw, language="text", wrap_lines=True)
            if assessment and assessment.trace:
                st.markdown("**Agent trace**")
                st.json(assessment.trace, expanded=False)

        if record.status in ("ready_for_approval", "needs_human_review"):
            col_a, col_b, col_c = st.columns(3)
            if col_a.button("Approve & send", key=f"{namespace}-approve-{record.id}",
                            use_container_width=True, disabled=not authed,
                            help=None if authed else "Enter operator name + PIN in the sidebar to approve."):
                was_in_review = record.status == "needs_human_review"
                mode, detail = "mock", "no draft to deliver"
                if draft:
                    draft.email_subject = st.session_state.get(f"{namespace}-subj-{record.id}", draft.email_subject)
                    draft.email_body = st.session_state.get(f"{namespace}-body-{record.id}", draft.email_body)
                    draft.approved_by = operator.strip()
                    mode, detail = deliver(draft)
                desk.set_status(record.id, "sent")
                if was_in_review:
                    record_promotion(desk, triage.exception_type)  # AI was too cautious here
                desk.log("info", "customer_email_sent", id=record.id,
                         ref=triage.shipment_ref or "-", by=operator.strip(),
                         delivery=mode, detail=detail)
                persist_and_rerun()
            if record.status == "ready_for_approval":
                if col_b.button("Send to review", key=f"{namespace}-review-{record.id}", use_container_width=True):
                    desk.set_status(record.id, "needs_human_review")
                    record_demotion(desk, triage.exception_type)  # AI was overconfident here
                    desk.log("warning", "sent_to_review", id=record.id, by=operator.strip() or "operator")
                    persist_and_rerun()
            if col_c.button("Dismiss", key=f"{namespace}-dismiss-{record.id}", use_container_width=True):
                desk.set_status(record.id, "dismissed")
                desk.log("info", "dismissed", id=record.id)
                persist_and_rerun()


with tab_inbox:
    if not inbox_records:
        st.info("Inbox is clear. Replay the Savannah storm or inject a message from the sidebar.")
    for record in inbox_records:
        render_exception(record, namespace="inbox")

with tab_map:
    if not cascades:
        st.info("No open exceptions to map. Replay the storm to see disruptions cascade.")
    else:
        st.caption(
            "One disruption is never one message. Each card groups the open exceptions "
            "that share a disruption source and traces how the impact propagates: "
            "disruption -> shipments -> delivery windows -> revenue at risk -> mitigation."
        )
        for cascade in cascades:
            tier_label = TIER_BADGE[cascade["worst_tier"]]
            st.markdown(
                f"**{tier_label} | {cascade['location']}** - {cascade['count']} exceptions, "
                f"${cascade['value_at_risk']:,.0f} at risk"
            )
            st.code(format_cascade(cascade), language="text")

with tab_review:
    if not review_records:
        st.info("Nothing waiting on a human. The agent is confident about everything open.")
    else:
        st.warning("These need human judgment: unclassified feeds, unidentified shipments, or low confidence.")
        for record in review_records:
            render_exception(record, namespace="review")

with tab_log:
    if desk.logs:
        st.code("\n".join(desk.logs[:120]), language="text")
    else:
        st.info("No activity yet.")

st.divider()
delivery_state = "SMTP configured - approvals deliver real email" if smtp_config() \
    else "SMTP not configured - approvals are recorded, delivery is mocked"
st.caption(
    f"Channels: feed drop + manual inject | Approval: operator + PIN | "
    f"Delivery: {delivery_state} | Routing: adaptive per exception type | "
    f"[Repo](https://github.com/sechan9999/FreightDesk)"
)