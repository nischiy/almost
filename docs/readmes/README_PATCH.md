
# Strategy Import Patch — UA/EN

## 🇺🇦 Що робить
- Автоматично замінює імпорти зі старих шляхів:
  - `core.strategy` або `core.logic.logic`
  → на **`core.logic.ema_rsi_atr`** (або інший модуль, який вкажеш).
- Перед записом робить ZIP-бекап змінених файлів: `_backup_import_patch_YYYYMMDD_HHMMSS.zip`.

## ▶️ Команди
```powershell
cd G:\Bot\almost
# Попередній перегляд (нічого не змінює):
powershell -ExecutionPolicy Bypass -File .\scripts\patch_strategy_imports.ps1 -ProjectRoot . -TargetModule core.logic.ema_rsi_atr -WhatIf
# Застосувати:
powershell -ExecutionPolicy Bypass -File .\scripts\patch_strategy_imports.ps1 -ProjectRoot . -TargetModule core.logic.ema_rsi_atr
# Перевірка:
python .\scripts\diagnostics\verify_strategy_imports.py
```
> За потреби можеш вказати інший модуль у `-TargetModule`.

## 🇬🇧 What it does
- Rewrites `core.strategy` and `core.logic.logic` imports to your single strategy module (default `core.logic.ema_rsi_atr`). Backs up changes.
