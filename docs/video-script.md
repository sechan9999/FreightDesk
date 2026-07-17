# FreightDesk 10-minute live demo script

This script is designed for a 9-minute presentation with roughly one minute of recovery time. It uses the deterministic demo path, so every judge sees the same scenario without requiring an API key or network-dependent model output.

## Before judges arrive

1. Open `http://localhost:8501`.
2. Keep browser zoom at 100% and the window wide enough to show the six metric tiles.
3. Click **Reset desk** once. Confirm the Inbox and Human review tabs both show `0`.
4. Keep the app on the main page. Do not pre-run the replay.
5. Have the repository open in a second tab only as a backup; the live app is the main proof.

## 0:00-0:45 | Problem and promise

**Click:** No click yet. Point to the empty Inbox and the sidebar.

**Say:**

"Freight teams get overwhelmed during disruptions, not because they lack notifications, but because every notification creates a decision. A single port storm produces EDI updates, broker emails, SMS alarms, and duplicates. Someone has to identify the shipment, assess the customer impact, and decide what must be handled first. FreightDesk turns that mess into an operator's exception desk."

"The key design choice is that it does not auto-send. It prepares the routine work and makes uncertainty obvious for a person to handle."

## 0:45-1:45 | Trigger the operational storm

**Click:** Click **Replay the Savannah storm (32 messages)**.

**Wait:** Let the page rerun. Point to the metric tiles.

**Say:**

"This replay is a realistic Savannah disruption scenario. Thirty-two raw messages arrive together. The desk accepts 29 unique messages and identifies three duplicate deliveries immediately. The result is a prioritized inbox, not 32 items for a person to read from scratch."

"Notice the two important queues: items ready for approval and items deliberately sent to Human review. That separation is the product."

## 1:45-3:30 | Walk the highest-risk exception end to end

**Click:** In **Inbox**, click the first red expander, labeled with `TRK-40045-A` and `PORT_DELAY`.

**Say:**

"The highest-risk case surfaces first: `TRK-40045-A`, a temperature-sensitive pharma shipment. FreightDesk extracted the shipment reference and issue from a raw carrier-style message, then assessed the impact."

**Click:** Point to **Assessment**, then scroll slightly if needed to show **Confidence**, **Rounds**, **Window missed**, and **At risk**.

**Say:**

"The investigation is bounded to five steps. Here, the desk concludes the delivery window is missed and puts $25,000 at risk. The cap matters: this is operational software, so it must not keep reasoning forever when a case is unclear."

**Click:** Point to **Agent trace** and expand it if it is collapsed.

**Say:**

"The trace makes the decision inspectable. An operator can see the evidence path rather than being asked to trust a black box."

## 3:30-4:45 | Show human control over the draft

**Click:** Click inside **Email subject**. Append ` - confirmed` and leave the cursor out of the field.

**Say:**

"The proposed customer message is editable. FreightDesk gets the operator from raw status update to a usable draft, but the operator owns the final wording and the send decision."

**Click:** Click **Approve & send**.

**Wait:** The page reruns. Point to the **Sent** metric increasing by one.

**Say:**

"One click records the approval and sends this case to the completed state. It cannot be accidentally transitioned again after that, which protects the workflow from duplicate action."

## 4:45-6:00 | Show the system behaving well when it is uncertain

**Click:** Click the **Human review** tab.

**Click:** Open the item with `NO-REF` or the malformed feed entry, whichever is visible first.

**Say:**

"Now for the behavior that matters most in real operations: not every message should be automated. This item lacks a usable shipment identity or is malformed. FreightDesk does not invent confidence. It routes the case here, preserves the raw input, and asks a human to decide."

"That is a safer outcome than a convincing but incorrect customer email."

## 6:00-7:00 | Prove duplicate suppression

**Click:** Click **Replay again (all duplicates)**.

**Wait:** Let the page rerun. Point to **Duplicates dropped**.

**Say:**

"Carrier systems redeliver. I can replay the same 32-message storm, and the desk treats every one as a duplicate rather than creating another queue. The duplicate counter increases while the actual operational workload does not."

"That is idempotency as a visible operator benefit, not just a backend claim."

## 7:00-8:00 | Prove a new message can enter safely

**Click:** In the sidebar, choose **Malformed feed** from **Sample**.

**Click:** Click **Inject message**.

**Click:** Click the **Human review** tab.

**Say:**

"I can also inject a bad message directly. The desk stays available, records the event, and routes the failure for review. A bad feed does not crash the session or disappear silently."

## 8:00-9:00 | Explain reliability and implementation plainly

**Click:** Click **Activity log** and point to recent entries.

**Say:**

"Every meaningful transition is recorded here: received, deduplicated, routed, and sent. Behind this UI are three guardrails: normalized-message idempotency, a five-step investigation limit, and confidence-based human escalation."

"For the live demo, the engine is deterministic by default. That makes the scenario reproducible and protects the presentation from a network or model-availability failure. A live OpenAI triage path exists behind explicit configuration, but it is not required to prove the workflow."

## 9:00-9:30 | Close

**Click:** Return to **Inbox**. Point to the remaining prioritized items and metrics.

**Say:**

"FreightDesk does not replace the freight operator's judgment. It gives that person a smaller, prioritized set of decisions, drafted customer communication, and a clear view of what needs attention now. In a disruption, that is the difference between an overloaded inbox and an operational command center."

## Recovery lines

- If the page refreshes: "The desk persists its demo state, so the operational picture survives a Streamlit rerun."
- If the first red item is not expanded: "The red pharma exception is the top-priority record in the Inbox."
- If timing is short: skip the direct malformed-message injection and move from Human review to the Activity log.
- If timing is long: open the internal action plan on the pharma record and connect it to the operator's approval decision.