# -*- coding: utf-8 -*-
from __future__ import annotations
"""
ExitManager: reconcile SL/TP для відкритої позиції.

Роль:
  - Зчитати активні openOrders.
  - Виділити чинні вихідні ордери (SL/TP) з closePosition=true, reduceOnly=true.
  - Порівняти з цільовими рівнями (з core/стратегії) і вирішити:
      * нічого не робити;
      * скасувати старі та поставити нові;
      * (опційно) використати cancelReplace (поки шлях "cancel+create" — простіше і надійніше).
  - Врахувати анти-дергання: гістерезис (не “розширювати” стоп) + пороги delta_abs/delta_pct + cooldown.

Залежності (локальні):
  - app.services.notifications: get_open_orders, cancel_order_via_rest, place_order_via_rest
  - app.services.exit_adapter: preview_exits (для побудови тіл нових SL/TP)
"""

import time
import logging
from typing import Dict, Any, Optional, List, Tuple

from app.services import notifications as net
from app.services.exit_adapter import preview_exits  # будуємо специ для нових SL/TP

log = logging.getLogger("ExitManager")


def _opposite(side_entry: str) -> str:
    s = (side_entry or "").strip().upper()
    if s == "BUY":
        return "SELL"
    if s == "SELL":
        return "BUY"
    return "SELL"


def _is_exit_order(o: Dict[str, Any], exit_side: str) -> bool:
    """
    Binance Futures openOrders поля (узагальнено):
      - type: STOP_MARKET | TAKE_PROFIT_MARKET | ...
      - side: BUY/SELL
      - closePosition: "true"/"false" (може бути bool у деяких респах)
      - reduceOnly: "true"/"false"
      - stopPrice: "12345.0"
    """
    t = str(o.get("type", "")).upper()
    if t not in ("STOP_MARKET", "TAKE_PROFIT_MARKET"):
        return False
    if str(o.get("side", "")).upper() != exit_side:
        return False

    def _as_bool(v: Any) -> bool:
        if isinstance(v, bool):
            return v
        return str(v).strip().lower() in ("1", "true", "yes", "y", "on")

    if not _as_bool(o.get("closePosition")):
        return False
    if not _as_bool(o.get("reduceOnly")):
        return False
    return True


