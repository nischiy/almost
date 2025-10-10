# Position Sizer Add-on (non-breaking)
This bundle adds adaptive sizing that calibrates **qty + leverage** to your *actual* wallet balance.
- No order placement, no side effects.
- Intended to be called from your order path; returns `(qty, leverage, meta)`.

Files:
- `utils/position_sizer.py` — core logic (public price/filters; inject balance provider)
- `scripts/diagnostics/leverage_sizer_cli.py` — CLI to preview the result

Quick start (CLI, using live project balance if available):
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\tools\safe_ops.ps1 preflight
.\.venv\Scripts\python.exe .\scripts\diagnostics\leverage_sizer_cli.py
```

Or force wallet via ENV:
```powershell
$env:WALLET_USDT=103
$env:SYMBOL='BTCUSDT'
$env:RISK_MARGIN_FRACTION=0.2
$env:PREFERRED_MAX_LEVERAGE=10
.\.venv\Scripts\python.exe .\scripts\diagnostics\leverage_sizer_cli.py
```

Integrate in code (example):
```python
from utils.position_sizer import compute_qty_leverage, SizerConfig
wallet_usdt = live_balance_usdt()  # <- your function
cfg = SizerConfig(risk_margin_fraction=0.2, preferred_max_leverage=10, desired_pos_usdt=None)
res = compute_qty_leverage("BTCUSDT", wallet_usdt, cfg=cfg)
qty, lev = res.qty, res.leverage
# Use qty, lev to prepare order, SL/TP sizing, etc. No exchange calls done here.
```
