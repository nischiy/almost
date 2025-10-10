#!/usr/bin/env python
# -*- coding: utf-8 -*-
import csv, time, os, sys, json
from pathlib import Path
from datetime import datetime, timezone, date

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common.env_utils import load_env_file, to_bool

def parse_env_floats(env, key, default=None):
    try:
        v = env.get(key)
        if v is None or str(v).strip()=="":
            return default
        return float(v)
    except Exception:
        return default

def today_utc(dtv: datetime) -> date:
    if dtv.tzinfo is None:
        return dtv.date()
    return dtv.astimezone(timezone.utc).date()

def read_trades_csv(path: Path):
    rows = []
    if not path.exists(): return rows
    with path.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                et = datetime.strptime(row["exit_time"] or row["entry_time"], "%Y-%m-%d %H:%M:%S")
            except Exception:
                continue
            pnl = float(row.get("pnl") or 0.0)
            rows.append({"time": et, "pnl": pnl})
    return rows

def compute_same_day_metrics(rows):
    today = datetime.now(timezone.utc).date()
    todays = [r for r in rows if today_utc(r["time"]) == today]
    total = len(todays)
    day_pnl = sum(r["pnl"] for r in todays)
    consec_losses = 0
    for r in reversed(todays):
        if r["pnl"] < 0: consec_losses += 1
        else: break
    return {"count": total, "day_pnl": day_pnl, "consec_losses": consec_losses}

def main():
    root = ROOT
    env = load_env_file(root / ".env")
    log_dir = Path(env.get("LOG_DIR") or "logs")
    health_root = Path(env.get("LOG_HEALTH_DIR") or (log_dir / "health"))
    health_dir = health_root / "guard"
    health_dir.mkdir(parents=True, exist_ok=True)
    run_dir = root / "run"; run_dir.mkdir(parents=True, exist_ok=True)

    max_loss_day = parse_env_floats(env, "RISK_MAX_LOSS_USD_DAY", 10.0)
    max_trades_day = int(float(env.get("RISK_MAX_TRADES_PER_DAY", 20)))
    max_consec_losses = int(float(env.get("RISK_MAX_CONSEC_LOSSES", 3)))
    max_dd_pct_day = parse_env_floats(env, "RISK_MAX_DD_PCT_DAY", None)
    current_equity = parse_env_floats(env, "CURRENT_EQUITY_USD", None)

    log_file = health_dir / "kill_switch.log"
    flag_file = run_dir / "TRADE_KILLED.flag"
    stop_flag = run_dir / "STOP_GUARD.flag"
    trades_csv = (log_dir / "trades" / "trades_exported.csv")

    def log(msg):
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with log_file.open("a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")
        print(msg, flush=True)

    log("Kill-Switch started. Watching trades CSV...")
    last_mtime = None
    intrv = 5.0

    while True:
        if stop_flag.exists():
            log("STOP_GUARD.flag detected → exiting Kill-Switch.")
            return 0
        try:
            mtime = trades_csv.stat().st_mtime if trades_csv.exists() else None
            if mtime != last_mtime:
                last_mtime = mtime
                rows = read_trades_csv(trades_csv)
                m = compute_same_day_metrics(rows)

                dd_hit = False
                dd_detail = None
                if max_dd_pct_day is not None and current_equity is not None and current_equity > 0:
                    dd_pct = (max(0.0, -m["day_pnl"]) / current_equity) * 100.0
                    if dd_pct >= max_dd_pct_day:
                        dd_hit = True
                        dd_detail = round(dd_pct, 4)

                reason = None
                if m["day_pnl"] <= -abs(max_loss_day):
                    reason = f"Daily loss limit hit: {m['day_pnl']} <= -{abs(max_loss_day)}"
                elif m["consec_losses"] >= max_consec_losses:
                    reason = f"Consecutive losses limit hit: {m['consec_losses']} >= {max_consec_losses}"
                elif m["count"] >= max_trades_day:
                    reason = f"Trades-per-day limit hit: {m['count']} >= {max_trades_day}"
                elif dd_hit:
                    reason = f"Daily drawdown pct hit: {dd_detail}% >= {max_dd_pct_day}%"

                if reason and not flag_file.exists():
                    payload = {
                        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "reason": reason,
                        "today_pnl": m["day_pnl"],
                        "today_trades": m["count"],
                        "today_consec_losses": m["consec_losses"],
                        "config": {
                            "RISK_MAX_LOSS_USD_DAY": max_loss_day,
                            "RISK_MAX_TRADES_PER_DAY": max_trades_day,
                            "RISK_MAX_CONSEC_LOSSES": max_consec_losses,
                            "RISK_MAX_DD_PCT_DAY": max_dd_pct_day,
                            "CURRENT_EQUITY_USD": current_equity
                        }
                    }
                    flag_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
                    log(f"KILL TRIGGERED -> {reason}. Flag at {flag_file}")
            time.sleep(intrv)
        except Exception as e:
            log(f"ERROR loop: {type(e).__name__}: {e}")
            time.sleep(2.0)

if __name__ == "__main__":
    raise SystemExit(main())
