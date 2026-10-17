import fs from 'node:fs';
import path from 'node:path';
export async function GET() {
  try {
    const p = path.join(process.cwd(), 'public', 'data', 'discovered_models.json');
    if (!fs.existsSync(p)) return new Response(JSON.stringify({ count: 0, models: [] }), { headers: { 'content-type': 'application/json' } });
    return new Response(fs.readFileSync(p, 'utf8'), { headers: { 'content-type': 'application/json' } });
  } catch (e) { return new Response(JSON.stringify({ count: 0, models: [] }), { headers: { 'content-type': 'application/json' } }); }
}
