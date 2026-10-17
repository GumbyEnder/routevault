import { getStore, currentUser, json, readBody, cookieHeader, profilePayload, startSession } from '../../../lib/legacy-server.mjs';
import { applyPatch } from '../../../lib/legacy-profile.mjs';
import { validPassword, hashPassword } from '../../../lib/legacy-auth.mjs';
export async function GET({ request }) {
  const user = await currentUser(request);
  if (!user) return json({ error: 'Sign in required' }, 401);
  const store = await getStore();
  const profile = await store.getProfile(user.id);
  return json(profilePayload(user, profile, { needs_merge: false }));
}
export async function PUT({ request }) {
  const user = await currentUser(request);
  if (!user) return json({ error: 'Sign in required' }, 401);
  const body = await readBody(request);
  const store = await getStore();
  const current = await store.getProfile(user.id);
  const saved = await store.saveProfile(user.id, applyPatch(current, body));
  return json(profilePayload(user, saved));
}
