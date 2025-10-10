# Adapter Pack v1 (non-breaking)
Call `build_order()` to get a full payload prepared by position_sizer + risk_guard.

Files:
- `utils/order_adapter.py`                 → library to build order payloads (no sending)
- `scripts/diagnostics/order_preview_cli.py` → CLI wrapper for quick preview

Usage:
```powershell
$env:WALLET_USDT=103; $env:SYMBOL="BTCUSDT"; $env:RISK_MARGIN_FRACTION=0.2; $env:PREFERRED_MAX_LEVERAGE=10
$env:SIDE="BUY"; $env:TYPE="MARKET"
.\.venv\Scripts\python.exe .\scripts\diagnostics\order_preview_cli.py

$env:SIDE="SELL"; $env:TYPE="LIMIT"; $env:PRICE=120000
.\.venv\Scripts\python.exe .\scripts\diagnostics\order_preview_cli.py
```
Integration (example in your order flow):
```python
from utils.order_adapter import build_order
res = build_order("BTCUSDT", "BUY", "MARKET", wallet_usdt,
                  risk_margin_fraction=0.2, preferred_max_leverage=10)
if res["risk_gate"]["can_trade"] and res["order_payload"]:
    payload = res["order_payload"]
    # pass payload to your existing sender/client
```
