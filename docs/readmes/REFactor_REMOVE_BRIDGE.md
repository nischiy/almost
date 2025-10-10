# Remove live_bridge

Видаляє `utils/live_bridge.py` та/або `app/services/bridge.py`, і **інлайнить** виклики `run_once(...)`:
```
df = md.get_klines(symbol, interval, limit=200)
decision = sig.decide(df, params)
if decision.get("action") in ("BUY","SELL","LONG","SHORT"):
    exe.place(decision)
```
Після цього повертається змінна `decision` (якщо виклик був у присвоєнні).

## Запуск
```powershell
cd G:\Bot\almost

# Попередній перегляд:
powershell -ExecutionPolicy Bypass -File .\scripts\refactor\remove_bridge.ps1 -ProjectRoot . -WhatIf

# Застосувати:
powershell -ExecutionPolicy Bypass -File .\scripts\refactor\remove_bridge.ps1 -ProjectRoot .

# Перевірити тести:
powershell -ExecutionPolicy Bypass -File .\scripts\tests\run_pytest.ps1
```
