# tests/conftest.py
# -*- coding: utf-8 -*-
"""
Глобальні фікстури та стабілізатор середовища для pytest.

- Завжди тримає CWD у корені репозиторію (щоб бачити .env / .env.example).
- Додає корінь у sys.path (стабільні імпорти app/, core/, tools/).
- Надає фікстуру df_klines з детермінованими цінами для юніт/інтеграційних тестів.
"""

from __future__ import annotations
import os
import sys
from pathlib import Path
from typing import Iterator

import pytest
import pandas as pd
import numpy as np

# ---- Стабілізація CWD та sys.path для кожного тесту ----
_ROOT = Path(__file__).resolve().parents[1]

@pytest.fixture(autouse=True, scope="function")
def _force_root_cwd_and_syspath() -> Iterator[None]:
    """
    Гарантує, що кожен тест виконується з CWD = корінь репозиторію,
    а корінь присутній у sys.path для стабільних імпортів.
    """
    try:
        os.chdir(_ROOT)
    except Exception:
        pass

    root_str = str(_ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)

    yield

    # Повертаємо CWD у корінь і після тесту (на випадок, якщо його змінювали)
    try:
        os.chdir(_ROOT)
    except Exception:
        pass


# ---- Утиліта для генерації синтетичних klines ----
def _gen_klines(n: int = 200, start_price: float = 100.0, step: float = 0.2) -> pd.DataFrame:
    """
    Створює детермінований DataFrame з колонками:
    ['open_time','open','high','low','close','volume'].

    - close: трендова лінія з легкою синус-болтанкою.
    - high/low: open/close ± невеликий діапазон.
    - volume: позитивна, помірно варійована.
    """
    rng = np.random.default_rng(42)
    idx = np.arange(n, dtype=np.int64)

    # Базова траєкторія ціни
    base = start_price + step * idx
    wobble = 0.8 * np.sin(idx / 7.0) + 0.4 * np.cos(idx / 11.0)
    close = base + wobble

    # open як попереднє close (перший = close)
    open_ = np.roll(close, 1)
    open_[0] = close[0]

    # high/low з невеликим спредом
    spread = 0.15 + 0.05 * rng.random(n)
    high = np.maximum(open_, close) + spread
    low = np.minimum(open_, close) - spread

    # volume позитивний
    volume = 100 + 10 * rng.random(n)

    # open_time як псевдо-мітка часу (int мс)
    open_time = (1_700_000_000_000 + 60_000 * idx).astype(np.int64)

    df = pd.DataFrame({
        "open_time": open_time,
        "open": open_.astype(float),
        "high": high.astype(float),
        "low": low.astype(float),
        "close": close.astype(float),
        "volume": volume.astype(float),
    })

    return df


# ---- Публічна фікстура, якої очікують тести ----
@pytest.fixture(scope="function")
def df_klines() -> pd.DataFrame:
    """
    Синтетичні котирування для тестів (200 рядків, стовпці як у kline).
    Базова серія достатньо “жива” для індикаторів (EMA/RSI/ATR тощо).
    """
    return _gen_klines(n=200, start_price=100.0, step=0.2)
