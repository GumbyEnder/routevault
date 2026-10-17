import pg from 'pg';

let pool = null;
export function getPool() {
  if (!pool) {
    pool = new pg.Pool({ connectionString: process.env.DATABASE_URL, max: 5, idleTimeoutMillis: 30_000 });
  }
  return pool;
}

// Value score mirrors the site rubric: weighted bench average ÷ blended price × 10.
const WEIGHTS = { reasoning: 32, coding: 25, agentic: 18, general: 15 };

export async function allModels() {
  const { rows } = await getPool().query(`
    WITH latest_bench AS (
      SELECT DISTINCT ON (bh.model_id, bh.benchmark_type)
             bh.model_id, bh.benchmark_type, bh.score
      FROM benchmark_history bh
      ORDER BY bh.model_id, bh.benchmark_type, bh.date DESC
    ),
    pivoted AS (
      SELECT model_id,
        MAX(CASE WHEN benchmark_type='reasoning' THEN score END) AS reasoning,
        MAX(CASE WHEN benchmark_type='coding' THEN score END)    AS coding,
        MAX(CASE WHEN benchmark_type='tool_use' THEN score END)   AS agentic,
        MAX(CASE WHEN benchmark_type='general_intelligence' THEN score END) AS general,
        MAX(CASE WHEN benchmark_type='context' THEN score END)    AS context
      FROM latest_bench GROUP BY model_id
    ),
    price_30d AS (
      SELECT model_id,
        (SELECT input_price + output_price FROM price_history ph2
          WHERE ph2.model_id = ph.model_id AND ph2.date >= now() - interval '30 days'
          ORDER BY ph2.date DESC LIMIT 1) AS recent,
        (SELECT input_price + output_price FROM price_history ph2
          WHERE ph2.model_id = ph.model_id AND ph2.date >= now() - interval '30 days'
          ORDER BY ph2.date ASC LIMIT 1) AS old
      FROM (SELECT DISTINCT model_id FROM price_history WHERE date >= now() - interval '30 days') ph
    ),
    bench_avg AS (
      -- Rubric v2026-08-14: weighted bench average over the benchmarks a model
      -- HAS (renormalized), matching pipeline compute.py. Missing = skipped,
      -- never zero. General falls back to reasoning (same AA series).
      SELECT model_id,
        SUM(w * s) / NULLIF(SUM(w), 0) AS bench_avg,
        COUNT(*) AS bench_count
      FROM (
        SELECT model_id, 'reasoning'::text AS k, reasoning AS s, 32.0 AS w FROM pivoted WHERE reasoning IS NOT NULL
        UNION ALL
        SELECT model_id, 'coding', coding, 25.0 FROM pivoted WHERE coding IS NOT NULL
        UNION ALL
        SELECT model_id, 'tool_use', agentic, 18.0 FROM pivoted WHERE agentic IS NOT NULL
        UNION ALL
        SELECT model_id, 'general', COALESCE(general, reasoning), 15.0 FROM pivoted
          WHERE (general IS NOT NULL OR reasoning IS NOT NULL)
        UNION ALL
        SELECT model_id, 'context', context, 7.0 FROM pivoted WHERE context IS NOT NULL
      ) b GROUP BY model_id
    )
    SELECT m.model_id, m.openrouter_id, m.display_name, m.provider, m.context_k,
           m.current_input_price::float8 AS input_price, m.current_output_price::float8 AS output_price,
           (m.current_input_price + m.current_output_price) AS total_price,
           m.rv_label, m.description, m.knowledge_cutoff, m.hermes_fit,
           p.reasoning, p.coding, p.agentic, p.general, p.context,
           b.bench_avg::float8 AS bench_avg, b.bench_count AS bench_count,
           CASE WHEN price_30d.old > 0 AND price_30d.recent IS NOT NULL
                THEN ((price_30d.recent - price_30d.old) / price_30d.old * 100)::numeric(6,2)
                ELSE NULL END::float8 AS price_change_30d,
           -- Value = weighted bench avg ÷ blended list price × 10 (pipeline parity).
           -- Free models: pipeline returns avg×100; keep it but flag so UI can badge "Free".
           CASE
             WHEN b.bench_avg IS NULL THEN NULL
             WHEN (m.current_input_price + m.current_output_price) <= 0
               THEN ROUND(b.bench_avg * 100, 2)::float8
             ELSE ROUND(b.bench_avg / (m.current_input_price + m.current_output_price) * 10, 2)::float8
           END AS value_score
    FROM models m
    LEFT JOIN pivoted p ON p.model_id = m.model_id
    LEFT JOIN bench_avg b ON b.model_id = m.model_id
    LEFT JOIN price_30d ON price_30d.model_id = m.model_id
    WHERE COALESCE(m.is_deprecated, FALSE) = FALSE
    ORDER BY value_score DESC NULLS LAST
  `);
  return rows;
}

// Trend-page data: the full catalog plus price history for the models that
// actually moved, so the charts render server-side without client fetches.
export async function trendsData() {
  const models = await allModels();
  const scored = models.filter((m) => m.value_score != null);
  const movers = scored
    .filter((m) => m.price_change_30d != null && m.price_change_30d !== 0)
    .sort((a, b) => a.price_change_30d - b.price_change_30d)
    .slice(0, 10);
  const hist = movers.length
    ? await getPool().query(
        `SELECT model_id, date, input_price, output_price FROM price_history
         WHERE model_id = ANY($1) ORDER BY model_id, date ASC`,
        [movers.map((m) => m.model_id)])
    : { rows: [] };
  const history = {};
  for (const r of hist.rows) {
    (history[r.model_id] = history[r.model_id] || []).push({
      date: r.date instanceof Date ? r.date.toISOString().slice(0, 10) : String(r.date).slice(0, 10),
      total: Number(r.input_price) + Number(r.output_price),
    });
  }
  return { models, movers, history };
}

export async function modelDetail(modelId) {
  const models = await allModels();
  const m = models.find((x) => x.model_id === modelId);
  if (!m) return null;
  const hist = await getPool().query(
    `SELECT date, input_price, output_price FROM price_history
     WHERE model_id = $1 ORDER BY date ASC LIMIT 40`, [modelId]);
  const benches = await getPool().query(
    `SELECT DISTINCT ON (benchmark_type) benchmark_type, date, score
     FROM benchmark_history WHERE model_id = $1 ORDER BY benchmark_type, date DESC`, [modelId]);
  return { model: m, price_history: hist.rows, benchmarks: benches.rows };
}

export async function logInterest(eventType, modelId, meta) {
  try {
    await getPool().query(
      `INSERT INTO interest_events (event_type, model_id, meta) VALUES ($1, $2, $3)`,
      [eventType, modelId || null, meta ? JSON.stringify(meta) : null]);
  } catch (_) { /* analytics must never break a page */ }
}
