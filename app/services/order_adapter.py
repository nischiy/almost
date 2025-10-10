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
import os, time
from dataclasses import asdict
from importlib.machinery import SourceFileLoader
from pathlib import Path
from typing import Dict, Any, Tuple

# robust local imports (fallback loader)
_APP_DIR = Path(__file__).resolve().parent
_ROOT = _APP_DIR.parent
def _load(name: str, path: Path):
    return SourceFileLoader(name, str(path)).load_module()

# --- position sizer (як було) ---
try:
    from core.positions.position_sizer import SizerConfig, compute_qty_leverage
except Exception:
    mod = _load("position_sizer", _ROOT/"utils"/"position_sizer.py")
    SizerConfig = getattr(mod, "SizerConfig")
    compute_qty_leverage = getattr(mod, "compute_qty_leverage")

# --- risk evaluate (стабільний API) ---
try:
    from core.risk_guard import evaluate
except Exception:
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

    cap_usd = _fenv("RISK_MAX_POS_USD", 100.0)
    qty_cap_raw = cap_usd / price
    qty_cap = _round_down_to_step(max(qty_cap_raw, 0.0), lot_step)  # кришка у крок лота (FLOOR)

    qty_formula = (risk_budget_day_remaining * k_eff) / (atr * tick_value)
    qty_raw = min(qty_cap_raw, qty_formula)

    # Піднімаємо до біржових мінімумів
    qty_up_min = max(qty_raw, min_qty)
    if qty_up_min * price < min_notional:
        qty_up_min = max(qty_up_min, (min_notional / price))

    # Округлюємо вгору до кроку
    qty_up_min = _round_up_to_step(qty_up_min, lot_step)

    # Остаточне ОБМЕЖЕННЯ кришкою (FLOOR)
    qty_final = min(qty_up_min, qty_cap)

    # Якщо cap < біржового мінімуму — зробити валідний лот НЕМОЖЛИВО
    if qty_cap <= 0 or qty_final <= 0 or qty_cap < _round_down_to_step(min_qty, lot_step):
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
        "final_limited_by_cap": qty_final < qty_up_min
    }

def build_order(symbol: str, side: str, otype: str, wallet_usdt: float, **kw) -> dict:
    side = (side or "BUY").upper()
    otype = (otype or "MARKET").upper()
    errors = []

    # --- базовий сайзинг ---
    cfg = SizerConfig(
        risk_margin_fraction=float(kw.get("risk_margin_fraction", 0.2)),
        preferred_max_leverage=int(kw.get("preferred_max_leverage", 10)),
        desired_pos_usdt=(float(kw["desired_pos_usdt"]) if "desired_pos_usdt" in kw and kw["desired_pos_usdt"] is not None else None)
    )
    sized = compute_qty_leverage(symbol, float(wallet_usdt), cfg=cfg)

    # --- evaluate ризиків через core.risk_guard ---
    st = kw.get("rg_state", {}) or {}
    metrics = {
        "daily_pnl_usd": float(st.get("pnl_today_usdt", 0.0)),
        "equity_usd": float(st.get("equity_usd", 0.0)),
        "start_equity_usd": float(st.get("start_equity_usd", st.get("equity_usd", 0.0))),
        "open_risk_usd": float(st.get("open_risk_usd", 0.0)),
        "trades_today": int(st.get("trades_today", 0)),
        "consec_losses": int(st.get("consec_losses", st.get("loss_streak", 0))),
    }
    ev = evaluate(metrics)
    ok = bool(ev.get("ok"))
    reason = ev
    limits_repr = {"source": "ENV@core.risk_guard"}

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

    # --- валідація LIMIT ціни ---
    payload = None
    price = kw.get("price")
    if otype == "LIMIT" and price is None:
        errors.append("PRICE is required for LIMIT orders")

    # --- додатковий захист: не створюємо payload, якщо кількість невалідна або менша за біржові мінімуми ---
    qty_ok = (
        getattr(sized, "qty", 0.0) is not None
        and float(getattr(sized, "qty", 0.0)) > 0.0
        and float(getattr(sized, "qty", 0.0)) >= float(getattr(sized, "min_qty", 0.0) or 0.0)
        and float(getattr(sized, "qty", 0.0)) * float(getattr(sized, "price", 0.0) or 0.0) >= float(getattr(sized, "min_notional", 0.0) or 0.0)
    )

    if ok and qty_ok and (otype != "LIMIT" or price is not None):
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
        "price": sized.price, "lot_step": sized.lot_step, "min_qty": sized.min_qty, "min_notional": sized.min_notional
    }
    if atr_budget_meta is not None:
        sizer_block["atr_budget"] = atr_budget_meta

    return {
        "risk_gate": {"can_trade": ok, "reason": reason, "state": {}, "limits": limits_repr},
        "sizer": sizer_block,
        "order_payload": payload,
        "errors": errors,
    }
