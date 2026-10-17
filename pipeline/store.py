"""SQLite persistence for models, live prices, benches, and snapshots."""

from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path
from typing import Any, Iterable

SCHEMA = """
CREATE TABLE IF NOT EXISTS models (
    model_id TEXT PRIMARY KEY,
    openrouter_id TEXT NOT NULL,
    display_name TEXT,
    provider TEXT NOT NULL,
    context_k INTEGER,
    current_input_price REAL,
    current_output_price REAL,
    rv_label TEXT,
    description TEXT,
    knowledge_cutoff TEXT,
    hermes_fit TEXT,
    is_deprecated INTEGER DEFAULT 0,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS price_history (
    model_id TEXT NOT NULL,
    date TEXT NOT NULL,
    input_price REAL NOT NULL,
    output_price REAL NOT NULL,
    source TEXT DEFAULT 'openrouter',
    PRIMARY KEY (model_id, date)
);

CREATE TABLE IF NOT EXISTS benchmark_history (
    model_id TEXT NOT NULL,
    date TEXT NOT NULL,
    benchmark_type TEXT NOT NULL,
    score REAL NOT NULL,
    source TEXT,
    PRIMARY KEY (model_id, date, benchmark_type)
);

CREATE TABLE IF NOT EXISTS ingest_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ran_at TEXT NOT NULL,
    model_count INTEGER,
    source TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS discovered_models (
    openrouter_id TEXT PRIMARY KEY,
    display_name TEXT,
    provider TEXT,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    promoted INTEGER DEFAULT 0,
    intelligence REAL,
    coding REAL,
    input_price REAL,
    output_price REAL,
    reason TEXT
);

CREATE TABLE IF NOT EXISTS news_items (
    id TEXT PRIMARY KEY,
    url TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    source TEXT NOT NULL,
    published_at TEXT,
    summary TEXT,
    ingested_at TEXT NOT NULL
);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    return conn


def upsert_model(conn: sqlite3.Connection, row: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO models (
            model_id, openrouter_id, display_name, provider, context_k,
            current_input_price, current_output_price, rv_label, description,
            knowledge_cutoff, hermes_fit, is_deprecated, updated_at
        ) VALUES (
            :model_id, :openrouter_id, :display_name, :provider, :context_k,
            :current_input_price, :current_output_price, :rv_label, :description,
            :knowledge_cutoff, :hermes_fit, :is_deprecated, :updated_at
        )
        ON CONFLICT(model_id) DO UPDATE SET
            openrouter_id=excluded.openrouter_id,
            display_name=excluded.display_name,
            provider=excluded.provider,
            context_k=excluded.context_k,
            current_input_price=excluded.current_input_price,
            current_output_price=excluded.current_output_price,
            rv_label=excluded.rv_label,
            description=excluded.description,
            knowledge_cutoff=excluded.knowledge_cutoff,
            hermes_fit=excluded.hermes_fit,
            is_deprecated=excluded.is_deprecated,
            updated_at=excluded.updated_at
        """,
        row,
    )


def upsert_price(
    conn: sqlite3.Connection,
    model_id: str,
    on: date,
    input_price: float,
    output_price: float,
    source: str = "openrouter",
) -> None:
    conn.execute(
        """
        INSERT INTO price_history (model_id, date, input_price, output_price, source)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(model_id, date) DO UPDATE SET
            input_price=excluded.input_price,
            output_price=excluded.output_price,
            source=excluded.source
        """,
        (model_id, on.isoformat(), input_price, output_price, source),
    )


def upsert_benchmark(
    conn: sqlite3.Connection,
    model_id: str,
    on: date,
    benchmark_type: str,
    score: float,
    source: str,
) -> None:
    conn.execute(
        """
        INSERT INTO benchmark_history (model_id, date, benchmark_type, score, source)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(model_id, date, benchmark_type) DO UPDATE SET
            score=excluded.score,
            source=excluded.source
        """,
        (model_id, on.isoformat(), benchmark_type, score, source),
    )


def record_run(conn: sqlite3.Connection, ran_at: str, model_count: int, notes: str) -> None:
    conn.execute(
        "INSERT INTO ingest_runs (ran_at, model_count, source, notes) VALUES (?, ?, ?, ?)",
        (ran_at, model_count, "openrouter", notes),
    )


def fetch_models(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    return [dict(r) for r in conn.execute("SELECT * FROM models ORDER BY model_id")]


def fetch_prices(conn: sqlite3.Connection) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for r in conn.execute(
        "SELECT * FROM price_history ORDER BY model_id, date"
    ):
        out.setdefault(r["model_id"], []).append(dict(r))
    return out


def fetch_benchmarks(conn: sqlite3.Connection) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for r in conn.execute(
        "SELECT * FROM benchmark_history ORDER BY model_id, date, benchmark_type"
    ):
        out.setdefault(r["model_id"], []).append(dict(r))
    return out


def upsert_discovered(conn: sqlite3.Connection, row: dict[str, Any], now: str) -> None:
    conn.execute(
        """
        INSERT INTO discovered_models (
            openrouter_id, display_name, provider, first_seen, last_seen,
            promoted, intelligence, coding, input_price, output_price, reason
        ) VALUES (
            :openrouter_id, :display_name, :provider, :first_seen, :last_seen,
            :promoted, :intelligence, :coding, :input_price, :output_price, :reason
        )
        ON CONFLICT(openrouter_id) DO UPDATE SET
            display_name=excluded.display_name,
            provider=excluded.provider,
            last_seen=excluded.last_seen,
            promoted=MAX(discovered_models.promoted, excluded.promoted),
            intelligence=excluded.intelligence,
            coding=excluded.coding,
            input_price=excluded.input_price,
            output_price=excluded.output_price,
            reason=excluded.reason
        """,
        {
            **row,
            "first_seen": now,
            "last_seen": now,
        },
    )


def fetch_discovered(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    return [
        dict(r)
        for r in conn.execute(
            "SELECT * FROM discovered_models ORDER BY promoted DESC, intelligence DESC, openrouter_id"
        )
    ]


def upsert_news(conn: sqlite3.Connection, item: dict[str, Any], ingested_at: str) -> None:
    conn.execute(
        """
        INSERT INTO news_items (id, url, title, source, published_at, summary, ingested_at)
        VALUES (:id, :url, :title, :source, :published_at, :summary, :ingested_at)
        ON CONFLICT(id) DO UPDATE SET
            title=excluded.title,
            source=excluded.source,
            published_at=COALESCE(excluded.published_at, news_items.published_at),
            summary=excluded.summary
        """,
        {**item, "ingested_at": ingested_at},
    )


def fetch_news(conn: sqlite3.Connection, limit: int = 80) -> list[dict[str, Any]]:
    return [
        dict(r)
        for r in conn.execute(
            """
            SELECT * FROM news_items
            ORDER BY COALESCE(published_at, ingested_at) DESC
            LIMIT ?
            """,
            (limit,),
        )
    ]


def counts(conn: sqlite3.Connection) -> dict[str, int]:
    def n(table: str) -> int:
        return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])

    return {
        "models": n("models"),
        "price_history": n("price_history"),
        "benchmark_history": n("benchmark_history"),
        "ingest_runs": n("ingest_runs"),
        "discovered_models": n("discovered_models"),
        "news_items": n("news_items"),
    }
