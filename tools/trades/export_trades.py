#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Export per-trade CSV by reconstructing round trips from common log sources.

Search order (first successful):
  1) logs/orders/*.jsonl  (one JSON object per line with trade/fill info)
  2) logs/orders/fills*.csv
  3) logs/decisions/*.csv (ENTRY/EXIT best-effort)

Output: logs/trades/trades_exported.csv
Columns:
  entry_time, exit_time, entry_price, exit_price, qty, side, pnl, fees, r, slippage, symbol
"""
import argparse, csv, json, sys, math
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

def norm_key(k: str) -> str:
    return (k or "").strip().lower()

def to_float(x) -> Optional[float]:
    try:
        if x is None: return None
        s = str(x).strip()
        if s == "" or s.lower() == "nan": return None
        return float(s)
    except Exception:
        return None

def parse_ts(v) -> Optional[datetime]:
    if v is None: return None
    # epoch ms/s detection
    try:
        iv = int(float(v))
        if iv > 10_000_000_000:  # ms
            return datetime.fromtimestamp(iv/1000, tz=timezone.utc).replace(tzinfo=None)
        return datetime.fromtimestamp(iv, tz=timezone.utc).replace(tzinfo=None)
    except Exception:
        pass
    fmts = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%S%z",
    ]
    s = str(v).strip()
    for f in fmts:
        try:
            dt = datetime.strptime(s, f)
            if dt.tzinfo: dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
            return dt
        except Exception:
            continue
    return None

def find_files(project_root: Path) -> List[Path]:
    cands = []
    cands += list((project_root / "logs" / "orders").glob("*.jsonl"))
    cands += list((project_root / "logs" / "orders").glob("fills*.csv"))
    cands += list((project_root / "logs" / "decisions").glob("*.csv"))
    return cands

def load_jsonl_fills(p: Path) -> List[Dict[str, Any]]:
    res: List[Dict[str, Any]] = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if not line: continue
            try:
                obj = json.loads(line)
                res.append(obj)
            except Exception:
                continue
    return res

def load_csv_rows(p: Path) -> List[Dict[str, Any]]:
    with p.open("r", encoding="utf-8", newline="") as f:
        rdr = csv.DictReader(f)
        return [row for row in rdr]

def extract_fills_from_jsonl(objs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    fills = []
    for o in objs:
        # flatten typical keys
        d = {norm_key(k): v for k, v in o.items()}
        # Some logs nest data under 'data' or 'fill'
        if 'data' in d and isinstance(o['data'], dict):
            dd = {norm_key(k): v for k, v in o['data'].items()}
            d.update(dd)
        # Accept rows that look like fills/executions
        keys = d.keys()
        if not any(k in keys for k in ["price","p","ap","avgprice"]): 
            continue
        if not any(k in keys for k in ["qty","q","lastqty","executedqty"]):
            continue
        # normalize
        symbol = d.get("symbol") or d.get("s")
        side = (d.get("side") or d.get("sd") or "").upper()
        price = to_float(d.get("price") or d.get("p") or d.get("ap") or d.get("avgprice"))
        qty = to_float(d.get("qty") or d.get("q") or d.get("lastqty") or d.get("executedqty"))
        ts = parse_ts(d.get("transacttime") or d.get("t") or d.get("time") or d.get("event_time") or d.get("ts"))
        realized = to_float(d.get("realizedpnl") or d.get("rpnl") or d.get("realized_pnl"))
        fee = to_float(d.get("commission") or d.get("fee"))
        if symbol and side and price and qty and ts:
            fills.append({
                "timestamp": ts, "symbol": str(symbol), "side": side, "price": price, "qty": qty,
                "realized_pnl": realized, "fee": fee
            })
    fills.sort(key=lambda x: x["timestamp"])
    return fills

def extract_fills_from_csv(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    nk = [{norm_key(k): k for k in r.keys()} for r in rows]
    fills = []
    for row, cols in zip(rows, nk):
        symbol = row.get(cols.get("symbol","")) or row.get(cols.get("s",""))
        side = (row.get(cols.get("side","")) or row.get(cols.get("sd","")) or "").upper()
        price = to_float(row.get(cols.get("price","")) or row.get(cols.get("avgprice","")) or row.get(cols.get("p","")))
        qty = to_float(row.get(cols.get("qty","")) or row.get(cols.get("executedqty","")) or row.get(cols.get("q","")))
        ts = parse_ts(row.get(cols.get("time","")) or row.get(cols.get("transacttime","")) or row.get(cols.get("t","")))
        realized = to_float(row.get(cols.get("realizedpnl","")) or row.get(cols.get("rpnl","")))
        fee = to_float(row.get(cols.get("commission","")) or row.get(cols.get("fee","")))
        if symbol and side and price and qty and ts:
            fills.append({
                "timestamp": ts, "symbol": str(symbol), "side": side, "price": price, "qty": qty,
                "realized_pnl": realized, "fee": fee
            })
    fills.sort(key=lambda x: x["timestamp"])
    return fills

def reconstruct_trades_from_fills(fills: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Position-based round-trip detection per symbol.
    For USDT-M futures we assume contractSize=1; use realized_pnl if provided.
    """
    trades: List[Dict[str, Any]] = []
    by_symbol: Dict[str, List[Dict[str, Any]]] = {}
    for f in fills:
        by_symbol.setdefault(f["symbol"], []).append(f)

    for sym, fs in by_symbol.items():
        pos = 0.0
        avg_price = 0.0
        entry_time = None
        cum_fee = 0.0
        cum_realized = 0.0
        side_dir = None  # "LONG" or "SHORT"
        entry_qty_abs = 0.0

        def sign_for(side: str) -> int:
            return 1 if side.startswith("B") or side.startswith("LONG") else -1

        for f in fs:
            sgn = sign_for(f["side"])
            q = f["qty"] * sgn
            price = f["price"]
            t = f["timestamp"]
            fee = f.get("fee") or 0.0
            rpnl = f.get("realized_pnl")
            cum_fee += fee
            if pos == 0.0:
                # opening new position
                pos = q
                avg_price = price
                entry_time = t
                side_dir = "LONG" if pos > 0 else "SHORT"
                entry_qty_abs = abs(pos)
                cum_realized = 0.0
            else:
                # if adding to same direction: update VWAP
                if (pos > 0 and q > 0) or (pos < 0 and q < 0):
                    new_pos = pos + q
                    if new_pos == 0:
                        # fully closed by equal opposite? handle below
                        pass
                    # weighted average price update
                    avg_price = (abs(pos)*avg_price + abs(q)*price) / (abs(pos)+abs(q))
                    pos = new_pos
                    entry_qty_abs = max(entry_qty_abs, abs(pos))
                else:
                    # reducing or reversing
                    new_pos = pos + q
                    # realized pnl for reduced portion
                    close_qty = abs(q) if abs(q) <= abs(pos) else abs(pos)
                    # PnL approximation if not provided per fill: (exit - entry)*qty for LONG; reversed for SHORT
                    approx_pnl = (price - avg_price)*close_qty if pos > 0 else (avg_price - price)*close_qty
                    realized_here = rpnl if (rpnl is not None) else approx_pnl
                    cum_realized += realized_here
                    pos = new_pos
                    # if position crosses zero -> trade closed
                    if pos == 0.0:
                        trades.append({
                            "entry_time": entry_time,
                            "exit_time": t,
                            "entry_price": round(float(avg_price), 8),
                            "exit_price": round(float(price), 8),
                            "qty": round(float(entry_qty_abs), 8),
                            "side": side_dir,
                            "pnl": round(float(cum_realized), 8),
                            "fees": round(float(cum_fee), 8),
                            "r": "",  # unknown at this stage
                            "slippage": "",
                            "symbol": sym
                        })
                        # reset
                        avg_price = 0.0
                        entry_time = None
                        cum_fee = 0.0
                        cum_realized = 0.0
                        side_dir = None
                        entry_qty_abs = 0.0
                    else:
                        # still open, keep avg_price the same
                        pass
    # sort trades by exit time
    trades.sort(key=lambda x: x["exit_time"] or x["entry_time"])
    return trades

def best_effort_from_decisions(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Highly heuristic: look for columns that hint ENTRY/EXIT with symbol/price/side/timestamp
    if not rows: return []
    cols = {c.lower(): c for c in rows[0].keys()}
    def col(*names):
        for n in names:
            if n in cols: return cols[n]
        return None
    c_event = col("event","action","type","decision")
    c_time  = col("time","timestamp","ts","decided_at")
    c_price = col("price","entry_price","signal_price")
    c_side  = col("side","signal","direction")
    c_sym   = col("symbol","sym","ticker","instrument")

    if not (c_event and c_time and c_price and c_side and c_sym):
        return []

    # build open/close pairs per symbol
    open_pos: Dict[str, Dict[str, Any]] = {}
    trades: List[Dict[str, Any]] = []

    def is_entry(v:str)->bool:
        v=v.upper()
        return "ENTRY" in v or v.startswith("BUY") or "OPEN" in v
    def is_exit(v:str)->bool:
        v=v.upper()
        return "EXIT" in v or v.startswith("SELL") or "CLOSE" in v

    for row in rows:
        ev = str(row[c_event])
        ts = parse_ts(row[c_time])
        pr = to_float(row[c_price])
        sd = str(row[c_side]).upper()
        sy = str(row[c_sym]).upper()
        if not (ev and ts and pr and sd and sy): 
            continue
        if is_entry(ev):
            if sy not in open_pos:
                open_pos[sy] = {"time": ts, "price": pr, "side": "LONG" if sd.startswith("B") else "SHORT"}
        elif is_exit(ev):
            op = open_pos.pop(sy, None)
            if op:
                side = op["side"]
                pnl = (pr - op["price"]) if side=="LONG" else (op["price"] - pr)
                trades.append({
                    "entry_time": op["time"],
                    "exit_time": ts,
                    "entry_price": round(float(op["price"]),8),
                    "exit_price": round(float(pr),8),
                    "qty": "",
                    "side": side,
                    "pnl": round(float(pnl),8),
                    "fees": "",
                    "r": "",
                    "slippage": "",
                    "symbol": sy
                })
    trades.sort(key=lambda x: x["exit_time"] or x["entry_time"])
    return trades

def write_csv(out_path: Path, trades: List[Dict[str, Any]]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["entry_time","exit_time","entry_price","exit_price","qty","side","pnl","fees","r","slippage","symbol"]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for t in trades:
            row = {k: t.get(k,"") for k in fieldnames}
            # serialize datetimes
            for k in ["entry_time","exit_time"]:
                v = row[k]
                if isinstance(v, datetime):
                    row[k] = v.strftime("%Y-%m-%d %H:%M:%S")
            w.writerow(row)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", type=str, default=".")
    args = ap.parse_args()

    root = Path(args.project_root).resolve()
    cands = find_files(root)
    if not cands:
        print("ERROR: No candidate log files found under logs/orders or logs/decisions.", file=sys.stderr)
        sys.exit(2)

    trades: List[Dict[str, Any]] = []
    # Pass 1: JSONL fills
    jsonls = [p for p in cands if p.suffix.lower()==".jsonl" and p.parent.name=="orders"]
    for p in jsonls:
        objs = load_jsonl_fills(p)
        fills = extract_fills_from_jsonl(objs)
        if fills:
            trades = reconstruct_trades_from_fills(fills)
            if trades: break

    # Pass 2: fills CSV
    if not trades:
        csvs = [p for p in cands if p.suffix.lower()==".csv" and p.parent.name=="orders" and p.name.lower().startswith("fills")]
        for p in csvs:
            rows = load_csv_rows(p)
            fills = extract_fills_from_csv(rows)
            if fills:
                trades = reconstruct_trades_from_fills(fills)
                if trades: break

    # Pass 3: decisions CSV (best effort)
    if not trades:
        decs = [p for p in cands if p.suffix.lower()==".csv" and p.parent.name=="decisions"]
        for p in decs:
            rows = load_csv_rows(p)
            trades = best_effort_from_decisions(rows)
            if trades: break

    if not trades:
        print("ERROR: Could not reconstruct trades from available logs.", file=sys.stderr)
        sys.exit(3)

    out_path = root / "logs" / "trades" / "trades_exported.csv"
    write_csv(out_path, trades)
    print(f"Exported {len(trades)} trades -> {out_path}")

if __name__ == "__main__":
    main()
