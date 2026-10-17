import { getStore, json, readBody, sendEmail, magicLinkEmail } from '../../../lib/legacy-server.mjs';
import { normalizeEmail, validEmail, hashPassword, randomToken, resetExpiry } from '../../../lib/legacy-auth.mjs';
import { trackAuthEvent } from '../../../lib/track.js';
export async function POST({ request }) {
  const body = await readBody(request);
  const email = normalizeEmail(body.email);
  if (!validEmail(email)) return json({ error: 'Enter a valid email' }, 400);
  if (!process.env.RESEND_API_KEY) return json({ error: 'Email sign-in is not configured yet' }, 503);
  const store = await getStore();
  let user = await store.findUserByEmail(email);
  const isNewUser = !user;
  if (!user) {
    const { hash, salt } = hashPassword(randomToken());
    user = await store.createUser({ email, passwordHash: hash, passwordSalt: salt, waitlistConverted: false });
  }
  trackAuthEvent(isNewUser ? 'sign_up' : 'magic_link_requested', { userId: user.id, email, method: isNewUser ? undefined : 'magic_link', request });
  const token = randomToken();
  await store.createResetToken(user.id, token, resetExpiry());
  const siteOrigin = process.env.PUBLIC_SITE_URL
    || (process.env.RAILWAY_PUBLIC_DOMAIN ? `https://${process.env.RAILWAY_PUBLIC_DOMAIN}` : null)
    || (new URL(request.url).origin.startsWith('http://localhost') ? 'https://routevault.ai' : new URL(request.url).origin);
  const link = `${siteOrigin}/api/magic/verify?token=${encodeURIComponent(token)}`;
  try {
    await sendEmail(email, 'Your RouteVault sign-in link', magicLinkEmail(link));
  } catch (err) {
    console.error('magic link email failed:', err.message);
    return json({ error: 'Could not send the email right now. Try again shortly.' }, 502);
  }
  return json({ ok: true, message: 'Check your inbox — the link is single-use and expires soon.' });
}
