import { getPool } from '../../lib/db.js';
import { ensureCatalogSchema } from '../../lib/catalog.js';

export async function POST({ request }) {
  if (process.env.RV_INGEST_TOKEN && request.headers.get('authorization') !== `Bearer ${process.env.RV_INGEST_TOKEN}`) {
    return new Response(JSON.stringify({ error: 'Unauthorized' }), { status: 401 });
  }
  let body;
  try { body = await request.json(); } catch (_) {
    return new Response(JSON.stringify({ error: 'Invalid JSON' }), { status: 400 });
  }
  const pool = getPool();
  await ensureCatalogSchema(pool);
  let models = 0, prices = 0, benches = 0;
  for (const m of body.models || []) {
    await pool.query(`
      INSERT INTO models (model_id, openrouter_id, display_name, provider, context_k,
        current_input_price, current_output_price, rv_label, description, knowledge_cutoff, hermes_fit, is_deprecated, updated_at)
      VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12, now())
      ON CONFLICT (model_id) DO UPDATE SET
        openrouter_id = EXCLUDED.openrouter_id, display_name = EXCLUDED.display_name,
        provider = EXCLUDED.provider, context_k = EXCLUDED.context_k,
        current_input_price = EXCLUDED.current_input_price,
        current_output_price = EXCLUDED.current_output_price,
        rv_label = EXCLUDED.rv_label, description = EXCLUDED.description,
        knowledge_cutoff = EXCLUDED.knowledge_cutoff, hermes_fit = EXCLUDED.hermes_fit,
        is_deprecated = EXCLUDED.is_deprecated, updated_at = now()`,
      [m.model_id, m.openrouter_id, m.display_name, m.provider, m.context_k,
       m.current_input_price, m.current_output_price, m.rv_label, m.description,
       m.knowledge_cutoff, m.hermes_fit, m.is_deprecated]);
    models++;
  }
  for (const p of body.price_history || []) {
    await pool.query(`
      INSERT INTO price_history (model_id, date, input_price, output_price, source)
      VALUES ($1,$2,$3,$4,$5)
      ON CONFLICT (model_id, date) DO UPDATE SET input_price = $3, output_price = $4, source = $5`,
      [p.model_id, p.date, p.input_price, p.output_price, p.source || 'pipeline']);
    prices++;
  }
  for (const b of body.benchmark_history || []) {
    await pool.query(`
      INSERT INTO benchmark_history (model_id, date, benchmark_type, score, source)
      VALUES ($1,$2,$3,$4,$5)
      ON CONFLICT (model_id, date, benchmark_type) DO UPDATE SET score = $4`,
      [b.model_id, b.date, b.benchmark_type, b.score, b.source || null]);
    benches++;
  }
  return new Response(JSON.stringify({ ok: true, models, price_history: prices || 0, benchmark_history: benches }), { headers: { 'content-type': 'application/json' } });
}
