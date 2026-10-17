import { getStore, json, readBody, cookieHeader, profilePayload, startSession } from '../../../lib/legacy-server.mjs';
import { validPassword, hashPassword } from '../../../lib/legacy-auth.mjs';
export async function POST({ request }) {
  const body = await readBody(request);
  if (!validPassword(body.password)) return json({ error: 'Password must be at least 8 characters' }, 400);
  const store = await getStore();
  const user = await store.consumeResetToken(body.token || '');
  if (!user) return json({ error: 'Reset link is invalid or expired' }, 400);
  const { hash, salt } = hashPassword(body.password);
  await store.updatePassword(user.id, hash, salt);
  await store.deleteSessionsForUser(user.id);
  const token = await startSession(user);
  const profile = await store.getProfile(user.id);
  return json(profilePayload(user, profile), 200, { 'Set-Cookie': cookieHeader(token) });
}
