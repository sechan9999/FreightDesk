-- FreightDesk SQLite schema (validated: see SPEC.md section 2)
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    hash        TEXT    NOT NULL UNIQUE,          -- sha256 of normalized raw
    channel     TEXT    NOT NULL CHECK (channel IN ('edi', 'email', 'sms', 'alert')),
    raw         TEXT    NOT NULL,
    received_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS exceptions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id   INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    shipment_ref TEXT,                             -- NULL when UNKNOWN/unparseable
    type         TEXT    NOT NULL CHECK (type IN (
                   'PORT_DELAY','CUSTOMS_HOLD','VESSEL_ROLLOVER','CHASSIS_SHORTAGE',
                   'WEATHER_DIVERT','REEFER_TEMP','ACCIDENT','MISSED_CUTOFF','UNKNOWN')),
    location     TEXT,
    severity     INTEGER NOT NULL CHECK (severity BETWEEN 1 AND 5),
    tier         TEXT    NOT NULL DEFAULT 'green' CHECK (tier IN ('red','orange','green')),
    summary      TEXT    NOT NULL DEFAULT '',
    status       TEXT    NOT NULL DEFAULT 'triaged' CHECK (status IN (
                   'triaged','investigating','drafting','ready_for_approval',
                   'needs_human_review','sent','dismissed')),
    created_at   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_exceptions_status ON exceptions(status);
CREATE INDEX IF NOT EXISTS idx_exceptions_tier   ON exceptions(tier);

CREATE TABLE IF NOT EXISTS assessments (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    exception_id   INTEGER NOT NULL UNIQUE REFERENCES exceptions(id) ON DELETE CASCADE,
    impact_summary TEXT    NOT NULL,
    window_missed  INTEGER NOT NULL CHECK (window_missed IN (0, 1)),
    affected_value REAL    NOT NULL DEFAULT 0,
    confidence     REAL    NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    rounds_used    INTEGER NOT NULL CHECK (rounds_used BETWEEN 0 AND 5),
    trace_json     TEXT    NOT NULL DEFAULT '[]'   -- list of {round, tool, args, result}
);

CREATE TABLE IF NOT EXISTS drafts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    exception_id  INTEGER NOT NULL UNIQUE REFERENCES exceptions(id) ON DELETE CASCADE,
    email_subject TEXT    NOT NULL,
    email_body    TEXT    NOT NULL,
    action_plan   TEXT    NOT NULL                 -- markdown bullet list
);
