#!/usr/bin/env python3
"""Fetch provider prices (models.dev) and upsert into the SQLite catalog.
Called by scripts/tick.sh before export."""
import json
import os
import sqlite3
import sys

sys.path.insert(0, os.environ.get('ROUTEVAULT_ROOT', '/mnt/nas/agents/Projects/RouteVault'))
from pipeline.ingest.provider_prices import fetch, extract, FOCUS_PROVIDERS  # noqa: E402
from pipeline.ingest.nous_prices import rows as nous_rows  # noqa: E402

ROOT = os.environ.get("ROUTEVAULT_ROOT", "/mnt/nas/agents/Projects/RouteVault")


def ensure(conn):
    conn.execute("""
      CREATE TABLE IF NOT EXISTS provider_prices (
        provider TEXT NOT NULL,
        model_id TEXT NOT NULL,
        model_name TEXT,
        input_per_m REAL,
        output_per_m REAL,
        cache_read_per_m REAL,
        context_k INTEGER,
        source_url TEXT,
        updated_at TEXT DEFAULT (datetime('now')),
        PRIMARY KEY (provider, model_id)
      )
    """)


def main(db_path):
    data = fetch()
    rows = extract(data)
    focus = [r for r in rows if r["provider"] in FOCUS_PROVIDERS]
    try:
        focus.extend(nous_rows())
    except Exception as e:  # noqa: BLE001
        print(f"nous portal fetch failed, continuing: {e}")
    conn = sqlite3.connect(db_path)
    ensure(conn)
    for r in focus:
        conn.execute("""
          INSERT INTO provider_prices (provider, model_id, model_name, input_per_m, output_per_m,
                                       cache_read_per_m, context_k, source_url, updated_at)
          VALUES (?,?,?,?,?,?,?,?,datetime('now'))
          ON CONFLICT(provider, model_id) DO UPDATE SET
            model_name=excluded.model_name, input_per_m=excluded.input_per_m,
            output_per_m=excluded.output_per_m, cache_read_per_m=excluded.cache_read_per_m,
            context_k=excluded.context_k, source_url=excluded.source_url, updated_at=datetime('now')
        """, (r["provider"], r["model_id"], r["model_name"], r["input_per_m"],
              r["output_per_m"], r["cache_read_per_m"], r["context_k"], r["source_url"]))
    conn.commit()
    n = conn.execute("SELECT COUNT(*) FROM provider_prices").fetchone()[0]
    conn.close()
    print(f"provider_prices: {len(focus)} focus rows upserted, {n} total")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data", "routevault.db"))
