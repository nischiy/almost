#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T0 Baseline metrics generator.
Scans your project's logs over the last 14 days and produces:
- logs/snapshots/T0_baseline.json
- reports/T0_metrics.md

It tries multiple plausible trade log locations and schemas to avoid coupling
to any single file format. If nothing usable is found, it fails with a clear message.
"""
import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any
import csv
import math
from datetime import datetime, timedelta
from collections import defaultdict

DATE_FMT = "%Y-%m-%d"
TS_FMTS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%fZ",
    "%Y-%m-%dT%H:%M:%S%z",
]

def parse_ts(v: str) -> Optional[datetime]:
    v = (v or "").strip()
    if not v:
        return None
    try:
        iv = int(float(v))
        if iv > 10_000_000_000:
            return datetime.utcfromtimestamp(iv / 1000.0)
        else:
            return datetime.utcfromtimestamp(iv)
    except Exception:
        pass
    for f in TS_FMTS:
        try:
            dt = datetime.strptime(v, f)
            if dt.tzinfo is not None:
                return dt.astimezone(tz=None).replace(tzinfo=None)
            return dt
        except Exception:
            continue
    return None

@dataclass
class Trade:
    open_time: datetime
    close_time: datetime
    side: str
    qty: float
    entry_price: float
    exit_price: float
    pnl: float
    fees: float = 0.0
    r: Optional[float] = None
    slippage: Optional[float] = None
    symbol: Optional[str] = None

def find_candidate_csvs(project_root: Path) -> List[Path]:
    patterns = [
        "logs/trades/*.csv",
        "logs/trades.csv",
        "logs/decisions/*trades*.csv",
        "logs/decisions/*.csv",
        "logs/orders/fills*.csv",
        "logs/**/*.csv",
    ]
    out: List[Path] = []
    for pat in patterns:
        out.extend(project_root.glob(pat))
    seen = set()
    uniq: List[Path] = []
    for p in out:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    return uniq

def float_or_none(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        s = str(x).strip()
        if s == "" or s.lower() == "nan":
            return None
        return float(s)
    except Exception:
        return None

def detect_and_parse_trades(csv_path: Path) -> List[Trade]:
    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cols = {c.strip().lower(): c for c in (reader.fieldnames or [])}

        def has(*need):
            return all(n in cols for n in need)

        trades: List[Trade] = []

        if has("entry_time", "exit_time", "entry_price", "exit_price", "qty", "side", "pnl"):
            for row in reader:
                try:
                    ot = parse_ts(row[cols["entry_time"]])
                    ct = parse_ts(row[cols["exit_time"]])
                    if not ot or not ct:
                        continue
                    trade = Trade(
                        open_time=ot,
                        close_time=ct,
                        side=str(row[cols["side"]]).upper(),
                        qty=float_or_none(row[cols["qty"]]) or 0.0,
                        entry_price=float_or_none(row[cols["entry_price"]]) or 0.0,
                        exit_price=float_or_none(row[cols["exit_price"]]) or 0.0,
                        pnl=float_or_none(row[cols["pnl"]]) or 0.0,
                        fees=float_or_none(row.get(cols.get("fees",""), None)) or 0.0,
                        r=float_or_none(row.get(cols.get("r",""), None)),
                        slippage=float_or_none(row.get(cols.get("slippage",""), None)),
                        symbol=row.get(cols.get("symbol",""), None) or None,
                    )
                    trades.append(trade)
                except Exception:
                    continue
            return trades
        return []

def filter_14_days(trades: List[Trade], now: datetime) -> List[Trade]:
    since = now - timedelta(days=14)
    return [t for t in trades if since <= t.close_time <= now]

def compute_metrics(trades: List[Trade]) -> Dict[str, Any]:
    if not trades:
        raise ValueError("No trades to compute metrics. Provide a per-trade CSV with the required columns.")

    wins = [t for t in trades if t.pnl > 0]
    losses = [t for t in trades if t.pnl < 0]
    sum_wins = sum(t.pnl for t in wins)
    sum_losses_abs = abs(sum(t.pnl for t in losses))
    total_pnl = sum(t.pnl for t in trades)

    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for t in sorted(trades, key=lambda x: x.close_time):
        equity += t.pnl
        peak = max(peak, equity)
        dd = peak - equity
        max_dd = max(max_dd, dd)

    pf = (sum_wins / sum_losses_abs) if sum_losses_abs > 0 else float("inf")
    win_rate = (len(wins) / len(trades)) * 100.0

    r_values = [t.r for t in trades if t.r is not None]
    avg_r = sum(r_values)/len(r_values) if r_values else None

    slips = [t.slippage for t in trades if t.slippage is not None]
    avg_slip = sum(slips)/len(slips) if slips else None

    by_day = defaultdict(int)
    for t in trades:
        day = t.close_time.strftime(DATE_FMT)
        by_day[day] += 1
    if trades:
        first_day = min(t.close_time for t in trades).date()
        last_day = max(t.close_time for t in trades).date()
        total_days = (last_day - first_day).days + 1
        days_with = len([d for d, n in by_day.items() if n > 0])
        days_without_pct = max(0.0, (total_days - days_with) / total_days * 100.0)
    else:
        days_without_pct = None

    mar = (total_pnl / max_dd) if max_dd > 0 else float("inf")

    return {
        "trades_count": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": round(win_rate, 2),
        "profit_factor": (None if math.isinf(pf) else round(pf, 4)),
        "net_pnl": round(total_pnl, 2),
        "max_drawdown": round(max_dd, 2),
        "mar_ratio": (None if math.isinf(mar) else round(mar, 4)),
        "avg_r": (None if avg_r is None else round(avg_r, 4)),
        "avg_slippage": (None if avg_slip is None else round(avg_slip, 6)),
        "days_without_trades_pct": (None if days_without_pct is None else round(days_without_pct, 2)),
    }

def write_outputs(project_root: Path, metrics: Dict[str, Any], source_file: Path) -> None:
    snap_dir = project_root / "logs" / "snapshots"
    rep_dir = project_root / "reports"
    snap_dir.mkdir(parents=True, exist_ok=True)
    rep_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_file": str(source_file),
        "window_days": 14,
        "metrics": metrics,
    }
    (snap_dir / "T0_baseline.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    m = metrics
    lines = [
        "# T0 Baseline Metrics (last 14 days)",
        "",
        f"- Generated (UTC): {payload['generated_at']}",
        f"- Source file: `{Path(source_file).name}`",
        "- Window: 14 days",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Trades | {m.get('trades_count')} |",
        f"| Wins | {m.get('wins')} |",
        f"| Losses | {m.get('losses')} |",
        f"| Win rate | {m.get('win_rate_pct')} % |",
        f"| Profit Factor | {m.get('profit_factor')} |",
        f"| Net PnL | {m.get('net_pnl')} |",
        f"| Max Drawdown | {m.get('max_drawdown')} |",
        f"| MAR ratio | {m.get('mar_ratio')} |",
        f"| Average R | {m.get('avg_r')} |",
        f"| Average slippage | {m.get('avg_slippage')} |",
        f"| % days without trades | {m.get('days_without_trades_pct')} % |",
        "",
        "## Notes & Assumptions",
        "- Metrics are computed from **closed trades** within the last 14 days.",
        "- **Profit Factor** = Sum(positive PnL) / Abs(Sum(negative PnL)).",
        "- **MAR (short-window)** = NetPnL / MaxDrawdown (not annualized).",
        "- **Average R** is reported only if an `R` column exists in the trade CSV.",
        "- **Average slippage** reported only if `slippage` column exists.",
    ]
    (rep_dir / "T0_metrics.md").write_text("\n".join(lines), encoding="utf-8")

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", type=str, default=".")
    args = ap.parse_args()

    project_root = Path(args.project_root).resolve()
    candidates = find_candidate_csvs(project_root)
    if not candidates:
        print("ERROR: No CSV candidates found under logs/. Please provide a per-trade CSV.", file=sys.stderr)
        sys.exit(2)

    parsed: List[Trade] = []
    used_file: Optional[Path] = None
    for csv_path in candidates:
        try:
            trades = detect_and_parse_trades(csv_path)
            if trades:
                parsed = trades
                used_file = csv_path
                break
        except Exception:
            continue

    if not parsed or not used_file:
        print("ERROR: Could not find a per-trade CSV with columns: entry_time, exit_time, entry_price, exit_price, qty, side, pnl.", file=sys.stderr)
        sys.exit(3)

    now = datetime.utcnow()
    windowed = filter_14_days(parsed, now)
    if not windowed:
        print("ERROR: No trades closed in the last 14 days in the parsed CSV.", file=sys.stderr)
        sys.exit(4)

    metrics = compute_metrics(windowed)
    write_outputs(project_root, metrics, used_file)

    print("=== T0 Baseline complete ===")
    for k, v in metrics.items():
        print(f"{k}: {v}")

if __name__ == "__main__":
    main()
