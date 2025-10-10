#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse, os, sys, csv, math
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common.env_utils import load_env_file, to_bool

def to_float(x):
    try:
        if x is None: return None
        s=str(x).strip()
        if s=="": return None
        return float(s)
    except Exception:
        return None

def sign_for(side: str) -> int:
    s=(side or "").upper()
    return 1 if (s.startswith("B") or s.startswith("LONG")) else -1

def reconstruct_trades(fills: List[Dict[str,Any]]) -> List[Dict[str,Any]]:
    fills.sort(key=lambda r: r["timestamp"])
    by_sym: Dict[str,List[Dict[str,Any]]] = {}
    for f in fills: by_sym.setdefault(f["symbol"], []).append(f)

    trades: List[Dict[str,Any]] = []
    for sym, fs in by_sym.items():
        pos=0.0; avg=0.0; entry_t=None; fees=0.0; rpnl_cum=0.0; entry_qty_abs=0.0; side_dir=None
        for f in fs:
            sgn = sign_for(f["side"]); q = f["qty"] * sgn; price = f["price"]; t = f["timestamp"]
            fees += f.get("fee") or 0.0; rp = f.get("realized_pnl")
            if pos == 0.0:
                pos = q; avg = price; entry_t = t; side_dir = "LONG" if pos>0 else "SHORT"; entry_qty_abs = abs(pos); rpnl_cum=0.0
            else:
                if (pos>0 and q>0) or (pos<0 and q<0):
                    new_pos = pos + q
                    if (abs(pos)+abs(q))>0:
                        avg = (abs(pos)*avg + abs(q)*price) / (abs(pos)+abs(q))
                    pos = new_pos; entry_qty_abs = max(entry_qty_abs, abs(pos))
                else:
                    new_pos = pos + q
                    close_qty = abs(q) if abs(q)<=abs(pos) else abs(pos)
                    approx = (price-avg)*close_qty if pos>0 else (avg-price)*close_qty
                    rpnl_cum += (rp if (rp is not None) else approx)
                    pos = new_pos
                    if pos == 0.0:
                        trades.append({
                            "entry_time": entry_t, "exit_time": t,
                            "entry_price": round(float(avg),8), "exit_price": round(float(price),8),
                            "qty": round(float(entry_qty_abs),8), "side": side_dir,
                            "pnl": round(float(rpnl_cum),8), "fees": round(float(fees),8),
                            "r": "", "slippage": "", "symbol": sym
                        })
                        avg=0.0; entry_t=None; fees=0.0; rpnl_cum=0.0; side_dir=None; entry_qty_abs=0.0
    trades.sort(key=lambda x: x["exit_time"] or x["entry_time"])
    return trades

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", type=str, default=".")
    ap.add_argument("--days", type=int, default=30)
    args = ap.parse_args()
    root = Path(args.project_root).resolve()
    env = load_env_file(root / ".env")
    is_testnet = to_bool(env.get("BINANCE_TESTNET","0"), default=False)
    api_key = env.get("BINANCE_API_KEY"); api_secret = env.get("BINANCE_API_SECRET")
    if not api_key or not api_secret:
        print("ERROR: Missing usable API credentials.", file=sys.stderr); return 2

    # Try UMFutures first, else legacy Client endpoints
    use_legacy = False
    try:
        from binance.um_futures import UMFutures
        um = UMFutures(key=api_key, secret=api_secret, testnet=is_testnet)
        end = datetime.now(timezone.utc); start = end - timedelta(days=args.days)
        start_ms = int(start.timestamp()*1000); end_ms = int(end.timestamp()*1000)
        info = um.exchange_info(); symbols = [s["symbol"] for s in info.get("symbols",[]) if s.get("status")=="TRADING" and s["symbol"].endswith("USDT")]
        symbols = symbols[:60]
        fills: List[Dict[str,Any]] = []
        for sym in symbols:
            try:
                data = um.user_trades(symbol=sym, startTime=start_ms, endTime=end_ms, limit=1000)
                for t in data or []:
                    ts = t.get("time") or t.get("T")
                    price = to_float(t.get("price") or t.get("p")); qty = to_float(t.get("qty") or t.get("q"))
                    side = "BUY" if t.get("buyer") else "SELL"; realized = to_float(t.get("realizedPnl") or t.get("realized_pnl"))
                    fee = to_float(t.get("commission"))
                    if ts and price and qty:
                        fills.append({
                            "timestamp": datetime.fromtimestamp(int(ts)/1000, tz=timezone.utc).replace(tzinfo=None),
                            "symbol": sym, "side": side, "price": price, "qty": qty,
                            "realized_pnl": realized, "fee": fee
                        })
            except Exception:
                continue
    except Exception as e:
        use_legacy = True

    if use_legacy:
        try:
            from binance.client import Client as LegacyClient
        except Exception as e:
            print(f"ERROR: Neither UMFutures nor Legacy Client available: {e}", file=sys.stderr)
            return 3
        cli = LegacyClient(api_key=api_key, api_secret=api_secret, testnet=is_testnet)
        end = datetime.now(timezone.utc); start = end - timedelta(days=args.days)
        start_ms = int(start.timestamp()*1000); end_ms = int(end.timestamp()*1000)
        # Legacy endpoints
        info = cli.futures_exchange_info()
        symbols = [s["symbol"] for s in info.get("symbols",[]) if s.get("status")=="TRADING" and s["symbol"].endswith("USDT")]
        symbols = symbols[:60]
        fills: List[Dict[str,Any]] = []
        for sym in symbols:
            try:
                data = cli.futures_account_trades(symbol=sym, startTime=start_ms, endTime=end_ms)
                for t in data or []:
                    ts = t.get("time") or t.get("T")
                    price = to_float(t.get("price") or t.get("p")); qty = to_float(t.get("qty") or t.get("q"))
                    side = "BUY" if t.get("buyer") else "SELL"; realized = to_float(t.get("realizedPnl") or t.get("realized_pnl"))
                    fee = to_float(t.get("commission"))
                    if ts and price and qty:
                        fills.append({
                            "timestamp": datetime.fromtimestamp(int(ts)/1000, tz=timezone.utc).replace(tzinfo=None),
                            "symbol": sym, "side": side, "price": price, "qty": qty,
                            "realized_pnl": realized, "fee": fee
                        })
            except Exception:
                continue

    if not fills:
        print("ERROR: No fills pulled from Binance in the given window.", file=sys.stderr); return 5

    trades = reconstruct_trades(fills)
    if not trades:
        print("ERROR: Could not reconstruct round-trips from fills.", file=sys.stderr); return 6

    out_path = root / "logs" / "trades" / "trades_exported.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["entry_time","exit_time","entry_price","exit_price","qty","side","pnl","fees","r","slippage","symbol"])
        w.writeheader()
        for t in trades:
            row = dict(t)
            for k in ["entry_time","exit_time"]:
                dtv = row[k]; row[k] = dtv.strftime("%Y-%m-%d %H:%M:%S")
            w.writerow(row)
    print(f"Exported {len(trades)} trades -> {out_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
