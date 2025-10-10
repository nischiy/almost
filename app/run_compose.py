# app/run_compose.py
from __future__ import annotations

import os
import time
import logging
from typing import Optional

from .bootstrap import resolve_runtime_mode, compose_trader_app


def _setup_console_logging(level: str = "INFO"):
    lvl = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=lvl,
        format="[%(asctime)s] %(levelname)s %(name)s: %(message)s"
    )


def main(run_once: Optional[bool] = None):
    cfg = resolve_runtime_mode()
    _setup_console_logging(cfg.log_level)
    log = logging.getLogger("Runner")

    # Якщо передано через аргумент — поважаємо; інакше читаємо з ENV або дефолт
    if run_once is None:
        run_once = os.environ.get("RUN_ONCE", "0") in ("1", "true", "True", "yes", "on")

    app = compose_trader_app(cfg)

    # TraderApp може мати методи start()/run_once(). Перевіримо обережно.
    has_run_once = hasattr(app, "run_once") and callable(getattr(app, "run_once"))
    has_start = hasattr(app, "start") and callable(getattr(app, "start"))

    if run_once and has_run_once:
        log.info("Running single iteration (one-shot).")
        try:
            app.run_once()
        except Exception as e:
            log.exception("One-shot iteration failed: %s", e)
        return

    if has_start:
        log.info("Starting main loop via TraderApp.start()")
        try:
            app.start()
        except KeyboardInterrupt:
            log.info("Interrupted by user. Exiting gracefully.")
        except Exception as e:
            log.exception("TraderApp.start() failed: %s", e)
        return

    # Фолбек: якщо немає start(), але є run_once(), організуємо простий цикл тут.
    if has_run_once:
        log.info("Starting loop (fallback) using run_once() + sleep=%.3fs", cfg.loop_sleep_sec)
        try:
            while True:
                app.run_once()
                time.sleep(cfg.loop_sleep_sec)
        except KeyboardInterrupt:
            log.info("Interrupted by user. Exiting gracefully.")
        except Exception as e:
            log.exception("Loop failed: %s", e)
        return

    # Якщо ми тут — у TraderApp немає жодного очікуваного методу
    raise RuntimeError("TraderApp has neither .start() nor .run_once() methods.")


if __name__ == "__main__":
    main()
