/* RouteVault shared client: data, scoring, stack, routing, accounts. */
const RV = {
  data: null,
  user: null,
  accountsLive: false,
  syncing: false,
  weights: { reasoning: 32, coding: 25, tool_use: 18, general_intelligence: 15, context: 7, speed: 3 },
  STACK_KEY: "routevault.stack.v1",
  WEIGHT_KEY: "routevault.weights.v1",
  ALERT_KEY: "routevault.alerts.v1",
  ROUTE_KEY: "routevault.routes.v1",
  WAITLIST_KEY: "routevault.waitlist",
  SKIN_KEY: "routevault.skin.v1",
};

/* --- Skins: Obsidian (dark, default) · Vellum (light) · Neon Grid (cyberpunk) --- */
const SKINS = [
  ["obsidian", "Obsidian"],
  ["vellum", "Vellum"],
  ["neon", "Neon Grid"],
];
const SKIN_LABEL = Object.fromEntries(SKINS);

function currentSkin() {
  const s = localStorage.getItem(RV.SKIN_KEY);
  return SKINS.some(([id]) => id === s) ? s : "obsidian";
}

function applySkin(id) {
  if (!SKINS.some(([sid]) => sid === id)) id = "obsidian";
  localStorage.setItem(RV.SKIN_KEY, id);
  document.documentElement.setAttribute("data-skin", id);
  $all("[data-skin-toggle]").forEach((btn) => {
    btn.textContent = SKIN_LABEL[id];
  });
}

function cycleSkin() {
  const order = SKINS.map(([id]) => id);
  const next = order[(order.indexOf(currentSkin()) + 1) % order.length];
  applySkin(next);
}

function mountSkin() {
  applySkin(currentSkin());
}


function $(sel, root = document) { return root.querySelector(sel); }
function $all(sel, root = document) { return [...root.querySelectorAll(sel)]; }

function fmtMoney(n, digits = 2) {
  if (n == null || Number.isNaN(n)) return "—";
  const d = Math.abs(n) < 0.1 ? 3 : digits;
  return `$${Number(n).toFixed(d)}`;
}

function fmtPct(n) {
  if (n == null || Number.isNaN(n)) return "—";
  const sign = n > 0 ? "+" : "";
  return `${sign}${Number(n).toFixed(1)}%`;
}

function pctClass(n) {
  if (n == null) return "dim";
  if (n < -0.5) return "good";
  if (n > 0.5) return "bad";
  return "dim";
}

function toast(msg) {
  let el = $("#rv-toast");
  if (!el) {
    el = document.createElement("div");
    el.id = "rv-toast";
    el.className = "toast";
    document.body.appendChild(el);
  }
  el.textContent = msg;
  el.style.display = "block";
  clearTimeout(el._t);
  el._t = setTimeout(() => { el.style.display = "none"; }, 2400);
}

function loadWeights() {
  try {
    const raw = localStorage.getItem(RV.WEIGHT_KEY);
    if (raw) Object.assign(RV.weights, JSON.parse(raw));
  } catch (_) { /* ignore */ }
}

function saveWeights() {
  localStorage.setItem(RV.WEIGHT_KEY, JSON.stringify(RV.weights));
  queueCloudSync();
}

function getStack() {
  try { return JSON.parse(localStorage.getItem(RV.STACK_KEY) || "[]"); }
  catch (_) { return []; }
}

function setStack(ids) {
  const uniq = [...new Set(ids)].slice(0, 20);
  localStorage.setItem(RV.STACK_KEY, JSON.stringify(uniq));
  updateStackCount();
  queueCloudSync();
  return uniq;
}

function addToStack(modelId) {
  const ids = getStack();
  if (!ids.includes(modelId)) ids.push(modelId);
  setStack(ids);
  toast(`${modelId} saved to My Stack`);
}

function removeFromStack(modelId) {
  setStack(getStack().filter((id) => id !== modelId));
  toast(`${modelId} removed`);
}

function updateStackCount() {
  $all("[data-stack-count]").forEach((el) => {
    el.textContent = String(getStack().length);
  });
}

function getAlerts() {
  try { return JSON.parse(localStorage.getItem(RV.ALERT_KEY) || "[]"); }
  catch (_) { return []; }
}

function setAlerts(rows) {
  localStorage.setItem(RV.ALERT_KEY, JSON.stringify((rows || []).slice(-30)));
}

function addAlert(rule) {
  const rows = getAlerts();
  rows.push({ id: Date.now(), created: new Date().toISOString(), ...rule });
  setAlerts(rows);
  queueCloudSync();
}

function getRoutes() {
  try { return JSON.parse(localStorage.getItem(RV.ROUTE_KEY) || "[]"); }
  catch (_) { return []; }
}

