
# Maintenance bundle (tests warnings + cleanup)

## Що входить
- `scripts/tests/silence_warnings.ps1` — прибирає Deprecation/FutureWarning у тестах:
  - `datetime.utcnow()` -> `datetime.now(datetime.UTC)`
  - частота `freq="T"` -> `freq="min"`
- `scripts/maintenance/clean_patch_artifacts.ps1` — видаляє тимчасові патч-скрипти та бекапи:
  - `scripts/patch_*.ps1`, `scripts/fix_*.ps1`, старі органайзери, `_backup_*.zip`, `*.bak.*`

## Як застосувати
```powershell
cd G:\Bot\almost

# 1) Прибрати варнінги у тестах
powershell -ExecutionPolicy Bypass -File .\scripts\tests\silence_warnings.ps1 -ProjectRoot .

# 2) Подивитись список видалення (сухий прогон)
powershell -ExecutionPolicy Bypass -File .\scripts\maintenance\clean_patch_artifacts.ps1 -ProjectRoot . -WhatIf

# 3) Видалити фактично
powershell -ExecutionPolicy Bypass -File .\scripts\maintenance\clean_patch_artifacts.ps1 -ProjectRoot .
```
