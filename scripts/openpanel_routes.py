#!/usr/bin/env python3
"""Find the OpenPanel projects route + create RouteVault project."""
import base64
import json
import os
import re
import urllib.error
import urllib.request

cfg = os.path.expanduser("~/.hermes/profiles/frodo/config.yaml")
m = re.search(r"api\.openpanel\.dev/mcp\?token=([A-Za-z0-9=_-]+)", open(cfg).read())
raw = base64.b64decode(m.group(1)).decode()
auth = "Basic " + base64.b64encode(raw.encode()).decode()
UA = {"Authorization": auth, "User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}


def get(path):
    req = urllib.request.Request("https://api.openpanel.dev" + path, headers=UA)
    try:
        return json.load(urllib.request.urlopen(req, timeout=15))
    except urllib.error.HTTPError as e:
        return {"_code": e.code, "_body": e.read().decode()[:120]}


def post(path, body):
    req = urllib.request.Request("https://api.openpanel.dev" + path,
        data=json.dumps(body).encode(), method="POST", headers=UA)
    try:
        return json.load(urllib.request.urlopen(req, timeout=15))
    except urllib.error.HTTPError as e:
        return {"_code": e.code, "_body": e.read().decode()[:200]}


for path in ("/projects", "/v1/projects", "/organizations/bns/projects"):
    r = get(path)
    print("GET", path, "->", json.dumps(r)[:160])

for path in ("/projects", "/v1/projects"):
    r = post(path, {"name": "RouteVault", "domain": "https://routevault.ai"})
    print("POST", path, "->", json.dumps(r)[:300])
