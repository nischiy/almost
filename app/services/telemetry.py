from __future__ import annotations
from typing import Any, Optional
import logging
import pandas as pd

from core.telemetry.health import log_health as _core_health  # type: ignore

class TelemetryService:
    def __init__(self, cfg=None, logger: Optional[logging.Logger]=None):
        self.cfg = cfg
        self.log = logger or logging.getLogger("Telemetry")

    def health(self, ok: bool=True, msg: str="", **extra: Any) -> None:
        try:
            _core_health(ok=ok, msg=msg, **extra)
        except Exception as e:
            self.log.info("[HEALTH] ok=%s %s extra=%s err=%s", ok, msg, extra, e)

    def snapshot(self, df: pd.DataFrame) -> None:
        try:
            # no heavy work; rely on core fallbacks from TraderApp if needed
            pass
        except Exception:
            pass

    def decision(self, data: dict) -> None:
        try:
            # no heavy work; rely on core fallbacks from TraderApp if needed
            pass
        except Exception:
            pass
