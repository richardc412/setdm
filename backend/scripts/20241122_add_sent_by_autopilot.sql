-- Adds a boolean flag to track whether outbound messages were sent by Autopilot
-- Run this script before deploying the autopilot flag feature.

BEGIN;

ALTER TABLE messages
ADD COLUMN IF NOT EXISTS sent_by_autopilot BOOLEAN NOT NULL DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_messages_sent_by_autopilot ON messages(sent_by_autopilot);

UPDATE messages
SET sent_by_autopilot = FALSE
WHERE sent_by_autopilot IS NULL;

COMMIT;


