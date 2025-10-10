from __future__ import annotations
import os
import json
from datetime import datetime, timezone
from typing import Any

try:
    import pandas as pd  # type: ignore
except Exception:  # на випадок, якщо pd нема в середовищі тестів
    pd = None  # type: ignore

def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def _utc_now_parts():
    now = datetime.now(timezone.utc)
    d = now.strftime("%Y-%m-%d")
    hms = now.strftime("%H%M%S")
    return now, d, hms

def save_snapshot(*args: Any, **kwargs: Any) -> None:
    """
    Лайтова версія: шукає DataFrame у args/kwargs і зберігає його в logs/snapshots/<date>/snapshot_<time>.(csv|parquet)
    Якщо DataFrame не знайдений або pandas відсутній - тихо виходить (но-оп).
    """
    if pd is None:
        return
    df = None
    # спробуємо знайти DF серед аргументів
    for v in list(args) + list(kwargs.values()):
        if pd is not None and hasattr(v, "__class__") and v.__class__.__name__ in ("DataFrame", "Series"):
            df = v  # type: ignore
            break
    if df is None:
        return
    _, d, hms = _utc_now_parts()
    outdir = os.path.join("logs", "snapshots", d)
    _ensure_dir(outdir)
    base = os.path.join(outdir, f"snapshot_{hms}")
    try:
        df.to_csv(base + ".csv", index=False)
    except Exception:
        pass
    try:
        # parquet може бути недоступний без pyarrow - тоді тихо скіпаємо
        df.to_parquet(base + ".parquet", index=False)  # type: ignore
    except Exception:
        pass

def log_decision(*args: Any, **kwargs: Any) -> None:
    """
    Лайт-логер рішення: шукає dict (або об'єкт з .__dict__) і апендить JSON у logs/health/<date>/health_<time>.jsonl.
    Якщо нічого підходящого не знайдено - но-оп.
    """
    payload = None
    for v in list(args) + list(kwargs.values()):
        if isinstance(v, dict):
            payload = v
            break
        if hasattr(v, "__dict__"):
            try:
                payload = dict(v.__dict__)  # best-effort
                break
            except Exception:
                continue
    if payload is None:
        return
    _, d, hms = _utc_now_parts()
    outdir = os.path.join("logs", "health", d)
    _ensure_dir(outdir)
    path = os.path.join(outdir, f"health_{hms}.jsonl")
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass
