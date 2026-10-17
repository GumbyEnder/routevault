import fs from 'node:fs';
import path from 'node:path';
import { getStore, startWeeklyDigest } from '../../lib/legacy-server.mjs';
import { getPool } from '../../lib/db.js';
import { migrate } from '../../lib/migrate.js';

let ready = false;
export async function GET() {
  if (!ready) {
    ready = true;
    await migrate().catch(() => {});
    const store = await getStore();
    await store.ping().catch((e) => console.error('store ping:', e.message));
    startWeeklyDigest(async () => {
      try {
        return JSON.parse(fs.readFileSync(path.join(process.cwd(), 'public', 'data', 'dataset.json'), 'utf8'));
      } catch (_) { return {}; }
    });
  }
  try {
    await getPool().query('SELECT 1');
    return new Response(JSON.stringify({ ok: true, store: 'postgres', accounts: true }), { headers: { 'content-type': 'application/json' } });
  } catch (e) {
    return new Response(JSON.stringify({ ok: false, error: e.message }), { status: 500, headers: { 'content-type': 'application/json' } });
  }
}
