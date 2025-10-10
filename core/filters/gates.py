from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, List
import os
from pathlib import Path
import pandas as pd
from datetime import datetime, timezone, date

def _today_dir() -> Path:
    return Path("logs/snapshots") / date.today().isoformat()

def _latest_snapshot_parquet() -> Path | None:
    d = _today_dir()
    if not d.exists():
        return None
    files = sorted([p for p in d.glob("*.parquet")], key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None

def _load_snapshot_df() -> pd.DataFrame | None:
    p = _latest_snapshot_parquet()
    if not p or not p.exists():
        return None
    try:
        return pd.read_parquet(p)
    except Exception:
        try:
            return pd.read_parquet(p, engine="pyarrow")
        except Exception:
            return None

@dataclass
class GateConfig:
    atr_window: int = int(os.getenv("GATE_ATR_WINDOW", "200"))
    atr_pctl_min: float = float(os.getenv("GATE_ATR_PCTL_MIN", "10"))
    atr_pctl_max: float = float(os.getenv("GATE_ATR_PCTL_MAX", "90"))
    utc_hours: str = os.getenv("GATE_UTC_HOURS", "0-24")               # "6-22"
    weekdays: str = os.getenv("GATE_ALLOW_WEEKDAYS", "1,2,3,4,5")      # 1..7
    htf_ema_window: int = int(os.getenv("GATE_HTF_EMA_WINDOW", "60"))

def _parse_hours(hs: str) -> tuple[int, int]:
    try:
        a, b = hs.split("-")
        return int(a), int(b)
    except Exception:
        return (0, 24)

def _weekday_ok(cfg: GateConfig, now_utc: datetime) -> bool:
    try:
        allowed = {int(x.strip()) for x in cfg.weekdays.split(",") if x.strip()}
    except Exception:
        allowed = {1,2,3,4,5}
    wd = ((now_utc.weekday() + 1 - 1) % 7) + 1  # Python Mon=0 -> 1..7
    return wd in allowed

def session_gate(now_utc: datetime, cfg: GateConfig) -> tuple[bool, str]:
    lo, hi = _parse_hours(cfg.utc_hours); hr = now_utc.hour
    ok = (lo <= hr < hi)
    return ok, f"session({hr} in {lo}-{hi})"

def atr_percentile_gate(df: pd.DataFrame, cfg: GateConfig) -> tuple[bool, str]:
    if df is None or "atr" not in df.columns or len(df) < 10:
        return True, "atr:skip"
    window = min(cfg.atr_window, len(df))
    series = df["atr"].tail(window).dropna()
    if series.empty:
        return True, "atr:skip"
    val = float(series.iloc[-1])
    p_low = float(series.quantile(cfg.atr_pctl_min/100.0))
    p_high = float(series.quantile(cfg.atr_pctl_max/100.0))
    ok = (p_low <= val <= p_high)
    return ok, f"atr:{val:.4f} in [{p_low:.4f},{p_high:.4f}]"

def htf_trend_gate(df: pd.DataFrame, side: str, cfg: GateConfig) -> tuple[bool, str]:
    if df is None or "close" not in df.columns or len(df) < cfg.htf_ema_window:
        return True, "htf:skip"
    w = cfg.htf_ema_window
    ema = df["close"].ewm(span=w, adjust=False).mean()
    last = float(df["close"].iloc[-1])
    last_ema = float(ema.iloc[-1])
    if side.upper() == "LONG":
        ok = last >= last_ema
    else:
        ok = last <= last_ema
    return ok, f"htf:{last:.2f} vs ema{w}:{last_ema:.2f}"

def evaluate_gates(side: str, now_utc: datetime | None = None, cfg: GateConfig | None = None) -> tuple[bool, List[str]]:
    now_utc = now_utc or datetime.now(timezone.utc)
    cfg = cfg or GateConfig()
    if not _weekday_ok(cfg, now_utc):
        return False, ["weekday:block"]
    ok_sess, msg_sess = session_gate(now_utc, cfg)
    df = _load_snapshot_df()
    ok_atr, msg_atr = atr_percentile_gate(df, cfg)
    ok_tr, msg_tr = htf_trend_gate(df, side, cfg)
    oks = [ok_sess, ok_atr, ok_tr]
    msgs = [msg_sess, msg_atr, msg_tr]
    return all(oks), msgs
