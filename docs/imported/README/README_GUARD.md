# Guard Pack (Kill-Switch + Health-Loop)

## Запуск
```
powershell -ExecutionPolicy Bypass -File .\scripts\start_guard.ps1
```
Зупинка:
```
powershell -ExecutionPolicy Bypass -File .\scripts\stop_guard.ps1
```

## Поведінка
- **Kill-Switch** читає `logs/trades/trades_exported.csv` і дивиться **сьогоднішні** угоди.
  - тригери: `RISK_MAX_LOSS_USD_DAY`, `RISK_MAX_CONSEC_LOSSES`, `RISK_MAX_TRADES_PER_DAY`,
    `RISK_MAX_DD_PCT_DAY` (якщо задано `CURRENT_EQUITY_USD`).
  - при спрацюванні пише `run/TRADE_KILLED.flag` з причиною.
- **Health-Loop** логгує пінг біржі, стежить за свіжістю `logs/decisions` та довгими паузами.

## Логи/артефакти
- `logs/health/kill_switch.log`
- `logs/health/health_loop.log`
- `logs/health/heartbeat.json`
- `run/TRADE_KILLED.flag` (JSON)
- `run/STOP_GUARD.flag` для м’якої зупинки

## Налаштування
У `.env` вже є більшість ключів. Додатково можна вказати:
```
CURRENT_EQUITY_USD=1000
```
щоб увімкнути контроль `RISK_MAX_DD_PCT_DAY`.