function setRoutes(rows) {
  localStorage.setItem(RV.ROUTE_KEY, JSON.stringify((rows || []).slice(-50)));
}

function addRoute(entry) {
  const prev = getRoutes();
  prev.push(entry);
  setRoutes(prev);
  queueCloudSync();
}

function localProfile() {
  return {
    stack: getStack(),
    weights: { ...RV.weights },
    alerts: getAlerts(),
    routes: getRoutes(),
  };
}

function applyProfile(profile) {
  if (!profile) return;
  if (profile.weights) {
    Object.assign(RV.weights, profile.weights);
    localStorage.setItem(RV.WEIGHT_KEY, JSON.stringify(RV.weights));
  }
  if (profile.stack) {
    localStorage.setItem(RV.STACK_KEY, JSON.stringify(profile.stack));
    updateStackCount();
  }
  if (profile.alerts) setAlerts(profile.alerts);
  if (profile.routes) setRoutes(profile.routes);
}

function waitlistEmail() {
  return (localStorage.getItem(RV.WAITLIST_KEY) || "").trim().toLowerCase();
}

function queueCloudSync() {
  if (!RV.user || RV.syncing) return;
  clearTimeout(RV._syncTimer);
  RV._syncTimer = setTimeout(() => {
    RV._syncTimer = null;
    void pushProfile();
  }, 250);
}

function flushCloudSync() {
  if (!RV.user) return;
  try {
    fetch("/api/profile", {
      method: "PUT",
      credentials: "same-origin",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(localProfile()),
      keepalive: true,
    });
  } catch (_) { /* ignore */ }
}

function clearPersonalLocal() {
  localStorage.removeItem(RV.STACK_KEY);
  localStorage.removeItem(RV.WEIGHT_KEY);
  localStorage.removeItem(RV.ALERT_KEY);
  localStorage.removeItem(RV.ROUTE_KEY);
  RV.weights = { reasoning: 32, coding: 25, tool_use: 18, general_intelligence: 15, context: 7, speed: 3 };
  updateStackCount();
}

