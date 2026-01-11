# utils/order_adapter.py
"""
Order Adapter (additive, non-breaking).
- Uses core.positions.position_sizer + core.risk_guard to prepare an order payload.
- Default: DRY_RUN_ONLY=1 (no sending). You can integrate by importing build_order().

Public API:
    build_order(symbol: str, side: str, otype: str, wallet_usdt: float, **kwargs) -> dict

kwargs (існуючі залишено) + нові для ATR-Budget:
    desired_pos_usdt: float|None
    risk_margin_fraction: float (default 0.2)
    preferred_max_leverage: int (default 10)
    price: float|None           (required for LIMIT)
    reduce_only: bool = False
    client_order_id: str|None   (auto-generated if None)

    # --- Risk/evaluate inputs (опціонально) ---
    rg_state:  dict = {
        "trades_today": int,
        "loss_streak": int,
        "pnl_today_usdt": float,
        "equity_usd": float,
        "start_equity_usd": float,
        "open_risk_usd": float,
        "consec_losses": int
    }

    # --- NEW: ATR-Risk Budget sizing (опційно) ---
    ps_mode: str = "atr_budget" | None
    atr: float
    tick_value: float
    risk_budget_day_remaining: float
    dd_pct_day: float = 0.0

    # Параметри k (усі опційні; інакше беруться з ENV з дефолтами)
    k_base: float
    k_min:  float
    k_max:  float
    k_slope: float
    recovery_dd_pct: float
"""

from __future__ import annotations
import os, time, math, json, ssl, urllib.request
from dataclasses import asdict
from importlib.machinery import SourceFileLoader
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from types import SimpleNamespace
import importlib.util

from core.config.env import get_env
from core.execution import binance_futures
# robust local imports (fallback loader)
_APP_DIR = Path(__file__).resolve().parent
_ROOT = _APP_DIR.parent
def _load(name: str, path: Path):
    return SourceFileLoader(name, str(path)).load_module()

# --- position sizer (як було) ---
if importlib.util.find_spec("core.positions.position_sizer"):
    from core.positions.position_sizer import SizerConfig, compute_qty_leverage
else:
    mod = _load("position_sizer", _ROOT/"utils"/"position_sizer.py")
    SizerConfig = getattr(mod, "SizerConfig")
    compute_qty_leverage = getattr(mod, "compute_qty_leverage")

# --- risk evaluate (стабільний API) ---
if importlib.util.find_spec("core.risk_guard"):
    from core.risk_guard import evaluate
else:
    mod = _load("risk_guard_core", _ROOT.parent/"core"/"risk_guard.py")
    evaluate = getattr(mod, "evaluate")

def _mk_id(prefix: str = "dryrun") -> str:
    return f"{prefix}-{int(time.time()*1000)}"

# ---------- helpers for ATR-Budget mode ----------
def _fenv(name: str, default: float) -> float:
    try:
        v = os.getenv(name, default)
        s = str(v).strip().strip('"').strip("'").replace("_","").replace(",","")
        if s.endswith("%"):
            s = s[:-1]
        return float(s)
    except Exception:
        return float(default)

def _env_optional_float(name: str) -> float | None:
    v = os.getenv(name)
    if v is None:
        return None
    s = str(v).strip().strip('"').strip("'").replace("_", "").replace(",", "")
    if not s:
        return None
    if s.endswith("%"):
        s = s[:-1]
    try:
        return float(s)
    except Exception:
        return None

def _env_optional_int(name: str) -> int | None:
    v = _env_optional_float(name)
    if v is None:
        return None
    try:
        return int(v)
    except Exception:
        return None

def _clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def _round_down_to_step(x: float, step: float) -> float:
    if step <= 0:
        return x
    n = int(x / step + 1e-12)
    return round(n * step, 12)

def _round_up_to_step(x: float, step: float) -> float:
    if step <= 0:
        return x
    n = int((x + step - 1e-12) / step)
    return round(n * step, 12)

_HTTP_CTX = ssl.create_default_context()
_PRICE_CACHE: Dict[str, Dict[str, Any]] = {}
_FILTERS_CACHE: Dict[str, Dict[str, Any]] = {}
_PRICE_TTL_SEC = 10.0
_FILTERS_TTL_SEC = 600.0

