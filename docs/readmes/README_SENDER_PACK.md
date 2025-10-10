# Sender Adapter Pack v1 (non-breaking, safe by default)
This pack adds a network sender (Binance Futures REST) that consumes our order payload.
By default it does **NOT** send orders: `DRY_RUN_ONLY=1` (preview only).

Files:
- `utils/signer.py`                → HMAC SHA256 signer for Binance
- `utils/sender_adapter.py`        → `place_order_via_rest(...)`, `set_leverage_via_rest(...)`
- `scripts/diagnostics/order_send_cli.py` → one-shot CLI using the adapter

Quick start (preview only):
```powershell
$env:WALLET_USDT=103; $env:SYMBOL="BTCUSDT"; $env:SIDE="BUY"; $env:TYPE="MARKET"
$env:RISK_MARGIN_FRACTION=0.2; $env:PREFERRED_MAX_LEVERAGE=10
.\.venv\Scripts\python.exe .\scripts\diagnostics\order_send_cli.py
```

Live send (dangerous; use at your own risk; START ON TESTNET):
```powershell
$env:BINANCE_FAPI_BASE="https://testnet.binancefuture.com"
$env:API_KEY="..."; $env:API_SECRET="..."; $env:DRY_RUN_ONLY=0
$env:WALLET_USDT=103; $env:SYMBOL="BTCUSDT"; $env:SIDE="BUY"; $env:TYPE="MARKET"
.\.venv\Scripts\python.exe .\scripts\diagnostics\order_send_cli.py
```

Outputs:
- Always writes a preview JSON under `logs/orders/YYYYMMDD/preview_*.json`
- If sent, writes execution JSON under `logs/orders/YYYYMMDD/sent_*.json`
- CLI prints absolute paths and `file:///` URIs.
