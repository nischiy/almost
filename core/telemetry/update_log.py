from __future__ import annotations
from pathlib import Path
from typing import Iterable, List, Optional, Union
from datetime import datetime, timezone
import json
import os

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _as_list(x: Union[str, Iterable[str]]) -> List[str]:
    if isinstance(x, str):
        return [x]
    return [str(i) for i in x]

def log_update(step: str, files: Union[str, Iterable[str]], notes: str = "", tags: Optional[Iterable[str]] = None) -> None:
    """Write a single changelog entry into logs/updates as JSONL and Markdown.

    - JSONL path: logs/updates/YYYY-MM-DD/updates.jsonl
    - Markdown path: logs/updates/CHANGELOG.md (append-only, human-readable)
    """
    day = datetime.utcnow().strftime("%Y-%m-%d")
    base = Path("logs") / "updates" / day
    base.mkdir(parents=True, exist_ok=True)
    jsonl = base / "updates.jsonl"
    md = Path("logs") / "updates" / "CHANGELOG.md"

    entry = {
        "ts": _now_iso(),
        "step": step.strip(),
        "files": _as_list(files),
        "notes": notes.strip(),
        "tags": list(tags) if tags is not None else [],
        "by": "assistant"  # marker who added
    }

    # JSONL
    with jsonl.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # Markdown
    md.parent.mkdir(parents=True, exist_ok=True)
    with md.open("a", encoding="utf-8") as f:
        f.write(f"- {entry['ts']} — **{entry['step']}** — files: {', '.join(entry['files'])}" + ("\n" if not entry["notes"] else f"\n  - {entry['notes']}\n"))
