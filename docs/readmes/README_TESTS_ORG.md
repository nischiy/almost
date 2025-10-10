
# Clean Tests Layout — update

- Тепер є **окремий** раннер для pytest: `scripts/tests/run_pytest.ps1`.
- Твій існуючий `scripts/run_tests.ps1` (unittest) перенесено в `scripts/tests/run.ps1` і НЕ перезаписано.
- Жодних дублів `conftest.py` по підпапках.

## ▶️ Команди
```powershell
cd G:\Bot\almost
# Організувати структуру (оновлена версія):
powershell -ExecutionPolicy Bypass -File .\scripts\tests\organize_tests.ps1 -ProjectRoot .

# Запустити PYTEST (саме його):
powershell -ExecutionPolicy Bypass -File .\scripts\tests\run_pytest.ps1
```
