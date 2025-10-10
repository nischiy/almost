#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fallback: build per-trade CSV from UM Futures income history (realizedPnl events).
Used when user_trades/futures_account_trades returns empty.

Output schema:
entry_time, exit_time, entry_price, exit_price, qty, side, pnl, fees, r, slippage, symbol
"""
import argparse, os, sys, csv
from pathlib import Path
from datetime import datetime, timedelta, timezone

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common.env_utils import load_env_file, to_bool

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", type=str, default=".")
    ap.add_argument("--days", type=int, default=365)
    args = ap.parse_args()

    root = Path(args.project_root).resolve()
    env = load_env_file(root / ".env")
    is_testnet = to_bool(env.get("BINANCE_TESTNET","0"), default=False)
    api_key = env.get("BINANCE_API_KEY"); api_secret = env.get("BINANCE_API_SECRET")
    if not api_key or not api_secret:
        print("ERROR: Missing usable API credentials.", file=sys.stderr); return 2

    try:
        from binance.client import Client as LegacyClient
    except Exception as e:
        print(f"ERROR: Cannot import python-binance legacy Client: {e}", file=sys.stderr)
        return 3

    cli = LegacyClient(api_key=api_key, api_secret=api_secret, testnet=is_testnet)

    end = datetime.now(timezone.utc); start = end - timedelta(days=args.days)
    start_ms = int(start.timestamp()*1000); end_ms = int(end.timestamp()*1000)

    # Pull income: realized pnl events (+ commissions for same timestamp to fill fees)
    try:
        income = cli.futures_income_history(startTime=start_ms, endTime=end_ms, limit=1000)
    except Exception as e:
        print(f"ERROR: futures_income_history failed: {e}", file=sys.stderr)
        return 4

    if not income:
        print("ERROR: No income entries returned in the given window.", file=sys.stderr)
        return 5

    rows = []
    commissions = {}
    for it in income:
        itype = it.get("incomeType")
        try:
            ts = int(it.get("time"))
        except Exception:
            ts = None
        sym = it.get("symbol") or ""
        amt_str = it.get("income") or "0"
        try:
            amt = float(amt_str)
        except Exception:
            amt = 0.0

        if itype == "COMMISSION":
            if ts:
                key = (sym, ts)
                commissions[key] = commissions.get(key, 0.0) + amt
            continue

        if itype != "REALIZED_PNL":
            continue

        if not ts:
            continue
        dt = datetime.fromtimestamp(ts/1000, tz=timezone.utc).replace(tzinfo=None)
        side = "LONG" if amt >= 0 else "SHORT"
        fee = 0.0
        key = (sym, ts)
        if key in commissions:
            fee = abs(commissions[key])

        rows.append({
            "entry_time": dt,
            "exit_time": dt,
            "entry_price": "",
            "exit_price": "",
            "qty": "",
            "side": side,
            "pnl": round(amt,8),
            "fees": round(fee,8),
            "r": "",
            "slippage": "",
            "symbol": sym
        })

    if not rows:
        print("ERROR: No REALIZED_PNL income entries found.", file=sys.stderr)
        return 6

    out_path = root / "logs" / "trades" / "trades_exported.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["entry_time","exit_time","entry_price","exit_price","qty","side","pnl","fees","r","slippage","symbol"])
        w.writeheader()
        for r in rows:
            rr = dict(r)
            rr["entry_time"] = r["entry_time"].strftime("%Y-%m-%d %H:%M:%S")
            rr["exit_time"] = r["exit_time"].strftime("%Y-%m-%d %H:%M:%S")
            w.writerow(rr)

    print(f"Wrote {len(rows)} rows -> {out_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
