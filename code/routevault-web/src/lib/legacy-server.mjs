// Shared server-side helpers ported from staging server.js
import { randomToken, sessionExpiry } from './legacy-auth.mjs';
import { normalizeProfile, emptyProfile, needsMerge, hasPersonalData } from './legacy-profile.mjs';
import { openStore } from './store.mjs';

export const COOKIE = 'rv_session';
export const BASE = 'https://routevault.ai';

let storePromise = null;
export function getStore() {
  if (!storePromise) storePromise = openStore();
  return storePromise;
}

export function parseCookies(header) {
  const out = {};
  String(header || '').split(';').forEach((part) => {
    const idx = part.indexOf('=');
    if (idx === -1) return;
    out[part.slice(0, idx).trim()] = decodeURIComponent(part.slice(idx + 1).trim());
  });
  return out;
}

export function cookieHeader(token, { clear = false } = {}) {
  const secure = process.env.COOKIE_SECURE === '0' ? '' : '; Secure';
  if (clear) return `${COOKIE}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0${secure}`;
  return `${COOKIE}=${encodeURIComponent(token)}; Path=/; HttpOnly; SameSite=Lax; Max-Age=${30 * 24 * 60 * 60}${secure}`;
}

export function json(data, status = 200, headers = {}) {
  return new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json; charset=utf-8', ...headers } });
}

export async function readBody(request) {
  try { return await request.json(); } catch (_) { return {}; }
}

export function profilePayload(user, profile, extra = {}) {
  const p = normalizeProfile(profile);
  return {
    user: { id: user.id, email: user.email, waitlist_converted: Boolean(user.waitlist_converted), created_at: user.created_at },
    profile: { stack: p.stack, weights: p.weights, alerts: p.alerts, routes: p.routes, updated_at: profile.updated_at || null },
    ...extra,
  };
}

export async function currentUser(request) {
  const token = parseCookies(request.headers.get('cookie'))[COOKIE];
  if (!token) return null;
  const store = await getStore();
  return store.userForSession(token);
}

export async function startSession(user) {
  const token = randomToken();
  const store = await getStore();
  await store.createSession(user.id, token, sessionExpiry());
  return token;
}

export async function sendEmail(to, subject, html) {
  const key = process.env.RESEND_API_KEY;
  if (!key) throw new Error('RESEND_API_KEY not configured');
  const r = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: { Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ from: process.env.RV_EMAIL_FROM || 'RouteVault <auth@routevault.ai>', to: [to], subject, html }),
  });
  if (!r.ok) throw new Error(`Resend ${r.status}: ${await r.text()}`);
  return r.json();
}

export const magicLinkEmail = (link) => `<div style="font-family:system-ui,sans-serif;max-width:480px">
  <h2 style="margin:0 0 .5rem">Your RouteVault sign-in link</h2>
  <p style="color:#555">Click below to sign in (or create) your account. The link is single-use and valid for a short time.</p>
  <p><a href="${link}" style="display:inline-block;background:#1a365d;color:#fff;padding:.7rem 1.2rem;border-radius:8px;text-decoration:none">Sign in to RouteVault</a></p>
  <p style="color:#888;font-size:.85rem">Or paste this URL: ${link}</p>
  <p style="color:#888;font-size:.85rem">Didn't request this? Ignore this email.</p>
</div>`;

// Weekly Monday digest — started once from /api/health.
let digestStarted = false;
export function startWeeklyDigest(datasetLoader) {
  if (digestStarted) return;
  digestStarted = true;
  const fmtMoney = (n) => (n == null ? '—' : `$${Number(n).toFixed(Math.abs(n) < 0.1 ? 3 : 2)}`);
  async function tick() {
    try {
      if (!process.env.RESEND_API_KEY) return;
      const now = new Date();
      if (now.getUTCDay() !== 1) return;
      const week = now.toISOString().slice(0, 10);
      const store = await getStore();
      if (!(await store.digestDue(week))) return;
      const dataset = await datasetLoader();
      const ins = dataset.insights || {};
      const row = (m) => `<li><span class="mono">${m.model_id}</span> — ${m.rv_label} · in ${fmtMoney(m.input_price)} / out ${fmtMoney(m.output_price)} per M · Δ30d ${m.price_change_30d != null ? Number(m.price_change_30d).toFixed(1) + '%' : '—'}</li>`;
      const section = (title, items) => `<h3 style="margin:1rem 0 .3rem">${title}</h3>${items?.length ? `<ul style="padding-left:1.2rem;margin:0">${items.map(row).join('')}</ul>` : '<p style="color:#888">Nothing this week.</p>'}`;
      const html = `<div style="font-family:system-ui,sans-serif;max-width:560px">
        <h2 style="margin:0 0 .3rem">RouteVault weekly price digest</h2>
        <p style="color:#555">Week of ${week} · live OpenRouter list prices across ${dataset.model_count} models.</p>
        ${section('Value improvers (price came down)', ins.value_improvers)}
        ${section('Value regressions (price went up)', ins.value_regressions)}
        ${section('Biggest 30d price drops', ins.price_drops_30d)}
        <p style="margin-top:1.2rem"><a href="https://routevault.ai/trends">See the full trends →</a></p>
        <p style="color:#888;font-size:.85rem">You're receiving this because you subscribed at routevault.ai. One email a week, no marketing.</p>
      </div>`;
      const subs = await store.digestSubscribers();
      if (!subs.length) { await store.digestMarkSent(week, 0); return; }
      let sent = 0;
      for (const email of subs) {
        try { await sendEmail(email, `RouteVault digest — week of ${week}`, html); sent += 1; }
        catch (err) { console.error(`digest send failed for ${email}:`, err.message); }
      }
      await store.digestMarkSent(week, sent);
      console.log(`weekly digest sent to ${sent}/${subs.length} subscribers`);
    } catch (err) { console.error('weekly digest error:', err.message); }
  }
  void tick();
  setInterval(() => void tick(), 3_600_000).unref();
}
