
from __future__ import annotations
import os, sys, json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Iterable, Tuple, Any

try:
    from tools.common.env_utils import require_keys
except Exception:
    def require_keys(env: Dict[str,str], keys: Iterable[str]) -> Dict[str, Any]:
        missing = [k for k in keys if not str(env.get(k, "")).strip()]
        return {"ok": not missing, "missing": missing}

REQUIRED_MODULES = [
    ("python-binance", "binance", True),
    ("pandas", "pandas", True),
    ("numba", "numba", False),
    ("ta", "ta", False),
    ("pydantic", "pydantic", True),
    ("orjson", "orjson", False),
]

def check_modules() -> Dict[str, Any]:
    mods = []
    ok = True
    for pkg, imp_name, critical in REQUIRED_MODULES:
        try:
            __import__(imp_name)
            mods.append({"package": pkg, "import": imp_name, "ok": True, "critical": critical})
        except Exception as e:
            mods.append({"package": pkg, "import": imp_name, "ok": False, "critical": critical, "err": str(e)})
            if critical:
                ok = False

    uvloop_note = "skipped on Windows" if os.name == "nt" else "optional"
    return {"ok": ok, "modules": mods, "uvloop": {"ok": True, "note": uvloop_note}}

def load_env_file(env_path: str = ".env") -> Tuple[Dict[str,str], str|None]:
    env = {}
    err = None
    p = Path(env_path)
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.strip().startswith("#"):
                continue
            if "=" in line:
                k,v = line.split("=",1)
                env[k.strip()] = v.strip()
    else:
        err = f"{env_path} not found"
    env.update({k:v for k,v in os.environ.items() if isinstance(k,str) and isinstance(v,str)})
    return env, err

def _as_bool(env: Dict[str,str], key: str, default: bool) -> bool:
    val = str(env.get(key, str(int(default)))).strip().lower()
    return val in {"1","true","yes","on"}

def _as_float(env: Dict[str,str], key: str, default: float|None) -> float|None:
    s = str(env.get(key, "")).strip()
    if not s:
        return default
    try:
        return float(s)
    except Exception:
        return default

def validate_env(env: Dict[str,str]) -> Dict[str, Any]:
    must = ["ENV","EXCHANGE","SYMBOL","INTERVAL","QUOTE_ASSET",
            "ORDER_QTY_USD","RISK_MAX_TRADES_PER_DAY","PAPER_TRADING","TRADE_ENABLED"]
    res = require_keys(env, must)
    if not res.get("ok"):
        return {"ok": False, "reason": f"missing keys: {res.get('missing')}"}

    flags = {
        "PAPER_TRADING": _as_bool(env, "PAPER_TRADING", True),
        "TRADE_ENABLED": _as_bool(env, "TRADE_ENABLED", False),
        "BINANCE_TESTNET": _as_bool(env, "BINANCE_TESTNET", False),
    }
    creds_required = flags["TRADE_ENABLED"] and not (flags["PAPER_TRADING"] or flags["BINANCE_TESTNET"])
    if creds_required:
        have = require_keys(env, ["BINANCE_API_KEY","BINANCE_API_SECRET"])
        if not have.get("ok", False):
            return {"ok": False, "reason": "missing live creds", "creds_ok": False, "flags": flags}

    risk_keys = ["RISK_MAX_LOSS_USD_DAY","RISK_MAX_DD_PCT_DAY","RISK_MAX_POS_USD","RISK_MIN_EQUITY_USD"]
    risk = {}
    for k in risk_keys:
        v = _as_float(env, k, None)
        if v is not None and v < 0:
            return {"ok": False, "reason": f"negative {k}"}
        if v is not None:
            risk[k] = v

    return {"ok": True, "flags": flags, "creds_ok": True, "risk": risk}

def _preflight_dir() -> Path:
    d = Path("logs")/"preflight"/datetime.now(timezone.utc).strftime("%Y-%m-%d")
    d.mkdir(parents=True, exist_ok=True)
    return d

def run() -> int:
    env, env_err = load_env_file(".env")
    envv = validate_env(env)

    mods = check_modules()

    try:
        from tools.preflight import binance_checks
        symbol = env.get("SYMBOL","BTCUSDT")
        connectivity = binance_checks.connectivity(env, symbol)
    except Exception as e:
        connectivity = {"ok": False, "err": str(e)}

    ok = bool(envv.get("ok")) and bool(mods.get("ok")) and bool(connectivity.get("ok"))
    out = {
        "ok": ok,
        "env": envv,
        "modules": mods,
        "connectivity": connectivity,
        "env_load_err": env_err,
    }
    f = _preflight_dir()/f"preflight_{datetime.now(timezone.utc).strftime('%H%M%S')}.json"
    f.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Preflight OK" if ok else "Preflight FAIL")
    return 0 if ok else 1
