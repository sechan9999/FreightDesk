# FreightDesk Demo Script (verified against the live app)

> Full walkthrough ~= 4:30. Devpost cut (< 3:00): sections marked with a star only,
> in order 1 -> 2 -> 3 -> 4 -> 9 -> 10. Every claim below was verified against
> https://freightdesk.streamlit.app on 2026-07-16.

## * 1. Opening (0:00-0:25)

Say:
"Freight teams get overwhelmed during disruptions, not because they lack
notifications, but because every notification creates a decision. A single port
storm produces EDI updates, broker emails, SMS alarms, and duplicates. Someone
has to identify the shipment, assess the customer impact, and decide what must
be handled first. FreightDesk turns that mess into an operator's exception desk."

"The key design choice is that it does not auto-send. It prepares the routine
work and makes uncertainty obvious for a person to handle."

## * 2. Trigger the operational storm (0:25-0:55)

Click: "Replay the Savannah storm (32 messages)". Wait for rerun; point to metric tiles.

Say:
"This replay is a realistic Savannah disruption scenario. Thirty-two raw messages
arrive together. The desk accepts 29 unique messages and identifies three
duplicate deliveries immediately. The result is a prioritized inbox, not 32 items
for a person to read from scratch."

"Notice the two queues: Inbox holds 27 items ready to act on, and two cases were
deliberately sent to Human review. That separation is the product."

## * 3. Walk the highest-risk exception end to end (0:55-1:50)

Click: first red expander in Inbox - "TRK-40045-A - REEFER_TEMP - sev 5".

Say:
"The highest-risk case surfaces first: TRK-40045-A, a temperature-sensitive
pharma shipment. Notice the desk classified it as a reefer-risk case, not just
another port delay - the cold chain is what makes this the shipment that matters.
FreightDesk extracted the reference and the issue from a raw carrier message,
then assessed the impact."

Point to Assessment, then Confidence / Rounds / Window missed / At risk.

Say:
"The investigation is bounded to five tool rounds - here it used four, at
confidence 0.82. The desk concludes the delivery window is missed by 18 hours,
putting $25,000 at risk. The cap matters: this is operational software, so it
must not keep reasoning forever when a case is unclear."

Click: expand Agent trace.

Say:
"The trace makes the decision inspectable - shipment lookup, port conditions,
ETA impact. An operator sees the evidence path rather than being asked to trust
a black box."

## * 4. Human control over the draft (1:50-2:15)

Click: inside Email subject, append " - confirmed", click outside the field.

Say:
"The proposed customer message is editable. FreightDesk gets the operator from
raw status update to a usable draft, but the operator owns the final wording and
the send decision."

Click: Approve & send. Wait; point to Sent ticking to 1 and the case leaving the
Inbox (27 -> 26).

Say:
"One click records the approval and marks the case sent - dispatch is mocked in
this demo. Once sent, the case is terminal: it cannot be accidentally
transitioned again, which protects the workflow from duplicate action."

## 5. The system behaving well when uncertain (2:15-2:45)

Click: Human review tab. Open the "NO-REF - UNKNOWN" item.

Say:
"Now the behavior that matters most in real operations: not every message should
be automated. This is the malformed feed message - no usable shipment identity
at all. And below it, TRK-40042-A: a seal-number mismatch the desk couldn't
confidently classify. FreightDesk does not invent confidence. It routes these
here, preserves the raw input, and asks a human to decide."

"That is a safer outcome than a convincing but incorrect customer email."

## 6. Prove duplicate suppression (2:45-3:10)

Click: "Replay again (all duplicates)". Wait; point to Duplicates dropped (3 -> 35).

Say:
"Carrier systems redeliver. I can replay the same 32-message storm, and the desk
treats every single one as a duplicate. The counter jumps while the actual
workload does not change at all - idempotency as a visible operator benefit, not
just a backend claim."

## 7. A new message enters safely (3:10-3:35)

Sidebar: choose "Malformed feed" from Sample, click Inject message - ONCE ONLY
(a second injection would be suppressed as a duplicate mid-sentence). Click the
Human review tab.

Say:
"I can inject a bad message directly. The desk stays available, records the
event, and routes the failure for review. A bad feed does not crash the session
or disappear silently."

## 8. Reliability, plainly (3:35-4:00)

Click: Activity log; point to recent entries.

Say:
"Every meaningful transition is recorded: received, deduplicated, routed, sent.
Behind this UI are three guardrails: normalized-message idempotency, a
five-round investigation limit, and confidence-based human escalation."

"For this demo, the engine is deterministic by default - reproducible, and
immune to network or model-availability failures on stage. A live OpenAI triage
path exists behind explicit configuration, but it is not required to prove the
workflow."

## * 9. [DEVPOST ONLY - REQUIRED] How it was built (2:15-2:40 in the short cut)

Show: Codex session recording over this narration.

Say:
"I built FreightDesk with Codex using GPT-5.6, working from a written PRD and
technical spec. Codex [YOUR REAL ANECDOTE - what it scaffolded, one decision it
drove]. At runtime, GPT-5.6 powers the structured triage of raw carrier text,
the tool-calling investigation, and the drafted communications."

## * 10. Close (final 20s)

Click: return to Inbox; point to remaining prioritized items and metrics.

Say:
"FreightDesk does not replace the freight operator's judgment. It gives that
person a smaller, prioritized set of decisions, drafted customer communication,
and a clear view of what needs attention now. In a disruption, that is the
difference between an overloaded inbox and an operational command center."

---

Recording checklist:
- [ ] Reset desk before recording (fresh counters)
- [ ] 1080p, 100% zoom, mic check
- [ ] Devpost cut: verify < 3:00 and that "Codex" and "GPT-5.6" are both said aloud
- [ ] Video public on YouTube before submitting
