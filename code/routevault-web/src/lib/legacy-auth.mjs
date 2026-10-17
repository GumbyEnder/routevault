// ESM port of staging lib/auth.js — identical hashing so existing accounts work.
import crypto from 'node:crypto';

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const SCRYPT_KEYLEN = 64;
export const SESSION_DAYS = 30;

export const normalizeEmail = (email) => String(email || '').trim().toLowerCase();
export const validEmail = (email) => EMAIL_RE.test(normalizeEmail(email));
export const validPassword = (p) => typeof p === 'string' && p.length >= 8 && p.length <= 200;

export function hashPassword(password) {
  const salt = crypto.randomBytes(16).toString('hex');
  const hash = crypto.scryptSync(password, salt, SCRYPT_KEYLEN).toString('hex');
  return { salt, hash };
}

export function verifyPassword(password, salt, expectedHash) {
  try {
    const actual = crypto.scryptSync(password, salt, SCRYPT_KEYLEN);
    const expected = Buffer.from(expectedHash, 'hex');
    if (actual.length !== expected.length) return false;
    return crypto.timingSafeEqual(actual, expected);
  } catch (_) { return false; }
}

export const randomToken = () => crypto.randomBytes(32).toString('hex');
export const hashToken = (token) => crypto.createHash('sha256').update(String(token)).digest('hex');
export const sessionExpiry = (from = new Date()) => new Date(from.getTime() + SESSION_DAYS * 86400_000);
export const resetExpiry = (from = new Date()) => new Date(from.getTime() + 3_600_000);
export function publicUser(row) {
  if (!row) return null;
  return { id: row.id, email: row.email, waitlist_converted: Boolean(row.waitlist_converted), created_at: row.created_at };
}
