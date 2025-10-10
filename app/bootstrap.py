# app/bootstrap.py
from __future__ import annotations

import os
import logging
import importlib
import inspect
from dataclasses import dataclass
from typing import Any, Dict, Optional, Union, Callable, Tuple, Type


# ----------------------------- Config & utils ---------------------------------

@dataclass(frozen=True)
class AppConfig:
    symbol: str
    strategy_name: str
    paper_trading: bool
    trade_enabled: bool
    dry_run_only: bool
    loop_sleep_sec: float
    binance_fapi_base: Optional[str] = None
    log_dir: str = "logs"
    log_level: str = "INFO"


def _to_bool(val: Any, default: bool = False) -> bool:
    if val is None:
        return default
    if isinstance(val, bool):
        return val
    s = str(val).strip().lower()
    return s in ("1", "true", "yes", "y", "on")


def _to_float(val: Any, default: float) -> float:
    try:
        return float(val)
    except Exception:
        return default


def _get(obj: Any, name: str, default: Any) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _coerce_to_appconfig(cfg: Optional[Any], env: Optional[Dict[str, str]] = None) -> AppConfig:
    env = env or os.environ

    symbol = _get(cfg, "SYMBOL", env.get("SYMBOL", "BTCUSDT"))
    strategy_name = _get(cfg, "STRATEGY_NAME", env.get("STRATEGY_NAME", "baseline"))

    paper = _to_bool(_get(cfg, "PAPER_TRADING", env.get("PAPER_TRADING")), default=True)
    trade_enabled = _to_bool(_get(cfg, "TRADE_ENABLED", env.get("TRADE_ENABLED")), default=False)
    dry_run = _to_bool(_get(cfg, "DRY_RUN_ONLY", env.get("DRY_RUN_ONLY")), default=True)
    if paper:
        dry_run = True  # політика: paper ⇒ dry-run

    loop_sleep = _to_float(_get(cfg, "LOOP_SLEEP_SEC", env.get("LOOP_SLEEP_SEC")), 1.0)
    binance_fapi_base = _get(cfg, "BINANCE_FAPI_BASE", env.get("BINANCE_FAPI_BASE", None))
    log_dir = _get(cfg, "LOG_DIR", env.get("LOG_DIR", "logs"))

    raw_level = _get(cfg, "LOG_LEVEL", env.get("LOG_LEVEL", "INFO"))
    log_level = str(raw_level).upper() if not isinstance(raw_level, int) else {
        v: k for k, v in logging.__dict__.items() if isinstance(v, int)
    }.get(raw_level, "INFO")

    # Виставляємо назад в ENV для сервісів, що читають os.environ
    os.environ["PAPER_TRADING"] = "1" if paper else "0"
    os.environ["TRADE_ENABLED"] = "1" if trade_enabled else "0"
    os.environ["DRY_RUN_ONLY"] = "1" if dry_run else "0"
    os.environ.setdefault("SYMBOL", symbol)
    os.environ.setdefault("STRATEGY_NAME", strategy_name)
    if binance_fapi_base:
        os.environ.setdefault("BINANCE_FAPI_BASE", binance_fapi_base)
    os.environ.setdefault("LOG_DIR", log_dir)
    os.environ.setdefault("LOG_LEVEL", log_level)
    os.environ.setdefault("LOOP_SLEEP_SEC", str(loop_sleep))

    return AppConfig(
        symbol=symbol,
        strategy_name=strategy_name,
        paper_trading=paper,
        trade_enabled=trade_enabled,
        dry_run_only=dry_run,
        loop_sleep_sec=loop_sleep,
        binance_fapi_base=binance_fapi_base,
        log_dir=log_dir,
        log_level=log_level,
    )


def resolve_runtime_mode(env: Optional[Dict[str, str]] = None) -> AppConfig:
    return _coerce_to_appconfig(cfg=None, env=env)


def _ensure_logging(cfg: AppConfig) -> logging.Logger:
    level = getattr(logging, str(cfg.log_level).upper(), None)
    if not isinstance(level, int):
        try:
            level = int(cfg.log_level)
        except Exception:
            level = logging.INFO

    log = logging.getLogger("Bootstrap")
    log.setLevel(level)
    if not any(isinstance(h, logging.StreamHandler) for h in log.handlers):
        sh = logging.StreamHandler()
        sh.setLevel(level)
        sh.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s"))
        log.addHandler(sh)
    try:
        os.makedirs(cfg.log_dir, exist_ok=True)
        fp = os.path.join(cfg.log_dir, "bootstrap.log")
        if not any(isinstance(h, logging.FileHandler) for h in log.handlers):
            fh = logging.FileHandler(fp, encoding="utf-8")
            fh.setLevel(level)
            fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
            log.addHandler(fh)
    except Exception as e:
        log.warning("Cannot init file logging: %s", e)
    return log


