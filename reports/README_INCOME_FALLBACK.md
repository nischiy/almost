# Income Fallback — коли trades порожні

Деякі акаунти/ключі Binance UM Futures не повертають `user_trades`/`futures_account_trades` (або за період угод не було).
Щоб все одно отримати **per-trade CSV** для baseline, цей fallback бере **REALIZED_PNL** та **COMMISSION** з `/fapi/v1/income`
і перетворює кожен запис у "угоду".

- entry_time = exit_time = time
- pnl — як у income
- fees — з COMMISSION із тим же timestamp'ом (коли є)
- symbol — з income
- ціни/кількість пусті (не потрібні для PF/win-rate/MAR/MaxDD)

## Запуск
```
powershell -ExecutionPolicy Bypass -File .\scripts\pull_income_as_trades.ps1 -Days 365
powershell -ExecutionPolicy Bypass -File .\scripts\make_t0_baseline.ps1
```
