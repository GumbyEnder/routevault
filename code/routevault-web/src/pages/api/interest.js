import { json, readBody } from '../../lib/legacy-server.mjs';
import { logInterest } from '../../lib/db.js';
const ALLOWED = new Set(['page_view', 'quiz_complete', 'route_search', 'stack_add', 'digest_subscribe', 'model_open', 'share_link']);
export async function POST({ request }) {
  const body = await readBody(request);
  const type = String(body.type || '');
  if (!ALLOWED.has(type)) return json({ error: 'Unknown event' }, 400);
  await logInterest(type, body.model_id || null, { path: body.path, meta: body.meta });
  return json({ ok: true });
}
