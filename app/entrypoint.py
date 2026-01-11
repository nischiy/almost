from __future__ import annotations
import argparse
import os
import logging
import sys
from typing import Any
from app.bootstrap import compose_trader_app, resolve_runtime_mode
from core.config.env import load_dotenv_once, parse_bool

log = logging.getLogger("AppMain")

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="app.entrypoint", add_help=True)
    p.add_argument("--once", action="store_true")
    paper_group = p.add_mutually_exclusive_group()
    paper_group.add_argument(
        "--paper",
        dest="paper",
        nargs="?",
        const=True,
        default=None,
        type=parse_bool,
        metavar="BOOL",
        help="Enable paper trading (use env by default; optional BOOL like 1/0).",
    )
    paper_group.add_argument(
        "--no-paper",
        dest="paper",
        action="store_false",
        help="Disable paper trading (override env).",
    )
    trade_group = p.add_mutually_exclusive_group()
    trade_group.add_argument(
        "--enabled",
        dest="enabled",
        nargs="?",
        const=True,
        default=None,
        type=parse_bool,
        metavar="BOOL",
        help="Enable trading (use env by default; optional BOOL like 1/0).",
    )
    trade_group.add_argument(
        "--disabled",
        dest="enabled",
        action="store_false",
        help="Disable trading (override env).",
    )
    dry_group = p.add_mutually_exclusive_group()
    dry_group.add_argument(
        "--dry-run",
        dest="dry_run_only",
        nargs="?",
        const=True,
        default=None,
        type=parse_bool,
        metavar="BOOL",
        help="Enable dry-run mode (use env by default; optional BOOL like 1/0).",
    )
    dry_group.add_argument(
        "--live",
        dest="dry_run_only",
        action="store_false",
        help="Disable dry-run mode (override env).",
    )
    p.add_argument("--symbol", type=str, default=None)
    p.add_argument("--strategy", type=str, default=None)
    p.add_argument("--sleep", type=float, default=None, metavar="SECS")
    return p.parse_args(argv)

def _apply_overrides(args: Any) -> None:
    if getattr(args, "sleep", None) is not None:
        os.environ["LOOP_SLEEP_SEC"] = str(args.sleep)
    if getattr(args, "enabled", None) is not None:
        os.environ["TRADE_ENABLED"] = "1" if bool(args.enabled) else "0"
    if getattr(args, "paper", None) is not None:
        os.environ["PAPER_TRADING"] = "1" if bool(args.paper) else "0"
    if getattr(args, "dry_run_only", None) is not None:
        os.environ["DRY_RUN_ONLY"] = "1" if bool(args.dry_run_only) else "0"
    if getattr(args, "symbol", None):
        os.environ["SYMBOL"] = str(args.symbol).upper().strip()
    if getattr(args, "strategy", None):
        os.environ["STRATEGY_NAME"] = str(args.strategy).strip()

def main(argv: list[str] | None = None) -> int:
    load_dotenv_once()
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
    log.info("entrypoint.main() -> composing TraderApp")
    cfg = resolve_runtime_mode()
    app = compose_trader_app(cfg)
    app.start(oneshot=bool(args.once))
    return 0

if __name__ == "__main__":
    sys.exit(main())
