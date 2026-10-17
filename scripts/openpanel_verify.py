#!/usr/bin/env python3
"""Verify RouteVault OpenPanel project receives events (MCP streamable-HTTP handshake)."""
import json
import urllib.error
import urllib.request

TOK = "OGRhZTc0YTMtMmI0NC00ZWE3LTlhYTMtMDg2MDc1NGVlN2NkOnNlY19kYmNhYmIwZmQ4N2M1ZmI0M2NiYQ=="
URL = f"https://api.openpanel.dev/mcp?token={TOK}"
PID = "8dae74a3-2b44-4ea7-9aa3-0860754ee7cd"
HDRS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
    "User-Agent": "Mozilla/5.0",
}


def rpc(method, params, id=1, session=None):
    body = {"jsonrpc": "2.0", "id": id, "method": method}
    if params is not None:
        body["params"] = params
    h = dict(HDRS)
    if session:
        h["mcp-session-id"] = session
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers=h)
    resp = urllib.request.urlopen(req, timeout=30)
    sid = resp.headers.get("mcp-session-id")
    text = resp.read().decode()
    return sid, text


try:
    sid, text = rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                                   "clientInfo": {"name": "hermes", "version": "1.0"}})
    print("init ok, session:", (sid or "")[:12], "| body:", text[:120])
    rpc("notifications/initialized", None, id=None, session=sid) if sid else None
    sid2, text = rpc("tools/call", {"name": "query_events",
                                    "arguments": {"projectId": PID, "limit": 5}}, 2, session=sid)
    print("events:", text[:1200])
except urllib.error.HTTPError as e:
    print("HTTP", e.code, e.read().decode()[:300])