def _running_under_pytest() -> bool:
    return "PYTEST_CURRENT_TEST" in os.environ

def _allow_offline_fallback() -> bool:
    env = str(get_env("ENV", "production") or "production").lower()
    if env != "production":
        return True
    return _running_under_pytest()

def _env_float(name: str, default: float) -> float:
    try:
        v = os.getenv(name)
        if v is None:
            return default
        return float(str(v).strip())
    except Exception:
        return default

def _offline_price(symbol: str) -> float:
    sym = symbol.upper()
    return _env_float(f"OFFLINE_PRICE_{sym}", _env_float("OFFLINE_PRICE", 100.0))

def _offline_filters(symbol: str) -> Dict[str, dict]:
    sym = symbol.upper()
    defaults = {
        "BTCUSDT": {"min_qty": 1.5, "step": 0.1, "min_notional": 100.0},
    }
    base = defaults.get(sym, {"min_qty": 0.001, "step": 0.001, "min_notional": 0.0})
    min_qty = _env_float(f"OFFLINE_MIN_QTY_{sym}", _env_float("OFFLINE_MIN_QTY", float(base["min_qty"])))
    step = _env_float(f"OFFLINE_STEP_SIZE_{sym}", _env_float("OFFLINE_STEP_SIZE", float(base["step"])))
    min_notional = _env_float(
        f"OFFLINE_MIN_NOTIONAL_{sym}",
        _env_float("OFFLINE_MIN_NOTIONAL", float(base["min_notional"])),
    )
    return {
        "LOT_SIZE": {"minQty": f"{min_qty}", "stepSize": f"{step}"},
        "MIN_NOTIONAL": {"notional": f"{min_notional}"},
    }

def _http_json(url: str, timeout: int = 10) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "order-adapter/1.1"})
    with urllib.request.urlopen(req, timeout=timeout, context=_HTTP_CTX) as r:
        return json.loads(r.read().decode("utf-8"))

def _fetch_public_price(symbol: str) -> Tuple[Optional[float], Optional[str]]:
    base = os.environ.get("BINANCE_FAPI_BASE", "https://fapi.binance.com")
    try:
        data = _http_json(f"{base}/fapi/v1/ticker/price?symbol={symbol}")
    except Exception as e:
        return None, f"price_fetch_error:{e}"
    try:
        return float(data.get("price")), None
    except Exception as e:
        return None, f"price_parse_error:{e}"

def _fetch_exchange_filters(symbol: str) -> Tuple[Optional[Dict[str, dict]], Optional[str]]:
    try:
        info = binance_futures.exchange_info(symbol)
    except Exception as e:
        return None, f"exchange_info_error:{e}"
    if not isinstance(info, dict):
        return None, "invalid_response"
    sym_info = next((s for s in info.get("symbols", []) if s.get("symbol") == symbol), None)
    if not sym_info:
        return None, "symbol_not_found"
    fmap = {
        f.get("filterType"): f
        for f in sym_info.get("filters", [])
        if f.get("filterType")
    }
    if "MIN_NOTIONAL" not in fmap and "NOTIONAL" in fmap:
        fmap["MIN_NOTIONAL"] = fmap["NOTIONAL"]
    return fmap, None

def _cached_snapshot(cache: Dict[str, Dict[str, Any]], symbol: str, ttl: float) -> Optional[Dict[str, Any]]:
    if _running_under_pytest():
        return None
    now = time.time()
    cached = cache.get(symbol)
    if not cached:
        return None
    if now - float(cached.get("ts") or 0.0) > ttl:
        return None
    snap = dict(cached)
    snap["source"] = "cache"
    snap["origin"] = cached.get("source")
    return snap

def _get_price_snapshot(symbol: str, *, allow_fallback: bool) -> Dict[str, Any]:
    cached = _cached_snapshot(_PRICE_CACHE, symbol, _PRICE_TTL_SEC)
    if cached:
        return cached
    now = time.time()
    if _running_under_pytest() and allow_fallback:
        snap = {"value": _offline_price(symbol), "source": "fallback", "reason": "pytest_offline", "ts": now}
        _PRICE_CACHE[symbol] = dict(snap)
        return snap
    price_val, price_reason = _fetch_public_price(symbol)
    source = "exchange" if price_val is not None else "missing"
    snap = {"value": price_val, "source": source, "reason": price_reason, "ts": now}
    if price_val is None and allow_fallback:
        snap = {
            "value": _offline_price(symbol),
            "source": "fallback",
            "reason": price_reason or "offline_fallback",
            "ts": now,
        }
    _PRICE_CACHE[symbol] = dict(snap)
    return snap

