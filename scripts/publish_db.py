#!/usr/bin/env python3
"""Publish the pipeline's SQLite catalog (models, price_history, benchmark_history)
to the Astro web app's Postgres via POST /api/ingest.

Called by scripts/tick.sh after every pipeline run. Token + URL come from
ROUTVAULT publish env (default /home/gumbyender/.config/routevault/publish.env).
"""
import json
import os
import sqlite3
import sys
import urllib.request

ROOT = os.environ.get("ROUTEVAULT_ROOT", "/mnt/nas/agents/Projects/RouteVault")
ENV_FILE = os.environ.get("RV_PUBLISH_ENV", os.path.expanduser("~/.config/routevault/publish.env"))


def load_env():
    env = {}
    path = os.path.expanduser("~/.config/routevault/publish.env")
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
    return env


def main():
    load_env()
    url = os.environ.get("RV_WEB_URL", "https://routevault.ai")
    token = os.environ.get("RV_INGEST_TOKEN")
    if not url or not token:
        print("publish: RV_WEB_URL / RV_INGEST_TOKEN missing, skipping")
        return 0
    db_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data", "routevault.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    models = [dict(r) for r in conn.execute("SELECT * FROM models")]
    price_history = [dict(r) for r in conn.execute(
        "SELECT model_id, date, input_price, output_price, source FROM price_history")]
    benchmark_history = [dict(r) for r in conn.execute(
        "SELECT model_id, date, benchmark_type, score, source FROM benchmark_history")]

    payload = {
        "models": models,
        "price_history": price_history,
        "benchmark_history": benchmark_history,
    }
    body = json.dumps(payload, default=str).encode()
    req = urllib.request.Request(
        f"{url.rstrip('/')}/api/ingest",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            out = json.loads(resp.read())
            print(f"publish: {out}")
    except Exception as e:  # noqa: BLE001
        print(f"publish FAILED: {e}")
        return 1

    # Refresh legacy client data + OG images, then redeploy the web service.
    web = os.path.join(ROOT, "code", "routevault-web")
    staging_data = os.path.join(ROOT, "code", "routevault-staging", "data")
    for name in ("dataset.json", "news.json", "discovered_models.json", "local-models.json", "provider-prices.json"):
        src = os.path.join(staging_data, name)
        if os.path.exists(src):
            os.makedirs(os.path.join(web, "public", "data"), exist_ok=True)
            _copy(src, os.path.join(web, "public", "data", name))
    try:
        import subprocess
        subprocess.run(["python3", os.path.join(ROOT, "scripts", "gen_og.py")], check=False, timeout=300)
    except Exception as e:  # noqa: BLE001
        print(f"og gen failed: {e}")
    if os.environ.get("RV_WEB_DEPLOY", "1") == "1" and os.path.exists(os.path.join(web, "railway.json")):
        import subprocess
        import glob
        import shutil as _shutil
        railway_bin = _shutil.which("railway")
        if not railway_bin:
            for pat in (os.path.expanduser("~/.nvm/versions/node/*/bin/railway"),
                        os.path.expanduser("~/.local/bin/railway"),
                        "/usr/local/bin/railway"):
                m = sorted(glob.glob(pat))
                if m:
                    railway_bin = m[-1]
                    break
        if not railway_bin:
            print("web deploy failed: railway CLI not found in PATH or nvm/local fallbacks")
            return 0
        r = subprocess.run([railway_bin, "up", "--service", "routevault-web", "--detach"],
                           cwd=web, capture_output=True, text=True, timeout=600)
        print("web deploy queued" if r.returncode == 0 else f"web deploy failed: {r.stderr[-200:]}")
    return 0


def _copy(src, dst):
    import shutil
    shutil.copyfile(src, dst)


if __name__ == "__main__":
    sys.exit(main())
