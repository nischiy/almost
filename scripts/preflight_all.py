#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/preflight_all.py  (calls core.env_loader.load_env_files)
- Single source: core.env_loader
- Adds project root to sys.path
- Explicitly calls load_env_files() if present
"""
import os, sys, json, time, hmac, hashlib, urllib.parse, urllib.request, datetime, pathlib, re, importlib, inspect

# sys.path -> ensure 'core' is importable
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

LOG_DIR = PROJECT_ROOT / "logs" / "preflight" / datetime.date.today().isoformat()
LOG_DIR.mkdir(parents=True, exist_ok=True)

def write_json(name, obj):
    p = LOG_DIR / name
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(p)

def getenv_bool(v, default=False):
    if v is None: return default
    return v.strip().lower() in ("1","true","yes","on","y")

def parse_number(s):
    if s is None:
        return False, None
    t = s.strip().strip('"').strip("'")
    t = re.split(r'\s[#;]|//', t, maxsplit=1)[0].strip()
    t = t.replace("_","").replace(",","").replace(" ","")
    m = re.search(r'^([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)(%)?$', t)
    if not m:
        return False, None
    return True, float(m.group(1))

REQ_KEYS = [
    "BINANCE_API_KEY",
    "BINANCE_API_SECRET",
    "PAPER_TRADING",
    "TRADE_ENABLED",
    "RISK_MAX_DD_PCT_DAY",
    "RISK_MAX_LOSS_USD_DAY",
    "RISK_MAX_TRADES_PER_DAY",
    "RISK_MAX_CONSEC_LOSSES",
    "RISK_MIN_EQUITY_USD",
]

def required_keys_check(env):
    return [k for k in REQ_KEYS if not env.get(k)]

def validate_modes(env):
    return {
        "paper_trading": getenv_bool(env.get("PAPER_TRADING","1")),
        "trade_enabled": getenv_bool(env.get("TRADE_ENABLED","0")),
        "warnings": []
    }

def validate_risk(env):
    keys = [
        "RISK_MAX_DD_PCT_DAY",
        "RISK_MAX_LOSS_USD_DAY",
        "RISK_MAX_TRADES_PER_DAY",
        "RISK_MAX_CONSEC_LOSSES",
        "RISK_MIN_EQUITY_USD",
    ]
    issues, values, raw = {}, {}, {}
    for k in keys:
        raw[k] = env.get(k)
        ok, val = parse_number(env.get(k))
        if not ok:
            issues[k] = "not a number"
            continue
        if k.endswith("_PCT_DAY"):
            if not (0 <= val <= 100):
                issues[k] = "percent must be within [0,100]"
        elif val < 0:
            issues[k] = "must be non-negative"
        values[k] = val
    return {"values": values, "issues": issues, "raw": raw}

def http_get_json(url, headers=None, timeout=10):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))

def binance_server_time():
    t = http_get_json("https://fapi.binance.com/fapi/v1/time")
    return {"serverTime": t.get("serverTime", None), "clientTime": int(time.time()*1000)}

def binance_exchange_info():
    ei = http_get_json("https://fapi.binance.com/fapi/v1/exchangeInfo")
    symbols = []
    for s in ei.get("symbols", [])[:30]:
        symbols.append({
            "symbol": s.get("symbol"),
            "status": s.get("status"),
            "contractType": s.get("contractType"),
            "filters": [f.get("filterType") for f in s.get("filters",[])]
        })
    return {"timezone": ei.get("timezone"), "serverTime": ei.get("serverTime"), "symbols_preview": symbols}

def sign_params(params, secret):
    qs = urllib.parse.urlencode(params, doseq=True)
    sig = hmac.new(secret.encode(), qs.encode(), hashlib.sha256).hexdigest()
    return qs + "&signature=" + sig

def binance_account_ping(key, secret):
    endpoint = "https://fapi.binance.com/fapi/v2/balance"
    ts = int(time.time()*1000)
    qs = sign_params({"timestamp": ts, "recvWindow": 5000}, secret)
    req = urllib.request.Request(endpoint + "?" + qs, headers={"X-MBX-APIKEY": key})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return {"ok": True, "http": resp.getcode()}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def load_env_via_canonical_module():
    import importlib
    mod = importlib.import_module("core.env_loader")
    # 1) Prefer exact API you have:
    fn = getattr(mod, "load_env_files", None)
    if callable(fn):
        try:
            fn()
            return "load_env_files()"
        except Exception as e:
            return f"load_env_files() ERROR: {e}"
    # 2) Fallbacks (in case you later rename):
    for name in ("load_env","load","initialize","init","setup","ensure_loaded","apply_env","apply","read_env","read"):
        f = getattr(mod, name, None)
        if callable(f):
            try:
                f()
                return f"{name}()"
            except Exception:
                continue
    return "<no-entry-found>"

def main():
    status = {"errors": [], "warnings": []}
    used = load_env_via_canonical_module()

    env_view = {k: os.environ.get(k) for k in REQ_KEYS}
    write_json("env_check.json", {"loader_entry": used, "keys": env_view})

    missing = required_keys_check(env_view)
    if missing:
        status["errors"].append(f"Missing required keys: {', '.join(missing)}")

    modes = validate_modes(env_view)
    risk = validate_risk(env_view)

    conn = {}
    try:
        st = binance_server_time()
        conn["time"] = st
        drift_ms = abs(st["serverTime"] - st["clientTime"]) if st["serverTime"] else None
        if drift_ms is not None and drift_ms > 3000:
            status["warnings"].append(f"Clock drift > 3s: {drift_ms} ms")
    except Exception as e:
        status["errors"].append(f"Server time check failed: {e}")

    try:
        ei = binance_exchange_info()
        conn["exchangeInfo"] = {"timezone": ei.get("timezone"), "serverTime": ei.get("serverTime"), "symbols_preview": ei.get("symbols_preview")}
    except Exception as e:
        status["errors"].append(f"exchangeInfo failed: {e}")

    if env_view.get("BINANCE_API_KEY") and env_view.get("BINANCE_API_SECRET"):
        ping = binance_account_ping(env_view["BINANCE_API_KEY"], env_view["BINANCE_API_SECRET"])
        conn["account_ping"] = ping
        if not ping.get("ok"):
            status["warnings"].append("API keys present but signed ping failed (check IP whitelist/permissions).")

    write_json("connectivity.json", conn)
    write_json("risk_validation.json", risk)
    write_json("modes.json", modes)

    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    summary = {
        "timestamp": now_utc,
        "env_loader_entry": used,
        "required_keys_missing": missing,
        "modes": modes,
        "risk_issues": risk["issues"],
        "warnings": status["warnings"],
        "errors": status["errors"],
        "dod_pass": (not status["errors"]) and (len(status["warnings"]) == 0) and (len(risk["issues"]) == 0)
    }
    write_json("preflight_summary.json", summary)

    if summary["dod_pass"]:
        print("Preflight: PASS")
        sys.exit(0)
    else:
        print("Preflight: FAIL")
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        print("RAW_ENV_VALUES:")
        print(json.dumps(env_view, indent=2, ensure_ascii=False))
        sys.exit(1)

if __name__ == "__main__":
    main()
