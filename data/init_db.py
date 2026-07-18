#!/usr/bin/env python3
"""
RouteVault - SQLite Initialization Script
Creates the routevault.db database with models and price_history tables.
Seeds 18 core models + generates 90 days of realistic price history.
"""

import sqlite3
import os
from datetime import datetime, timedelta
import random

DB_PATH = os.path.join(os.path.dirname(__file__), "routevault.db")

# Seed data matching our enriched model-sources table
MODELS = [
    {"model_id": "claude-3.7-sonnet", "provider": "Anthropic", "context_k": 200, "input_price": 3.00, "output_price": 15.00, "rv_label": "Project Planner"},
    {"model_id": "gpt-4o", "provider": "OpenAI", "context_k": 128, "input_price": 2.50, "output_price": 10.00, "rv_label": "Researcher"},
    {"model_id": "claude-3.5-sonnet", "provider": "Anthropic", "context_k": 200, "input_price": 3.00, "output_price": 15.00, "rv_label": "Senior Developer"},
    {"model_id": "o1-preview", "provider": "OpenAI", "context_k": 128, "input_price": 15.00, "output_price": 60.00, "rv_label": "Deep Thinker"},
    {"model_id": "gemini-2.5-pro", "provider": "Google", "context_k": 1000, "input_price": 1.25, "output_price": 5.00, "rv_label": "Researcher"},
    {"model_id": "grok-2-1212", "provider": "xAI", "context_k": 128, "input_price": 2.00, "output_price": 2.00, "rv_label": "Project Planner"},
    {"model_id": "deepseek-r1", "provider": "DeepSeek", "context_k": 128, "input_price": 0.55, "output_price": 2.19, "rv_label": "Budget"},
    {"model_id": "deepseek-v3", "provider": "DeepSeek", "context_k": 128, "input_price": 0.14, "output_price": 0.28, "rv_label": "Budget Everyday"},
    {"model_id": "llama-3.1-405b", "provider": "Meta", "context_k": 128, "input_price": 0.80, "output_price": 0.80, "rv_label": "Researcher"},
    {"model_id": "mistral-large-latest", "provider": "Mistral", "context_k": 128, "input_price": 2.00, "output_price": 6.00, "rv_label": "Senior Developer"},
    {"model_id": "qwen2.5-72b", "provider": "Alibaba", "context_k": 128, "input_price": 0.25, "output_price": 0.25, "rv_label": "Budget"},
    {"model_id": "o1-mini", "provider": "OpenAI", "context_k": 128, "input_price": 1.10, "output_price": 4.40, "rv_label": "Junior Developer"},
    {"model_id": "command-r-plus", "provider": "Cohere", "context_k": 128, "input_price": 2.50, "output_price": 10.00, "rv_label": "Project Planner"},
    {"model_id": "jamba-1.5-large", "provider": "AI21", "context_k": 256, "input_price": 2.00, "output_price": 8.00, "rv_label": "Researcher"},
    {"model_id": "gemini-2.5-flash", "provider": "Google", "context_k": 1000, "input_price": 0.075, "output_price": 0.30, "rv_label": "Budget Everyday"},
    {"model_id": "gpt-4o-mini", "provider": "OpenAI", "context_k": 128, "input_price": 0.15, "output_price": 0.60, "rv_label": "Budget Everyday"},
    {"model_id": "phi-4", "provider": "Microsoft", "context_k": 16, "input_price": 0.07, "output_price": 0.14, "rv_label": "Budget Everyday"},
]

def create_tables(conn):
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_id TEXT UNIQUE NOT NULL,
            provider TEXT NOT NULL,
            context_k INTEGER,
            current_input_price REAL,
            current_output_price REAL,
            rv_label TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_id TEXT NOT NULL,
            date DATE NOT NULL,
            input_price REAL NOT NULL,
            output_price REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (model_id) REFERENCES models (model_id),
            UNIQUE(model_id, date)
        )
    """)
    
    # Index for fast time-series queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_history_model_date ON price_history(model_id, date)")
    
    conn.commit()
    print("✓ Tables created")

def seed_models(conn):
    cursor = conn.cursor()
    
    for model in MODELS:
        cursor.execute("""
            INSERT OR REPLACE INTO models 
            (model_id, provider, context_k, current_input_price, current_output_price, rv_label)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            model["model_id"], 
            model["provider"], 
            model["context_k"], 
            model["input_price"], 
            model["output_price"], 
            model["rv_label"]
        ))
    
    conn.commit()
    print(f"✓ {len(MODELS)} models seeded")

def generate_price_history(conn):
    cursor = conn.cursor()
    
    today = datetime.now().date()
    
    for model in MODELS:
        model_id = model["model_id"]
        current_input = model["input_price"]
        current_output = model["output_price"]
        
        # Start from 90 days ago
        start_price_in = current_input * random.uniform(0.92, 1.18)  # realistic historical variance
        start_price_out = current_output * random.uniform(0.92, 1.18)
        
        price_in = start_price_in
        price_out = start_price_out
        
        for i in range(90):
            date = today - timedelta(days=89 - i)
            
            # Small daily movement (±3-7%)
            price_in *= random.uniform(0.93, 1.07)
            price_out *= random.uniform(0.93, 1.07)
            
            # Clamp to reasonable bounds relative to current price
            price_in = max(current_input * 0.65, min(current_input * 1.45, price_in))
            price_out = max(current_output * 0.65, min(current_output * 1.45, price_out))
            
            cursor.execute("""
                INSERT OR REPLACE INTO price_history (model_id, date, input_price, output_price)
                VALUES (?, ?, ?, ?)
            """, (model_id, date, round(price_in, 4), round(price_out, 4)))
    
    conn.commit()
    print(f"✓ 90-day price history generated for {len(MODELS)} models")

def main():
    print("Initializing RouteVault database...\n")
    
    # Remove old DB if exists (for clean re-runs)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("Removed previous database")
    
    conn = sqlite3.connect(DB_PATH)
    
    try:
        create_tables(conn)
        seed_models(conn)
        generate_price_history(conn)
        
        # Quick verification
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM models")
        model_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM price_history")
        history_count = cursor.fetchone()[0]
        
        print(f"\n✓ Database created successfully at: {DB_PATH}")
        print(f"  - Models: {model_count}")
        print(f"  - Price history records: {history_count}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()