def _import_module(name: str):
    return importlib.import_module(name)


def _construct_with_filtered_kwargs(cls: Type, base_kwargs: Dict[str, Any]):
    try:
        sig = inspect.signature(cls.__init__)
        allowed = {k: v for k, v in base_kwargs.items() if k in sig.parameters}
    except (ValueError, TypeError):
        allowed = base_kwargs
    return cls(**allowed) if allowed else cls()


# ------------------------ Thin adapters (function or class) --------------------

def _resolve_callable(mod, names: Tuple[str, ...]) -> Optional[Callable[..., Any]]:
    for n in names:
        obj = getattr(mod, n, None)
        if callable(obj):
            return obj
    return None


def _resolve_class_with_methods(
    mod,
    method_pairs: Tuple[Tuple[str, ...], Tuple[str, ...]],
    *,
    prefer_suffixes: Tuple[str, ...] = ("service", "client", "provider"),
) -> Optional[Type]:
    """
    Шукає клас у модулі, який має два необхідні методи (з вказаних варіантів назв).
    method_pairs: ((methodA_names...), (methodB_names...))
    """
    need_a, need_b = method_pairs
    candidates: list[Type] = []
    for attr_name in dir(mod):
        cls = getattr(mod, attr_name, None)
        if not inspect.isclass(cls):
            continue
        methods = dir(cls)
        ok_a = any(m in methods for m in need_a)
        ok_b = any(m in methods for m in need_b)
        if ok_a and ok_b:
            candidates.append(cls)
    if not candidates:
        return None
    # якщо є кілька — пріоритезуємо за суфіксами
    lower = {c: c.__name__.lower() for c in candidates}
    for suf in prefer_suffixes:
        for c in candidates:
            if lower[c].endswith(suf):
                return c
    return candidates[0]


class MarketDataAdapter:
    """
    Працює з:
      - модульними функціями: get_klines(...), get_latest_price(...)
      - або з класом у модулі, що має відповідні методи (напр., MarketDataClient, MarketDataService)
    """
    FN_KLINES = ("get_klines", "fetch_klines", "klines")
    FN_PRICE = ("get_latest_price", "latest_price", "get_price", "price")

    def __init__(self, *, module_name: str = "app.services.market_data", cfg=None, symbol: str | None = None, logger=None, **_):
        self.cfg = cfg
        self.symbol = symbol
        self.log = logger or logging.getLogger("MarketData")
        mod = _import_module(module_name)

        # 1) спроба: модульні функції
        fn_kl = _resolve_callable(mod, self.FN_KLINES)
        fn_pr = _resolve_callable(mod, self.FN_PRICE)

        if fn_kl and fn_pr:
            self._kind = "module_functions"
            self._fn_klines = fn_kl
            self._fn_price = fn_pr
            self._cls_inst = None
        else:
            # 2) спроба: знайти клас із потрібними методами
            cls = _resolve_class_with_methods(mod, (self.FN_KLINES, self.FN_PRICE))
            if not cls:
                raise ImportError("market_data: neither functions nor class with required methods found")
            self._kind = "class_instance"
            self._cls_inst = _construct_with_filtered_kwargs(cls, {"cfg": cfg, "symbol": symbol, "logger": logger})
            self._fn_klines = None
            self._fn_price = None

    def get_klines(self, symbol: str | None = None, interval: str = "1m", limit: int = 500, **kwargs):
        sym = symbol or self.symbol
        if not sym:
            raise ValueError("symbol is required for get_klines()")
        if self._kind == "module_functions":
            return self._fn_klines(sym, interval=interval, limit=limit, **kwargs)
        # class_instance
        # шукаємо доступну назву методу
        for name in self.FN_KLINES:
            if hasattr(self._cls_inst, name):
                return getattr(self._cls_inst, name)(sym, interval=interval, limit=limit, **kwargs)
        raise AttributeError("market_data class instance lost klines method")

    def get_latest_price(self, symbol: str | None = None, **kwargs) -> float:
        sym = symbol or self.symbol
        if not sym:
            raise ValueError("symbol is required for get_latest_price()")
        if self._kind == "module_functions":
            return self._fn_price(sym, **kwargs)
        for name in self.FN_PRICE:
            if hasattr(self._cls_inst, name):
                return getattr(self._cls_inst, name)(sym, **kwargs)
        raise AttributeError("market_data class instance lost price method")


