#!/usr/bin/env python3
"""
Export model data + recent price history to JSON for the frontend.
"""
import sqlite3
import json
from datetime import datetime

DB = "routevault.db"
OUT = "../data/models.json"

conn = sqlite3.connect(DB)
cursor = conn.cursor()

cursor.execute("""
    SELECT model_id, provider, context_k, current_input_price, current_output_price, rv_label
    FROM models
""")
models = cursor.fetchall()

data = {"generated_at": datetime.now().isoformat(), "models": []}

for model in models:
    model_id, provider, context, inp, out, label = model
    
    cursor.execute("""
        SELECT date, input_price, output_price 
        FROM price_history 
        WHERE model_id = ? 
        ORDER BY date DESC 
        LIMIT 90
    """, (model_id,))
    history = [{"date": d, "input": i, "output": o} for d, i, o in cursor.fetchall()]
    
    data["models"].append({
        "model_id": model_id,
        "provider": provider,
        "context_k": context,
        "current_input_price": inp,
        "current_output_price": out,
        "rv_label": label,
        "price_history": history
    })

with open(OUT, "w") as f:
    json.dump(data, f, indent=2)

print(f"Exported {len(data['models'])} models to {OUT}")
conn.close()