#!/usr/bin/env python3
"""Generate price change report across all models (30/60/90 day view)."""
import sqlite3
from datetime import datetime, timedelta

DB = "routevault.db"
conn = sqlite3.connect(DB)
cursor = conn.cursor()

print("\nRouteVault Price Change Report\n")
print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print("=" * 70)

cursor.execute("SELECT model_id, current_input_price FROM models ORDER BY provider")
models = cursor.fetchall()

for model_id, current_price in models:
    cursor.execute("""
        SELECT input_price 
        FROM price_history 
        WHERE model_id = ? 
        ORDER BY date
    """, (model_id,))
    prices = [row[0] for row in cursor.fetchall()]
    
    if len(prices) < 30:
        continue
    
    p30 = prices[-30]
    p60 = prices[-60] if len(prices) >= 60 else prices[0]
    p90 = prices[0]
    current = current_price
    
    change_30 = ((current - p30) / p30) * 100
    change_60 = ((current - p60) / p60) * 100
    change_90 = ((current - p90) / p90) * 100
    
    arrow_30 = "↓" if change_30 < 0 else "↑" if change_30 > 0 else "→"
    arrow_60 = "↓" if change_60 < 0 else "↑" if change_60 > 0 else "→"
    arrow_90 = "↓" if change_90 < 0 else "↑" if change_90 > 0 else "→"
    
    print(f"{model_id:25} 30d: {arrow_30}{change_30:+6.1f}%   60d: {arrow_60}{change_60:+6.1f}%   90d: {arrow_90}{change_90:+6.1f}%")

print("\n" + "=" * 70)
conn.close()
