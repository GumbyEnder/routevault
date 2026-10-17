// Server-side OpenPanel event tracking for auth endpoints.
// Ingest: POST https://api.openpanel.dev/track with openpanel-client-id/-secret headers.
// Env is read via globalThis indirection so the bundler cannot inline build-time
// values for OPENPANEL_* — those exist only in the Railway runtime environment.
import { createHash } from 'node:crypto';

const env = globalThis.process?.env || {};
const CLIENT_ID = env.OPENPANEL_CLIENT_ID || '8dae74a3-2b44-4ea7-9aa3-0860754ee7cd';
const CLIENT_SECRET = env.OPENPANEL_CLIENT_SECRET || '';

function emailHash(email) {
  return createHash('sha256').update(String(email).toLowerCase().trim()).digest('hex');
}

// Fire-and-forget: never blocks or fails the auth flow.
export function trackAuthEvent(event, { userId, email, request, ...props } = {}) {
  if (!CLIENT_SECRET) {
    console.error('openpanel track skipped: no OPENPANEL_CLIENT_SECRET at runtime');
    return;
  }
  try {
    const profileId = userId || (email ? 'em_' + emailHash(email).slice(0, 32) : undefined);
    const payload = {
      type: 'track',
      payload: {
        name: event,
        profileId,
        properties: { ...(email ? { email_hash: emailHash(email) } : {}), ...props },
        ...(request?.headers?.get('x-forwarded-for') ? { ip: request.headers.get('x-forwarded-for').split(',')[0].trim() } : {}),
        ...(request?.headers?.get('user-agent') ? { userAgent: request.headers.get('user-agent') } : {}),
      },
    };
    fetch('https://api.openpanel.dev/track', {
      method: 'POST',
      headers: {
        'openpanel-client-id': CLIENT_ID,
        'openpanel-client-secret': CLIENT_SECRET,
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36',
      },
      body: JSON.stringify(payload),
    }).then((r) => { if (!r.ok) console.error('openpanel track rejected:', event, r.status); })
      .catch((err) => console.error('openpanel track failed:', err.message));
  } catch (err) {
    console.error('openpanel track error:', err.message);
  }
}
