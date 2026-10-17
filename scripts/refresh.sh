#!/usr/bin/env bash
# Refresh live catalog. Writes SQLite on local disk, copies JSON back to NAS.
set -euo pipefail
ROOT="${ROUTEVAULT_ROOT:-/mnt/nas/agents/Projects/RouteVault}"
WORK="${ROUTEVAULT_WORK:-/tmp/routevault-work}"
mkdir -p "$WORK/data" "$WORK/code/routevault-staging/data"
rsync -a --delete "$ROOT/pipeline/" "$WORK/pipeline/"
if [[ -f "$ROOT/data/routevault.db" ]]; then
  cp -f "$ROOT/data/routevault.db" "$WORK/data/routevault.db"
fi
python3 -m pipeline.run --root "$WORK" --backfill-history
cp -f "$WORK/data/routevault.db" "$ROOT/data/routevault.db"
cp -f "$WORK/data/models.json" "$ROOT/data/models.json"
cp -f "$WORK/data/analytical_dataset.json" "$ROOT/data/analytical_dataset.json"
mkdir -p "$ROOT/code/routevault-staging/data"
cp -f "$WORK/code/routevault-staging/data/dataset.json" "$ROOT/code/routevault-staging/data/dataset.json"
cp -f "$WORK/code/routevault-staging/data/models.json" "$ROOT/code/routevault-staging/data/models.json"
echo "refreshed $ROOT/code/routevault-staging/data/dataset.json"
