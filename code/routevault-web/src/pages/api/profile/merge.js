import { getStore, currentUser, json, readBody, profilePayload } from '../../../lib/legacy-server.mjs';
import { normalizeProfile, mergeProfiles } from '../../../lib/legacy-profile.mjs';
export async function POST({ request }) {
  const user = await currentUser(request);
  if (!user) return json({ error: 'Sign in required' }, 401);
  const body = await readBody(request);
  const strategy = body.strategy || 'union';
  const store = await getStore();
  const cloud = await store.getProfile(user.id);
  const local = normalizeProfile(body.local || {});
  const saved = await store.saveProfile(user.id, mergeProfiles(local, cloud, strategy));
  return json(profilePayload(user, saved, { strategy }));
}
