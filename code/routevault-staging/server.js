const http = require("http");
const fs = require("fs");
const path = require("path");
const { openStore } = require("./lib/store");
const {
  normalizeEmail,
  validEmail,
  validPassword,
  hashPassword,
  verifyPassword,
  randomToken,
  sessionExpiry,
  resetExpiry,
  publicUser,
} = require("./lib/auth");
const {
  emptyProfile,
  normalizeProfile,
  hasPersonalData,
  needsMerge,
  mergeProfiles,
  applyPatch,
} = require("./lib/profile");

const ROOT = __dirname;
const COOKIE = "rv_session";
const MIME = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".md": "text/markdown; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".ico": "image/x-icon",
  ".txt": "text/plain; charset=utf-8",
};

function parseCookies(header) {
  const out = {};
  String(header || "")
    .split(";")
    .forEach((part) => {
      const idx = part.indexOf("=");
      if (idx === -1) return;
      out[part.slice(0, idx).trim()] = decodeURIComponent(part.slice(idx + 1).trim());
    });
  return out;
}

function cookieHeader(token, { clear = false } = {}) {
  const secure = process.env.COOKIE_SECURE === "0" ? "" : "; Secure";
  if (clear) {
    return `${COOKIE}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0${secure}`;
  }
  return `${COOKIE}=${encodeURIComponent(token)}; Path=/; HttpOnly; SameSite=Lax; Max-Age=${30 * 24 * 60 * 60}${secure}`;
}

function send(res, status, body, headers = {}) {
  const payload = typeof body === "string" || Buffer.isBuffer(body) ? body : JSON.stringify(body);
  const extra = typeof body === "object" && !Buffer.isBuffer(body) && typeof body !== "string"
    ? { "Content-Type": "application/json; charset=utf-8" }
    : {};
  res.writeHead(status, { ...extra, ...headers });
  res.end(payload);
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let size = 0;
    req.on("data", (chunk) => {
      size += chunk.length;
      if (size > 200_000) {
        reject(Object.assign(new Error("Body too large"), { status: 413 }));
        req.destroy();
        return;
      }
      chunks.push(chunk);
    });
    req.on("end", () => {
      const raw = Buffer.concat(chunks).toString("utf8");
      if (!raw) return resolve({});
      try {
        resolve(JSON.parse(raw));
      } catch (_) {
        reject(Object.assign(new Error("Invalid JSON"), { status: 400 }));
      }
    });
    req.on("error", reject);
  });
}

function safeJoin(root, urlPath) {
  const decoded = decodeURIComponent((urlPath || "/").split("?")[0]);
  const cleaned = decoded.replace(/\\/g, "/");
  if (cleaned.includes("\0") || cleaned.includes("..")) return null;
  const rel = cleaned === "/" ? "index.html" : cleaned.replace(/^\/+/, "");
  const abs = path.normalize(path.join(root, rel));
  if (!abs.startsWith(root)) return null;
  return abs;
}

function profilePayload(user, profile, extra = {}) {
  const p = normalizeProfile(profile);
  return {
    user: publicUser(user),
    profile: {
      stack: p.stack,
      weights: p.weights,
      alerts: p.alerts,
      routes: p.routes,
      updated_at: profile.updated_at || null,
    },
    ...extra,
  };
}