class OrderServiceAdapter:
    """
    Працює з:
      - модульною функцією place(...)
      - або з класом, що має метод place(...)
    """
    def __init__(self, *, module_name: str = "app.services.order_service", cfg=None, symbol: str | None = None, logger=None, **_):
        self.cfg = cfg
        self.symbol = symbol
        self.log = logger or logging.getLogger("OrderService")
        mod = _import_module(module_name)

        # 1) модульна функція
        fn_place = getattr(mod, "place", None)
        if callable(fn_place):
            self._kind = "module_function"
            self._fn_place = fn_place
            self._cls_inst = None
            return

        # 2) клас із методом place
        cls = None
        for attr_name in dir(mod):
            c = getattr(mod, attr_name, None)
            if inspect.isclass(c) and hasattr(c, "place") and callable(getattr(c, "place")):
                cls = c
                break
        if not cls:
            raise ImportError("order_service: place(...) function or class with .place missing")

        self._kind = "class_instance"
        self._cls_inst = _construct_with_filtered_kwargs(cls, {"cfg": cfg, "symbol": symbol, "logger": logger})
        self._fn_place = None

    def place(self, symbol: str | None = None, **kwargs) -> Dict[str, Any]:
        sym = symbol or self.symbol
        if not sym:
            raise ValueError("symbol is required for place()")
        if self._kind == "module_function":
            return self._fn_place(sym, **kwargs)
        return self._cls_inst.place(sym, **kwargs)


# -------------------------------- Composition ----------------------------------

def compose_trader_app(cfg: Optional[Union[AppConfig, Dict[str, Any], Any]] = None):
    app_cfg = cfg if isinstance(cfg, AppConfig) else _coerce_to_appconfig(cfg)
    log = _ensure_logging(app_cfg)

    # 1) TraderApp
    TraderApp = getattr(_import_module("app.run"), "TraderApp")
    app_logger = logging.getLogger("TraderApp")
    trader_app = _construct_with_filtered_kwargs(TraderApp, {
        "logger": app_logger,
        "symbol": app_cfg.symbol,
        "cfg": cfg if cfg is not None else app_cfg,
    })

    # 2) Wire adapters
    setattr(trader_app, "md", MarketDataAdapter(cfg=cfg or app_cfg, symbol=app_cfg.symbol, logger=logging.getLogger("MarketData")))
    log.info("Wired MarketDataAdapter -> trader_app.md")

    setattr(trader_app, "exe", OrderServiceAdapter(cfg=cfg or app_cfg, symbol=app_cfg.symbol, logger=logging.getLogger("OrderService")))
    log.info("Wired OrderServiceAdapter -> trader_app.exe")

    # 3) Wire class-based services (якщо є)
    _wire_class_service(trader_app, "app.services.signal", "SignalService", "sig", log, logger_name="Signal", kwargs={"cfg": cfg or app_cfg, "symbol": app_cfg.symbol})
    _wire_class_service(trader_app, "app.services.exit_manager", "ExitManager", "exit", log, logger_name="ExitManager", kwargs={"cfg": cfg or app_cfg, "symbol": app_cfg.symbol})
    _wire_class_service(trader_app, "app.services.telemetry", "TelemetryService", "tel", log, logger_name="Telemetry", kwargs={"cfg": cfg or app_cfg, "symbol": app_cfg.symbol})
    _wire_class_service(trader_app, "app.services.execution", "ExecutionService", "executor", log, logger_name="Execution", kwargs={"cfg": cfg or app_cfg, "symbol": app_cfg.symbol})

    log.info(
        "Mode: PAPER=%s, TRADE_ENABLED=%s, DRY_RUN_ONLY=%s, SYMBOL=%s, STRATEGY=%s",
        app_cfg.paper_trading, app_cfg.trade_enabled, app_cfg.dry_run_only, app_cfg.symbol, app_cfg.strategy_name
    )

    return trader_app


def _wire_class_service(trader_app, module_path: str, class_name: str, attr_name: str,
                        log: logging.Logger, *, logger_name: str, kwargs: Dict[str, Any]):
    try:
        mod = _import_module(module_path)
        cls = getattr(mod, class_name)
        if not inspect.isclass(cls):
            raise TypeError(f"{module_path}.{class_name} is not a class")
        instance = _construct_with_filtered_kwargs(cls, {"logger": logging.getLogger(logger_name), **(kwargs or {})})
        setattr(trader_app, attr_name, instance)
        log.info("Wired %s -> trader_app.%s", class_name, attr_name)
    except Exception as e:
        log.warning("Skip wiring %s: %s", class_name, e)
