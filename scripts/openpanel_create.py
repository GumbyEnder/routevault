#!/usr/bin/env python3
"""Create the RouteVault project in OpenPanel (org bns) and print its client ID.
Token source: frodo config.yaml MCP URL (client:secret pair)."""
import base64
import json
import os
import re
import urllib.request

cfg = os.path.expanduser("~/.hermes/profiles/frodo/config.yaml")
m = re.search(r"api\.openpanel\.dev/mcp\?token=([A-Za-z0-9=_-]+)", open(cfg).read())
raw = base64.b64decode(m.group(1)).decode()
cid, sec = raw.split(":")
auth = base64.b64encode(raw.encode()).decode()

for hdr in (f"Basic {auth}", f"Bearer {sec}"):
    req = urllib.request.Request(
        "https://api.openpanel.dev/projects/",
        data=json.dumps({"name": "RouteVault", "domain": "https://routevault.ai"}).encode(),
        method="POST",
        headers={"Authorization": hdr, "Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"},
    )
    try:
        out = json.load(urllib.request.urlopen(req, timeout=15))
        print("CREATED:", json.dumps(out, indent=1))
        break
    except Exception as e:  # noqa: BLE001
        print(hdr.split()[0], "failed:", e)
