const { emptyProfile, normalizeProfile } = require("./profile");
const { hashToken } = require("./auth");

function newId() {
  return require("crypto").randomUUID();
}

function createMemoryStore() {
  const users = new Map();
  const usersByEmail = new Map();
  const sessions = new Map();
  const profiles = new Map();
  const resets = new Map();

  return {
    kind: "memory",
    async ping() {
      return true;
    },
    async migrate() {},
    async addDigestSubscriber(email) { return 1; },
    async digestDue() { return false; },
    async digestSubscribers() { return []; },
    async digestMarkSent() {},
    async createUser({ email, passwordHash, passwordSalt, waitlistConverted }) {
      if (usersByEmail.has(email)) {
        const err = new Error("An account with that email already exists");
        err.status = 409;
        throw err;
      }
      const user = {
        id: newId(),
        email,
        password_hash: passwordHash,
        password_salt: passwordSalt,
        waitlist_converted: Boolean(waitlistConverted),
        created_at: new Date().toISOString(),
      };
      users.set(user.id, user);
      usersByEmail.set(email, user);
      profiles.set(user.id, { ...emptyProfile(), updated_at: new Date().toISOString() });
      return user;
    },
    async findUserByEmail(email) {
      return usersByEmail.get(email) || null;
    },
    async findUserById(id) {
      return users.get(id) || null;
    },
    async updatePassword(userId, passwordHash, passwordSalt) {
      const user = users.get(userId);
      if (!user) return null;
      user.password_hash = passwordHash;
      user.password_salt = passwordSalt;
      return user;
    },
    async markWaitlistConverted(userId) {
      const user = users.get(userId);
      if (user) user.waitlist_converted = true;
      return user;
    },
    async createSession(userId, token, expiresAt) {
      sessions.set(hashToken(token), {
        user_id: userId,
        expires_at: expiresAt.toISOString(),
      });
    },
    async userForSession(token) {
      const row = sessions.get(hashToken(token));
      if (!row) return null;
      if (new Date(row.expires_at) <= new Date()) {
        sessions.delete(hashToken(token));
        return null;
      }
      return users.get(row.user_id) || null;
    },
    async deleteSession(token) {
      sessions.delete(hashToken(token));
    },
    async deleteSessionsForUser(userId) {
      for (const [key, row] of sessions) {
        if (row.user_id === userId) sessions.delete(key);
      }
    },
    async getProfile(userId) {
      return profiles.get(userId) || { ...emptyProfile(), updated_at: new Date().toISOString() };
    },
    async saveProfile(userId, profile) {
      const saved = { ...normalizeProfile(profile), updated_at: new Date().toISOString() };
      profiles.set(userId, saved);
      return saved;
    },
    async createResetToken(userId, token, expiresAt) {
      resets.set(hashToken(token), {
        user_id: userId,
        expires_at: expiresAt.toISOString(),
        used: false,
      });
    },
    async consumeResetToken(token) {
      const key = hashToken(token);
      const row = resets.get(key);
      if (!row || row.used || new Date(row.expires_at) <= new Date()) return null;
      row.used = true;
      return users.get(row.user_id) || null;
    },
    async close() {},
  };
}

