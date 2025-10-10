
# Fix timezone: datetime.UTC -> timezone.utc

## Що робить
Править `tests/conftest.py`, щоб використовувати сумісний варіант `timezone.utc` і додає `from datetime import timezone`, якщо імпорту бракує.

## Команди
```powershell
cd G:\Bot\almost
powershell -ExecutionPolicy Bypass -File .\scripts\tests\fix_timezone_utc.ps1 -ProjectRoot .
powershell -ExecutionPolicy Bypass -File .\scripts\tests\run_pytest.ps1
```
