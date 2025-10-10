
import os
import re
from datetime import datetime, timezone
from typing import Dict, Any, Iterable

def load_env_file(path: str) -> Dict[str, str]:
    data: Dict[str, str] = {}
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$', line)
                if not m:
                    continue
                k, v = m.group(1), m.group(2)
                if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                    v = v[1:-1]
                data[k] = v
    # Overlay with real environment ONLY if value is non-empty
    # Empty strings or whitespace in the OS env will NOT override .env
    for k, v in os.environ.items():
        if v is None:
            continue
        sv = str(v).strip()
        if sv != "":
            data[k] = sv
    return data

def to_bool(x: Any) -> bool:
    if isinstance(x, bool):
        return x
    if x is None:
        return False
    s = str(x).strip().lower()
    return s in {"1","true","yes","y","on"}

def require_keys(env: Dict[str,str], keys: Iterable[str]) -> Dict[str, str]:
    missing = [k for k in keys if not str(env.get(k, "")).strip()]
    return {"ok": len(missing)==0, "missing": missing}

def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def dumps_json(obj: Any) -> str:
    try:
        import orjson
        return orjson.dumps(obj, option=orjson.OPT_INDENT_2).decode("utf-8")
    except Exception:
        import json
        return json.dumps(obj, indent=2, ensure_ascii=False, default=str)

def write_json(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(dumps_json(obj))