def _pick_current_exits(open_orders: List[Dict[str, Any]], exit_side: str) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Повертає (sl, tp) — перший знайдений кожного типу."""
    sl = tp = None
    for o in open_orders:
        if not _is_exit_order(o, exit_side):
            continue
        tt = str(o.get("type", "")).upper()
        if tt == "STOP_MARKET" and sl is None:
            sl = o
        elif tt == "TAKE_PROFIT_MARKET" and tp is None:
            tp = o
        if sl and tp:
            break
    return sl, tp


def _need_update(kind: str, side_entry: str, old_price: Optional[float], new_price: Optional[float],
                 *, delta_abs: float, delta_pct: float, hysteresis: bool) -> bool:
    """
    Вирішує, чи оновлювати конкретний вихід:
      - hysteresis: для LONG — SL тільки вгору (тільки tighten), TP тільки вгору;
                    для SHORT — SL тільки вниз, TP тільки вниз (аналогічно tighten).
      - пороги: abs(new-old) >= max(delta_abs, delta_pct * ref), де ref = max(|old|, |new|).
    """
    if new_price is None:
        return False
    if old_price is None:
        return True

    # пороги
    ref = max(abs(old_price), abs(new_price), 1e-9)
    need_by_delta = abs(new_price - old_price) >= max(delta_abs, delta_pct * ref)
    if not need_by_delta:
        return False

    if not hysteresis:
        return True

    side = (side_entry or "").strip().upper()
    k = (kind or "").upper()  # "SL" | "TP"

    if side == "BUY":
        if k == "SL":
            # tighten лише вгору
            return new_price > old_price
        if k == "TP":
            return new_price > old_price
    elif side == "SELL":
        if k == "SL":
            # tighten лише вниз
            return new_price < old_price
        if k == "TP":
            return new_price < old_price

    # fallback (неповинно сюди доходити)
    return True


class ExitManager:
    """
    Менеджер стану вихідних ордерів. Тримає cooldown у пам'яті.
    """
    def __init__(self, *, cooldown_sec: float = 60.0,
                 delta_abs: float = 0.0, delta_pct: float = 0.001,
                 hysteresis: bool = True):
        self.cooldown_sec = float(cooldown_sec)
        self.delta_abs = float(delta_abs)
        self.delta_pct = float(delta_pct)
        self.hysteresis = bool(hysteresis)
        self._last_update_ts: Dict[str, float] = {}

    def _cooldown_ok(self, symbol: str, now_ts: float) -> bool:
        last = self._last_update_ts.get(symbol)
        if last is None:
            return True
        return (now_ts - last) >= self.cooldown_sec

    def reconcile(self, *, symbol: str, side_entry: str,
                  sl_target: Optional[float], tp_target: Optional[float]) -> Dict[str, Any]:
        """
        Головний метод. Повертає детальний план і результати:
          {
            "cooldown_skipped": bool,
            "current": {"sl": {...}|None, "tp": {...}|None},
            "target": {"sl": <float|None>, "tp": <float|None>},
            "plan": {
               "cancel_ids": [ ... ],
               "create": [ {"type": "...", "stopPrice": ...}, ... ],
            },
            "results": [ {"action":"cancel"|"create","request":..., "response":...}, ... ]
          }
        """
        now_ts = time.time()
        exit_side = _opposite(side_entry)

        out: Dict[str, Any] = {
            "cooldown_skipped": False,
            "current": {"sl": None, "tp": None},
            "target": {"sl": sl_target, "tp": tp_target},
            "plan": {"cancel_ids": [], "create": []},
            "results": [],
        }

        # 0) cooldown
        if not self._cooldown_ok(symbol, now_ts):
            out["cooldown_skipped"] = True
            return out

        # 1) зчитати openOrders
        oo = net.get_open_orders(symbol)
        orders = oo if isinstance(oo, list) else oo.get("orders") or oo.get("data") or []
        sl_cur, tp_cur = _pick_current_exits(orders, exit_side)
        out["current"]["sl"] = sl_cur
        out["current"]["tp"] = tp_cur

        def _get_stop(o: Optional[Dict[str, Any]]) -> Optional[float]:
            if not o:
                return None
            try:
                return float(o.get("stopPrice"))
            except Exception:
                return None

        sl_old = _get_stop(sl_cur)
        tp_old = _get_stop(tp_cur)

        # 2) вирішити, що робити з SL
        if sl_target is None:
            # цілі SL немає — скасувати, якщо є
            if sl_cur and sl_cur.get("orderId") is not None:
                out["plan"]["cancel_ids"].append({"orderId": sl_cur["orderId"]})
        else:
            if sl_cur is None or _need_update("SL", side_entry, sl_old, sl_target,
                                              delta_abs=self.delta_abs, delta_pct=self.delta_pct,
                                              hysteresis=self.hysteresis):
                # створити/оновити
                out["plan"]["cancel_ids"].extend(
                    [{"orderId": sl_cur["orderId"]}] if sl_cur and sl_cur.get("orderId") is not None else []
                )
                out["plan"]["create"].append({"type": "STOP_MARKET", "stopPrice": float(sl_target)})

        # 3) вирішити, що робити з TP
        if tp_target is None:
            if tp_cur and tp_cur.get("orderId") is not None:
                out["plan"]["cancel_ids"].append({"orderId": tp_cur["orderId"]})
        else:
            if tp_cur is None or _need_update("TP", side_entry, tp_old, tp_target,
                                              delta_abs=self.delta_abs, delta_pct=self.delta_pct,
                                              hysteresis=self.hysteresis):
                out["plan"]["cancel_ids"].extend(
                    [{"orderId": tp_cur["orderId"]}] if tp_cur and tp_cur.get("orderId") is not None else []
                )
                out["plan"]["create"].append({"type": "TAKE_PROFIT_MARKET", "stopPrice": float(tp_target)})

        # 4) виконати план через notifications
        #    4.1) cancel
        for cid in out["plan"]["cancel_ids"]:
            try:
                resp = net.cancel_order_via_rest(symbol=symbol, orderId=cid.get("orderId"))
                out["results"].append({"action": "cancel", "request": cid, "response": resp})
            except Exception as e:
                out["results"].append({"action": "cancel", "request": cid, "error": str(e)})

        #    4.2) create (через exit_adapter preview + notifications.place)
        if out["plan"]["create"]:
            # preview сформує тіло (side/flags), ми лише відправимо
            # NB: preview_exits приймає обидва рівні; побудуємо пачкою.
            sl_val = None
            tp_val = None
            for spec in out["plan"]["create"]:
                if spec["type"] == "STOP_MARKET":
                    sl_val = spec["stopPrice"]
                elif spec["type"] == "TAKE_PROFIT_MARKET":
                    tp_val = spec["stopPrice"]
            preview = preview_exits(symbol, side_entry, sl_val, tp_val)
            for spec in preview.get("orders", []):
                try:
                    resp = net.place_order_via_rest(**spec)
                    out["results"].append({"action": "create", "request": spec, "response": resp})
                except Exception as e:
                    out["results"].append({"action": "create", "request": spec, "error": str(e)})

        # 5) оновити cooldown-мітку, якщо щось міняли
        if out["plan"]["cancel_ids"] or out["plan"]["create"]:
            self._last_update_ts[symbol] = now_ts

        return out