def _get_filters_snapshot(symbol: str, *, allow_fallback: bool) -> Dict[str, Any]:
    cached = _cached_snapshot(_FILTERS_CACHE, symbol, _FILTERS_TTL_SEC)
    if cached:
        return cached
    now = time.time()
    if _running_under_pytest() and allow_fallback:
        filters_map = _offline_filters(symbol)
        snap = {"value": filters_map, "source": "fallback", "reason": "pytest_offline", "ts": now}
        _FILTERS_CACHE[symbol] = dict(snap)
        return snap
    filters_map, filters_reason = _fetch_exchange_filters(symbol)
    source = "exchange" if filters_map is not None else "missing"
    snap = {"value": filters_map, "source": source, "reason": filters_reason, "ts": now}
    if filters_map is None and allow_fallback:
        snap = {
            "value": _offline_filters(symbol),
            "source": "fallback",
            "reason": filters_reason or "offline_fallback",
            "ts": now,
        }
    _FILTERS_CACHE[symbol] = dict(snap)
    return snap

def preflight_market_data(symbol: str) -> Dict[str, Any]:
    allow_fallback = _allow_offline_fallback()
    price_snap = _get_price_snapshot(symbol, allow_fallback=allow_fallback)
    filters_snap = _get_filters_snapshot(symbol, allow_fallback=allow_fallback)
    filters_map = filters_snap.get("value")
    step_size, min_qty, min_notional = _extract_filter_values(filters_map)
    filters_snap = {
        **filters_snap,
        "raw": filters_map,
        "step_size": step_size,
        "min_qty": min_qty,
        "min_notional": min_notional,
    }
    return {"price": price_snap, "filters": filters_snap}

def _extract_filter_values(filters: Dict[str, dict] | None) -> Tuple[float, float, float]:
    fmap = filters or {}
    lot = fmap.get("LOT_SIZE") or {}
    step_size = float(lot.get("stepSize", 0.0)) if lot else 0.0
    min_qty = float(lot.get("minQty", 0.0)) if lot else 0.0
    min_notional_raw = (fmap.get("MIN_NOTIONAL") or {}).get("notional")
    if min_notional_raw is None:
        min_notional_raw = (fmap.get("MIN_NOTIONAL") or {}).get("minNotional")
    min_notional = float(min_notional_raw or 0.0)
    return step_size, min_qty, min_notional

