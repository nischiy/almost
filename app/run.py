from __future__ import annotations
import os
import sys
import time
import logging
import inspect
from datetime import datetime, timezone
from importlib import import_module
from typing import Callable, Optional, Any, Dict

import pandas as pd

from app.decision import normalize_decision, normalize_side
from core.config.env import get_env, get_bool, load_dotenv_once, dotenv_loaded

LOG_NAME = "BotRun"

def _setup_logging() -> logging.Logger:
    logger = logging.getLogger(LOG_NAME)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)
    try:
        os.makedirs("logs", exist_ok=True)
        fh = logging.FileHandler("logs/runtime.log", encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except Exception:
        pass
    return logger

class TraderApp:
    """Фасад життєвого циклу бота, сумісний з тестами."""
    def __init__(self, cfg: Any=None, symbol: Optional[str]=None, interval: Optional[str]=None, logger: Optional[logging.Logger]=None):
        self.log = logger or _setup_logging()
        self.cfg = cfg
        self.symbol = symbol or get_env("SYMBOL", "BTCUSDT")
        self.interval = interval or get_env("INTERVAL", "1m")
        self.paper = get_bool("PAPER_TRADING", True)
        self.trade_enabled = get_bool("TRADE_ENABLED", False)
        self.md = None   # expects get_klines(symbol, interval, limit=...)
        self.sig = None  # expects decide(df, params_dict) -> dict
        self.risk = None # expects can_open(decision) -> (ok, reason)
        self.exe = None  # expects place(symbol, side, otype, wallet_usdt, **kwargs)
        self.tel = None  # optional snapshot/decision/health

    def run_once(self) -> None:
        wallet_usdt = _get_wallet_usdt()
        preflight = _read_preflight(self.symbol, wallet_usdt)
        preflight_rejects = list(preflight.get("rejects") or [])
        df = None
        if getattr(self, "md", None) and hasattr(self.md, "get_klines"):
            try:
                df = self.md.get_klines(self.symbol, self.interval, limit=1000)
                df = _ensure_utc_timestamps(df)
                df = _filter_closed_candles(df)
            except Exception as e:
                self.log.exception("md.get_klines failed: %s", e)
                df = None

        if getattr(self, "tel", None) and hasattr(self.tel, "snapshot") and df is not None:
            try:
                self.tel.snapshot(df)
            except Exception:
                pass

        decision = None
        sig_available = getattr(self, "sig", None) and hasattr(self.sig, "decide")
        if sig_available and df is not None and not df.empty:
            try:
                params: Dict[str, Any] = _build_strategy_params(self.cfg)
                decision = self.sig.decide(df, params)  # DICT-only контракт
            except Exception as e:
                self.log.exception("sig.decide failed: %s", e)
                decision = {"side": "HOLD", "action": "HOLD", "reason": "signal_error"}
        elif sig_available:
            decision = {"side": "HOLD", "action": "HOLD", "reason": "no_market_data"}

        if not isinstance(decision, dict):
            self.log.info("run_once: no decision; symbol=%s interval=%s", self.symbol, self.interval)
            decision = {"side": "HOLD", "action": "HOLD", "reason": "signal_empty"}

        decision = normalize_decision(decision, fallback_reason="signal_empty")
        strategy_name = decision.get("strategy") or get_env("STRATEGY_NAME", "ema_rsi_atr")

        # телеметрія рішення
        if getattr(self, "tel", None) and hasattr(self.tel, "decision"):
            try:
                self.tel.decision(decision)
            except Exception:
                pass

        execution_info: Dict[str, Any] = {"submitted": False, "reason": "hold_action"}
        sizing: Optional[Dict[str, Any]] = None

        if preflight_rejects:
            decision["action"] = "HOLD"
            decision["side"] = "HOLD"
            decision["reason"] = "missing_exchange_data"
            decision["reasons"] = preflight_rejects
            execution_info = {"submitted": False, "reason": "missing_exchange_data", "blockers": preflight_rejects}
        else:
            # risk-gate
            ok, reason = True, ""
            if getattr(self, "risk", None) and hasattr(self.risk, "can_open"):
                try:
                    ok, reason = self.risk.can_open(decision)
                except Exception as e:
                    self.log.exception("risk.can_open failed: %s", e)
                    ok, reason = False, "risk_error"

            if not ok:
                self.log.info("run_once: blocked by risk (%s)", reason)
                execution_info = {"submitted": False, "reason": "risk_reject", "detail": reason}
                _log_decision_details(
                    self.log,
                    decision,
                    strategy_name,
                    sizing=None,
                    execution=execution_info,
                )
                if normalize_side(decision.get("side") or decision.get("action")) in {"HOLD", "UNKNOWN"}:
                    self.log.info("run_once: HOLD — nothing to execute")
                if getattr(self, "tel", None) and hasattr(self.tel, "health"):
                    try:
                        self.tel.health(ok=False, msg=reason)
                    except Exception:
                        pass
            else:
                # execution
                if getattr(self, "exe", None) and hasattr(self.exe, "place"):
                    try:
                        side = normalize_side(decision.get("side") or decision.get("action"))
                        if side in {"HOLD", "UNKNOWN"}:
                            self.log.info("run_once: HOLD — nothing to execute")
                            execution_info = {"submitted": False, "reason": "hold_action"}
                            _log_decision_details(
                                self.log,
                                decision,
                                strategy_name,
                                sizing=None,
                                execution=execution_info,
                            )
                        else:
                            res = _call_execution(self.exe.place, decision, symbol=self.symbol)
                            if isinstance(res, dict):
                                self.log.info("execution: submitted=%s reason=%s", res.get("submitted"), res.get("reason"))
                                preview = res.get("preview") or {}
                                sizer = preview.get("sizer") or {}
                                sizing = {
                                    "size_usd": sizer.get("size_usd"),
                                    "qty_raw": sizer.get("qty_raw"),
                                    "qty_final": sizer.get("qty_final"),
                                    "step_size": sizer.get("lot_step"),
                                    "min_qty": sizer.get("min_qty"),
                                    "min_notional": sizer.get("min_notional"),
                                }
                                if sizer.get("size_usd") is not None:
                                    decision["size_usd"] = sizer.get("size_usd")
                                if sizer.get("qty_final") is not None:
                                    decision["qty"] = sizer.get("qty_final")
                                execution_info = {
                                    "submitted": res.get("submitted"),
                                    "reason": res.get("reason"),
                                    "blockers": preview.get("blockers"),
                                }
                                _log_decision_details(
                                    self.log,
                                    decision,
                                    strategy_name,
                                    sizing=sizing,
                                    execution=execution_info,
                                )
                            else:
                                self.log.info("execution: done (non-dict response)")
                    except Exception as e:
                        self.log.exception("execution failed: %s", e)
                        execution_info = {"submitted": False, "reason": "execution_error", "detail": str(e)}
                else:
                    self.log.info("run_once: no execution service wired; decision=%s", decision)
                    execution_info = {"submitted": False, "reason": "no_execution_service"}

        _log_tick_summary(self.log, decision, strategy_name, preflight, execution_info)

    def start(self, oneshot: Optional[bool]=None) -> None:
        if oneshot is None:
            oneshot = (
                os.environ.get("APP_RUN_ONESHOT", "0") == "1"
                or ("PYTEST_CURRENT_TEST" in os.environ)
                or (os.environ.get("CI", "0") == "1")
            )
        self.log.info("TraderApp.start(symbol=%s, interval=%s, paper=%s, trade_enabled=%s, oneshot=%s)",
                      self.symbol, self.interval, self.paper, self.trade_enabled, oneshot)
        if oneshot:
            self.run_once()
            return
        i = 0
        try:
            while True:
                i += 1
                self.log.info("Tick #%d", i)
                self.run_once()
                sleep_sec = float(os.environ.get("LOOP_SLEEP_SEC", "5"))
                time.sleep(sleep_sec)
        except KeyboardInterrupt:
            self.log.info("TraderApp shutdown requested.")

def _try_get_main() -> Optional[Callable[..., None]]:
    candidates = [
        ("app.entrypoint", "main"),
        ("app.app", "main"),
        ("app.bootstrap", "main"),
    ]
    for mod_name, func_name in candidates:
        try:
            mod = import_module(mod_name)
        except Exception:
            continue
        fn = getattr(mod, func_name, None)
        if callable(fn):
            return fn
    return None

def _print_env(logger: logging.Logger) -> None:
    keys = [
        "SYMBOL",
        "INTERVAL",
        "STRATEGY_NAME",
        "PAPER_TRADING",
        "TRADE_ENABLED",
        "DRY_RUN_ONLY",
        "BINANCE_TESTNET",
    ]
    msg = {k: get_env(k) for k in keys}
    msg["dotenv_loaded"] = dotenv_loaded()
    msg["api_key_present"] = bool(get_env("API_KEY"))
    msg["api_secret_present"] = bool(get_env("API_SECRET"))
    logger.info("Startup env: %s", msg)

def _heartbeat(logger: logging.Logger, oneshot: bool) -> None:
    logger.info("No explicit app main() found. Heartbeat mode%s.", " (oneshot)" if oneshot else "")
    if oneshot:
        logger.info("Heartbeat #1 - exit (test/CI mode).")
        return
    i = 0
    try:
        while True:
            i += 1
            logger.info("Heartbeat #%d - bot idle (set TRADE_ENABLED=1 to trade).", i)
            time.sleep(5)
    except KeyboardInterrupt:
        logger.info("Shutdown requested. Bye.")

def _is_testish_env() -> bool:
    """Детекція середовища тестів/CI."""
    env = os.environ
    return (
        env.get("APP_RUN_ONESHOT", "0") == "1"
        or "PYTEST_CURRENT_TEST" in env
        or "PYTEST_ADDOPTS" in env
        or "PYTEST_XDIST_WORKER" in env
        or env.get("CI", "0") == "1"
    )

# ================== helpers (тільки для run.py) ==================
def _cfg_public_attrs(cfg: Any) -> Dict[str, Any]:
    """
    Витягує публічні атрибути cfg у dict.
    Беремо лише примітиви (str/int/float/bool/None), щоб уникати важких об'єктів.
    """
    prim = (str, int, float, bool, type(None))
    out: Dict[str, Any] = {}
    if cfg is None:
        return out
    for name in dir(cfg):
        if name.startswith("_"):
            continue
        try:
            val = getattr(cfg, name)
        except Exception:
            continue
        if isinstance(val, prim):
            out[name] = val
    return out

def _build_strategy_params(cfg: Any) -> Dict[str, Any]:
    """
    Єдина точка формування параметрів для стратегії (DICT only).
    - Забезпечує ключ 'strategy' з ENV або дефолтом.
    - Додає symbol, якщо він є в cfg/ENV.
    - Додає всі публічні примітивні атрибути cfg (сумісність зі старим кодом).
    """
    params: Dict[str, Any] = _cfg_public_attrs(cfg)
    # strategy
    params["strategy"] = os.getenv("STRATEGY_NAME", params.get("STRATEGY_NAME", "ema_rsi_atr"))
    # symbol
    if "symbol" not in params and "SYMBOL" in params:
        params["symbol"] = params["SYMBOL"]
    params.setdefault("symbol", os.getenv("SYMBOL", "BTCUSDT"))
    return params


def _ensure_utc_timestamps(df: Any) -> Any:
    if df is None or not hasattr(df, "columns"):
        return df
    for col in ("open_time", "close_time", "time"):
        if col in df.columns:
            series = pd.to_datetime(df[col], utc=True, errors="coerce")
            df[col] = series
    return df


def _filter_closed_candles(df: Any) -> Any:
    if df is None or not hasattr(df, "columns") or df.empty:
        return df
    now = datetime.now(timezone.utc)
    if "close_time" in df.columns:
        closed = df["close_time"] <= now
    elif "open_time" in df.columns:
        closed = df["open_time"] <= now
    else:
        return df
    filtered = df.loc[closed]
    return filtered if not filtered.empty else df.iloc[0:0]


def _call_execution(place_fn: Callable[..., Any], decision: Dict[str, Any], *, symbol: str) -> Any:
    sig = inspect.signature(place_fn)
    params = sig.parameters
    if "decision" in params:
        return place_fn(decision=decision)

    positional = [p for p in params.values() if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
    has_kwargs = any(p.kind == p.VAR_KEYWORD for p in params.values())
    if len(positional) <= 1 and not has_kwargs:
        return place_fn(decision)

    payload = _build_execution_payload(decision, symbol)
    return place_fn(**payload)


def _build_execution_payload(decision: Dict[str, Any], symbol: str) -> Dict[str, Any]:
    side = normalize_side(decision.get("side") or decision.get("action"))
    otype = decision.get("type") or decision.get("otype") or "MARKET"
    wallet_usdt = decision.get("wallet_usdt")
    if wallet_usdt is None:
        wallet_usdt = float(os.getenv("WALLET_USDT", "1000"))
    drop = {"side", "action", "type", "otype", "wallet_usdt", "symbol"}
    extra = {k: v for k, v in decision.items() if k not in drop}
    return {"symbol": symbol, "side": side, "otype": otype, "wallet_usdt": wallet_usdt, **extra}

def _get_wallet_usdt() -> Optional[float]:
    raw = os.getenv("WALLET_USDT")
    if raw is None:
        return None
    try:
        return float(str(raw).strip())
    except Exception:
        return None

def _read_preflight(symbol: str, wallet_usdt: Optional[float]) -> Dict[str, Any]:
    ts = time.time()
    try:
        from app.services import order_service
        return order_service.preflight_read(symbol, wallet_usdt)
    except Exception as e:
        reason = f"preflight_error:{e}"
        return {
            "account": {"equity_usd": None, "wallet_usdt": None, "source": "missing", "reason": reason, "ts": ts},
            "filters": {"step_size": None, "min_qty": None, "min_notional": None, "source": "missing", "reason": reason, "ts": ts},
            "price": {"value": None, "source": "missing", "reason": reason, "ts": ts},
            "rejects": [reason],
        }

def _log_tick_summary(logger: logging.Logger, decision: Dict[str, Any], strategy: str,
                      preflight: Dict[str, Any], execution: Dict[str, Any]) -> None:
    account = preflight.get("account") or {}
    filters = preflight.get("filters") or {}
    price = preflight.get("price") or {}
    reasons = decision.get("reasons")
    if not reasons:
        reasons = [decision.get("reason")] if decision.get("reason") else []
    risk_pct = None
    try:
        risk_pct = float(str(get_env("RISK_PER_TRADE_PCT", "")).strip())
    except Exception:
        risk_pct = None
    equity_val = account.get("equity_usd")
    risk_usd = None
    if equity_val is not None and risk_pct is not None:
        try:
            risk_usd = float(equity_val) * (float(risk_pct) / 100.0)
        except Exception:
            risk_usd = None
    payload = {
        "strategy": strategy,
        "action": decision.get("action") or decision.get("side"),
        "reasons": reasons,
        "account": {
            "equity_usd": account.get("equity_usd"),
            "wallet_usdt": account.get("wallet_usdt"),
            "source": account.get("source"),
            "ts": account.get("ts"),
        },
        "filters": {
            "step_size": filters.get("step_size"),
            "min_qty": filters.get("min_qty"),
            "min_notional": filters.get("min_notional"),
            "tick_size": filters.get("tick_size"),
            "source": filters.get("source"),
            "ts": filters.get("ts"),
        },
        "price": {
            "last": price.get("value"),
            "source": price.get("source"),
            "ts": price.get("ts"),
        },
        "risk": {
            "risk_usd": risk_usd,
            "qty_min": None,
            "qty_final": decision.get("qty"),
            "sl_base": decision.get("sl"),
            "sl_final": None,
            "leverage_selected": None,
        },
        "execution": execution,
    }
    logger.info("tick_summary: %s", payload)

def _log_decision_details(logger: logging.Logger, decision: Dict[str, Any], strategy: str,
                          *, sizing: Optional[Dict[str, Any]], execution: Optional[Dict[str, Any]]) -> None:
    indicators = decision.get("indicators")
    if not indicators:
        indicators = {
            "ema_fast": decision.get("ema_fast"),
            "ema_slow": decision.get("ema_slow"),
            "rsi": decision.get("rsi"),
            "atr": decision.get("atr"),
        }
    price = decision.get("price")
    sl = decision.get("sl")
    tp = decision.get("tp")
    rr = None
    if price and sl and tp:
        risk = abs(float(price) - float(sl))
        reward = abs(float(tp) - float(price))
        rr = (reward / risk) if risk > 0 else None
    logger.info(
        "decision: strategy=%s action=%s reason=%s reasons=%s price=%s indicators=%s size_usd=%s qty=%s sl=%s tp=%s rr=%s sizing=%s execution=%s",
        strategy,
        decision.get("action") or decision.get("side"),
        decision.get("reason"),
        decision.get("reasons"),
        price,
        indicators,
        decision.get("size_usd"),
        decision.get("qty"),
        sl,
        tp,
        rr,
        sizing,
        execution,
    )

def main() -> None:
    load_dotenv_once()
    logger = _setup_logging()
    logger.info("=== Bot startup ===")
    _print_env(logger)

    fn = _try_get_main()
    oneshot_like = _is_testish_env()
    trade_enabled = get_bool("TRADE_ENABLED", False)
    api_key_present = bool(get_env("API_KEY", ""))

    if fn is not None:
        # Якщо НЕ бойовий режим (TRADE_ENABLED!=1) або немає API_KEY, або test/CI —
        # виконуємо одноразовий цикл через entrypoint і завершуємось.
        if (not trade_enabled) or (not api_key_present) or oneshot_like:
            logger.info("Delegating to entrypoint in oneshot (reason: trade_enabled=%s, api_key=%s, testish=%s).",
                        trade_enabled, "yes" if api_key_present else "no", oneshot_like)
            try:
                fn(["--once"])
            except TypeError:
                fn()
            return

        # Бойовий режим — звичайний старт
        try:
            fn()
        except KeyboardInterrupt:
            logger.info("Graceful shutdown.")
        except Exception as e:
            logger.exception("Unhandled exception from app entrypoint: %s", e)
            sys.exit(1)
    else:
        # Нема явного entrypoint — heartbeat; але в тест/CI зробимо oneshot
        _heartbeat(logger, oneshot_like)

if __name__ == "__main__":
    main()
