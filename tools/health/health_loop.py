#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys, time, json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common.env_utils import load_env_file, to_bool

def parse_interval_minutes(s: str, default=1) -> int:
    if not s: return default
    s = s.strip().lower()
    if s.endswith("m"):
        try: return int(float(s[:-1]))
        except: return default
    if s.endswith("h"):
        try: return int(float(s[:-1]) * 60)
        except: return default
    try: return int(float(s))
    except: return default

def latest_mtime(path: Path) -> float:
    if not path.exists(): return 0.0
    if path.is_file(): return path.stat().st_mtime
    mt = 0.0
    any_file = False
    for p in path.glob("**/*"):
        try:
            mt = max(mt, p.stat().st_mtime)
            any_file = True
        except Exception:
            pass
    return mt if any_file else 0.0

def main():
    root = ROOT
    env = load_env_file(root / ".env")
    log_dir = Path(env.get("LOG_DIR") or "logs")
    decisions_dir = Path(env.get("LOG_DECISIONS_DIR") or (log_dir / "decisions"))
    health_root = Path(env.get("LOG_HEALTH_DIR") or (log_dir / "health"))
    health_dir = health_root / "guard"
    health_dir.mkdir(parents=True, exist_ok=True)
    run_dir = root / "run"; run_dir.mkdir(parents=True, exist_ok=True)

    interval_s = max(15, parse_interval_minutes(env.get("INTERVAL","1m")) * 60)
    tolerate_stale_multiplier = 5

    health_log = health_dir / "health_loop.log"
    heartbeat = health_dir / "heartbeat.json"
    stop_flag = run_dir / "STOP_GUARD.flag"

    def log(msg):
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with health_log.open("a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")
        print(msg, flush=True)

    def ping_latency():
        try:
            from binance.client import Client as LegacyClient
            api_key = env.get("BINANCE_API_KEY"); api_secret = env.get("BINANCE_API_SECRET")
            is_testnet = to_bool(env.get("BINANCE_TESTNET","0"), default=False)
            cli = LegacyClient(api_key=api_key, api_secret=api_secret, testnet=is_testnet)
            t0 = time.perf_counter()
            _ = cli.futures_ping()
            return (time.perf_counter() - t0) * 1000.0
        except Exception as e:
            log(f"ping ERROR: {type(e).__name__}: {e}")
            return None

    log("Health-Loop started.")
    last_monotonic = time.monotonic()
    while True:
        if stop_flag.exists():
            log("STOP_GUARD.flag detected → exiting Health-Loop.")
            return 0

        lat_ms = ping_latency()
        dec_mtime = latest_mtime(decisions_dir)

        stale_sec = None if dec_mtime == 0.0 else int(time.time() - dec_mtime)
        stale_warn = False
        if stale_sec is not None and stale_sec > tolerate_stale_multiplier * interval_s:
            stale_warn = True

        now_mon = time.monotonic()
        step = now_mon - last_monotonic
        last_monotonic = now_mon
        drift_warn = step > (tolerate_stale_multiplier * interval_s)

        beat = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "latency_ms": None if lat_ms is None else round(lat_ms,2),
            "decisions_stale_sec": stale_sec,
            "stale_warn": stale_warn,
            "drift_sec": round(step,2),
            "drift_warn": drift_warn
        }
        heartbeat.write_text(json.dumps(beat, indent=2), encoding="utf-8")

        prefix = "WARN " if (stale_warn or drift_warn) else ""
        msg = f"{prefix}ping={beat['latency_ms']}ms; decisions_stale={beat['decisions_stale_sec']}; drift={beat['drift_sec']}s"
        log(msg)

        time.sleep( max(10, int(interval_s/2)) )

if __name__ == "__main__":
    raise SystemExit(main())
