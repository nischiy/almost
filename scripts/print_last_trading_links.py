import pathlib

def to_uri(p: pathlib.Path) -> str:
    return p.resolve().as_uri()

root = pathlib.Path(".").resolve()
health_root = root / "logs" / "health"
if health_root.exists():
    dirs = sorted([p for p in health_root.iterdir() if p.is_dir()], reverse=True)
    if dirs:
        latest = dirs[0]
        jsonl = sorted(latest.glob("health_*.jsonl"), reverse=True)
        md    = sorted(latest.glob("health_*.md"), reverse=True)
        print("Latest health:", latest)
        if jsonl: print("JSONL:", to_uri(jsonl[0]))
        if md:    print("MD:",    to_uri(md[0]))
orders_dir = root / "logs" / "orders"
if orders_dir.exists():
    csvs = sorted(orders_dir.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    if csvs: print("Orders CSV:", to_uri(csvs[0]))
equity_dir = root / "logs" / "equity"
if equity_dir.exists():
    csvs = sorted(equity_dir.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    if csvs: print("Equity CSV:", to_uri(csvs[0]))
