// ESM port of staging lib/store.js (Postgres store + digest tables).
import { hashToken } from './legacy-auth.mjs';
import { emptyProfile, normalizeProfile } from './legacy-profile.mjs';
import { getPool } from './db.js';

export async function openStore() {
  const pool = getPool();
  await pool.query(`
    CREATE TABLE IF NOT EXISTS users (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      email TEXT NOT NULL UNIQUE,
      password_hash TEXT NOT NULL,
      password_salt TEXT NOT NULL,
      waitlist_converted BOOLEAN NOT NULL DEFAULT FALSE,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS sessions (
      token_hash TEXT PRIMARY KEY,
      user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      expires_at TIMESTAMPTZ NOT NULL
    );
    CREATE TABLE IF NOT EXISTS profiles (
      user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
      stack JSONB NOT NULL DEFAULT '[]'::jsonb,
      weights JSONB NOT NULL DEFAULT '{}'::jsonb,
      alerts JSONB NOT NULL DEFAULT '[]'::jsonb,
      routes JSONB NOT NULL DEFAULT '[]'::jsonb,
      updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS reset_tokens (
      token_hash TEXT PRIMARY KEY,
      user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      expires_at TIMESTAMPTZ NOT NULL,
      used BOOLEAN NOT NULL DEFAULT FALSE
    );
    CREATE TABLE IF NOT EXISTS digest_subscribers (
      email TEXT PRIMARY KEY,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS digest_log (
      week TEXT PRIMARY KEY,
      sent_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      recipients INTEGER
    );
  `).catch((e) => console.error('store migrate:', e.message));

  return {
    kind: 'postgres',
    async ping() { await pool.query('SELECT 1'); return true; },
    async createUser({ email, passwordHash, passwordSalt, waitlistConverted }) {
      try {
        const { rows } = await pool.query(
          `INSERT INTO users (email, password_hash, password_salt, waitlist_converted)
           VALUES ($1,$2,$3,$4)
           RETURNING id, email, password_hash, password_salt, waitlist_converted, created_at`,
          [email, passwordHash, passwordSalt, Boolean(waitlistConverted)]);
        await pool.query('INSERT INTO profiles (user_id) VALUES ($1)', [rows[0].id]);
        return rows[0];
      } catch (err) {
        if (err.code === '23505') { const e = new Error('An account with that email already exists'); e.status = 409; throw e; }
        throw err;
      }
    },
    async findUserByEmail(email) { return (await pool.query('SELECT * FROM users WHERE email = $1', [email])).rows[0] || null; },
    async findUserById(id) { return (await pool.query('SELECT * FROM users WHERE id = $1', [id])).rows[0] || null; },
    async updatePassword(userId, passwordHash, passwordSalt) {
      const { rows } = await pool.query(
        'UPDATE users SET password_hash=$2, password_salt=$3 WHERE id=$1 RETURNING id, email, password_hash, password_salt, waitlist_converted, created_at',
        [userId, passwordHash, passwordSalt]);
      return rows[0] || null;
    },
    async markWaitlistConverted(userId) {
      const { rows } = await pool.query('UPDATE users SET waitlist_converted=TRUE WHERE id=$1 RETURNING *', [userId]);
      return rows[0] || null;
    },
    async createSession(userId, token, expiresAt) {
      await pool.query('INSERT INTO sessions (token_hash, user_id, expires_at) VALUES ($1,$2,$3)', [hashToken(token), userId, expiresAt.toISOString()]);
    },
    async userForSession(token) {
      const { rows } = await pool.query(
        'SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id WHERE s.token_hash = $1 AND s.expires_at > now()',
        [hashToken(token)]);
      return rows[0] || null;
    },
    async deleteSession(token) { await pool.query('DELETE FROM sessions WHERE token_hash = $1', [hashToken(token)]); },
    async deleteSessionsForUser(userId) { await pool.query('DELETE FROM sessions WHERE user_id = $1', [userId]); },
    async getProfile(userId) {
      const { rows } = await pool.query('SELECT * FROM profiles WHERE user_id = $1', [userId]);
      const row = rows[0];
      if (!row) return { ...emptyProfile(), updated_at: new Date().toISOString() };
      return { ...normalizeProfile(row), updated_at: row.updated_at };
    },
    async saveProfile(userId, profile) {
      const next = normalizeProfile(profile);
      const { rows } = await pool.query(
        `INSERT INTO profiles (user_id, stack, weights, alerts, routes, updated_at)
         VALUES ($1,$2::jsonb,$3::jsonb,$4::jsonb,$5::jsonb, now())
         ON CONFLICT (user_id) DO UPDATE SET stack=EXCLUDED.stack, weights=EXCLUDED.weights,
           alerts=EXCLUDED.alerts, routes=EXCLUDED.routes, updated_at=now() RETURNING *`,
        [userId, JSON.stringify(next.stack), JSON.stringify(next.weights), JSON.stringify(next.alerts), JSON.stringify(next.routes)]);
      return { ...normalizeProfile(rows[0]), updated_at: rows[0].updated_at };
    },
    async createResetToken(userId, token, expiresAt) {
      await pool.query('INSERT INTO reset_tokens (token_hash, user_id, expires_at) VALUES ($1,$2,$3)', [hashToken(token), userId, expiresAt.toISOString()]);
    },
    async consumeResetToken(token) {
      const { rows } = await pool.query(
        'UPDATE reset_tokens SET used = TRUE WHERE token_hash = $1 AND used = FALSE AND expires_at > now() RETURNING user_id',
        [hashToken(token)]);
      if (!rows[0]) return null;
      return this.findUserById(rows[0].user_id);
    },
    async addDigestSubscriber(email) {
      await pool.query('INSERT INTO digest_subscribers (email) VALUES ($1) ON CONFLICT DO NOTHING', [email]);
      return (await pool.query('SELECT count(*)::int AS n FROM digest_subscribers')).rows[0].n;
    },
    async digestDue(week) { return (await pool.query('SELECT 1 FROM digest_log WHERE week = $1', [week])).rows.length === 0; },
    async digestSubscribers() { return (await pool.query('SELECT email FROM digest_subscribers ORDER BY created_at')).rows.map((r) => r.email); },
    async digestMarkSent(week, recipients) {
      await pool.query('INSERT INTO digest_log (week, recipients) VALUES ($1,$2) ON CONFLICT DO NOTHING', [week, recipients]);
    },
    async close() {},
  };
}
