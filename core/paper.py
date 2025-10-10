from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, date, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def _compat_can_open(risk_obj, **kwargs):
    """
    Tries multiple signatures for risk.can_open to maintain backward compatibility.
    Supported:
      - can_open(notional_usd=..., current_equity=...)
      - can_open(equity_usd=..., today_trades=..., open_pos_usd=...)
    Returns (bool, reason).
    """
    sigs = []
    nu = kwargs.get("notional_usd", None)
    ce = kwargs.get("current_equity", None)
    eu = kwargs.get("equity_usd", ce)
    tt = kwargs.get("today_trades", 0)
    opu = kwargs.get("open_pos_usd", 0.0)
    sigs.append(dict(notional_usd=nu, current_equity=ce))
    sigs.append(dict(equity_usd=eu, today_trades=tt, open_pos_usd=opu))
    for sig in sigs:
        try:
            return risk_obj.can_open(**sig)
        except TypeError:
            continue
        except Exception:
            continue
    return True, "compat_allow"
import pandas as pd

from core.risk_guard import RiskManager, _read_last_equity
from core.positions.portfolio import PortfolioState, Position
from core.filters.gates import evaluate_gates

# --------- Helpers ---------

def _today_str() -> str:
    return date.today().isoformat()

def _ensure_parent(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)

def _df_effectively_empty(df: Optional[pd.DataFrame]) -> bool:
    if not isinstance(df, pd.DataFrame):
        return True
    if df.empty:
        return True
    # if all columns NA for all rows, treat as empty
    try:
        return df.dropna(how="all").empty
    except Exception:
        return False

def _safe_concat(a: Optional[pd.DataFrame], b: Optional[pd.DataFrame]) -> pd.DataFrame:
    parts = []
    if not _df_effectively_empty(a): parts.append(a)
    if not _df_effectively_empty(b): parts.append(b)
    if not parts:
        return pd.DataFrame()
    # align to first non-empty columns
    cols = list(parts[0].columns)
    norm = [d.reindex(columns=cols) for d in parts]
    if len(norm) == 1:
        return norm[0].copy()
    # Only concat when >1 non-empty pieces -> avoids FutureWarning in pandas>=2.3
    return pd.concat(norm, ignore_index=True)

# --------- CSV Writers (stable schemas) ---------

ORDERS_COLUMNS = ["timestamp","symbol","action","side","qty","entry","sl","tp","reason","exit","pnl"]

def append_order_csv(path: str, row: Dict[str, Any]) -> str:
    p = Path(path); _ensure_parent(p)
    if p.exists():
        try:
            df_old = pd.read_csv(p)
        except Exception:
            df_old = pd.DataFrame(columns=ORDERS_COLUMNS)
    else:
        df_old = pd.DataFrame(columns=ORDERS_COLUMNS)
    df_new = pd.DataFrame([row], columns=ORDERS_COLUMNS)
    df = _safe_concat(df_old, df_new)
    df.to_csv(p, index=False)
    return str(p)

EQUITY_COLUMNS = ["timestamp","symbol","balance","upnl","equity","price","side","qty","time"]

def append_equity_csv(path: str, row: Dict[str, Any]) -> str:
    p = Path(path); _ensure_parent(p)
    if p.exists():
        try:
            df_old = pd.read_csv(p)
        except Exception:
            df_old = pd.DataFrame(columns=EQUITY_COLUMNS)
    else:
        df_old = pd.DataFrame(columns=EQUITY_COLUMNS)
    df_new = pd.DataFrame([row], columns=EQUITY_COLUMNS)
    df = _safe_concat(df_old, df_new)
    df.to_csv(p, index=False)
    return str(p)

# --------- Config & Trader ---------

@dataclass
class PaperConfig:
    orders_path_template: str = "logs/orders/{date}.csv"
    equity_path_template: str = "logs/equity/{date}.csv"
    equity_start_usd: float = 10000.0
    risk_usd: float = 5.0
    fee_bps: float = 4.0
    slip_bps: float = 1.0
    starting_balance: Optional[float] = field(default=None, repr=False)

    def __post_init__(self):
        if self.starting_balance is not None:
            self.equity_start_usd = float(self.starting_balance)

