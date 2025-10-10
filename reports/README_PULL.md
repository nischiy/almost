# Binance Pull Kit — fetch UM Futures trades and build per‑trade CSV

Коли локальних логів немає, витягуємо історію угод прямо з Binance (UM Futures) і складаємо `logs/trades/trades_exported.csv` для baseline‑метрик.

## Підготовка
1. У `.env` додай ключі:
```
BINANCE_API_KEY=...
BINANCE_API_SECRET=...
# опційно
BINANCE_TESTNET=1   # якщо на тестнеті
```
2. Переконайся, що venv активовано. Скрипт сам поставить `python-binance>=1.0.19`, якщо його нема.

## Запуск
```
powershell -ExecutionPolicy Bypass -File .\scripts\pull_trades_from_binance.ps1 -Days 45
```
(вікно в днях можна змінювати)

Результат:
```
logs	rades	rades_exported.csv
```

## Далі
Запусти baseline:
```
powershell -ExecutionPolicy Bypass -File .\scripts\make_t0_baseline.ps1
```

## Примітки
- Скрипт обходить до ~60 найпопулярніших `*USDT` символів і тягне `user_trades` у вказаному вікні.
- PnL береться із `realizedPnl`, якщо присутній, або рахується приблизно по ціні.
- Якщо за обраний період взагалі не було угод, розшир часове вікно `-Days`.
