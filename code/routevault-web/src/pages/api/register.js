import { getStore, json, readBody, cookieHeader, profilePayload, startSession } from '../../lib/legacy-server.mjs';
import { normalizeEmail, validEmail, validPassword, hashPassword } from '../../lib/legacy-auth.mjs';
import { normalizeProfile, emptyProfile, needsMerge, hasPersonalData } from '../../lib/legacy-profile.mjs';
import { trackAuthEvent } from '../../lib/track.js';
export async function POST({ request }) {
  const body = await readBody(request);
  const email = normalizeEmail(body.email);
  if (!validEmail(email)) return json({ error: 'Enter a valid email' }, 400);
  if (!validPassword(body.password)) return json({ error: 'Password must be at least 8 characters' }, 400);
  const { hash, salt } = hashPassword(body.password);
  try {
    const store = await getStore();
    const user = await store.createUser({ email, passwordHash: hash, passwordSalt: salt, waitlistConverted: Boolean(body.waitlist) });
    const token = await startSession(user);
    const profile = await store.getProfile(user.id);
    const local = normalizeProfile(body.local || {});
    trackAuthEvent('sign_up', { userId: user.id, email, request });
    return json(profilePayload(user, profile, { needs_merge: needsMerge(local, emptyProfile()) ? false : needsMerge(local, profile), local_has_data: hasPersonalData(local) }), 201, { 'Set-Cookie': cookieHeader(token) });
  } catch (err) {
    return json({ error: err.message || 'Could not create the account' }, err.status || 500);
  }
}
