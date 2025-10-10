from __future__ import annotations
import argparse
import os
import logging
import sys
from typing import Any
from app.run import TraderApp  # сумісність

log = logging.getLogger("AppMain")

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="app.entrypoint", add_help=True)
    p.add_argument("--once", action="store_true")
    p.add_argument("--paper", action="store_true")
    p.add_argument("--enabled", action="store_true")
    p.add_argument("--symbol", type=str, default=None)
    p.add_argument("--strategy", type=str, default=None)
    p.add_argument("--sleep", type=float, default=None, metavar="SECS")
    return p.parse_args(argv)

def _apply_overrides(args: Any) -> None:
    if getattr(args, "sleep", None) is not None:
        os.environ["LOOP_SLEEP_SEC"] = str(args.sleep)
    if hasattr(args, "enabled"):
        os.environ["TRADE_ENABLED"] = "1" if bool(args.enabled) else "0"
    if hasattr(args, "paper"):
        os.environ["PAPER_TRADING"] = "1" if bool(args.paper) else "0"
    if getattr(args, "symbol", None):
        os.environ["SYMBOL"] = str(args.symbol).upper().strip()
    if getattr(args, "strategy", None):
        os.environ["STRATEGY_NAME"] = str(args.strategy).strip()

def main(argv: list[str] | None = None) -> int:
    # базова конфігурація логів, щоб бачити в консолі тікі/події
    logging.basicConfig(
        level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,  # щоб не мовчало, навіть якщо щось налаштовано раніше
    )

    if argv is None:
        argv = sys.argv[1:]
    args = _parse_args(argv)
    _apply_overrides(args)

    log = logging.getLogger("AppMain")
    log.info("entrypoint.main() -> constructing TraderApp")
    app = TraderApp()
    app.start(oneshot=bool(args.once))
    return 0

if __name__ == "__main__":
    sys.exit(main())