function createPostgresStore(pool) {
  return {
    kind: "postgres",
    async ping() {
      await pool.query("SELECT 1");
      return true;
    },
    async migrate() {
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
          recipients INTEGER NOT NULL
        );
      `);
    },
    async addDigestSubscriber(email) {
      await pool.query(`INSERT INTO digest_subscribers (email) VALUES ($1) ON CONFLICT DO NOTHING`, [email]);
      const { rows } = await pool.query(`SELECT count(*)::int AS n FROM digest_subscribers`);
      return rows[0].n;
    },
    async digestDue(week) {
      const { rows } = await pool.query(`SELECT 1 FROM digest_log WHERE week = $1`, [week]);
      return rows.length === 0;
    },
    async digestSubscribers() {
      const { rows } = await pool.query(`SELECT email FROM digest_subscribers ORDER BY created_at`);
      return rows.map((r) => r.email);
    },
    async digestMarkSent(week, recipients) {
      await pool.query(`INSERT INTO digest_log (week, recipients) VALUES ($1, $2) ON CONFLICT DO NOTHING`, [week, recipients]);
    },
    async createUser({ email, passwordHash, passwordSalt, waitlistConverted }) {
      try {
        const { rows } = await pool.query(
          `INSERT INTO users (email, password_hash, password_salt, waitlist_converted)
           VALUES ($1, $2, $3, $4)
           RETURNING id, email, password_hash, password_salt, waitlist_converted, created_at`,
          [email, passwordHash, passwordSalt, Boolean(waitlistConverted)],
        );
        const user = rows[0];
        await pool.query(`INSERT INTO profiles (user_id) VALUES ($1)`, [user.id]);
        return user;
      } catch (err) {
        if (err.code === "23505") {
          const conflict = new Error("An account with that email already exists");
          conflict.status = 409;
          throw conflict;
        }
        throw err;
      }
    },
    async findUserByEmail(email) {
      const { rows } = await pool.query(`SELECT * FROM users WHERE email = $1`, [email]);
      return rows[0] || null;
    },
    async findUserById(id) {
      const { rows } = await pool.query(`SELECT * FROM users WHERE id = $1`, [id]);
      return rows[0] || null;
    },
    async updatePassword(userId, passwordHash, passwordSalt) {
      const { rows } = await pool.query(
        `UPDATE users SET password_hash = $2, password_salt = $3 WHERE id = $1
         RETURNING id, email, password_hash, password_salt, waitlist_converted, created_at`,
        [userId, passwordHash, passwordSalt],
      );
      return rows[0] || null;
    },
    async markWaitlistConverted(userId) {
      const { rows } = await pool.query(
        `UPDATE users SET waitlist_converted = TRUE WHERE id = $1
         RETURNING id, email, password_hash, password_salt, waitlist_converted, created_at`,
        [userId],
      );
      return rows[0] || null;
    },
    async createSession(userId, token, expiresAt) {
      await pool.query(
        `INSERT INTO sessions (token_hash, user_id, expires_at) VALUES ($1, $2, $3)`,
        [hashToken(token), userId, expiresAt.toISOString()],
      );
    },
    async userForSession(token) {
      const { rows } = await pool.query(
        `SELECT u.* FROM sessions s
         JOIN users u ON u.id = s.user_id
         WHERE s.token_hash = $1 AND s.expires_at > now()`,
        [hashToken(token)],
      );
      return rows[0] || null;
    },
    async deleteSession(token) {
      await pool.query(`DELETE FROM sessions WHERE token_hash = $1`, [hashToken(token)]);
    },
    async deleteSessionsForUser(userId) {
      await pool.query(`DELETE FROM sessions WHERE user_id = $1`, [userId]);
    },
    async getProfile(userId) {
      const { rows } = await pool.query(`SELECT * FROM profiles WHERE user_id = $1`, [userId]);
      const row = rows[0];
      if (!row) return { ...emptyProfile(), updated_at: new Date().toISOString() };
      return {
        ...normalizeProfile(row),
        updated_at: row.updated_at,
      };
    },
    async saveProfile(userId, profile) {
      const next = normalizeProfile(profile);
      const { rows } = await pool.query(
        `INSERT INTO profiles (user_id, stack, weights, alerts, routes, updated_at)
         VALUES ($1, $2::jsonb, $3::jsonb, $4::jsonb, $5::jsonb, now())
         ON CONFLICT (user_id) DO UPDATE SET
           stack = EXCLUDED.stack,
           weights = EXCLUDED.weights,
           alerts = EXCLUDED.alerts,
           routes = EXCLUDED.routes,
           updated_at = now()
         RETURNING *`,
        [userId, JSON.stringify(next.stack), JSON.stringify(next.weights), JSON.stringify(next.alerts), JSON.stringify(next.routes)],
      );
      return { ...normalizeProfile(rows[0]), updated_at: rows[0].updated_at };
    },
    async createResetToken(userId, token, expiresAt) {
      await pool.query(
        `INSERT INTO reset_tokens (token_hash, user_id, expires_at) VALUES ($1, $2, $3)`,
        [hashToken(token), userId, expiresAt.toISOString()],
      );
    },
    async consumeResetToken(token) {
      const { rows } = await pool.query(
        `UPDATE reset_tokens SET used = TRUE
         WHERE token_hash = $1 AND used = FALSE AND expires_at > now()
         RETURNING user_id`,
        [hashToken(token)],
      );
      if (!rows[0]) return null;
      return this.findUserById(rows[0].user_id);
    },
    async close() {
      await pool.end();
    },
  };
}

async function openStore(env = process.env) {
  if (env.RV_STORE === "memory" || !env.DATABASE_URL) {
    return createMemoryStore();
  }
  const { Pool } = require("pg");
  const pool = new Pool({
    connectionString: env.DATABASE_URL,
    ssl: env.DATABASE_SSL === "0" ? false : undefined,
    max: 5,
  });
  const store = createPostgresStore(pool);
  await store.migrate();
  return store;
}

module.exports = { openStore, createMemoryStore, createPostgresStore };
