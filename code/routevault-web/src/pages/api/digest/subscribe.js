import { getStore, json, readBody, sendEmail } from '../../../lib/legacy-server.mjs';
import { normalizeEmail, validEmail } from '../../../lib/legacy-auth.mjs';
export async function POST({ request }) {
  const body = await readBody(request);
  const email = normalizeEmail(body.email);
  if (!validEmail(email)) return json({ error: 'Enter a valid email' }, 400);
  const store = await getStore();
  const count = await store.addDigestSubscriber(email);
  try {
    await sendEmail(email, "You're on the RouteVault weekly price digest",
      `<div style="font-family:system-ui,sans-serif;max-width:480px">
        <p>You'll get one short email each Monday: the week's biggest value improvers, regressions, and price drops across the catalog.</p>
        <p style="color:#888;font-size:.85rem">No marketing, no card, one email a week. Manage nothing — if you want off, reply and we'll remove you.</p>
      </div>`);
  } catch (err) { console.error('digest welcome email failed:', err.message); }
  return json({ ok: true, message: `Subscribed. ${count} subscriber(s) on the list — first email lands Monday.` });
}
