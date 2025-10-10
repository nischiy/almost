# Position Sizer Add-on v2 (non-breaking)
Adds robust `utils/position_sizer.py` + path-safe diagnostics:
- `scripts/diagnostics/leverage_sizer_cli.py`  → CLI using `WALLET_USDT`
- `scripts/diagnostics/qty_guard_example.py`  → dry-run guard demo before order

Quick start:
```powershell
$env:WALLET_USDT=103
$env:SYMBOL="BTCUSDT"
$env:RISK_MARGIN_FRACTION=0.2
$env:PREFERRED_MAX_LEVERAGE=10
.\.venv\Scripts\python.exe .\scripts\diagnostics\leverage_sizer_cli.py
.\.venv\Scripts\python.exe .\scripts\diagnostics\qty_guard_example.py
```

Integrate (pseudo-code in your order path):
```python
from utils.position_sizer import compute_qty_leverage, SizerConfig
wallet_usdt = live_balance_usdt()  # your real balance provider
cfg = SizerConfig(risk_margin_fraction=0.20, preferred_max_leverage=10, desired_pos_usdt=None)
res = compute_qty_leverage("BTCUSDT", wallet_usdt, cfg=cfg)
qty, lev = res.qty, res.leverage
# Proceed to build order with qty & leverage
```
