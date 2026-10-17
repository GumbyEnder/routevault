import { allModels } from '../lib/db.js';
export async function GET() {
  const origin = 'https://routevault.ai';
  const pages = ['', '/models', '/trends', '/route', '/quiz', '/stack', '/how-we-score', '/lab', '/pricing'];
  let models = [];
  try { models = await allModels(); } catch (_) {}
  const urls = [...pages.map((p) => `${origin}${p}`), ...models.map((m) => `${origin}/model/${m.model_id}`)];
  return new Response(`<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls.map((u) => `<url><loc>${u}</loc></url>`).join('\n')}\n</urlset>`, { headers: { 'content-type': 'application/xml' } });
}
