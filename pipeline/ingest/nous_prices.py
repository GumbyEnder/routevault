"""
Ingest the Nous Portal inference catalog (OpenAI-style /v1/models with per-token pricing).
Provider key: nous-portal. Prices converted to USD per million tokens.
"""
import json
import urllib.request

SOURCE_URL = "https://inference-api.nousresearch.com/v1/models"
USER_AGENT = "RouteVault/1.0 (https://routevault.ai)"
PROVIDER = "nous-portal"


def fetch():
    req = urllib.request.Request(SOURCE_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read().decode())
    return d.get("data", [])


def rows():
    out = []
    for m in fetch():
        p = m.get("pricing") or {}
        if not p or p.get("prompt") is None:
            continue
        ctx = m.get("context_length") or 0
        pin = float(p["prompt"]) * 1_000_000
        pout = float(p.get("completion") or 0) * 1_000_000
        cache = p.get("input_cache_read")
        batch = ":batch" in m["id"] or any("batch" in a for a in (m.get("aliases") or []))
        note_parts = []
        if batch:
            note_parts.append("batch pricing (half)")
        if p.get("overrides"):
            note_parts.append("tiered above 100k prompt tokens")
        out.append({
            "provider": PROVIDER,
            "model_id": m["id"],
            "model_name": m.get("name") or m["id"],
            "input_per_m": round(pin, 4),
            "output_per_m": round(pout, 4),
            "cache_read_per_m": (round(float(cache) * 1_000_000, 4) if cache is not None else None),
            "context_k": int(ctx / 1000) if ctx else None,
            "source_url": "https://portal.nousresearch.com/models",
            "note": "; ".join(note_parts),
        })
    return out


if __name__ == "__main__":
    rows_ = rows()
    print(json.dumps(rows_[:3], indent=1))
    print("nous-portal priced rows:", len(rows_))