def _apply_atr_budget(
    sized,
    *,
    atr: float,
    tick_value: float,
    risk_budget_day_remaining: float,
    dd_pct_day: float | None,
    lot_step: float,
    min_qty: float,
    min_notional: float,
    price: float
) -> Tuple[float, Dict[str, Any]]:
    """
    qty_atr = min(RISK_MAX_POS_USD/price, (risk_budget_day_remaining * k_eff) / (ATR * tick_value))
    => Далі: виконуємо обидві групи обмежень:
       - біржові (min_qty, min_notional, lot_step)
       - наші (cap по RISK_MAX_POS_USD)
    ВАЖЛИВО: остаточно qty НЕ може перевищувати cap. Якщо cap < біржового мінімуму — ордер блокуємо (applied=False).
    """
    # Параметри з ENV (можна перевизначити через kwargs у build_order)
    k_base  = _fenv("PS_K_BASE", 1.0)
    k_min   = _fenv("PS_K_MIN",  0.25)
    k_max   = _fenv("PS_K_MAX",  1.0)
    k_slope = _fenv("PS_K_SLOPE", 0.04)
    rec_th  = _fenv("PS_RECOVERY_DD_PCT", 0.5)

    # Динаміка k
    dd = max(0.0, float(dd_pct_day or 0.0))
    if dd > rec_th:
        k_eff = k_base * (1.0 - k_slope * dd)
        k_eff = _clip(k_eff, k_min, k_base)
    else:
        k_eff = _clip(k_base, k_min, k_max)

    # Валідація входів
    if atr is None or atr <= 0 or tick_value is None or tick_value <= 0 or risk_budget_day_remaining is None or risk_budget_day_remaining <= 0 or price <= 0:
        return sized.qty, {
            "mode": "atr_budget",
            "applied": False,
            "reason": "bad_inputs",
            "atr": atr, "tick_value": tick_value,
            "risk_budget_day_remaining": risk_budget_day_remaining,
            "k_eff": k_eff
        }

    cap_usd = _env_optional_float("RISK_MAX_POS_USD")
    qty_cap_raw = None
    qty_cap = None
    if cap_usd is not None and cap_usd > 0:
        qty_cap_raw = cap_usd / price
        qty_cap = _round_down_to_step(max(qty_cap_raw, 0.0), lot_step)  # кришка у крок лота (FLOOR)

    qty_formula = (risk_budget_day_remaining * k_eff) / (atr * tick_value)
    qty_raw = min(qty_cap_raw, qty_formula) if qty_cap_raw is not None else qty_formula

    # Піднімаємо до біржових мінімумів
    qty_up_min = max(qty_raw, min_qty)
    if qty_up_min * price < min_notional:
        qty_up_min = max(qty_up_min, (min_notional / price))

    # Округлюємо вгору до кроку
    qty_up_min = _round_up_to_step(qty_up_min, lot_step)

    # Остаточне ОБМЕЖЕННЯ кришкою (FLOOR)
    qty_final = min(qty_up_min, qty_cap) if qty_cap is not None else qty_up_min

    # Якщо cap < біржового мінімуму — зробити валідний лот НЕМОЖЛИВО
    if qty_final <= 0:
        return sized.qty, {
            "mode": "atr_budget",
            "applied": False,
            "reason": "cap_below_exchange_min",
            "atr": atr, "tick_value": tick_value,
            "risk_budget_day_remaining": risk_budget_day_remaining,
            "k_eff": k_eff,
            "qty_formula": qty_formula,
            "qty_cap_raw": qty_cap_raw,
            "qty_cap_floor": qty_cap,
            "min_qty": min_qty,
            "min_notional": min_notional
        }
    if qty_cap is not None and (qty_cap <= 0 or qty_cap < _round_down_to_step(min_qty, lot_step)):
        return sized.qty, {
            "mode": "atr_budget",
            "applied": False,
            "reason": "cap_below_exchange_min",
            "atr": atr, "tick_value": tick_value,
            "risk_budget_day_remaining": risk_budget_day_remaining,
            "k_eff": k_eff,
            "qty_formula": qty_formula,
            "qty_cap_raw": qty_cap_raw,
            "qty_cap_floor": qty_cap,
            "min_qty": min_qty,
            "min_notional": min_notional
        }

    return float(qty_final), {
        "mode": "atr_budget",
        "applied": True,
        "atr": atr, "tick_value": tick_value,
        "risk_budget_day_remaining": risk_budget_day_remaining,
        "k_eff": k_eff,
        "qty_formula": qty_formula,
        "qty_cap_raw": qty_cap_raw,
        "qty_cap_floor": qty_cap,
        "qty_up_min": qty_up_min,
        "final_limited_by_cap": qty_final < qty_up_min if qty_cap is not None else False
    }

