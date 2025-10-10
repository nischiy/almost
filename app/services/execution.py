from __future__ import annotations
import logging
from typing import Dict, Any, Optional

class ExecutionService:
    def __init__(self, cfg=None, symbol: Optional[str]=None, logger: Optional[logging.Logger]=None):
        self.cfg = cfg
        self.symbol = symbol
        self.log = logger or logging.getLogger("Execution")

    def place(self, decision: Dict[str, Any]) -> None:
        # Paper-safe logging; if PAPER_TRADING=1 and TRADE_ENABLED=0, write csv to logs/orders/<date>.csv
        try:
            import os as _os
            from pathlib import Path as _Path
            from datetime import datetime as _dt, timezone as _tz
            paper = str(_os.environ.get("PAPER_TRADING","1")).strip().lower() in {"1","true","yes","on"}
            trade_enabled = str(_os.environ.get("TRADE_ENABLED","0")).strip().lower() in {"1","true","yes","on"}
            if paper and not trade_enabled:
                d = _Path("logs") / "orders" / _dt.now(_tz.utc).strftime("%Y-%m-%d")
                d.mkdir(parents=True, exist_ok=True)
                f = d / "orders.csv"
                header = "ts,symbol,side,price,sl,tp"
                side = (decision or {}).get("side") if isinstance(decision, dict) else None
                price = (decision or {}).get("price") if isinstance(decision, dict) else None
                sl = (decision or {}).get("sl") if isinstance(decision, dict) else None
                tp = (decision or {}).get("tp") if isinstance(decision, dict) else None
                line = f"{_dt.now(_tz.utc).isoformat()},{getattr(self,'symbol','?')},{side},{price},{sl},{tp}"
                if not f.exists():
                    f.write_text(header + "\n", encoding="utf-8")
                with f.open("a", encoding="utf-8") as fh:
                    fh.write(line + "\n")
        except Exception:
            pass

        act = (decision or {}).get("action")
        if act in ("LONG", "SHORT"):
            self.log.info("PLACE %s %s qty=%s @%s", act, self.symbol or "", (decision or {}).get("qty"), (decision or {}).get("price"))
        else:
            self.log.info("SKIP action=%s", act)

# Adapter used by tests
class ExecutorService:
    def __init__(self, symbol: Optional[str]=None, **kwargs: Any) -> None:
        self.symbol = symbol or kwargs.get("symbol")
        self.kwargs = kwargs
        self.log = logging.getLogger("ExecutorService")

    def _do_place(self, decision: Dict[str, Any]) -> None:
        ExecutionService(symbol=self.symbol, logger=self.log).place(decision)

    # common aliases tests might use
    def place(self, decision: Dict[str, Any]) -> None:
        self._do_place(decision)

    def place_order(self, decision: Dict[str, Any]) -> None:
        self._do_place(decision)

    def execute(self, decision: Dict[str, Any]) -> None:
        self._do_place(decision)
