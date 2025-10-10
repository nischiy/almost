from __future__ import annotations
import argparse
from core.telemetry.update_log import log_update

def main() -> None:
    p = argparse.ArgumentParser(description="Append an update entry to logs/updates")
    p.add_argument("--step", required=True, help="Short title of the change")
    p.add_argument("--files", required=True, help="Comma-separated file paths that changed")
    p.add_argument("--notes", default="", help="Optional notes/details")
    p.add_argument("--tags", default="", help="Comma-separated tags")
    args = p.parse_args()

    files = [s.strip() for s in args.files.split(",") if s.strip()]
    tags = [s.strip() for s in args.tags.split(",") if s.strip()]
    log_update(step=args.step, files=files, notes=args.notes, tags=tags)

if __name__ == "__main__":
    main()