def build_order(symbol: str, side: str, otype: str, wallet_usdt: float, **kw) -> dict:
    raw_side = (side or "BUY").upper()
    if raw_side in ("BUY", "LONG"):
        side = "BUY"
    elif raw_side in ("SELL", "SHORT"):
        side = "SELL"
    else:
        side = raw_side
    otype = (otype or "MARKET").upper()
    errors = []
    blockers = []
    side_ok = side in ("BUY", "SELL")
    if not side_ok:
        msg = f"invalid side: {raw_side}"
        errors.append(msg)
        blockers.append(msg)

    # --- базовий сайзинг ---
    preferred_max_leverage = kw.get("preferred_max_leverage")
    if preferred_max_leverage is None:
        preferred_max_leverage = _env_optional_int("PREFERRED_MAX_LEVERAGE")
    if preferred_max_leverage is None:
        preferred_max_leverage = _env_optional_int("LEVERAGE")
    if preferred_max_leverage is None:
        preferred_max_leverage = 10

    risk_margin_fraction = kw.get("risk_margin_fraction")
    if risk_margin_fraction is None:
        risk_margin_fraction = _env_optional_float("RISK_MARGIN_FRACTION")
    if risk_margin_fraction is None:
        risk_margin_fraction = 0.2

    desired_pos_usdt = kw.get("desired_pos_usdt")
    if desired_pos_usdt is None:
        desired_pos_usdt = kw.get("size_usd")
    if desired_pos_usdt is None:
        desired_pos_usdt = kw.get("size")

    cfg = SizerConfig(
        risk_margin_fraction=float(risk_margin_fraction),
        preferred_max_leverage=int(preferred_max_leverage),
        desired_pos_usdt=(float(desired_pos_usdt) if desired_pos_usdt is not None else None),
    )

    st = kw.get("rg_state", {}) or {}
    equity_raw = st.get("equity_usd", kw.get("equity_usd"))
    equity_source = st.get("equity_source") or ("exchange" if equity_raw else "missing")
    equity_reason = st.get("equity_reason")
    equity_usd = float(equity_raw or 0.0)
    if equity_usd <= 0:
        if _allow_offline_fallback():
            equity_usd = float(wallet_usdt or 0.0)
            if equity_usd > 0 and equity_source == "missing":
                equity_source = "fallback"
                equity_reason = equity_reason or "fallback_wallet_usdt"
        else:
            blockers.append("stale_or_missing_exchange_data")

    sizing_wallet_usdt = equity_usd if equity_usd > 0 else (float(wallet_usdt or 0.0) if _allow_offline_fallback() else 0.0)

    market_snapshot = preflight_market_data(symbol)
    price_snap = market_snapshot.get("price") or {}
    filters_snap = market_snapshot.get("filters") or {}
    price_val = price_snap.get("value")
    price_source = price_snap.get("source") or "missing"
    price_reason = price_snap.get("reason")
    filters_map = filters_snap.get("raw")
    filters_source = filters_snap.get("source") or "missing"
    filters_reason = filters_snap.get("reason")
    filter_step_size = filters_snap.get("step_size") or 0.0
    filter_min_qty = filters_snap.get("min_qty") or 0.0
    filter_min_notional = filters_snap.get("min_notional") or 0.0
    if price_val is None or filters_map is None:
        blockers.append("stale_or_missing_exchange_data")

    if price_val is not None and filters_map is not None:
        sized = compute_qty_leverage(
            symbol,
            float(sizing_wallet_usdt),
            get_price=lambda _: float(price_val),
            get_filters=lambda _: filters_map or {},
            cfg=cfg,
        )
    else:
        sized = SimpleNamespace(
            qty=0.0,
            leverage=0,
            notional=0.0,
            margin_used=0.0,
            margin_cap=0.0,
            min_leverage_needed=0,
            price=float(price_val or 0.0),
            lot_step=float(filter_step_size or 0.0),
            min_qty=float(filter_min_qty or 0.0),
            min_notional=float(filter_min_notional or 0.0),
            meta={"notes": ["missing_exchange_data"]},
        )

    # --- evaluate ризиків через core.risk_guard ---
    equity_usd = float(equity_usd or 0.0)
    start_equity_raw = st.get("start_equity_usd", st.get("equity_usd"))
    start_equity_usd = float(start_equity_raw or 0.0)
    if start_equity_usd <= 0:
        start_equity_usd = equity_usd
    metrics = {
        "daily_pnl_usd": float(st.get("pnl_today_usdt", 0.0)),
        "equity_usd": float(equity_usd),
        "start_equity_usd": float(start_equity_usd),
        "open_risk_usd": float(st.get("open_risk_usd", 0.0)),
        "trades_today": int(st.get("trades_today", 0)),
        "consec_losses": int(st.get("consec_losses", st.get("loss_streak", 0))),
    }
    ev = evaluate(metrics)
    ok = bool(ev.get("ok"))
    reason = ev
    limits_repr = {"source": "ENV@core.risk_guard"}
    if not ok:
        violations = ev.get("violations") or []
        if violations:
            details = "; ".join(
                f"{v.get('limit')} value={v.get('value')} limit={v.get('limit_value')}"
                for v in violations
            )
            blockers.append(f"risk_gate: {details}")
        else:
            blockers.append("risk_gate: blocked")

    # --- NEW: ATR-Risk Budget sizing ---
    ps_mode = (kw.get("ps_mode") or "").lower().strip()
    atr = kw.get("atr")
    tick_value = kw.get("tick_value")
    risk_budget_day_remaining = kw.get("risk_budget_day_remaining")
    dd_pct_day = kw.get("dd_pct_day", 0.0)

    # allow override of k params via kwargs
    for name in ("k_base", "k_min", "k_max", "k_slope", "recovery_dd_pct"):
        if name in kw and kw[name] is not None:
            os.environ.setdefault({
                "k_base": "PS_K_BASE",
                "k_min": "PS_K_MIN",
                "k_max": "PS_K_MAX",
                "k_slope": "PS_K_SLOPE",
                "recovery_dd_pct": "PS_RECOVERY_DD_PCT",
            }[name], str(kw[name]))

    atr_budget_meta = None
    atr_blocked = False
    if ps_mode == "atr_budget":
        new_qty, meta = _apply_atr_budget(
            sized,
            atr=float(atr) if atr is not None else None,
            tick_value=float(tick_value) if tick_value is not None else None,
            risk_budget_day_remaining=float(risk_budget_day_remaining) if risk_budget_day_remaining is not None else None,
            dd_pct_day=float(dd_pct_day) if dd_pct_day is not None else 0.0,
            lot_step=float(getattr(sized, "lot_step", 0.0) or 0.0),
            min_qty=float(getattr(sized, "min_qty", 0.0) or 0.0),
            min_notional=float(getattr(sized, "min_notional", 0.0) or 0.0),
            price=float(getattr(sized, "price", 0.0) or 0.0),
        )
        atr_budget_meta = meta
        try:
            sized.qty = new_qty
            sized.notional = new_qty * float(getattr(sized, "price", 0.0) or 0.0)
        except Exception:
            pass
        if meta.get("applied") is False and meta.get("reason") == "cap_below_exchange_min":
            atr_blocked = True
            blockers.append("atr_budget: cap_below_exchange_min")

    # --- USD-based sizing from env/equity (deterministic) ---
    # Formula:
    #   risk_usd = equity_usd * (RISK_PER_TRADE_PCT / 100)
    #   target_usd = min(ORDER_QTY_USD, risk_usd, RISK_MAX_POS_USD) for available values
    # Qty rounding:
    #   qty_raw = target_usd / price
    #   qty_final = floor(qty_raw to lot_step) to satisfy Binance LOT_SIZE
    env_order_usd = _env_optional_float("ORDER_QTY_USD")
    risk_pct = _env_optional_float("RISK_PER_TRADE_PCT")
    max_pos_usd = _env_optional_float("RISK_MAX_POS_USD")
    sizing_inputs_present = any(
        v is not None for v in (cfg.desired_pos_usdt, env_order_usd, risk_pct, max_pos_usd)
    )

    base_order_usd = cfg.desired_pos_usdt if cfg.desired_pos_usdt is not None else env_order_usd
    if base_order_usd is None and sizing_inputs_present:
        base_order_usd = 0.0
    risk_usd = None
    if equity_usd > 0 and risk_pct is not None:
        risk_usd = equity_usd * (risk_pct / 100.0)

    target_candidates = [v for v in (base_order_usd, risk_usd, max_pos_usd) if v is not None and v > 0]
    target_usd = min(target_candidates) if target_candidates else None
    if target_usd is None and base_order_usd is not None:
        target_usd = float(base_order_usd)
    if not sizing_inputs_present:
        target_usd = None

    qty_raw = None
    qty_final = None
    sizing_blocked = False
    price_val = float(getattr(sized, "price", 0.0) or 0.0)
    lot_step = float(getattr(sized, "lot_step", 0.0) or 0.0)
    min_qty = float(getattr(sized, "min_qty", 0.0) or 0.0)
    min_notional = float(getattr(sized, "min_notional", 0.0) or 0.0)
    if sizing_inputs_present and ps_mode != "atr_budget" and target_usd is not None and target_usd > 0 and price_val > 0:
        qty_raw = target_usd / price_val
        qty_final = _round_down_to_step(qty_raw, lot_step) if lot_step > 0 else qty_raw
        if qty_final <= 0 or qty_final < min_qty:
            blockers.append(
                "invalid_sizing: qty_below_min_qty qty={qty} min_qty={min_qty}".format(
                    qty=qty_final,
                    min_qty=min_qty,
                )
            )
            sizing_blocked = True
        elif qty_final * price_val < min_notional:
            blockers.append(
                "invalid_sizing: notional_below_min_notional qty={qty} min_notional={min_notional}".format(
                    qty=qty_final,
                    min_notional=min_notional,
                )
            )
            sizing_blocked = True
        else:
            fee_frac = cfg.fee_bps / 10000.0
            buffer_frac = cfg.extra_buffer_pct
            notional = qty_final * price_val
            margin_cap = float(getattr(sized, "margin_cap", 0.0) or 0.0)
            denom = margin_cap / (1.0 + fee_frac + buffer_frac) if margin_cap > 0 else 0.0
            min_lev = int(max(1, math.ceil(notional / denom))) if denom > 0 else 999999
            lev = int(max(1, min(max(1, cfg.preferred_max_leverage), max(1, min_lev))))
            margin_used = notional / lev * (1.0 + fee_frac + buffer_frac)
            sized.qty = float(qty_final)
            sized.notional = float(notional)
            sized.leverage = int(lev)
            sized.min_leverage_needed = int(min_lev)
            sized.margin_used = float(margin_used)

    # --- валідація LIMIT ціни ---
    payload = None
    price = kw.get("price")
    if otype == "LIMIT" and price is None:
        msg = "PRICE is required for LIMIT orders"
        errors.append(msg)
        blockers.append(msg)

    # --- додатковий захист: не створюємо payload, якщо кількість невалідна або менша за біржові мінімуми ---
    qty_ok = (
        getattr(sized, "qty", 0.0) is not None
        and float(getattr(sized, "qty", 0.0)) > 0.0
        and float(getattr(sized, "qty", 0.0)) >= float(getattr(sized, "min_qty", 0.0) or 0.0)
        and float(getattr(sized, "qty", 0.0)) * float(getattr(sized, "price", 0.0) or 0.0) >= float(getattr(sized, "min_notional", 0.0) or 0.0)
    )
    if not qty_ok:
        blockers.append(
            "invalid_sizing: qty={qty} min_qty={min_qty} notional={notional} min_notional={min_notional}".format(
                qty=getattr(sized, "qty", None),
                min_qty=getattr(sized, "min_qty", None),
                notional=float(getattr(sized, "qty", 0.0) or 0.0) * float(getattr(sized, "price", 0.0) or 0.0),
                min_notional=getattr(sized, "min_notional", None),
            )
        )

    if ok and side_ok and qty_ok and not atr_blocked and not sizing_blocked and (otype != "LIMIT" or price is not None):
        payload = {
            "symbol": symbol,
            "side": side,
            "type": otype,
            "quantity": sized.qty,
            "leverage": sized.leverage,
            "timeInForce": "GTC",
            "reduceOnly": bool(kw.get("reduce_only", False)),
            "newClientOrderId": kw.get("client_order_id") or _mk_id("dryrun")
        }
        if otype == "LIMIT":
            payload["price"] = float(price)

    # --- збір відповіді ---
    sizer_block = {
        "qty": sized.qty, "leverage": sized.leverage, "min_leverage_needed": sized.min_leverage_needed,
        "notional": sized.notional, "margin_used": sized.margin_used, "margin_cap": sized.margin_cap,
        "price": sized.price, "lot_step": sized.lot_step, "step_size": sized.lot_step,
        "min_qty": sized.min_qty, "min_notional": sized.min_notional,
        "size_usd": target_usd, "qty_raw": qty_raw, "qty_final": qty_final
    }
    sizer_block["data_sources"] = {
        "equity": {"value": equity_usd, "source": equity_source, "reason": equity_reason},
        "price": {"value": price_val, "source": price_source, "reason": price_reason},
        "filters": {
            "source": filters_source,
            "reason": filters_reason,
            "step_size": filter_step_size,
            "min_qty": filter_min_qty,
            "min_notional": filter_min_notional,
        },
    }
    if atr_budget_meta is not None:
        sizer_block["atr_budget"] = atr_budget_meta

    return {
        "risk_gate": {"can_trade": ok, "reason": reason, "state": {}, "limits": limits_repr},
        "sizer": sizer_block,
        "order_payload": payload,
        "errors": errors,
        "blockers": blockers,
    }
