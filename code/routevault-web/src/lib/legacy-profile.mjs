// ESM port of staging lib/profile.js — identical normalization/merge semantics.
export const DEFAULT_WEIGHTS = { reasoning: 32, coding: 25, tool_use: 18, general_intelligence: 15, context: 7, speed: 3 };
export const CAPS = { stack: 20, alerts: 30, routes: 50 };
const asArray = (v) => (Array.isArray(v) ? v : []);

export function normalizeWeights(raw) {
  const src = raw && typeof raw === 'object' ? raw : {};
  const out = { ...DEFAULT_WEIGHTS };
  for (const key of Object.keys(DEFAULT_WEIGHTS)) {
    const n = Number(src[key]);
    if (Number.isFinite(n)) out[key] = n;
  }
  return out;
}
export function normalizeStack(raw) {
  const ids = asArray(raw).map((id) => String(id || '').trim()).filter(Boolean);
  return [...new Set(ids)].slice(0, CAPS.stack);
}
export function normalizeAlerts(raw) {
  return asArray(raw).map((row) => {
    if (!row || typeof row !== 'object') return null;
    const model_id = String(row.model_id || '').trim();
    if (!model_id) return null;
    const below = Number(row.below);
    return { id: row.id ?? Date.now(), created: row.created || new Date().toISOString(), model_id, below: Number.isFinite(below) ? below : -5 };
  }).filter(Boolean).slice(-CAPS.alerts);
}
export function normalizeRoutes(raw) {
  return asArray(raw).filter((row) => row && typeof row === 'object').slice(-CAPS.routes);
}
export function emptyProfile() {
  return { stack: [], weights: { ...DEFAULT_WEIGHTS }, alerts: [], routes: [] };
}
export function normalizeProfile(raw) {
  const src = raw && typeof raw === 'object' ? raw : {};
  return { stack: normalizeStack(src.stack), weights: normalizeWeights(src.weights), alerts: normalizeAlerts(src.alerts), routes: normalizeRoutes(src.routes) };
}
const weightsAreDefault = (w) => JSON.stringify(normalizeWeights(w)) === JSON.stringify(DEFAULT_WEIGHTS);
export function hasPersonalData(profile) {
  const p = normalizeProfile(profile);
  return p.stack.length > 0 || p.alerts.length > 0 || p.routes.length > 0 || !weightsAreDefault(p.weights);
}
const profilesEqual = (a, b) => JSON.stringify(normalizeProfile(a)) === JSON.stringify(normalizeProfile(b));
export function needsMerge(local, cloud) {
  return hasPersonalData(local) && hasPersonalData(cloud) && !profilesEqual(local, cloud);
}
const alertKey = (r) => `${r.model_id}::${r.below}`;
const routeKey = (r) => `${r.resolved_at || ''}::${r.chosen || ''}::${r.chosen_slug || ''}`;
function unionBy(localList, cloudList, keyFn, cap) {
  const seen = new Set(); const out = [];
  for (const row of [...localList, ...cloudList]) {
    const key = keyFn(row);
    if (seen.has(key)) continue;
    seen.add(key); out.push(row);
  }
  return out.slice(0, cap);
}
export function mergeProfiles(localRaw, cloudRaw, strategy) {
  const local = normalizeProfile(localRaw);
  const cloud = normalizeProfile(cloudRaw);
  if (strategy === 'local') return local;
  if (strategy === 'cloud') return cloud;
  if (strategy !== 'union') { const err = new Error('Unknown merge strategy'); err.status = 400; throw err; }
  return {
    stack: [...new Set([...local.stack, ...cloud.stack])].slice(0, CAPS.stack),
    weights: local.weights,
    alerts: unionBy(local.alerts, cloud.alerts, alertKey, CAPS.alerts),
    routes: unionBy(local.routes, cloud.routes, routeKey, CAPS.routes),
  };
}
export function applyPatch(currentRaw, patchRaw) {
  const current = normalizeProfile(currentRaw);
  const patch = patchRaw && typeof patchRaw === 'object' ? patchRaw : {};
  const pick = (key) => (Object.prototype.hasOwnProperty.call(patch, key) ? patch[key] : current[key]);
  return normalizeProfile({ stack: pick('stack'), weights: pick('weights'), alerts: pick('alerts'), routes: pick('routes') });
}
