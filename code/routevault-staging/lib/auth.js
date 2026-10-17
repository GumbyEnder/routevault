const crypto = require("crypto");

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const SCRYPT_KEYLEN = 64;
const SESSION_DAYS = 30;

function normalizeEmail(email) {
  return String(email || "").trim().toLowerCase();
}

function validEmail(email) {
  return EMAIL_RE.test(normalizeEmail(email));
}

function validPassword(password) {
  return typeof password === "string" && password.length >= 8 && password.length <= 200;
}

function hashPassword(password) {
  const salt = crypto.randomBytes(16).toString("hex");
  const hash = crypto.scryptSync(password, salt, SCRYPT_KEYLEN).toString("hex");
  return { salt, hash };
}

function verifyPassword(password, salt, expectedHash) {
  try {
    const actual = crypto.scryptSync(password, salt, SCRYPT_KEYLEN);
    const expected = Buffer.from(expectedHash, "hex");
    if (actual.length !== expected.length) return false;
    return crypto.timingSafeEqual(actual, expected);
  } catch (_) {
    return false;
  }
}

function randomToken() {
  return crypto.randomBytes(32).toString("hex");
}

function hashToken(token) {
  return crypto.createHash("sha256").update(String(token)).digest("hex");
}

function sessionExpiry(from = new Date()) {
  return new Date(from.getTime() + SESSION_DAYS * 24 * 60 * 60 * 1000);
}

function resetExpiry(from = new Date()) {
  return new Date(from.getTime() + 60 * 60 * 1000);
}

function publicUser(row) {
  if (!row) return null;
  return {
    id: row.id,
    email: row.email,
    waitlist_converted: Boolean(row.waitlist_converted),
    created_at: row.created_at,
  };
}

module.exports = {
  SESSION_DAYS,
  normalizeEmail,
  validEmail,
  validPassword,
  hashPassword,
  verifyPassword,
  randomToken,
  hashToken,
  sessionExpiry,
  resetExpiry,
  publicUser,
};
