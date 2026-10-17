import { getStore, json, readBody } from '../../../lib/legacy-server.mjs';
import { normalizeEmail, validEmail, randomToken, resetExpiry } from '../../../lib/legacy-auth.mjs';
export async function POST({ request }) {
  const body = await readBody(request);
  const email = normalizeEmail(body.email);
  const store = await getStore();
  const user = validEmail(email) ? await store.findUserByEmail(email) : null;
  let issued = null;
  if (user) {
    const token = randomToken();
    await store.createResetToken(user.id, token, resetExpiry());
    if (process.env.RV_RETURN_RESET_TOKEN === '1') issued = token;
  }
  const payload = { ok: true, message: 'If that email has an account, a reset token was issued.' };
  if (issued) payload.reset_token = issued;
  return json(payload);
}
