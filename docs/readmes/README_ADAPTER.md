
# Strategy Adapter (v2) — UA/EN

## 🇺🇦 Що змінено
- Виправлено парсинг у PowerShell (here-string)
- Акуратне делегування до наявної функції в модулі (якщо є)
- Додано коректний `sys.path` у діагностиці, щоб уникнути `ModuleNotFoundError: core`

## ▶️ Команди
```powershell
cd G:\Bot\almost

# Попередній перегляд
powershell -ExecutionPolicy Bypass -File .\scripts\patch_strategy_adapter.ps1 -ProjectRoot . -WhatIf

# Застосувати
powershell -ExecutionPolicy Bypass -File .\scripts\patch_strategy_adapter.ps1 -ProjectRoot .

# Перевірити
python -c "import core.logic.ema_rsi_atr as s; print('OK:', any(hasattr(s, n) for n in ('Strategy','decide','signal')))"
python -c "import core.logic.ema_rsi_atr as s; print([n for n in ('Strategy','decide','signal') if hasattr(s,n)])"

# Діагностика
python .\scripts\diagnostics\inspect_strategy_module.py
```
