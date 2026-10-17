// Catalog tables mirror the pipeline's SQLite schema. Ingested from the NAS
// pipeline (scripts/publish_db.py) after every tick; read-only for the site.
export async function ensureCatalogSchema(pool) {
  await pool.query(`
    CREATE TABLE IF NOT EXISTS models (
      model_id TEXT PRIMARY KEY,
      openrouter_id TEXT,
      display_name TEXT,
      provider TEXT,
      context_k INTEGER,
      current_input_price NUMERIC,
      current_output_price NUMERIC,
      rv_label TEXT,
      description TEXT,
      knowledge_cutoff TEXT,
      hermes_fit TEXT,
      is_deprecated BOOLEAN DEFAULT FALSE,
      updated_at TEXT
    );
    CREATE TABLE IF NOT EXISTS price_history (
      model_id TEXT NOT NULL,
      date DATE NOT NULL,
      input_price NUMERIC,
      output_price NUMERIC,
      source TEXT,
      PRIMARY KEY (model_id, date)
    );
    CREATE TABLE IF NOT EXISTS benchmark_history (
      model_id TEXT NOT NULL,
      date DATE NOT NULL,
      benchmark_type TEXT NOT NULL,
      score NUMERIC,
      source TEXT,
      PRIMARY KEY (model_id, date, benchmark_type)
    );
  `);
}
