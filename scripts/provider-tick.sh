#!/usr/bin/env bash
# 2x/day models.dev + Nous Portal provider-price refresh only (no full pipeline,
# no OpenRouter ingest, no deploy). The heavy 4x/day catalog tick in tick.sh also
# refreshes provider prices; this job just closes the intraday gap on /compare.
set -euo pipefail
ROOT="${ROUTEVAULT_ROOT:-/mnt/nas/agents/Projects/RouteVault}"
WORK="${ROUTEVAULT_WORK:-/tmp/routevault-provider-tick}"

mkdir -p "$WORK/data"
cp -f "$ROOT/data/routevault.db" "$WORK/data/routevault.db"

PYTHONPATH="$ROOT" python3 "$ROOT/pipeline/ingest/store_provider_prices.py" "$WORK/data/routevault.db"

cp -f "$WORK/data/routevault.db" "$ROOT/data/routevault.db"

python3 - "$WORK/data/routevault.db" <<'EOF'
import json, sqlite3, sys, datetime
conn = sqlite3.connect(sys.argv[1])
conn.row_factory = sqlite3.Row
rows = [dict(r) for r in conn.execute("SELECT * FROM provider_prices ORDER BY provider, model_id")]
out = {"generated_at": datetime.datetime.now(datetime.UTC).isoformat(),
       "source": "models.dev", "count": len(rows), "rows": rows}
for dst in ("/mnt/nas/agents/Projects/RouteVault/code/routevault-staging/data/provider-prices.json",
            "/mnt/nas/agents/Projects/RouteVault/code/routevault-web/public/data/provider-prices.json"):
    open(dst, "w").write(json.dumps(out))
print(f"provider tick: {len(rows)} rows written at {out['generated_at']}")
EOF
