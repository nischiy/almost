
# MarketData base_url hotpatch — UA/EN

## 🇺🇦 Що робить
Акуратно монкіпатчить існуючий `HttpMarketData.__init__`, щоб він приймав `base_url=...` як kwargs, навіть якщо оригінальна сигнатура його не має. Оригінальний конструктор викликається як є; зайві аргументи проковтуються без падіння.

## ▶️ Команди
```powershell
cd G:\Bot\almost
powershell -ExecutionPolicy Bypass -File .\scripts\patch_market_data_baseurl.ps1 -ProjectRoot .
# Потім:
powershell -ExecutionPolicy Bypass -File .\scripts\tests\run_pytest.ps1
```
