// Ensure schema; run once at server start.
import { getPool } from './db.js';

export async function migrate() {
  const pool = getPool();
  await pool.query(`
    CREATE TABLE IF NOT EXISTS interest_events (
      id BIGSERIAL PRIMARY KEY,
      ts TIMESTAMPTZ NOT NULL DEFAULT now(),
      event_type TEXT NOT NULL,
      model_id TEXT,
      meta JSONB
    );
    CREATE INDEX IF NOT EXISTS interest_events_type_ts ON interest_events (event_type, ts);
    CREATE INDEX IF NOT EXISTS interest_events_model ON interest_events (model_id);
  `).catch((e) => console.error('migrate interest:', e.message));
}
