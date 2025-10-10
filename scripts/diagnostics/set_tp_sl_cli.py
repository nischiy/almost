#!/usr/bin/env python3
# scripts/diagnostics/set_tp_sl_cli.py  (path-robust)
from __future__ import annotations
import os, sys, json
from pathlib import Path
from importlib.machinery import SourceFileLoader

_THIS = Path(__file__).resolve()
_PROJ_ROOT = _THIS.parents[2]
_UTILS_DIR = _PROJ_ROOT / "utils"
_EXIT_PATH = _UTILS_DIR / "exit_adapter.py"

if str(_PROJ_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJ_ROOT))
if str(_UTILS_DIR) not in sys.path:
    sys.path.insert(0, str(_UTILS_DIR))

try:
from app.services.exit_adapter import preview_exits, send_exits
except Exception:
    mod = SourceFileLoader("exit_adapter", str(_EXIT_PATH)).load_module()
    preview_exits = mod.preview_exits
    send_exits = mod.send_exits

def envf(name: str, default=None, cast=float):
    v = os.environ.get(name)
    if v is None: return default
    try: return cast(v)
    except Exception: return default

def main():
    symbol = os.environ.get("SYMBOL", "BTCUSDT")
    side = os.environ.get("SIDE", "BUY")  # entry side
    sl = envf("SL_PRICE", None, float)
    tp = envf("TP_PRICE", None, float)
    do_send = int(envf("SEND_EXITS", 0, float))  # 0=preview; 1=send

    data = send_exits(symbol, side, sl, tp) if do_send == 1 else preview_exits(symbol, side, sl, tp)
    # Write log
    import time
    ts = time.strftime("%Y%m%d")
    outdir = (_PROJ_ROOT / "logs" / "exits" / ts)
    outdir.mkdir(parents=True, exist_ok=True)
    fname = outdir / f"exits_{int(time.time()*1000)}.json"
    fname.write_text(json.dumps(data, indent=2), encoding="utf-8")
    abs_path = fname.resolve()
    file_uri = "file:///" + str(abs_path).replace("\\", "/")
    print(json.dumps({"written": str(fname), "written_abs": str(abs_path), "file_uri": file_uri, **data}, indent=2))

if __name__ == "__main__":
    main()

