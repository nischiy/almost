from __future__ import annotations
import os
import sys
import time
import logging
from importlib import import_module
from typing import Callable, Optional, Any, Dict

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
    def __init__(self, cfg: Any=None, symbol: Optional[str]=None, interval: Optional[str]=None):
        self.log = _setup_logging()
        self.cfg = cfg
        self.symbol = symbol or os.environ.get("SYMBOL", "BTCUSDT")
        self.interval = interval or os.environ.get("INTERVAL", "1m")
        self.paper = os.environ.get("PAPER_TRADING", "1") != "0"
        self.trade_enabled = os.environ.get("TRADE_ENABLED", "0") == "1"
        self.md = None   # expects get_klines(symbol, interval, limit=...)
        self.sig = None  # expects decide(df, params_dict) -> dict
        self.risk = None # expects can_open(decision) -> (ok, reason)
        self.exe = None  # expects place(symbol, side, otype, wallet_usdt, **kwargs)
        self.tel = None  # optional snapshot/decision/health

    def run_once(self) -> None:
        df = None
        if getattr(self, "md", None) and hasattr(self.md, "get_klines"):
            try:
                df = self.md.get_klines(self.symbol, self.interval, limit=1000)
            except Exception as e:
                self.log.exception("md.get_klines failed: %s", e)
                df = None

        if getattr(self, "tel", None) and hasattr(self.tel, "snapshot") and df is not None:
            try:
                self.tel.snapshot(df)
            except Exception:
                pass

        decision = None
        if getattr(self, "sig", None) and hasattr(self.sig, "decide") and df is not None:
            try:
                params: Dict[str, Any] = _build_strategy_params(self.cfg)
                decision = self.sig.decide(df, params)  # DICT-only контракт
            except Exception as e:
                self.log.exception("sig.decide failed: %s", e)
                decision = None

        if not isinstance(decision, dict):
            self.log.info("run_once: no decision; symbol=%s interval=%s", self.symbol, self.interval)
            return

        # телеметрія рішення
        if getattr(self, "tel", None) and hasattr(self.tel, "decision"):
            try:
                self.tel.decision(decision)
            except Exception:
                pass

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
            if getattr(self, "tel", None) and hasattr(self.tel, "health"):
                try:
                    self.tel.health(ok=False, msg=reason)
                except Exception:
                    pass
            return

        # execution
        if getattr(self, "exe", None) and hasattr(self.exe, "place"):
            try:
                side = str(decision.get("side", "HOLD")).upper()
                if side == "HOLD":
                    self.log.info("run_once: HOLD — nothing to execute")
                    return
                otype = decision.get("type") or decision.get("otype") or "MARKET"
                wallet_usdt = decision.get("wallet_usdt")
                if wallet_usdt is None:
                    wallet_usdt = float(os.getenv("WALLET_USDT", "1000"))

                # приберемо дублікати ключів, які передаємо позиційно
                drop = {"side", "type", "otype", "wallet_usdt", "symbol"}
                kwargs = {k: v for k, v in decision.items() if k not in drop}

                res = self.exe.place(self.symbol, side, otype, wallet_usdt, **kwargs)
                if isinstance(res, dict):
                    self.log.info("execution: submitted=%s reason=%s", res.get("submitted"), res.get("reason"))
                else:
                    self.log.info("execution: done (non-dict response)")
            except Exception as e:
                self.log.exception("execution failed: %s", e)
        else:
            self.log.info("run_once: no execution service wired; decision=%s", decision)

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
    safe_keys = ["SYMBOL", "PAPER_TRADING", "TRADE_ENABLED", "BINANCE_FAPI_BASE", "STRATEGY_NAME", "INTERVAL"]
    msg = {k: os.environ.get(k) for k in safe_keys if k in os.environ}
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

def main() -> None:
    logger = _setup_logging()
    logger.info("=== Bot startup ===")
    _print_env(logger)

    fn = _try_get_main()
    oneshot_like = _is_testish_env()
    trade_enabled = os.environ.get("TRADE_ENABLED", "0") == "1"
    api_key_present = bool(os.environ.get("API_KEY", ""))

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
