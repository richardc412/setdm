-- Adds per-chat assist/autopilot mode flags (manual, ai-assisted, autopilot)
-- Run this script in pgAdmin (or any PostgreSQL client) before deploying the feature.

BEGIN;

ALTER TABLE chats
ADD COLUMN IF NOT EXISTS assist_mode VARCHAR(32) NOT NULL DEFAULT 'manual';

CREATE INDEX IF NOT EXISTS idx_chats_assist_mode ON chats(assist_mode);

UPDATE chats
SET assist_mode = 'manual'
WHERE assist_mode IS NULL;

COMMIT;

