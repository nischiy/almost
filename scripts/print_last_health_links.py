import os, glob, pathlib

ROOT = pathlib.Path(".").resolve()
HEALTH_ROOT = ROOT / "logs" / "health"

if not HEALTH_ROOT.exists():
    print("No health directory found:", HEALTH_ROOT)
    raise SystemExit(0)

# Find latest date folder
date_dirs = sorted([p for p in HEALTH_ROOT.iterdir() if p.is_dir()], reverse=True)
if not date_dirs:
    print("No dated health folders under", HEALTH_ROOT)
    raise SystemExit(0)

latest = date_dirs[0]
jsonl = sorted(latest.glob("health_*.jsonl"), reverse=True)
md = sorted(latest.glob("health_*.md"), reverse=True)

def to_file_uri(p: pathlib.Path) -> str:
    # Windows-safe file URI
    return p.resolve().as_uri()

print("Latest health folder:", latest.resolve())
if jsonl:
    p = jsonl[0].resolve()
    print("JSONL:", p)
    print("JSONL (URI):", to_file_uri(p))
else:
    print("JSONL: not found")

if md:
    p = md[0].resolve()
    print("Markdown:", p)
    print("Markdown (URI):", to_file_uri(p))
else:
    print("Markdown: not found")
