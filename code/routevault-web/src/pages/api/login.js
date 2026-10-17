import { getStore, json, readBody, cookieHeader, profilePayload, startSession } from '../../lib/legacy-server.mjs';
import { normalizeEmail, validEmail, verifyPassword } from '../../lib/legacy-auth.mjs';
import { normalizeProfile, needsMerge, hasPersonalData } from '../../lib/legacy-profile.mjs';
import { trackAuthEvent } from '../../lib/track.js';
export async function POST({ request }) {
  const body = await readBody(request);
  const email = normalizeEmail(body.email);
  const store = await getStore();
  const user = validEmail(email) ? await store.findUserByEmail(email) : null;
  if (!user || !verifyPassword(body.password || '', user.password_salt, user.password_hash)) {
    return json({ error: 'Email or password is wrong' }, 401);
  }
  if (body.waitlist) await store.markWaitlistConverted(user.id);
  const fresh = await store.findUserById(user.id);
  const token = await startSession(fresh);
  const profile = await store.getProfile(fresh.id);
  const local = normalizeProfile(body.local || {});
  trackAuthEvent('login', { userId: fresh.id, email, request });
  return json(profilePayload(fresh, profile, { needs_merge: needsMerge(local, profile), local_has_data: hasPersonalData(local) }), 200, { 'Set-Cookie': cookieHeader(token) });
}
