#!/usr/bin/env bash
# 4x-daily RouteVault tick: live prices, new-model discovery, AI/tech news.
# Writes SQLite on local disk, copies JSON back to NAS, then Railway-up the site.
set -euo pipefail
ROOT="${ROUTEVAULT_ROOT:-/mnt/nas/agents/Projects/RouteVault}"
WORK="${ROUTEVAULT_WORK:-/tmp/routevault-work}"
DEPLOY="${ROUTEVAULT_DEPLOY:-1}"
RAILWAY_PROJECT="${RAILWAY_PROJECT:-37267b3e-5395-431d-beda-f1982c9fb32c}"
RAILWAY_ENV="${RAILWAY_ENV:-production}"
RAILWAY_SERVICE="${RAILWAY_SERVICE:-routevault}"

mkdir -p "$WORK/data" "$WORK/code/routevault-staging/data"

# Ensure the railway CLI is on PATH under cron (no login shell, nvm not sourced).
if ! command -v railway >/dev/null 2>&1; then
  for d in "$HOME"/.nvm/versions/node/*/bin "$HOME"/.local/bin /usr/local/bin; do
    if [ -x "$d/railway" ]; then export PATH="$d:$PATH"; break; fi
  done
fi
rsync -a --delete "$ROOT/pipeline/" "$WORK/pipeline/"
if [[ -f "$ROOT/data/routevault.db" ]]; then
  cp -f "$ROOT/data/routevault.db" "$WORK/data/routevault.db"
fi

python3 -m pipeline.run --root "$WORK" --discover --news
python3 "$ROOT/pipeline/ingest/store_provider_prices.py" "$WORK/data/routevault.db" || echo "provider prices fetch failed, continuing"

cp -f "$WORK/data/routevault.db" "$ROOT/data/routevault.db"
python3 -c "
import json, sqlite3
conn = sqlite3.connect('$WORK/data/routevault.db')
conn.row_factory = sqlite3.Row
rows = [dict(r) for r in conn.execute('SELECT * FROM provider_prices ORDER BY provider, model_id')]
out = {'generated_at': __import__('datetime').datetime.now(__import__('datetime').UTC).isoformat(), 'source': 'models.dev', 'count': len(rows), 'rows': rows}
open('$ROOT/code/routevault-staging/data/provider-prices.json','w').write(json.dumps(out))
import os
_web = os.path.join('$ROOT', 'code', 'routevault-web', 'public', 'data', 'provider-prices.json')
os.makedirs(os.path.dirname(_web), exist_ok=True)
open(_web, 'w').write(json.dumps(out))
print('provider-prices.json written', len(rows))
"
cp -f "$WORK/data/models.json" "$ROOT/data/models.json"
cp -f "$WORK/data/analytical_dataset.json" "$ROOT/data/analytical_dataset.json"
mkdir -p "$ROOT/code/routevault-staging/data"
cp -f "$WORK/code/routevault-staging/data/dataset.json" "$ROOT/code/routevault-staging/data/dataset.json"
cp -f "$WORK/code/routevault-staging/data/models.json" "$ROOT/code/routevault-staging/data/models.json"
if [[ -f "$WORK/data/news.json" ]]; then
  cp -f "$WORK/data/news.json" "$ROOT/data/news.json"
  cp -f "$WORK/data/news.json" "$ROOT/code/routevault-staging/data/news.json"
fi
if [[ -f "$WORK/data/discovered_models.json" ]]; then
  cp -f "$WORK/data/discovered_models.json" "$ROOT/data/discovered_models.json"
  cp -f "$WORK/data/discovered_models.json" "$ROOT/code/routevault-staging/data/discovered_models.json"
fi

echo "tick wrote $ROOT/code/routevault-staging/data/dataset.json"

# Publish catalog to the Astro web app's Postgres (ingest endpoint).
if [[ -f "$HOME/.config/routevault/publish.env" ]]; then
  set +e
  python3 "$ROOT/scripts/publish_db.py" "$WORK/data/routevault.db"
  set -e
else
  echo "publish env missing, skipping web ingest"
fi

if [[ "$DEPLOY" != "1" ]]; then
  echo "skip railway up (ROUTEVAULT_DEPLOY=$DEPLOY)"
  exit 0
fi

if ! command -v railway >/dev/null 2>&1; then
  echo "railway CLI missing even after PATH fallback; NAS catalog updated, live site not pushed"
  exit 2
fi

cd "$ROOT/code/routevault-staging"
railway up --detach -m "catalog+news tick" \
  --project "$RAILWAY_PROJECT" \
  --environment "$RAILWAY_ENV" \
  --service "$RAILWAY_SERVICE"
echo "railway up queued"