async function createApp(options = {}) {
  const store = options.store || (await openStore(options.env || process.env));
  const resetTokens = new Map();

  async function currentUser(req) {
    const token = parseCookies(req.headers.cookie)[COOKIE];
    if (!token) return null;
    return store.userForSession(token);
  }

  async function requireUser(req, res) {
    const user = await currentUser(req);
    if (!user) {
      send(res, 401, { error: "Sign in required" });
      return null;
    }
    return user;
  }

  async function startSession(res, user) {
    const token = randomToken();
    await store.createSession(user.id, token, sessionExpiry());
    return token;
  }

  async function sendEmail(to, subject, html) {
    const key = process.env.RESEND_API_KEY;
    if (!key) throw new Error("RESEND_API_KEY not configured");
    const r = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        from: process.env.RV_EMAIL_FROM || "RouteVault <auth@routevault.ai>",
        to: [to],
        subject,
        html,
      }),
    });
    if (!r.ok) throw new Error(`Resend ${r.status}: ${await r.text()}`);
    return r.json();
  }

  function magicLinkEmail(link) {
    return `<div style="font-family:system-ui,sans-serif;max-width:480px">
      <h2 style="margin:0 0 .5rem">Your RouteVault sign-in link</h2>
      <p style="color:#555">Click below to sign in (or create) your account. The link is single-use and valid for a short time.</p>
      <p><a href="${link}" style="display:inline-block;background:#1a365d;color:#fff;padding:.7rem 1.2rem;border-radius:8px;text-decoration:none">Sign in to RouteVault</a></p>
      <p style="color:#888;font-size:.85rem">Or paste this URL: ${link}</p>
      <p style="color:#888;font-size:.85rem">Didn't request this? Ignore this email.</p>
    </div>`;
  }

  const server = http.createServer(async (req, res) => {
    try {
      const url = new URL(req.url, "http://localhost");
      if (url.pathname === "/api/health") {
        await store.ping();
        let newsCount = 0;
        try {
          const newsPath = path.join(ROOT, "data", "news.json");
          if (fs.existsSync(newsPath)) {
            newsCount = JSON.parse(fs.readFileSync(newsPath, "utf8")).count || 0;
          }
        } catch (_) {}
        return send(res, 200, { ok: true, store: store.kind, accounts: true, news: newsCount });
      }

      if (url.pathname === "/api/news" && req.method === "GET") {
        const newsPath = path.join(ROOT, "data", "news.json");
        if (!fs.existsSync(newsPath)) return send(res, 200, { count: 0, items: [], generated_at: null });
        const payload = JSON.parse(fs.readFileSync(newsPath, "utf8"));
        return send(res, 200, payload);
      }

      if (url.pathname === "/api/discoveries" && req.method === "GET") {
        const discPath = path.join(ROOT, "data", "discovered_models.json");
        if (!fs.existsSync(discPath)) return send(res, 200, { count: 0, models: [] });
        return send(res, 200, JSON.parse(fs.readFileSync(discPath, "utf8")));
      }

      if (url.pathname === "/api/me" && req.method === "GET") {
        const user = await currentUser(req);
        if (!user) return send(res, 200, { user: null, accounts: true });
        const profile = await store.getProfile(user.id);
        return send(res, 200, profilePayload(user, profile, { accounts: true }));
      }

      if (url.pathname === "/api/register" && req.method === "POST") {
        const body = await readBody(req);
        const email = normalizeEmail(body.email);
        if (!validEmail(email)) return send(res, 400, { error: "Enter a valid email" });
        if (!validPassword(body.password)) return send(res, 400, { error: "Password must be at least 8 characters" });
        const { hash, salt } = hashPassword(body.password);
        const user = await store.createUser({
          email,
          passwordHash: hash,
          passwordSalt: salt,
          waitlistConverted: Boolean(body.waitlist),
        });
        const token = await startSession(res, user);
        const profile = await store.getProfile(user.id);
        const local = normalizeProfile(body.local || {});
        return send(res, 201, profilePayload(user, profile, {
          needs_merge: needsMerge(local, emptyProfile()) ? false : needsMerge(local, profile),
          local_has_data: hasPersonalData(local),
        }), { "Set-Cookie": cookieHeader(token) });
      }

      if (url.pathname === "/api/login" && req.method === "POST") {
        const body = await readBody(req);
        const email = normalizeEmail(body.email);
        const user = validEmail(email) ? await store.findUserByEmail(email) : null;
        if (!user || !verifyPassword(body.password || "", user.password_salt, user.password_hash)) {
          return send(res, 401, { error: "Email or password is wrong" });
        }
        if (body.waitlist) await store.markWaitlistConverted(user.id);
        const fresh = await store.findUserById(user.id);
        const token = await startSession(res, fresh);
        const profile = await store.getProfile(fresh.id);
        const local = normalizeProfile(body.local || {});
        return send(res, 200, profilePayload(fresh, profile, {
          needs_merge: needsMerge(local, profile),
          local_has_data: hasPersonalData(local),
        }), { "Set-Cookie": cookieHeader(token) });
      }

      if (url.pathname === "/api/logout" && req.method === "POST") {
        const token = parseCookies(req.headers.cookie)[COOKIE];
        if (token) await store.deleteSession(token);
        return send(res, 200, { ok: true, user: null }, { "Set-Cookie": cookieHeader("", { clear: true }) });
      }

      if (url.pathname === "/api/magic/request" && req.method === "POST") {
        const body = await readBody(req);
        const email = normalizeEmail(body.email);
        if (!validEmail(email)) return send(res, 400, { error: "Enter a valid email" });
        if (!process.env.RESEND_API_KEY) return send(res, 503, { error: "Email sign-in is not configured yet" });
        let user = await store.findUserByEmail(email);
        if (!user) {
          const { hash, salt } = hashPassword(randomToken()); // passwordless start; user can set one via reset later
          user = await store.createUser({ email, passwordHash: hash, passwordSalt: salt, waitlistConverted: false });
        }
        const token = randomToken();
        await store.createResetToken(user.id, token, resetExpiry());
        const base = `https://${req.headers.host || "routevault.ai"}`;
        const link = `${base}/api/magic/verify?token=${encodeURIComponent(token)}`;
        try {
          await sendEmail(email, "Your RouteVault sign-in link", magicLinkEmail(link));
        } catch (err) {
          console.error("magic link email failed:", err.message);
          return send(res, 502, { error: "Could not send the email right now. Try again shortly." });
        }
        return send(res, 200, { ok: true, message: "Check your inbox — the link is single-use and expires soon." });
      }

      if (url.pathname === "/api/magic/verify" && req.method === "GET") {
        const token = url.searchParams.get("token") || "";
        const user = await store.consumeResetToken(token);
        if (!user) {
          return send(res, 200, `<!DOCTYPE html><html><head><meta charset="utf-8"><title>RouteVault</title></head><body style="font-family:system-ui;display:grid;place-items:center;height:100vh;margin:0"><div style="text-align:center"><h1>Link expired</h1><p>This sign-in link is invalid or already used.</p><p><a href="/login.html">Request a new one</a></p></div></body></html>`);
        }
        const token2 = await startSession(res, user);
        const base = `https://${req.headers.host || "routevault.ai"}`;
        return send(res, 302, "", { "Set-Cookie": cookieHeader(token2), Location: `${base}/account.html` });
      }

      if (url.pathname === "/api/password/forgot" && req.method === "POST") {
        const body = await readBody(req);
        const email = normalizeEmail(body.email);
        const user = validEmail(email) ? await store.findUserByEmail(email) : null;
        let issued = null;
        if (user) {
          const token = randomToken();
          await store.createResetToken(user.id, token, resetExpiry());
          if (process.env.RV_RETURN_RESET_TOKEN === "1") {
            issued = token;
            resetTokens.set(email, token);
          }
        }
        const payload = { ok: true, message: "If that email has an account, a reset token was issued." };
        if (issued) payload.reset_token = issued;
        return send(res, 200, payload);
      }

      if (url.pathname === "/api/password/reset" && req.method === "POST") {
        const body = await readBody(req);
        if (!validPassword(body.password)) return send(res, 400, { error: "Password must be at least 8 characters" });
        const user = await store.consumeResetToken(body.token || "");
        if (!user) return send(res, 400, { error: "Reset link is invalid or expired" });
        const { hash, salt } = hashPassword(body.password);
        await store.updatePassword(user.id, hash, salt);
        await store.deleteSessionsForUser(user.id);
        const token = await startSession(res, user);
        const profile = await store.getProfile(user.id);
        return send(res, 200, profilePayload(user, profile), { "Set-Cookie": cookieHeader(token) });
      }

      if (url.pathname === "/api/profile" && req.method === "GET") {
        const user = await requireUser(req, res);
        if (!user) return;
        const profile = await store.getProfile(user.id);
        const local = url.searchParams.get("local") === "1" ? emptyProfile() : null;
        return send(res, 200, profilePayload(user, profile, {
          needs_merge: false,
        }));
      }

      if (url.pathname === "/api/profile" && req.method === "PUT") {
        const user = await requireUser(req, res);
        if (!user) return;
        const body = await readBody(req);
        const current = await store.getProfile(user.id);
        const next = applyPatch(current, body);
        const saved = await store.saveProfile(user.id, next);
        return send(res, 200, profilePayload(user, saved));
      }

      if (url.pathname === "/api/profile/merge" && req.method === "POST") {
        const user = await requireUser(req, res);
        if (!user) return;
        const body = await readBody(req);
        const strategy = body.strategy || "union";
        const cloud = await store.getProfile(user.id);
        const local = normalizeProfile(body.local || {});
        const merged = mergeProfiles(local, cloud, strategy);
        const saved = await store.saveProfile(user.id, merged);
        return send(res, 200, profilePayload(user, saved, { strategy }));
      }

      if (url.pathname === "/api/digest/subscribe" && req.method === "POST") {
        const body = await readBody(req);
        const email = normalizeEmail(body.email);
        if (!validEmail(email)) return send(res, 400, { error: "Enter a valid email" });
        const count = await store.addDigestSubscriber(email);
        try {
          await sendEmail(email, "You're on the RouteVault weekly price digest",
            `<div style="font-family:system-ui,sans-serif;max-width:480px">
              <p>You'll get one short email each Monday: the week's biggest value improvers, regressions, and price drops across the catalog.</p>
              <p style="color:#888;font-size:.85rem">No marketing, no card, one email a week. Manage nothing — if you want off, reply and we'll remove you.</p>
            </div>`);
        } catch (err) {
          console.error("digest welcome email failed:", err.message);
        }
        return send(res, 200, { ok: true, message: `Subscribed. ${count} subscriber(s) on the list — first email lands Monday.` });
      }

      if (url.pathname.startsWith("/api/")) {
        return send(res, 404, { error: "Not found" });
      }

      if (req.method !== "GET" && req.method !== "HEAD") {
        return send(res, 405, { error: "Method not allowed" });
      }

      let filePath = safeJoin(ROOT, url.pathname);
      if (!filePath) return send(res, 400, "Bad path");
      if (fs.existsSync(filePath) && fs.statSync(filePath).isDirectory()) {
        filePath = path.join(filePath, "index.html");
      }
      if (!fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
        // Extensionless page routes: /route -> /route.html
        const withHtml = `${filePath}.html`;
        if (fs.existsSync(withHtml) && fs.statSync(withHtml).isFile()) {
          filePath = withHtml;
        } else {
          return send(res, 404, "Not found");
        }
      }
      const ext = path.extname(filePath).toLowerCase();
      const body = fs.readFileSync(filePath);
      const headers = { "Content-Type": MIME[ext] || "application/octet-stream" };
      // Static assets (css/js/json): short cache so deploys reach browsers quickly.
      // HTML: revalidate every time.
      if ([".css", ".js", ".json"].includes(ext)) {
        headers["Cache-Control"] = "public, max-age=300, must-revalidate";
      } else if (ext === ".html") {
        headers["Cache-Control"] = "no-cache";
      }
      return send(res, 200, body, headers);
    } catch (err) {
      const status = err.status || 500;
      if (status >= 500) console.error(err);
      return send(res, status, { error: err.message || "Server error" });
    }
  });

  server.store = store;
  server._resetTokens = resetTokens;

  // Weekly price digest: sent Mondays (UTC) to digest_subscribers, once per week.
  async function sendWeeklyDigest() {
    try {
      if (!process.env.RESEND_API_KEY) return;
      const now = new Date();
      if (now.getUTCDay() !== 1) return; // Monday
      const week = now.toISOString().slice(0, 10);
      if (!(await store.digestDue(week))) return;
      const dataset = JSON.parse(fs.readFileSync(path.join(ROOT, "data", "dataset.json"), "utf8"));
      const ins = dataset.insights || {};
      const row = (m) => `<li><span class="mono">${m.model_id}</span> — ${m.rv_label} · in ${fmtMoney2(m.input_price)} / out ${fmtMoney2(m.output_price)} per M · Δ30d ${m.price_change_30d != null ? m.price_change_30d.toFixed(1) + "%" : "—"}</li>`;
      const section = (title, items) => `<h3 style="margin:1rem 0 .3rem">${title}</h3>${items?.length ? `<ul style="padding-left:1.2rem;margin:0">${items.map(row).join("")}</ul>` : `<p style="color:#888">Nothing this week.</p>`}`;
      const html = `<div style="font-family:system-ui,sans-serif;max-width:560px">
        <h2 style="margin:0 0 .3rem">RouteVault weekly price digest</h2>
        <p style="color:#555">Week of ${week} · live OpenRouter list prices across ${dataset.model_count} models.</p>
        ${section("Value improvers (price came down)", ins.value_improvers)}
        ${section("Value regressions (price went up)", ins.value_regressions)}
        ${section("Biggest 30d price drops", ins.price_drops_30d)}
        <p style="margin-top:1.2rem"><a href="https://routevault.ai/trends.html">See the full trends →</a></p>
        <p style="color:#888;font-size:.85rem">You're receiving this because you subscribed at routevault.ai. One email a week, no marketing.</p>
      </div>`;
      const subs = await store.digestSubscribers();
      if (!subs.length) { await store.digestMarkSent(week, 0); return; }
      let sent = 0;
      for (const email of subs) {
        try {
          await sendEmail(email, `RouteVault digest — week of ${week}`, html);
          sent += 1;
        } catch (err) {
          console.error(`digest send failed for ${email}:`, err.message);
        }
      }
      await store.digestMarkSent(week, sent);
      console.log(`weekly digest sent to ${sent}/${subs.length} subscribers`);
    } catch (err) {
      console.error("weekly digest error:", err.message);
    }
  }
  function fmtMoney2(n) { return n == null ? "—" : `$${Number(n).toFixed(Math.abs(n) < 0.1 ? 3 : 2)}`; }
  void sendWeeklyDigest();
  setInterval(() => void sendWeeklyDigest(), 60 * 60 * 1000).unref();
  return server;
}

async function main() {
  const port = Number(process.env.PORT || 8080);
  const server = await createApp();
  server.listen(port, "0.0.0.0", () => {
    console.log(`RouteVault listening on ${port} (${server.store.kind})`);
  });
}

if (require.main === module) {
  main().catch((err) => {
    console.error(err);
    process.exit(1);
  });
}

module.exports = { createApp, cookieHeader, COOKIE };
