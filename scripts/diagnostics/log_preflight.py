#!/usr/bin/env python3
# scripts/diagnostics/log_preflight.py  (path-robust + rich output)
from __future__ import annotations
import os, sys, json, time
from pathlib import Path
from importlib.machinery import SourceFileLoader

_THIS = Path(__file__).resolve()
_PROJ_ROOT = _THIS.parents[2]
_DIAG_DIR = _PROJ_ROOT / "scripts" / "diagnostics"
_PF_PATH = _DIAG_DIR / "preflight_v2.py"

if str(_PROJ_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJ_ROOT))
if str(_DIAG_DIR) not in sys.path:
    sys.path.insert(0, str(_DIAG_DIR))

try:
    import scripts.diagnostics.preflight_v2 as pf
except Exception:
    pf = SourceFileLoader("preflight_v2", str(_PF_PATH)).load_module()

def run_preflight_capture() -> dict:
    ok, err = pf.ping_ok()
    drift, srv, loc = pf.check_time_drift()
    SYMBOL = os.environ.get("SYMBOL", "BTCUSDT")
    fs, sym, fstats = {}, {}, {}
    try:
        ex = pf.exchange_info(SYMBOL)
        fs, sym = pf.filters_map(ex, SYMBOL)
        px = pf.price(SYMBOL)
        fstats = pf.check_symbol_filters(fs, px)
    except Exception:
        pass
    return {
        "ping_ok": ok, "ping_err": err,
        "time": {"server": srv, "local": loc, "drift_ms": drift, "drift_ok": drift <= int(os.environ.get("PREFLIGHT_MAX_DRIFT_MS","1500"))},
        "symbol": SYMBOL,
        "filters_found": list(fs.keys()) if fs else [],
        "symbol_status": sym.get("status") if sym else None,
        "qty_constraints": fstats,
    }

def main():
    data = run_preflight_capture()
    ts = time.strftime("%Y%m%d")
    outdir = _PROJ_ROOT / "logs" / "preflight" / ts
    outdir.mkdir(parents=True, exist_ok=True)
    fname = outdir / f"{int(time.time()*1000)}.json"
    fname.write_text(json.dumps(data, indent=2), encoding="utf-8")
    abs_path = fname.resolve()
    file_uri = "file:///" + str(abs_path).replace("\\", "/")
    print(json.dumps({"written": str(fname), "written_abs": str(abs_path), "file_uri": file_uri}, indent=2))

if __name__ == "__main__":
    main()