async function api(path, opts = {}) {
  const res = await fetch(path, {
    credentials: "same-origin",
    headers: { "content-type": "application/json", ...(opts.headers || {}) },
    ...opts,
  });
  let data = {};
  try { data = await res.json(); } catch (_) { /* ignore */ }
  if (!res.ok) {
    const err = new Error(data.error || `Request failed (${res.status})`);
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

async function pushProfile() {
  if (!RV.user) return;
  RV.syncing = true;
  try {
    await api("/api/profile", { method: "PUT", body: JSON.stringify(localProfile()) });
  } catch (err) {
    toast(err.message || "Could not sync");
  } finally {
    RV.syncing = false;
  }
}

function renderAuthNav() {
  const host = $("#rv-auth");
  if (!host) return;
  if (!RV.accountsLive) {
    host.innerHTML = `<a class="rv-cta" href="quiz.html">Find a model</a>`;
    return;
  }
  if (RV.user) {
    host.innerHTML = `<a class="rv-ghost" href="account.html">${RV.user.email}</a>
      <button class="rv-ghost" type="button" id="rv-logout">Log out</button>`;
    const btn = $("#rv-logout");
    if (btn) btn.onclick = () => void logout();
    return;
  }
  host.innerHTML = `<a class="rv-ghost" href="login.html">Log in</a>
    <a class="rv-cta" href="register.html">Create account</a>`;
}

async function refreshSession() {
  try {
    const data = await api("/api/me");
    RV.accountsLive = data.accounts !== false;
    RV.user = data.user || null;
    if (RV.user && data.profile && !sessionStorage.getItem("rv.merge.pending") && !RV._syncTimer) {
      applyProfile(data.profile);
    }
  } catch (_) {
    RV.accountsLive = false;
    RV.user = null;
  }
  renderAuthNav();
  updateStackCount();
  return RV.user;
}

async function logout() {
  try { await api("/api/logout", { method: "POST", body: "{}" }); }
  catch (_) { /* still clear local session UI */ }
  RV.user = null;
  sessionStorage.removeItem("rv.merge.pending");
  sessionStorage.removeItem("rv.merge.cloud");
  clearPersonalLocal();
  renderAuthNav();
  toast("Signed out. This browser is a guest again.");
  if (/account\.html|merge\.html$/.test(location.pathname)) location.href = "login.html";
}

function valueScore(model, weights = RV.weights) {
  const b = model.benchmarks || {};
  const map = {
    reasoning: b.reasoning || 0,
    coding: b.coding || 0,
    tool_use: b.tool_use || 0,
    general_intelligence: b.general_intelligence || b.reasoning || 0,
    context: b.context || 0,
    speed: b.speed || 0,
  };
  let num = 0, den = 0;
  for (const [k, w] of Object.entries(weights)) {
    if (!map[k] && map[k] !== 0) continue;
    num += map[k] * w;
    den += w;
  }
  if (!den) return 0;
  const avg = num / den;
  const price = model.total_price || 0;
  if (price <= 0) return Math.round(avg * 100) / 100;
  return Math.round((avg / price) * 10 * 100) / 100;
}

async function loadDataset() {
  if (RV.data) return RV.data;
  loadWeights();
  const res = await fetch("data/dataset.json", { cache: "no-store" });
  if (!res.ok) throw new Error(`dataset.json ${res.status}`);
  RV.data = await res.json();
  for (const m of RV.data.models) {
    m._liveValue = valueScore(m);
  }
  updateStackCount();
  const banner = $("[data-honesty]");
  if (banner && RV.data.honesty) banner.textContent = RV.data.honesty.banner;
  const asof = $("[data-asof]");
  if (asof) asof.textContent = `as of ${RV.data.as_of} · ${RV.data.model_count} models`;
  return RV.data;
}

function modelById(id) {
  return RV.data?.models.find((m) => m.model_id === id) || null;
}

function detailById(id) {
  return RV.data?.details?.[id] || null;
}

function navHtml(active) {
  const links = [
    ["models.html", "Explorer"],
    ["trends.html", "Trends"],
    ["route.html", "Route"],
    ["quiz.html", "Quiz"],
    ["stack.html", "My Stack"],
    ["how-we-score.html", "Scoring"],
    ["lab.html", "Local Lab"],
    ["ecosystem.html", "Harnesses"],
    ["pricing.html", "Pricing"],
  ];
  return `
    <div class="rv-banner"><span data-honesty>Loading live catalog…</span></div>
    <nav class="rv-nav"><div class="rv-nav-inner">
      <a class="rv-brand" href="index.html"><span class="rv-mark">R</span> RouteVault</a>
      <div class="rv-links">
        ${links.map(([href, label]) =>
          `<a href="${href}" class="${active === href ? "active" : ""}">${label}</a>`
        ).join("")}
      </div>
      <div style="display:flex;gap:.45rem;align-items:center;flex-wrap:wrap">
        <button class="rv-ghost" type="button" data-skin-toggle id="rv-skin" title="Change skin">Obsidian</button>
        <span id="rv-auth" style="display:flex;gap:.45rem;align-items:center;flex-wrap:wrap"></span>
      </div>
    </div></nav>`;
}

function mountNav(active) {
  mountSkin();
  const host = $("#rv-shell");
  if (host) host.insertAdjacentHTML("afterbegin", navHtml(active));
  const skinBtn = $("#rv-skin");
  if (skinBtn) skinBtn.onclick = cycleSkin;
  void refreshSession();
}

function footHtml() {
  return `<footer class="rv-foot">
    RouteVault v1a · live OpenRouter prices · Artificial Analysis indexes via OpenRouter ·
    history is weekly OpenRouter list prices (OpenRouterList, up to 6 months) ·
    accounts sync Stack in the cloud · not billed ·
    <span data-asof></span><br><br>
    RouteVault™ 2026 · © 2026 Veanox · A product of Veanox
  </footer>`;
}

function mountFoot() {
  document.body.insertAdjacentHTML("beforeend", footHtml());
}

function qs(name) {
  return new URLSearchParams(location.search).get(name);
}

const PROVIDER_COLORS = {
  anthropic: "#d4a017", openai: "#10a37f", google: "#4285f4", "x-ai": "#bfc9d1",
  "meta": "#0866ff", "mistralai": "#fa500f", "deepseek": "#4d6bfe", "qwen": "#6c5ce7",
  "z-ai": "#e0533d", "nvidia": "#76b900", "amazon-bedrock": "#ff9900", "cohere": "#39594d",
  "microsoft": "#00a4ef", "perplexity": "#20808d", "minimax": "#f03e5e", "moonshotai": "#1c1c3c",
};
function providerColor(provider) {
  const key = (provider || "").toLowerCase();
  if (PROVIDER_COLORS[key]) return PROVIDER_COLORS[key];
  let h = 0;
  for (const ch of key) h = (h * 31 + ch.charCodeAt(0)) % 360;
  return `hsl(${h}, 62%, 52%)`;
}
function providerMark(provider) {
  const color = providerColor(provider);
  const letter = (provider || "?").charAt(0).toUpperCase();
  return `<span title="${provider}" style="display:inline-grid;place-items:center;width:1.15rem;height:1.15rem;border-radius:4px;background:${color};color:#fff;font-size:.68rem;font-weight:700;vertical-align:-2px;margin-right:.45rem">${letter}</span>`;
}

function sparklineSVG(history, width = 72, height = 20) {
  const pts = (history || [])
    .map((p) => (p.price != null ? Number(p.price) : (p.input != null && p.output != null ? Number(p.input) + Number(p.output) : null)))
    .filter((v) => v != null && !Number.isNaN(v))
    .slice(-14);
  if (pts.length < 2) return `<span class="dim" style="font-size:.7rem">—</span>`;
  const min = Math.min(...pts), max = Math.max(...pts);
  const span = max - min || 1;
  const step = width / (pts.length - 1);
  const coords = pts.map((p, i) => `${(i * step).toFixed(1)},${(height - 2 - ((p - min) / span) * (height - 4)).toFixed(1)}`);
  const color = pts[pts.length - 1] <= pts[0] ? "var(--good)" : "var(--bad)";
  return `<svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" style="vertical-align:middle" aria-hidden="true">
    <polyline points="${coords.join(" ")}" fill="none" stroke="${color}" stroke-width="1.5"/>
    <circle cx="${coords[coords.length - 1].split(",")[0]}" cy="${coords[coords.length - 1].split(",")[1]}" r="1.8" fill="${color}"/>
  </svg>`;
}

function modelHistory(dataset, modelId) {
  const det = dataset?.details?.[modelId];
  return det?.price_history || [];
}

function agentPrompt(openrouterId, modelId) {
  return `Use my RouteVault pick for this task: model "${openrouterId}" (RouteVault id: ${modelId}) served via OpenRouter.

Setup:
1. Use OPENROUTER_API_KEY from the environment (or .env). Base URL: https://openrouter.ai/api/v1
2. Set the default model for chat/completions to "${openrouterId}".
3. Send one short test completion and one streaming request; print the model id from each response to confirm routing.
4. If the model rejects a request (context length, moderation, capacity), say so plainly and suggest the next model on the same equivalence tier from https://routevault.ai rather than silently switching providers.

Keep all other settings at their defaults. Do not print the API key.`;
}

async function copyAgentPrompt(openrouterId, modelId) {
  const text = agentPrompt(openrouterId, modelId);
  try {
    await navigator.clipboard.writeText(text);
    toast("Agent prompt copied — paste it into Claude Code / Codex / your agent");
  } catch (_) {
    toast("Copy failed — check clipboard permissions");
  }
}

function labelOptions(models) {
  return [...new Set(models.map((m) => m.rv_label))].sort();
}

function routeForTier(tierName, models) {
  const spec = (RV.data?.equivalence || []).find((t) => t.tier === tierName);
  if (!spec) return null;
  const pick = models.find((m) => m.model_id === spec.pick);
  return { spec, pick };
}

function savingsVs(current, candidate) {
  if (!current || !candidate) return null;
  const a = current.total_price;
  const b = candidate.total_price;
  if (!a) return null;
  const pct = ((a - b) / a) * 100;
  const monthly = Math.max(0, (current.monthly_est || 0) - (candidate.monthly_est || 0));
  return { pct, monthly, from: current.model_id, to: candidate.model_id };
}

window.RV = RV;
window.loadDataset = loadDataset;
window.addToStack = addToStack;
window.removeFromStack = removeFromStack;
window.getStack = getStack;
window.valueScore = valueScore;
window.fmtMoney = fmtMoney;
window.fmtPct = fmtPct;
window.pctClass = pctClass;
window.mountNav = mountNav;
window.mountFoot = mountFoot;
window.modelById = modelById;
window.detailById = detailById;
window.qs = qs;
window.copyAgentPrompt = copyAgentPrompt;
window.providerMark = providerMark;
window.providerColor = providerColor;
window.sparklineSVG = sparklineSVG;
window.modelHistory = modelHistory;
window.toast = toast;
window.labelOptions = labelOptions;
window.routeForTier = routeForTier;
window.savingsVs = savingsVs;
window.addAlert = addAlert;
window.getAlerts = getAlerts;
window.saveWeights = saveWeights;
window.loadWeights = loadWeights;
window.getRoutes = getRoutes;
window.addRoute = addRoute;
window.localProfile = localProfile;
window.applyProfile = applyProfile;
window.waitlistEmail = waitlistEmail;
window.api = api;
window.applySkin = applySkin;
window.cycleSkin = cycleSkin;
window.currentSkin = currentSkin;
window.refreshSession = refreshSession;
window.logout = logout;
window.pushProfile = pushProfile;
window.clearPersonalLocal = clearPersonalLocal;
window.addEventListener("pagehide", flushCloudSync);
