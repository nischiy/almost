
# Market Data get_klines shape patch — UA/EN

## 🇺🇦 Що робить
Нормалізує вихід `HttpMarketData.get_klines(...)` до точного набору колонок:
`open_time, open, high, low, close, volume, close_time`. Працює як обгортка навколо твоєї реалізації, не ламаючи її.

## ▶️ Команди
```powershell
cd G:\Bot\almost
powershell -ExecutionPolicy Bypass -File .\scripts\patch_market_data_klines_shape.ps1 -ProjectRoot .
# потім
powershell -ExecutionPolicy Bypass -File .\scripts\tests\run_pytest.ps1
```
