
# OHLC Normalizer Patch — UA/EN

## 🇺🇦 Що робить
- Додає у `core\logic\ema_rsi_atr.py` безпечний `_atr()` та хелпери для **підбору колонок** OHLC:
  - high/High/H/HighPrice, low/Low/L/LowPrice, close/Close/C/Price/Last
- Якщо немає high/low — використовує `close` як заміну (для smoke-тестів це дає ATR ≈ середнє |Δclose|).

## ▶️ Команди
```powershell
cd G:\Bot\almost

# Попередній перегляд (нічого не змінює):
powershell -ExecutionPolicy Bypass -File .\scripts\patch_ema_ohlc_normalizer.ps1 -ProjectRoot . -WhatIf

# Застосувати:
powershell -ExecutionPolicy Bypass -File .\scripts\patch_ema_ohlc_normalizer.ps1 -ProjectRoot .

# Швидкий smoke:
powershell -ExecutionPolicy Bypass -File .\scripts\diagnostics\smoke_decide.ps1
```