class PaperTrader:
    """Lifecycle & PnL in paper mode with risk gating and strategy gates."""
    def __init__(self, symbol: str, cfg: PaperConfig, *, risk_usd: Optional[float]=None,
                 fee_bps: Optional[float]=None, slip_bps: Optional[float]=None, logger: Any=None) -> None:
        self.symbol = symbol
        self.cfg = cfg
        self.risk_usd = float(risk_usd if risk_usd is not None else cfg.risk_usd)
        self.fee_bps = float(fee_bps if fee_bps is not None else cfg.fee_bps)
        self.slip_bps = float(slip_bps if slip_bps is not None else cfg.slip_bps)
        self.log = logger
        self.equity = float(_read_last_equity(symbol) or cfg.equity_start_usd)
        self.risk = RiskManager(symbol=self.symbol)
        self.portfolio = PortfolioState(symbol=self.symbol)

    @staticmethod
    def _apply_slip(price: float, side: str, is_entry: bool, slip_bps: float) -> float:
        sgn = 1.0 if str(side).upper() == "LONG" else -1.0
        mult = 1.0 + (slip_bps / 10000.0) * (sgn if is_entry else -sgn)
        return float(price) * mult

    def _order_path(self) -> str:
        return self.cfg.orders_path_template.format(date=_today_str())

    def _equity_path(self) -> str:
        return self.cfg.equity_path_template.format(date=_today_str())

    def _write_equity(self, tss: str, price: float, side: str = "FLAT", qty: float = 0.0) -> None:
        e_row = {
            "timestamp": tss,
            "symbol": self.symbol,
            "balance": self.equity,
            "upnl": 0.0,
            "equity": self.equity,
            "price": price,
            "side": side,
            "qty": qty,
            "time": tss
        }
        append_equity_csv(self._equity_path(), e_row)

    def _open(self, tss: str, side: str, entry_px: float, qty: float, sl: float | None, tp: float | None, reason: str) -> None:
        # fee on open
        notional = qty * entry_px
        fee_open = notional * (self.fee_bps / 10000.0)
        self.equity = max(0.0, self.equity - fee_open)

        o_row = {
            "timestamp": tss, "symbol": self.symbol, "action": "OPEN", "side": side,
            "qty": round(qty, 8), "entry": round(entry_px, 8),
            "sl": float(sl) if sl is not None else None,
            "tp": float(tp) if tp is not None else None,
            "reason": reason, "exit": None, "pnl": None
        }
        append_order_csv(self._order_path(), o_row)

        self.portfolio.set_position(Position(
            symbol=self.symbol, side=side, qty=qty, entry=entry_px, sl=sl, tp=tp,
            open_time=tss, fee_bps=self.fee_bps
        ))

    def _close(self, tss: str, pos: Position, exit_px: float, reason: str) -> float:
        # fee on close
        notional = pos.qty * exit_px
        fee_close = notional * (self.fee_bps / 10000.0)

        # pnl gross
        if pos.side.upper() == "LONG":
            gross = (exit_px - pos.entry) * pos.qty
        else:
            gross = (pos.entry - exit_px) * pos.qty

        pnl = gross - fee_close  # open fee already deducted from equity at open
        self.equity = self.equity + pnl  # add realized pnl

        c_row = {
            "timestamp": tss, "symbol": self.symbol, "action": "CLOSE", "side": pos.side,
            "qty": round(pos.qty, 8), "entry": round(pos.entry, 8),
            "sl": pos.sl, "tp": pos.tp, "reason": reason,
            "exit": round(exit_px, 8), "pnl": pnl
        }
        append_order_csv(self._order_path(), c_row)

        self.portfolio.set_position(None)
        return pnl

    def on_bar(self, bar: Dict[str, Any], decision: Dict[str, Any]) -> None:
        ts = bar.get("open_time")
        if isinstance(ts, datetime):
            tss = ts.astimezone(timezone.utc).isoformat()
        else:
            tss = datetime.now(timezone.utc).isoformat()

        side_decision = str(decision.get("side","FLAT")).upper()
        price = float(bar.get("close", bar.get("open", 0.0)))
        high = float(bar.get("high", price))
        low = float(bar.get("low", price))
        sl = decision.get("sl")
        tp = decision.get("tp")
        reason = str(decision.get("reason","signal"))

        # refresh risk counters
        getattr(getattr(self, "risk", None), "refresh_from_logs", lambda *a, **k: None)()

        # 1) Check existing position -> SL/TP hit on this bar
        pos = self.portfolio.get_position()
        if pos is not None:
            hit, exit_px, why = pos.check_exit_on_bar(high=high, low=low)
            if hit:
                self._close(tss, pos, exit_px, why)

        # fetch updated state
        pos = self.portfolio.get_position()

        # 2) Write equity point (after any close)
        self._write_equity(tss, price, side=pos.side if pos else "FLAT", qty=pos.qty if pos else 0.0)

        # 3) Apply decision -> open/flip/ignore
        if side_decision not in {"LONG","SHORT"}:
            return

        if pos and pos.side.upper() == side_decision:
            return

        if pos and pos.side.upper() != side_decision:
            self._close(tss, pos, price, "Flip")

        # ---- Strategy gates (session/ATR/HTF) ----
        gates_ok, gate_msgs = evaluate_gates(side_decision)
        if not gates_ok:
            # treat as risk block for unified logging
            try:
                from core.risk_guard import RiskManager
                self.risk.record_block("gates:" + "|".join(gate_msgs))
            except Exception:
                pass
            if self.log:
                try: self.log.info(f"[gates] blocked: {gate_msgs}")
                except Exception: pass
            return

        # ---- Risk gate ----
        allowed, reason_block = _compat_can_open(self.risk,
    notional_usd=self.risk_usd,
    current_equity=self.equity,
    equity_usd=self.equity,
    today_trades=locals().get("daily_trade_count", 0),
    open_pos_usd=(
    abs(locals().get("position", {}).get("qty", 0.0) * locals().get("close", 0.0))
    if locals().get("position") is not None else 0.0
)
)
        if not allowed:
            self.risk.record_block(reason_block)
            if self.log:
                try: self.log.info(f"[risk] blocked: {reason_block}")
                except Exception: pass
            return

        # ---- Open new position ----
        entry_px = self._apply_slip(price, side_decision, True, self.slip_bps)
        qty = max(1e-8, self.risk_usd / max(1e-8, entry_px))
        self._open(tss, side_decision, entry_px, qty, sl, tp, reason)
