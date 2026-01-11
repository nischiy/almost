from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping, Optional

from core.env_loader import load_env_files, discover_env_files

_DOTENV_STATUS: Optional[bool] = None

_TRUE = {"1", "true", "yes", "y", "on"}
_FALSE = {"0", "false", "no", "n", "off"}


def parse_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in _TRUE:
        return True
    if text in _FALSE:
        return False
    return default


def get_env(name: str, default: Optional[str] = None, env: Optional[Mapping[str, str]] = None) -> Optional[str]:
    source = env if env is not None else os.environ
    return source.get(name, default)


def get_bool(name: str, default: bool = False, env: Optional[Mapping[str, str]] = None) -> bool:
    return parse_bool(get_env(name, None, env=env), default=default)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_dotenv_once(*, override: bool = False) -> bool:
    global _DOTENV_STATUS
    if _DOTENV_STATUS is not None:
        return _DOTENV_STATUS

    if get_bool("DOTENV_DISABLE", False):
        _DOTENV_STATUS = False
        return _DOTENV_STATUS

    root = _repo_root()
    paths = discover_env_files(start=root)
    if paths:
        load_env_files(paths=paths, override=override)
    _DOTENV_STATUS = True if paths else False
    return _DOTENV_STATUS


def dotenv_loaded() -> bool:
    return bool(_DOTENV_STATUS)

