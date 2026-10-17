#!/usr/bin/env python3
"""Probe OpenPanel API auth styles with the MCP token pair; print error bodies."""
import base64
import json
import os
import re
import urllib.error
import urllib.request

cfg = os.path.expanduser("~/.hermes/profiles/frodo/config.yaml")
m = re.search(r"api\.openpanel\.dev/mcp\?token=([A-Za-z0-9=_-]+)", open(cfg).read())
raw = base64.b64decode(m.group(1)).decode()
cid, sec = raw.split(":")
for name, hdr in (
    ("Basic", "Basic " + base64.b64encode(raw.encode()).decode()),
    ("Bearer-sec", "Bearer " + sec),
    ("Bearer-cid", "Bearer " + cid),
):
    req = urllib.request.Request("https://api.openpanel.dev/projects/", headers={"Authorization": hdr, "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"})
    try:
        body = json.load(urllib.request.urlopen(req, timeout=15))
        print(name, "OK:", json.dumps(body)[:200])
        break
    except urllib.error.HTTPError as e:
        print(name, e.code, e.read().decode()[:150])
