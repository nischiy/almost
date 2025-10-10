
# Tests & Execution Adapter Patch — UA/EN

## 🇺🇦 Що входить
- **tests/conftest.py**: єдиний bootstrap + фікстура `df_klines` (OHLCV DataFrame).
- **scripts/patch_tests_and_exec.ps1**: додає в `app\services\execution.py` клас **ExecutorService** (легкий адаптер, що делегує до модульних функцій, якщо вони є).
- **scripts/tests/run_pytest.ps1**: явний раннер pytest.

## ▶️ Команди
```powershell
cd G:\Bot\almost
# 1) Розпакуй архів поверх проєкту
# 2) Додай ExecutorService (створює бекап):
powershell -ExecutionPolicy Bypass -File .\scripts\patch_tests_and_exec.ps1 -ProjectRoot .
# 3) Запусти pytest
powershell -ExecutionPolicy Bypass -File .\scripts\tests\run_pytest.ps1
```
Очікування: колекція тестів проходить, помилка з імпортом **ExecutorService** зникає, фікстура `df_klines` стає доступною.
