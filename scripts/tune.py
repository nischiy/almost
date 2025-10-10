# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, json, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--symbol', default='BTCUSDT')
    ap.add_argument('--interval', default='1m')
    ap.add_argument('--days', type=int, default=14)
    ap.add_argument('--n_iter', type=int, default=100)
    ap.add_argument('--fee_bps', type=float, default=4.0)
    ap.add_argument('--slip_bps', type=float, default=1.0)
    ap.add_argument('--w_trades', type=float, default=0.05)
    args = ap.parse_args()
    # This is a safe stub to avoid failures when called by PowerShell wrappers.
    # It intentionally does not run heavy tuning. Replace later with your Optuna-based tuner.
    print(json.dumps({
        "ok": True,
        "note": "tune.py stub executed successfully; replace with real tuner when ready.",
        "params": vars(args)
    }, ensure_ascii=False))
    return 0

if __name__ == '__main__':
    sys.exit(main())
