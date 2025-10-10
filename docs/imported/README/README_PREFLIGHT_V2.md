# Preflight v2

Зміни:
- timezone-aware дати (без DeprecationWarning)
- консольний підсумок (які саме чеки впали)
- `PRE_FLIGHT_SKIP_API=1` дозволяє **пропустити** `api`/`account`/`drift` (зручно для paper)
- відсутні RISK_* тепер **warning**, а не fail (ризик-модуль має дефолти)

Приклади:
```powershell
# Paper-only перевірка (без реальних ключів)
$env:PRE_FLIGHT_SKIP_API = "1"
$env:SYMBOL = "BTCUSDT"
python .\scripts\preflight_live.py

# Повна перевірка перед live
$env:PRE_FLIGHT_SKIP_API = "0"
$env:BINANCE_API_KEY = "<key>"
$env:BINANCE_API_SECRET = "<secret>"
python .\scripts\preflight_live.py
```
```
FAILED checks: env, api, account   # приклад
{"ok": false, "path": "logs\\preflight\\2025-09-16\\preflight_....json"}
```
