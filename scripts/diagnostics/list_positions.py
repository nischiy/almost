#!/usr/bin/env python3
# scripts/diagnostics/list_positions.py
# shared helpers (inline copy per file for simplicity)
from __future__ import annotations
import os, ssl, json, time, hmac, hashlib, urllib.parse as up
from urllib import request

BINANCE_FAPI_BASE = os.environ.get("BINANCE_FAPI_BASE", "https://fapi.binance.com")

def _headers():
    return {"X-MBX-APIKEY": os.environ.get("API_KEY",""), "User-Agent": "live-verify/1.0"}

def _signed_qs(params: dict) -> str:
    params = dict(params)
    params.setdefault("timestamp", int(time.time()*1000))
    params.setdefault("recvWindow", 5000)
    qs = up.urlencode(params, doseq=True)
    sig = hmac.new(os.environ.get("API_SECRET","").encode("utf-8"), qs.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{qs}&signature={sig}"

def _get(path: str, params: dict):
    url = BINANCE_FAPI_BASE.rstrip("/") + path + "?" + _signed_qs(params)
    ctx = ssl.create_default_context()
    r = request.Request(url, headers=_headers())
    with request.urlopen(r, context=ctx, timeout=15) as h:
        raw = h.read().decode("utf-8")
    try: return json.loads(raw)
    except Exception: return {"raw": raw}

def _post(path: str, params: dict):
    url = BINANCE_FAPI_BASE.rstrip("/") + path
    body = _signed_qs(params).encode("utf-8")
    ctx = ssl.create_default_context()
    r = request.Request(url, data=body, headers=_headers(), method="POST")
    with request.urlopen(r, context=ctx, timeout=15) as h:
        raw = h.read().decode("utf-8")
    try: return json.loads(raw)
    except Exception: return {"raw": raw}

import sys, json
def main():
    data = _get("/fapi/v2/positionRisk", {})
    # filter only non-zero positions
    out = [p for p in data if float(p.get("positionAmt",0)) != 0.0]
    print(json.dumps(out, indent=2))
if __name__ == "__main__":
    main()
