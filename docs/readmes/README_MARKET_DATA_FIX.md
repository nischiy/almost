
# Market Data Adapter Hotfix — UA/EN

## 🇺🇦 Що робить
Виправляє блок адаптера у `app\services\market_data.py` (раніше був `try:` без `except/finally` → `SyntaxError`). Замінює на безпечну умову `if 'HttpMarketData' not in globals(): ...`.

## ▶️ Команди
```powershell
cd G:\Bot\almost
powershell -ExecutionPolicy Bypass -File .\scripts\fix_market_data_adapter.ps1 -ProjectRoot .
# потім
powershell -ExecutionPolicy Bypass -File .\scripts\tests\run_pytest.ps1
```
