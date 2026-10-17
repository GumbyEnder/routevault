import { getStore, cookieHeader, startSession } from '../../../lib/legacy-server.mjs';
import { trackAuthEvent } from '../../../lib/track.js';
export async function GET({ request, redirect }) {
  const token = new URL(request.url).searchParams.get('token') || '';
  const store = await getStore();
  const user = await store.consumeResetToken(token);
  if (!user) {
    return new Response('<!DOCTYPE html><html><head><meta charset="utf-8"><title>RouteVault</title></head><body style="font-family:system-ui;display:grid;place-items:center;height:100vh;margin:0"><div style="text-align:center"><h1>Link expired</h1><p>This sign-in link is invalid or already used.</p><p><a href="/login">Request a new one</a></p></div></body></html>', { headers: { 'content-type': 'text/html' } });
  }
  const token2 = await startSession(user);
  trackAuthEvent('login', { userId: user.id, email: user.email, method: 'magic_link', request });
  return new Response(null, { status: 302, headers: { 'Set-Cookie': cookieHeader(token2), Location: '/account' } });
}
