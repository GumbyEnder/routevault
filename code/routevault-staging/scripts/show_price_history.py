#!/usr/bin/env python3
"""Quick utility to show 90-day price history for a model."""
import sqlite3
import sys

DB = "routevault.db"

def show_history(model_id):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    
    print(f"\nPrice History for: {model_id}\n")
    print(f"{'Date':<12} {'Input':>10} {'Output':>10} {'Change'}")
    print("-" * 40)
    
    cursor.execute("""
        SELECT date, input_price, output_price 
        FROM price_history 
        WHERE model_id = ? 
        ORDER BY date
    """, (model_id,))
    
    rows = cursor.fetchall()
    if not rows:
        print("No data found.")
        return
    
    prev_in = rows[0][1]
    for date, inp, out in rows:
        change = ""
        if inp != prev_in:
            pct = ((inp - prev_in) / prev_in) * 100
            arrow = "↑" if inp > prev_in else "↓"
            change = f"{arrow} {abs(pct):.1f}%"
        print(f"{date:<12} ${inp:>8.4f}  ${out:>8.4f}  {change}")
        prev_in = inp
    
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python show_price_history.py <model_id>")
        print("Example: python show_price_history.py deepseek-v3")
        sys.exit(1)
    show_history(sys.argv[1])
