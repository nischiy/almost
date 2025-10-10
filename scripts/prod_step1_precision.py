# -*- coding: utf-8 -*-
"""
prod_step1_precision.py
Step 1 (LIVE-ready): додаємо модуль core/precision.py з парсером exchangeInfo (tickSize, stepSize, minNotional)
та підключаємо легкий хук у app/run.py (тільки імпорт + завантаження фільтрів). Жодних змін у торговій логіці.
"""
from __future__ import annotations

import os
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
TARGET_PREC = ROOT / "core" / "precision.py"
TARGET_RUN = ROOT / "app" / "run.py"
CACHE_DIR = ROOT / "logs" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

PRECISION_CODE = r"""# -*- coding: utf-8 -*-
from __future__ import annotations
import os, json, math
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional

try:
    import requests  # type: ignore
except Exception:
    requests = None  # type: ignore

_CACHE = {}
_CACHE_PATH = Path("logs/cache/exchangeInfo.json")
_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

def _now_iso():
    return datetime.now(timezone.utc).isoformat()

def _load_cache() -> Dict[str, Any]:
    if _CACHE:
        return _CACHE
    if _CACHE_PATH.exists():
        try:
            data = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                _CACHE.update(data)
        except Exception:
            pass
    return _CACHE

def _save_cache():
    try:
        _CACHE_PATH.write_text(json.dumps(_CACHE, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

def _fetch_exchange_info(symbol: str) -> Optional[Dict[str, Any]]:
    if requests is None:
        return None
    url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return None
    syms = {s["symbol"]: s for s in data.get("symbols", []) if "symbol" in s}
    return syms.get(symbol)

def _to_float(s: Any, default: float) -> float:
    try:
        return float(s)
    except Exception:
        return default

def _parse_filters(sym: Dict[str, Any]) -> Dict[str, Any]:
    # defaults
    out = {
        "price_tick": 0.01,
        "qty_step": 0.001,
        "min_qty": 0.0,
        "min_notional": 0.0,
        "quote_precision": sym.get("quotePrecision", 8),
        "base_precision": sym.get("baseAssetPrecision", 8),
        "raw": sym,
        "updated_at": _now_iso(),
    }
    for f in sym.get("filters", []):
        t = f.get("filterType")
        if t == "PRICE_FILTER":
            out["price_tick"] = _to_float(f.get("tickSize"), out["price_tick"])
        elif t == "LOT_SIZE":
            out["qty_step"] = _to_float(f.get("stepSize"), out["qty_step"])
            out["min_qty"] = _to_float(f.get("minQty"), out["min_qty"])
        elif t in ("MIN_NOTIONAL", "NOTIONAL"):
            n = f.get("minNotional")
            if n is None:
                # деякі символи мають масив notional фільтрів
                n = f.get("notional", 0.0)
            out["min_notional"] = _to_float(n, out["min_notional"])
    return out

def get_filters(symbol: str, force_refresh: bool=False) -> Dict[str, Any]:
    symbol = symbol.upper()
    cache = _load_cache()
    if not force_refresh and symbol in cache:
        return cache[symbol]
    sym = _fetch_exchange_info(symbol)
    if not sym:
        # якщо немає інтернету чи 403 - вертаємо останній кеш або дефолт
        return cache.get(symbol, {
            "price_tick": 0.01, "qty_step": 0.001, "min_qty": 0.0, "min_notional": 0.0,
            "quote_precision": 8, "base_precision": 8, "raw": None, "updated_at": _now_iso(),
        })
    parsed = _parse_filters(sym)
    cache[symbol] = parsed
    _save_cache()
    return parsed

def _round_to_step(x: float, step: float) -> float:
    if step <= 0:
        return x
    # Binance вимагає кратність step; виконуємо підлогу до найближчого кроку
    return math.floor(x / step) * step

def round_price(price: float, filters: Dict[str, Any]) -> float:
    tick = float(filters.get("price_tick", 0.01))
    return _round_to_step(price, tick)

def round_qty(qty: float, filters: Dict[str, Any]) -> float:
    step = float(filters.get("qty_step", 0.001))
    return _round_to_step(qty, step)

def enforce_min_notional(qty: float, price: float, filters: Dict[str, Any]) -> float:
    # Підіймає qty до minNotional (якщо потрібно), з урахуванням stepSize.
    step = float(filters.get("qty_step", 0.001))
    min_notional = float(filters.get("min_notional", 0.0))
    if min_notional <= 0:
        return qty
    notional = qty * price
    if notional >= min_notional:
        return qty
    need = min_notional / max(price, 1e-12)
    # округлити вгору до кратності step
    k = math.ceil(need / max(step, 1e-12))
    return max(k * step, float(filters.get("min_qty", 0.0)))
"""

def backup(path: Path):
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    bak = Path(str(path) + f".bak_prod_step1_{ts}")
    bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return bak

def ensure_precision_module():
    TARGET_PREC.parent.mkdir(parents=True, exist_ok=True)
    if TARGET_PREC.exists():
        backup(TARGET_PREC)
    TARGET_PREC.write_text(PRECISION_CODE, encoding="utf-8")
    print(f"[OK] Wrote: {TARGET_PREC}")

def patch_run_import_and_init():
    if not TARGET_RUN.exists():
        print(f"[WARN] app/run.py not found: {TARGET_RUN}")
        return
    src = TARGET_RUN.read_text(encoding="utf-8")
    orig = src

    # 1) import
    if "from core.precision import get_filters" not in src:
        src = src.replace(
            "from core.telemetry import save_snapshot, log_decision",
            "from core.telemetry import save_snapshot, log_decision\nfrom core.precision import get_filters, round_price, round_qty, enforce_min_notional",
        )

    # 2) init filters once (у __init__ TraderApp)
    # знайдемо клас TraderApp і його __init__
    if "class TraderApp" in src and "def __init__(" in src and "self.filters = get_filters(self.symbol)" not in src:
        lines = src.splitlines()
        out = []
        in_init = False
        for i, line in enumerate(lines):
            out.append(line)
            if (not in_init) and line.strip().startswith("def __init__("):
                in_init = True
                continue
            if in_init:
                # після першого присвоєння self.symbol або на початку блоку ініт - вставимо загрузку фільтрів
                if "self.symbol" in line and "=" in line and "get_filters" not in line:
                    out.append(" " * (len(line) - len(line.lstrip())) + "self.filters = get_filters(self.symbol)")
                    in_init = False
        new_src = "\n".join(out)
        src = new_src

    if src != orig:
        backup(TARGET_RUN)
        TARGET_RUN.write_text(src, encoding="utf-8")
        print(f"[OK] Patched: {TARGET_RUN}")
    else:
        print("[OK] run.py already has precision imports/init")

def main():
    ensure_precision_module()
    patch_run_import_and_init()
    print("[DONE] Step 1 (precision module + run.py import/init) applied.")

if __name__ == "__main__":
    main()

