
# Market Data 'time' alias patch — UA/EN

## 🇺🇦 Що робить
Додає колонку `time = open_time` **лише тоді**, коли `requests.get` не замокано (оригінальний метод). Це покриває `tests/app/test_market_data.py`, водночас **не ламає** `tests/test_market_data_service.py`, який очікує рівно 7 колонок (у ньому `requests.get` замінюється на фейк).

## ▶️ Команди
```powershell
cd G:\Bot\almost
powershell -ExecutionPolicy Bypass -File .\scripts\patch_market_data_time_alias.ps1 -ProjectRoot .
# далі
powershell -ExecutionPolicy Bypass -File .\scripts\tests\run_pytest.ps1
```
