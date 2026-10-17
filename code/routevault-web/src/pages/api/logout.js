import { getStore, json, parseCookies, cookieHeader } from '../../lib/legacy-server.mjs';
export async function POST({ request }) {
  const token = parseCookies(request.headers.get('cookie'))['rv_session'];
  if (token) (await getStore()).deleteSession(token);
  return json({ ok: true, user: null }, 200, { 'Set-Cookie': cookieHeader('', { clear: true }) });
}
