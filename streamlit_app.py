import json
from pathlib import Path

import streamlit as st

from freightdesk.config import Settings
from freightdesk.pipeline import process_message
from freightdesk.store import Desk

st.set_page_config(page_title="FreightDesk - AI Exception Desk", page_icon="🚚", layout="wide")

SEED_PATH = Path(__file__).parent / "data" / "seed_messages.jsonl"
TIER_BADGE = {"red": "🔴", "orange": "🟠", "green": "🟢"}
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
        st.session_state.desk = Desk()
        st.session_state.replayed = False
    return st.session_state.desk


def load_seed() -> list[dict]:
    return [json.loads(l) for l in SEED_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]


desk = get_desk()

# ---- sidebar ---------------------------------------------------------------
with st.sidebar:
    st.header("Desk settings")
    threshold = st.slider(
        "Confidence threshold for auto-queue", 0.50, 0.90, 0.70, 0.05,
        help="Drafts at or above this confidence go to the approval inbox; below it, a human reviews first.",
    )
    st.header("Inject a single message")
    sample_key = st.selectbox("Sample", list(SAMPLE_MESSAGES.keys()))
    custom = st.text_area("Or paste a raw carrier message", height=90, placeholder="STATUS: CNTR ... / any email or SMS text")
    if st.button("Inject message", use_container_width=True):
        raw = custom.strip() or SAMPLE_MESSAGES[sample_key]
        process_message(raw, "email" if custom.strip() else "edi", desk, Settings(confidence_threshold=threshold))
        st.rerun()
    st.caption(
        "Engine: deterministic stub standing in for GPT-5.6 (zero tokens, reproducible). "
        "Set FREIGHTDESK_USE_OPENAI=1 + OPENAI_API_KEY for the live-LLM triage path. "
        "[Repo](https://github.com/sechan9999/FreightDesk)"
    )

settings = Settings(confidence_threshold=threshold)

# ---- header ------------------------------------------------------------------
st.title("🚚 FreightDesk")
st.caption(
    "**An AI exception desk for freight ops.** Raw carrier messages in - triaged, "
    "investigated (bounded agent, max 5 tool rounds), prioritized, and drafted for "
    "one-click approval. Humans keep the judgment calls."
)

b1, b2, b3 = st.columns([2, 2, 1])
if b1.button("🌩️ Replay the Savannah storm (32 messages)", type="primary", use_container_width=True):
    for m in load_seed():
        process_message(m["raw"], m["channel"], desk, settings)
    st.session_state.replayed = True
    st.rerun()
if b2.button("Replay again (all duplicates)", use_container_width=True,
             help="Re-sends the same 32 messages: idempotency drops every one of them.",
             disabled=not st.session_state.get("replayed")):
    for m in load_seed():
        process_message(m["raw"], m["channel"], desk, settings)
    st.rerun()
if b3.button("Reset desk", use_container_width=True):
    st.session_state.clear()
    st.rerun()

# ---- metrics -----------------------------------------------------------------
m = desk.metrics()
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Ingested", m["ingested"])
c2.metric("Duplicates dropped", m["duplicates"])
c3.metric("Ready for approval", m["ready"])
c4.metric("Needs human review", m["review"])
c5.metric("Sent", m["sent"])
c6.metric("Value at risk", f"${m['value_at_risk']:,.0f}")

if st.session_state.get("replayed"):
    reds = [r for r in desk.sorted_open() if r.tier == "red"]
    if reds:
        top = reds[0]
        st.error(
            f"**{m['ingested']} messages triaged.** Highest risk: "
            f"**{top.triage.shipment_ref or 'unidentified'}** - {top.assessment.impact_summary if top.assessment else top.triage.summary} "
            f"Customer response already drafted below.",
            icon="🚨",
        )

# ---- panels --------------------------------------------------------------------
open_recs = desk.sorted_open()
review_recs = desk.by_status("needs_human_review")
tab_inbox, tab_review, tab_log = st.tabs([
    f"Inbox ({len(open_recs)})",
    f"Human review ({len(review_recs)})",
    "Activity log",
])


def render_exception(rec, in_review_tab=False):
    t, a, d = rec.triage, rec.assessment, rec.draft
    badge = TIER_BADGE[rec.tier]
    title = (f"{badge} {t.shipment_ref or 'NO-REF'} · {t.exception_type} · "
             f"sev {t.severity} · {STATUS_LABEL[rec.status]}")
    with st.expander(title, expanded=False):
        left, right = st.columns([3, 2])
        with left:
            st.markdown(f"**Summary:** {t.summary}")
            st.markdown(f"**Customer impact:** {t.customer_impact}")
            if a:
                st.markdown(f"**Assessment:** {a.impact_summary}")
                st.markdown(
                    f"**Confidence:** {a.confidence:.2f} · **Rounds:** {a.rounds_used}/5 · "
                    f"**Window missed:** {'yes' if a.window_missed else 'no'} · "
                    f"**At risk:** ${a.affected_value:,.0f}"
                )
            if d:
                subject = st.text_input("Email subject", d.email_subject, key=f"subj-{rec.id}")
                body = st.text_area("Customer email draft (editable)", d.email_body,
                                    height=200, key=f"body-{rec.id}")
                st.markdown("**Internal action plan**")
                st.markdown(d.action_plan)
        with right:
            st.markdown("**Raw message**")
            st.code(rec.raw, language="text", wrap_lines=True)
            if a and a.trace:
                st.markdown("**Agent trace**")
                st.json(a.trace, expanded=False)

        if rec.status in ("ready_for_approval", "needs_human_review"):
            col_a, col_b, col_c = st.columns(3)
            if col_a.button("✅ Approve & send", key=f"approve-{rec.id}", use_container_width=True):
                if d:
                    d.email_subject = st.session_state.get(f"subj-{rec.id}", d.email_subject)
                    d.email_body = st.session_state.get(f"body-{rec.id}", d.email_body)
                desk.set_status(rec.id, "sent")
                desk.log("info", "customer_email_sent", id=rec.id, ref=t.shipment_ref or "-")
                st.rerun()
            if rec.status == "ready_for_approval":
                if col_b.button("👀 Send to review", key=f"review-{rec.id}", use_container_width=True):
                    desk.set_status(rec.id, "needs_human_review")
                    desk.log("warning", "sent_to_review", id=rec.id, by="operator")
                    st.rerun()
            if col_c.button("🗑 Dismiss", key=f"dismiss-{rec.id}", use_container_width=True):
                desk.set_status(rec.id, "dismissed")
                desk.log("info", "dismissed", id=rec.id)
                st.rerun()


with tab_inbox:
    if not open_recs:
        st.info("Inbox is clear. Replay the Savannah storm or inject a message from the sidebar.")
    for rec in open_recs:
        render_exception(rec)

with tab_review:
    if not review_recs:
        st.info("Nothing waiting on a human. The agent is confident about everything open.")
    else:
        st.warning(
            "These need human judgment: unclassified feeds, unidentified shipments, "
            "or confidence below the threshold."
        )
        for rec in review_recs:
            render_exception(rec, in_review_tab=True)

with tab_log:
    if desk.logs:
        st.code("\n".join(desk.logs[:120]), language="text")
    else:
        st.info("No activity yet.")
